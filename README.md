# Pi-hole Statistics Monitor  

<img width="491" height="438" alt="image" src="https://github.com/user-attachments/assets/7ded21a1-061c-4362-b8c8-ab4095438ae4" />


[Deutsche Version / German Version](README_DE.md)

A Python script that automatically fetches statistics from a Pi-hole server, writes them to a text file, and optionally sends them to Discord via webhook as a formatted embed.

## Features

- **Automatic Statistics Retrieval**: Fetches current DNS filtering statistics from your Pi-hole server
- **Text File Logging**: Saves all statistics with timestamps to a text file
- **Discord Integration**: Sends formatted embeds with statistics to a Discord channel
- **Top Clients Display**: Shows the top 4 most active clients with their names and query counts
- **Color-Coded Status Display**: Green (>50% block rate), Orange (25-50%), Red (<25%)
- **Number Formatting**: Numbers with thousands separators for better readability

## Prerequisites

- Python 3.x
- Pi-hole Server (accessible via HTTP/HTTPS)
- Pi-hole Admin password
- (Optional) Discord Webhook URL for notifications

## Installation

### 1. Clone repository or download files

```bash
git clone <repository-url>
cd Pihole-Stats
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `requests==2.31.0`

## Configuration

Open the `pihole_stats.py` file and adjust the following variables (lines 13-16):

```python
# Configuration
PIHOLE_URL = "PiHole-URL:Port"              # e.g., "http://192.168.1.100"
PASSWORD = "PiHole-AdminPassword"            # Your Pi-hole admin password
OUTPUT_FILE = "pihole_stats.txt"             # Name of the output file
DISCORD_WEBHOOK_URL = "Discord-WebhookURL"   # Discord webhook URL (optional)
```

### Configuration parameters explained:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `PIHOLE_URL` | URL of your Pi-hole server with port | `http://192.168.1.100` or `http://pihole.local` |
| `PASSWORD` | Admin password of your Pi-hole | `your-secure-password` |
| `OUTPUT_FILE` | Name of the output file for statistics | `pihole_stats.txt` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | `https://discord.com/api/webhooks/...` |

### Setting up Discord Webhook (optional)

1. Go to your Discord server
2. Navigate to channel settings
3. Select "Integrations" → "Webhooks"
4. Click "New Webhook"
5. Copy the webhook URL
6. Paste the URL into the configuration

## Usage

### Manual Execution

**Linux/Mac:**
```bash
python3 pihole_stats.py
```

**Windows:**
- Double-click `run_pihole_stats.bat` or
- In command prompt: `python pihole_stats.py`

### Output

The script generates two types of output:

#### 1. Text File (`pihole_stats.txt`)
```
[2025-12-07 14:30:35] Total Queries: 69.083 | Queries Blocked: 28.146 | Percentage Blocked: 40.7 % | Domains in List: 433.206
[2025-12-07 14:33:00] Total Queries: 69.204 | Queries Blocked: 28.175 | Percentage Blocked: 40.7 % | Domains in List: 433.206
```

Each line contains:
- **Timestamp**: When the statistics were retrieved
- **Total Queries**: Total number of DNS queries
- **Queries Blocked**: Number of blocked queries
- **Percentage Blocked**: Percentage of blocked queries
- **Domains in List**: Number of domains on the blocklist

#### 2. Discord Embed

A formatted embed with the following information:
- Total Queries
- Queries Blocked
- Block Rate (in percent)
- Domains on List
- Active Clients
- Status
- Top 4 Clients (with names and IP addresses)

**Color Coding:**
- **Green**: Block rate ≥ 50%
- **Orange**: Block rate 25-50%
- **Red**: Block rate < 25%

## Automation

### Windows (Task Scheduler)

1. Open "Task Scheduler"
2. Create a new task
3. Trigger: e.g., every 30 minutes
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `pihole_stats.py`
   - Start in: Path to this project

### Linux/Mac (Cron)

Open crontab:
```bash
crontab -e
```

Add a line (e.g., every 30 minutes):
```cron
*/30 * * * * cd /path/to/project && python3 pihole_stats.py
```

More examples:
```cron
# Every hour
0 * * * * cd /path/to/project && python3 pihole_stats.py

# Every day at 8:00 AM
0 8 * * * cd /path/to/project && python3 pihole_stats.py

# Every 15 minutes
*/15 * * * * cd /path/to/project && python3 pihole_stats.py
```

## How It Works

### 1. API Token Generation
The script generates an API token by double SHA256 hashing the admin password:
```
SHA256(SHA256(password))
```

### 2. Authentication
- Login via `/api/auth` endpoint
- Session ID (SID) is extracted and used for further requests
- SID is sent in the `X-FTL-SID` header

### 3. Data Retrieval
The script fetches the following endpoints:
- `/api/stats/summary` - Summary statistics
- `/api/stats/top_clients` - Top clients by queries
- `/api/clients` - Client information with names

### 4. Data Processing
- Extracts relevant statistics from the API response
- Maps IP addresses to client names
- Formats numbers with thousands separators
- Calculates block rate percentages

### 5. Output
- Writes statistics to text file (append mode)
- Sends formatted Discord embed

## Troubleshooting

### "Login Error" or Status Code 401
- Check the Pi-hole admin password
- Ensure the Pi-hole URL is correct
- Check if Pi-hole is reachable: `ping <pihole-ip>`

### "Connection Error" or Timeout
- Check firewall settings
- Ensure Pi-hole is running
- Verify the URL and port

### Discord Webhook not working
- Check the webhook URL
- Ensure the webhook hasn't been deleted
- Check Discord channel permissions

### No client names are displayed
- Pi-hole must know client names/hostnames
- Check in the Pi-hole web GUI under "Clients"
- Alternatively, names can be configured manually in Pi-hole

### Script hangs or runs very slowly
- Increase timeout values (lines 43, 70, 84, 105, 302)
- Check network connection to Pi-hole server

## Privacy and Security

- **Password Storage**: The admin password is stored in plain text in the file
  - Protect the file from unauthorized access
  - Consider using environment variables
- **Discord Webhooks**: Sent unencrypted over HTTPS
- **Log Files**: Contain no sensitive data, only statistics

### Recommended Security Improvements

Use environment variables instead of hardcoding:
```python
import os
PIHOLE_URL = os.getenv('PIHOLE_URL', 'http://localhost')
PASSWORD = os.getenv('PIHOLE_PASSWORD')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
```

Then set the environment variables:
```bash
# Linux/Mac
export PIHOLE_PASSWORD="your-password"
export PIHOLE_URL="http://192.168.1.100"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Windows
set PIHOLE_PASSWORD=your-password
set PIHOLE_URL=http://192.168.1.100
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## File Structure

```
Pihole-Stats/
├── pihole_stats.py          # Main script
├── run_pihole_stats.bat     # Windows batch file to run the script
├── requirements.txt         # Python dependencies
├── pihole_stats.txt         # Output file (automatically created)
├── README.md               # This file (English)
└── README_DE.md            # German version
```

## Technical Details

### API Endpoints

The script uses the Pi-hole FTL API v6:
- **Auth**: `POST /api/auth` - Authentication
- **Summary**: `GET /api/stats/summary` - Summary statistics
- **Top Clients**: `GET /api/stats/top_clients` - Most active clients
- **Clients Info**: `GET /api/clients` - Client details with names

### Data Structure

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

## License

This project is freely usable. Please note that this is a private monitoring tool and no warranty is provided.

## Support

For problems or questions:
1. Check the troubleshooting section
2. Ensure all configurations are correct
3. Check Pi-hole logs for more information

## Changelog

### Version 1.0
- Initial release
- Pi-hole API integration
- Discord webhook support
- Top clients display with names
- Text file logging
