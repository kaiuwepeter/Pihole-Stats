#!/usr/bin/env python3
"""
Pi-hole Statistics Fetcher
Ruft Statistiken vom Pi-hole Dashboard ab und schreibt sie in eine Textdatei
"""

import requests
import json
import hashlib
from datetime import datetime, timezone

# Konfiguration
PIHOLE_URL = "PiHole-URL:Port"
PASSWORD = "PiHole-AdminPassword"
OUTPUT_FILE = "pihole_stats.txt"
DISCORD_WEBHOOK_URL = "Discord-WebhookURL"

def get_api_token(password):
    """Erstellt API Token aus Passwort (double SHA256 hash)"""
    hash1 = hashlib.sha256(password.encode()).hexdigest()
    hash2 = hashlib.sha256(hash1.encode()).hexdigest()
    return hash2

def get_pihole_stats():
    """Ruft die Pi-hole Statistiken ab"""
    # Generiere API Token
    api_token = get_api_token(PASSWORD)

    print(f"Verbinde mit: {PIHOLE_URL}")
    print(f"API Token: {api_token[:20]}...")
    print()

    # Session erstellen und Login durchführen
    session = requests.Session()

    print("Login durchführen...")
    try:
        # Login mit Session
        login_url = f"{PIHOLE_URL}/api/auth"
        login_data = {"password": PASSWORD}
        headers = {"Content-Type": "application/json"}

        login_response = session.post(login_url, json=login_data, headers=headers, timeout=10)
        print(f"Login Status Code: {login_response.status_code}")

        if login_response.status_code == 200:
            print("Login erfolgreich!")
            login_data_response = login_response.json()
            print(f"Login Antwort: {json.dumps(login_data_response, indent=2)[:300]}")

            # SID extrahieren falls vorhanden
            sid = login_data_response.get('session', {}).get('sid')
            if sid:
                print(f"Session ID: {sid[:20]}...")
                session.headers.update({"X-FTL-SID": sid})
        else:
            print(f"Login Antwort: {login_response.text[:300]}")
    except Exception as e:
        print(f"Login Fehler: {e}")

    print()

    # Sammle alle benötigten Daten
    all_data = {}

    # 1. Summary Statistiken abrufen
    print("Rufe Summary-Statistiken ab...")
    try:
        url = f"{PIHOLE_URL}/api/stats/summary"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            all_data['summary'] = response.json()
            print(f"✓ Summary erfolgreich abgerufen")
        else:
            print(f"✗ Summary Fehler: {response.status_code}")
    except Exception as e:
        print(f"✗ Summary Fehler: {e}")

    # 2. Top Clients abrufen
    print("Rufe Top Clients ab...")
    try:
        url = f"{PIHOLE_URL}/api/stats/top_clients"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            all_data['top_clients'] = response.json()
            print(f"✓ Top Clients erfolgreich abgerufen")
        else:
            print(f"✗ Top Clients Fehler: {response.status_code}")
    except Exception as e:
        print(f"✗ Top Clients Fehler: {e}")

    # 3. Client-Informationen (mit Namen) abrufen
    print("Rufe Client-Informationen ab...")
    client_endpoints = [
        "/api/clients",
        "/api/network/clients",
        "/api/dns/clients"
    ]

    for endpoint in client_endpoints:
        try:
            url = f"{PIHOLE_URL}{endpoint}"
            response = session.get(url, timeout=10)

            if response.status_code == 200:
                all_data['clients_info'] = response.json()
                print(f"✓ Client-Informationen von {endpoint} abgerufen")
                print(f"  Datenstruktur: {json.dumps(response.json(), indent=2)[:500]}")
                break
            else:
                print(f"  {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"  {endpoint}: Fehler - {e}")

    print()

    if all_data.get('summary'):
        return all_data

    return None

def send_discord_webhook(stats):
    """Sendet die Statistiken als Discord Embed"""
    if not stats:
        print("Keine Daten für Discord verfügbar")
        return False

    try:
        # Neue API-Struktur verarbeiten
        summary = stats.get('summary', {})
        queries_data = summary.get('queries', {})
        gravity_data = summary.get('gravity', {})
        clients_data = summary.get('clients', {})

        # Werte extrahieren
        total_queries = queries_data.get('total', 0)
        queries_blocked = queries_data.get('blocked', 0)
        domains_on_list = gravity_data.get('domains_being_blocked', 0)
        active_clients = clients_data.get('active', 0)

        # Top Clients verarbeiten
        top_clients_data = stats.get('top_clients', {})
        clients_info_data = stats.get('clients_info', {})

        # Client-Namen Mapping erstellen
        client_names_map = {}
        if clients_info_data:
            # Versuche verschiedene Strukturen
            clients_list = (
                clients_info_data.get('clients', []) or
                clients_info_data.get('data', []) or
                []
            )

            # Falls es ein Dict ist, versuche es zu konvertieren
            if isinstance(clients_list, dict):
                temp_list = []
                for key, value in clients_list.items():
                    if isinstance(value, dict):
                        value['id'] = key
                        temp_list.append(value)
                clients_list = temp_list

            # Erstelle Mapping von IP/MAC zu Name
            for client in clients_list:
                if isinstance(client, dict):
                    # 'client' kann IP oder MAC sein
                    client_id = client.get('client', '')
                    comment = client.get('comment', '')

                    # Name aus verschiedenen Feldern (comment hat Priorität)
                    name = comment or client.get('name', '') or client.get('hostname', '')

                    if client_id and name:
                        client_names_map[client_id] = name

                    # Auch alternative Felder versuchen
                    ip = client.get('ip', '')
                    mac = client.get('mac', '')
                    if ip and name:
                        client_names_map[ip] = name
                    if mac and name:
                        client_names_map[mac] = name

        # Top Clients extrahieren
        top_clients = top_clients_data.get('clients', [])

        # Namen zu Top Clients hinzufügen
        for client in top_clients:
            if isinstance(client, dict):
                ip = client.get('ip', '')
                # Verwende den Namen aus dem Mapping, falls vorhanden
                if ip in client_names_map:
                    client['display_name'] = client_names_map[ip]
                elif client.get('name'):
                    client['display_name'] = client['name']
                else:
                    client['display_name'] = ip

        # Percentage berechnen
        if total_queries > 0:
            percentage_blocked = (queries_blocked / total_queries) * 100
        else:
            percentage_blocked = 0

        # Zahlen formatieren
        def format_number(num):
            if isinstance(num, (int, float)):
                return f"{int(num):,}".replace(',', '.')
            return str(num)

        # Farbe basierend auf Blockrate
        if percentage_blocked >= 50:
            color = 0x2ecc71  # Grün - hohe Blockrate
        elif percentage_blocked >= 25:
            color = 0xf39c12  # Orange - mittlere Blockrate
        else:
            color = 0xe74c3c  # Rot - niedrige Blockrate

        # Top 4 Clients formatieren
        top_clients_text = ""
        if top_clients and len(top_clients) > 0:
            for i, client in enumerate(top_clients[:4], 1):
                client_name = client.get('display_name', client.get('ip', 'Unknown'))
                client_queries = client.get('count', 0)
                client_ip = client.get('ip', '')

                # Wenn Name und IP unterschiedlich sind, zeige beides
                if client_name != client_ip and client_ip:
                    top_clients_text += f"{i}. **{client_name}** ({client_ip}) - {format_number(client_queries)} queries\n"
                else:
                    top_clients_text += f"{i}. **{client_name}** - {format_number(client_queries)} queries\n"
        else:
            top_clients_text = "Keine Client-Daten verfügbar"

        # Discord Embed erstellen
        embed = {
            "title": "📊 Pi-hole Statistiken",
            "description": f"Aktuelle DNS-Filterstatistiken von deinem Pi-hole Server",
            "color": color,
            "fields": [
                {
                    "name": "🔍 Total Queries",
                    "value": f"```{format_number(total_queries)}```",
                    "inline": True
                },
                {
                    "name": "🛡️ Queries Blocked",
                    "value": f"```{format_number(queries_blocked)}```",
                    "inline": True
                },
                {
                    "name": "📈 Block Rate",
                    "value": f"```{percentage_blocked:.1f} %```",
                    "inline": True
                },
                {
                    "name": "📋 Domains on List",
                    "value": f"```{format_number(domains_on_list)}```",
                    "inline": True
                },
                {
                    "name": "👥 Active Clients",
                    "value": f"```{format_number(active_clients)}```",
                    "inline": True
                },
                {
                    "name": "⚡ Status",
                    "value": "```Online```",
                    "inline": True
                },
                {
                    "name": "🏆 Top 4 Clients",
                    "value": top_clients_text,
                    "inline": False
                }
            ],
            "thumbnail": {
                "url": "https://pi-hole.net/wp-content/uploads/2016/12/Vortex-R.png"
            },
            "footer": {
                "text": "Pi-hole Stats Monitor",
                "icon_url": "https://pi-hole.net/wp-content/uploads/2016/12/Vortex-R.png"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Webhook Payload
        payload = {
            "username": "Pi-hole Monitor",
            "avatar_url": "https://pi-hole.net/wp-content/uploads/2016/12/Vortex-R.png",
            "embeds": [embed]
        }

        # An Discord senden
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 204:
            print("✅ Discord Webhook erfolgreich gesendet!")
            return True
        else:
            print(f"❌ Discord Webhook Fehler: Status Code {response.status_code}")
            print(f"Antwort: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Fehler beim Senden des Discord Webhooks: {e}")
        import traceback
        traceback.print_exc()
        return False


def write_stats_to_file(stats):
    """Schreibt die Statistiken in eine Textdatei"""
    if not stats:
        print("Keine Daten verfügbar")
        return

    try:
        # Neue API-Struktur verarbeiten
        summary = stats.get('summary', {})
        queries_data = summary.get('queries', {})
        gravity_data = summary.get('gravity', {})

        # Werte extrahieren - neue API-Struktur
        total_queries = queries_data.get('total', 0)
        queries_blocked = queries_data.get('blocked', 0)
        domains_on_list = gravity_data.get('domains_being_blocked', 0)

        # Percentage berechnen
        if total_queries > 0:
            percentage_blocked = (queries_blocked / total_queries) * 100
        else:
            percentage_blocked = 0

        # Zahlen formatieren
        def format_number(num):
            if isinstance(num, (int, float)):
                return f"{int(num):,}".replace(',', '.')
            return str(num)

        # Text formatieren
        output_text = (
            f"Total Queries: {format_number(total_queries)} | "
            f"Queries Blocked: {format_number(queries_blocked)} | "
            f"Percentage Blocked: {percentage_blocked:.1f} % | "
            f"Domains in List: {format_number(domains_on_list)}"
        )

        # Timestamp hinzufügen
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_output = f"[{timestamp}] {output_text}\n"

        # In Datei schreiben (append mode = anhängen)
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(full_output)

        print(f"\nStatistiken erfolgreich in '{OUTPUT_FILE}' hinzugefügt:")
        print(output_text)

    except Exception as e:
        print(f"Fehler beim Schreiben der Datei: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Hauptfunktion"""
    print("Pi-hole Statistiken werden abgerufen...")
    stats = get_pihole_stats()

    if stats:
        # Statistiken in Datei schreiben
        write_stats_to_file(stats)

        # Discord Webhook senden
        print("\n" + "="*50)
        print("Discord Webhook wird gesendet...")
        print("="*50)
        send_discord_webhook(stats)
    else:
        print("Konnte keine Statistiken abrufen.")

if __name__ == "__main__":
    main()
