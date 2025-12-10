# Pi-hole Statistics Monitor  

<img width="491" height="438" alt="image" src="https://github.com/user-attachments/assets/0479178f-7935-466e-9d43-11f74c754a60" />


[English Version / Englische Version](README.md)

Ein Python-Script, das automatisch Statistiken von einem Pi-hole Server abruft, sie in eine Textdatei schreibt und optional via Discord Webhook als formatiertes Embed versendet.

## Features

- **Automatischer Statistik-Abruf**: Ruft aktuelle DNS-Filterstatistiken von deinem Pi-hole Server ab
- **Textdatei-Logging**: Speichert alle Statistiken mit Zeitstempel in einer Textdatei
- **Discord Integration**: Sendet formatierte Embeds mit Statistiken an einen Discord-Channel
- **Top Clients Anzeige**: Zeigt die Top 4 aktivsten Clients mit ihren Namen und Query-Anzahl
- **Farbcodierte Status-Anzeige**: Grün (>50% Blockrate), Orange (25-50%), Rot (<25%)
- **Deutsche Formatierung**: Zahlen mit Punkten als Tausendertrennzeichen

## Voraussetzungen

- Python 3.x
- Pi-hole Server (erreichbar über HTTP/HTTPS)
- Pi-hole Admin-Passwort
- (Optional) Discord Webhook URL für Benachrichtigungen

## Installation

### 1. Repository klonen oder Dateien herunterladen

```bash
git clone <repository-url>
cd Pihole-Stats
```

### 2. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Benötigte Pakete:**
- `requests==2.31.0`

## Konfiguration

Öffne die Datei `pihole_stats.py` und passe folgende Variablen an (Zeilen 13-16):

```python
# Konfiguration
PIHOLE_URL = "PiHole-URL:Port"              # z.B. "http://192.168.1.100"
PASSWORD = "PiHole-AdminPassword"            # Dein Pi-hole Admin-Passwort
OUTPUT_FILE = "pihole_stats.txt"             # Name der Ausgabedatei
DISCORD_WEBHOOK_URL = "Discord-WebhookURL"   # Discord Webhook URL (optional)
```

### Konfigurationsparameter erklärt:

| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `PIHOLE_URL` | URL deines Pi-hole Servers mit Port | `http://192.168.1.100` oder `http://pihole.local` |
| `PASSWORD` | Admin-Passwort deines Pi-hole | `dein-sicheres-passwort` |
| `OUTPUT_FILE` | Name der Ausgabedatei für die Statistiken | `pihole_stats.txt` |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL für Benachrichtigungen | `https://discord.com/api/webhooks/...` |

### Discord Webhook einrichten (optional)

1. Gehe zu deinem Discord Server
2. Navigiere zu den Channel-Einstellungen
3. Wähle "Integrationen" → "Webhooks"
4. Klicke auf "Neuer Webhook"
5. Kopiere die Webhook-URL
6. Füge die URL in die Konfiguration ein

## Verwendung

### Manuelle Ausführung

**Linux/Mac:**
```bash
python3 pihole_stats.py
```

**Windows:**
- Doppelklick auf `run_pihole_stats.bat` oder
- In der Kommandozeile: `python pihole_stats.py`

### Ausgabe

Das Script erzeugt zwei Arten von Ausgaben:

#### 1. Textdatei (`pihole_stats.txt`)
```
[2025-12-07 14:30:35] Total Queries: 69.083 | Queries Blocked: 28.146 | Percentage Blocked: 40.7 % | Domains in List: 433.206
[2025-12-07 14:33:00] Total Queries: 69.204 | Queries Blocked: 28.175 | Percentage Blocked: 40.7 % | Domains in List: 433.206
```

Jede Zeile enthält:
- **Zeitstempel**: Wann die Statistik abgerufen wurde
- **Total Queries**: Gesamtanzahl der DNS-Anfragen
- **Queries Blocked**: Anzahl der blockierten Anfragen
- **Percentage Blocked**: Prozentsatz der blockierten Anfragen
- **Domains in List**: Anzahl der Domains auf der Blockliste

#### 2. Discord Embed

Ein formatiertes Embed mit folgenden Informationen:
- Total Queries
- Queries Blocked
- Block Rate (in Prozent)
- Domains on List
- Active Clients
- Status
- Top 4 Clients (mit Namen und IP-Adressen)

**Farbcodierung:**
- **Grün**: Blockrate ≥ 50%
- **Orange**: Blockrate 25-50%
- **Rot**: Blockrate < 25%

## Automatisierung

### Windows (Task Scheduler)

1. Öffne "Aufgabenplanung" (Task Scheduler)
2. Erstelle eine neue Aufgabe
3. Trigger: z.B. alle 30 Minuten
4. Aktion: Programm starten
   - Programm: `python.exe`
   - Argumente: `pihole_stats.py`
   - Verzeichnis: Pfad zu diesem Projekt

### Linux/Mac (Cron)

Öffne crontab:
```bash
crontab -e
```

Füge eine Zeile hinzu (z.B. alle 30 Minuten):
```cron
*/30 * * * * cd /pfad/zum/projekt && python3 pihole_stats.py
```

Weitere Beispiele:
```cron
# Jede Stunde
0 * * * * cd /pfad/zum/projekt && python3 pihole_stats.py

# Jeden Tag um 8:00 Uhr
0 8 * * * cd /pfad/zum/projekt && python3 pihole_stats.py

# Alle 15 Minuten
*/15 * * * * cd /pfad/zum/projekt && python3 pihole_stats.py
```

## Funktionsweise

### 1. API-Token-Generierung
Das Script generiert ein API-Token durch doppeltes SHA256-Hashing des Admin-Passworts:
```
SHA256(SHA256(password))
```

### 2. Authentifizierung
- Login via `/api/auth` Endpoint
- Session-ID (SID) wird extrahiert und für weitere Anfragen verwendet
- SID wird im Header `X-FTL-SID` mitgesendet

### 3. Datenabfrage
Das Script ruft folgende Endpoints ab:
- `/api/stats/summary` - Zusammenfassende Statistiken
- `/api/stats/top_clients` - Top-Clients nach Anfragen
- `/api/clients` - Client-Informationen mit Namen

### 4. Datenverarbeitung
- Extrahiert relevante Statistiken aus der API-Antwort
- Mappt IP-Adressen zu Client-Namen
- Formatiert Zahlen mit deutschen Tausendertrennzeichen
- Berechnet Blockrate-Prozentsätze

### 5. Ausgabe
- Schreibt Statistiken in Textdatei (append mode)
- Sendet formatiertes Discord Embed

## Fehlerbehebung

### "Login Fehler" oder Status Code 401
- Überprüfe das Pi-hole Admin-Passwort
- Stelle sicher, dass die Pi-hole URL korrekt ist
- Überprüfe, ob Pi-hole erreichbar ist: `ping <pihole-ip>`

### "Connection Error" oder Timeout
- Überprüfe die Firewall-Einstellungen
- Stelle sicher, dass Pi-hole läuft
- Überprüfe die URL und den Port

### Discord Webhook funktioniert nicht
- Überprüfe die Webhook-URL
- Stelle sicher, dass der Webhook nicht gelöscht wurde
- Überprüfe die Discord-Channel-Berechtigungen

### Keine Client-Namen werden angezeigt
- Pi-hole muss Client-Namen/Hostnamen kennen
- Überprüfe in der Pi-hole Web-GUI unter "Clients"
- Alternativ können Namen manuell in Pi-hole konfiguriert werden

### Script hängt oder läuft sehr langsam
- Erhöhe die Timeout-Werte (Zeilen 43, 70, 84, 105, 302)
- Überprüfe die Netzwerkverbindung zum Pi-hole Server

## Datenschutz und Sicherheit

- **Passwort-Speicherung**: Das Admin-Passwort wird im Klartext in der Datei gespeichert
  - Schütze die Datei vor unbefugtem Zugriff
  - Erwäge die Verwendung von Umgebungsvariablen
- **Discord Webhooks**: Werden unverschlüsselt über HTTPS gesendet
- **Log-Dateien**: Enthalten keine sensiblen Daten, nur Statistiken

### Empfohlene Sicherheitsverbesserungen

Verwende Umgebungsvariablen statt Hardcoding:
```python
import os
PIHOLE_URL = os.getenv('PIHOLE_URL', 'http://localhost')
PASSWORD = os.getenv('PIHOLE_PASSWORD')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
```

Setze dann die Umgebungsvariablen:
```bash
# Linux/Mac
export PIHOLE_PASSWORD="dein-passwort"
export PIHOLE_URL="http://192.168.1.100"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Windows
set PIHOLE_PASSWORD=dein-passwort
set PIHOLE_URL=http://192.168.1.100
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Dateistruktur

```
Pihole-Stats/
├── pihole_stats.py          # Hauptscript
├── run_pihole_stats.bat     # Windows Batch-Datei zum Ausführen
├── requirements.txt         # Python-Abhängigkeiten
├── pihole_stats.txt         # Ausgabedatei (wird automatisch erstellt)
├── README.md               # Englische Version
└── README_DE.md            # Diese Datei (Deutsch)
```

## Technische Details

### API Endpoints

Das Script verwendet die Pi-hole FTL API v6:
- **Auth**: `POST /api/auth` - Authentifizierung
- **Summary**: `GET /api/stats/summary` - Zusammenfassende Statistiken
- **Top Clients**: `GET /api/stats/top_clients` - Aktivste Clients
- **Clients Info**: `GET /api/clients` - Client-Details mit Namen

### Datenstruktur

**Summary Response:**
```json
{
  "queries": {
    "total": 69083,
    "blocked": 28146
  },
  "gravity": {
    "domains_being_blocked": 433206
  },
  "clients": {
    "active": 12
  }
}
```

**Top Clients Response:**
```json
{
  "clients": [
    {
      "ip": "192.168.1.100",
      "count": 1234,
      "name": "device-name"
    }
  ]
}
```

## Lizenz

Dieses Projekt ist frei verwendbar. Bitte beachte, dass es sich um ein privates Monitoring-Tool handelt und keine Garantie übernommen wird.

## Support

Bei Problemen oder Fragen:
1. Überprüfe die Fehlerbehebung-Sektion
2. Stelle sicher, dass alle Konfigurationen korrekt sind
3. Prüfe die Pi-hole Logs für weitere Informationen

## Changelog

### Version 1.0
- Initiales Release
- Pi-hole API Integration
- Discord Webhook Support
- Top Clients Anzeige mit Namen
- Textdatei-Logging
