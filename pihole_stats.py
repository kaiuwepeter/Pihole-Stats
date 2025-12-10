#!/usr/bin/env python3
"""
Pi-hole Statistics Fetcher
Ruft Statistiken vom Pi-hole Dashboard ab und schreibt sie in eine Textdatei
Pi-hole api docs: http://pi-hole-ip:port/api/docs/
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

            # SID und CSRF extrahieren falls vorhanden
            sid = login_data_response.get('session', {}).get('sid')
            csrf = login_data_response.get('session', {}).get('csrf')
            if sid:
                print(f"Session ID: {sid[:20]}...")
                session.headers.update({"X-FTL-SID": sid})
                if csrf:
                    session.headers.update({"X-FTL-CSRF": csrf})
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
            print(f"[OK] Summary erfolgreich abgerufen")
        else:
            print(f"[FEHLER] Summary Fehler: {response.status_code}")
    except Exception as e:
        print(f"[FEHLER] Summary Fehler: {e}")

    # 2. Top Clients abrufen
    print("Rufe Top Clients ab...")
    try:
        url = f"{PIHOLE_URL}/api/stats/top_clients"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            all_data['top_clients'] = response.json()
            print(f"[OK] Top Clients erfolgreich abgerufen")
        else:
            print(f"[FEHLER] Top Clients Fehler: {response.status_code}")
    except Exception as e:
        print(f"[FEHLER] Top Clients Fehler: {e}")

    # 3. Client-Informationen (mit Namen) abrufen
    print("Rufe Client-Informationen ab...")
    try:
        url = f"{PIHOLE_URL}/api/clients"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            all_data['clients_info'] = response.json()
            print(f"[OK] Client-Informationen abgerufen")
        else:
            print(f"[FEHLER] Clients Info: {response.status_code}")
    except Exception as e:
        print(f"[FEHLER] Clients Info: {e}")

    # 3b. Netzwerk-Geräte (MAC zu IP Mapping) abrufen
    print("Rufe Netzwerk-Geräte ab...")
    try:
        url = f"{PIHOLE_URL}/api/network/devices"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            all_data['network_devices'] = response.json()
            print(f"[OK] Netzwerk-Geräte abgerufen")
        else:
            print(f"[FEHLER] Netzwerk-Geräte: {response.status_code}")
    except Exception as e:
        print(f"[FEHLER] Netzwerk-Geräte: {e}")

    # 4. Top Blocked Clients abrufen
    print("Rufe Top Blocked Clients ab...")
    try:
        url = f"{PIHOLE_URL}/api/stats/top_clients"
        response = session.get(url, params={"blocked": "true"}, timeout=10)

        if response.status_code == 200:
            all_data['top_blocked_clients'] = response.json()
            print(f"[OK] Top Blocked Clients abgerufen")
        else:
            print(f"[FEHLER] Top Blocked Clients: {response.status_code}")
    except Exception as e:
        print(f"[FEHLER] Top Blocked Clients: {e}")

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
        network_devices_data = stats.get('network_devices', {})
        top_blocked_clients_data = stats.get('top_blocked_clients', {})

        # Client-Namen und Blockierungs-Mapping erstellen
        client_names_map = {}  # IP -> Name
        mac_to_name_map = {}   # MAC -> Name
        mac_to_ip_map = {}     # MAC -> IP
        client_blocked_map = {}

        # 1. MAC zu Name Mapping aus clients_info erstellen
        if clients_info_data:
            clients_list = clients_info_data.get('clients', [])

            for client in clients_list:
                if isinstance(client, dict):
                    client_id = client.get('client', '').lower()  # MAC oder IP
                    comment = client.get('comment', '')
                    name = comment or client.get('name', '') or client.get('hostname', '')

                    if client_id and name:
                        # Prüfe ob es eine IP ist (enthält Punkte)
                        if '.' in client_id:
                            client_names_map[client_id] = name
                        # Sonst ist es eine MAC-Adresse (enthält Doppelpunkte)
                        elif ':' in client_id:
                            mac_to_name_map[client_id] = name

        # 2. MAC zu IP Mapping aus network_devices erstellen
        if network_devices_data:
            devices = network_devices_data.get('devices', [])

            for device in devices:
                if isinstance(device, dict):
                    mac = device.get('hwaddr', '').lower()
                    ips = device.get('ips', [])

                    # Für jede IP die zu dieser MAC gehört
                    for ip_data in ips:
                        if isinstance(ip_data, dict):
                            ip = ip_data.get('ip', '')
                            if mac and ip:
                                mac_to_ip_map[mac] = ip

        # 3. IP zu Name Mapping erstellen (MAC -> Name + MAC -> IP = IP -> Name)
        for mac, name in mac_to_name_map.items():
            if mac in mac_to_ip_map:
                ip = mac_to_ip_map[mac]
                client_names_map[ip] = name

        # Blockierungs-Daten aus top_blocked_clients extrahieren
        if top_blocked_clients_data:
            blocked_clients = top_blocked_clients_data.get('clients', [])

            for blocked_client in blocked_clients:
                if isinstance(blocked_client, dict):
                    ip = blocked_client.get('ip', '')
                    blocked_count = blocked_client.get('count', 0)
                    name = blocked_client.get('name', '')

                    if ip:
                        client_blocked_map[ip] = blocked_count

                    # Namen hinzufügen falls vorhanden
                    if name and ip and ip not in client_names_map:
                        client_names_map[ip] = name

        # Top Clients extrahieren
        top_clients = top_clients_data.get('clients', [])

        # Namen und Blockierungen zu Top Clients hinzufügen
        for client in top_clients:
            if isinstance(client, dict):
                ip = client.get('ip', '')

                # Namen setzen
                if ip in client_names_map:
                    client['display_name'] = client_names_map[ip]
                elif client.get('name'):
                    client['display_name'] = client['name']
                else:
                    client['display_name'] = ip

                # Blockierte Queries setzen
                client['blocked'] = client_blocked_map.get(ip, 0)

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
                client_blocked = client.get('blocked', 0)
                client_ip = client.get('ip', '')

                # Wenn Name und IP unterschiedlich sind, zeige beides
                if client_name != client_ip and client_ip:
                    top_clients_text += f"{i}. **{client_name}** ({client_ip})\n"
                else:
                    top_clients_text += f"{i}. **{client_name}**\n"

                # Queries und Blockierungen anzeigen
                top_clients_text += f"   └ {format_number(client_queries)} queries | {format_number(client_blocked)} blocked\n"
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
            print("[OK] Discord Webhook erfolgreich gesendet!")
            return True
        else:
            print(f"[FEHLER] Discord Webhook Fehler: Status Code {response.status_code}")
            print(f"Antwort: {response.text}")
            return False

    except Exception as e:
        print(f"[FEHLER] Fehler beim Senden des Discord Webhooks: {e}")
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
