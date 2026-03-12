# SES Report - Project Notes

## What this does
Generates daily reports of AWS SES (Simple Email Service) events by parsing JSON files from SNS messages. Reports event types (Send, Bounce, Delivery, etc.) and counts emails sent per identity.

## Configuration
- Uses **Dynaconf** for configuration management
- Config file: `config.yaml`
- Current settings:
  - Email: from `jarle@he06.jarle.com` to `jarle+he06@jarle.com`
  - Data path: `/home/jarle/ses-events-2/YYYY/MM-DD/`
  - Looks back: 1 day (yesterday's data)
  - SMTP: localhost

## Setup
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running
```bash
# Basic (prints to stdout)
./ses-report.py

# Email report
./ses-report.py --email

# Silent email
./ses-report.py --quiet --email

# Store data to JSON Lines
./ses-report.py --store-data

# Store + email (typical cron usage)
./ses-report.py --quiet --email --store-data

# Debug mode
./ses-report.py --debug
```

## Cron Job
Runs daily at 02:00 hours:
```
0 2 * * * cd /home/jarle/prod/ses-report && /home/jarle/prod/ses-report/venv/bin/python /home/jarle/prod/ses-report/ses-report.py --quiet --email --store-data
```

## Important Paths
- Script location: `/home/jarle/prod/ses-report/`
- Python: `/home/jarle/prod/ses-report/venv/bin/python`
- Data directory: `/home/jarle/ses-events-2/` (configurable in config.yaml)
- Reports storage: `/home/jarle/prod/ses-report/reports/` (created automatically)

## Data Storage
When using `--store-data`, daily reports are saved as JSON Lines:
- Format: One JSON object per line
- Files: `reports/2025.jsonl`, `reports/2026.jsonl`, etc. (one file per year)
- Each entry contains: date, path, events, senders, hostname, script_path
- Running multiple times on the same date replaces the existing entry (no duplicates)

## Key Changes Made
- Added Dynaconf configuration (was hardcoded values)
- Renamed data_dir to sns_messages_dir in config
- All email settings, paths, and lookback days now in config.yaml
- Created requirements.txt for dependency management
- Added `--store-data` flag for JSON Lines storage with duplicate prevention

## Dependencies
- dynaconf>=3.2.0

## Notes
- The script expects JSON files with nested structure: `data['Message']` contains a JSON string with the actual event
- Email addresses changed from he03 to he06
- Data directory changed from `/home/jarle/ses-events` to `/home/jarle/ses-events-2`
