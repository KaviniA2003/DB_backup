# MySQL Backup & Google Drive Uploader

This tool automates MySQL database backups and uploads them to Google Drive using a Google Apps Script WebApp.

## Features

- Dumps a MySQL database to a `.sql` file
- Compresses the backup to `.sql.gz`
- Cleans up old backups (older than 7 days)
- Uploads the compressed backup to Google Drive via a WebApp

## Requirements

- Python 3.7+
- MySQL server and `mysqldump` utility
- Google Apps Script WebApp for Drive upload
- `requests` Python package

## Setup

1. **Install dependencies:**
   ```
   pip install requests
   ```

2. **Configure your database and WebApp:**
   - Edit `main.py` and set your database credentials (`DB_NAME`, `DB_USER`, etc.)
   - Set your Google Apps Script WebApp URL (`WEBAPP_URL`)

3. **Ensure `mysqldump` is available** in your system PATH.

## Usage

Run the backup script:
```
python main.py
```

## Notes

- Backups are stored in the `backups/mysql` directory.
- Only `.sql.gz` files are uploaded to Google Drive.
- Old backups (older than 7 days) are deleted
