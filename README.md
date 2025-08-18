# DB_backup
# MySQL Backup & Google Drive Uploader

This project automates MySQL database backups and uploads them to a specified Google Drive folder.
## https://script.google.com/macros/s/AKfycbyauF4_0gBs8oEWfCIXdIea9HAvdpaPzkSTFWwbomn-9xlrxRvuOdzfI3oyJ-rymrTPSQ/exec
## Features

- Dumps a MySQL database to a `.sql` file
- Compresses the backup to `.sql.gz`
- Cleans up old backups (older than 7 days)
- Uploads the compressed backup to Google Drive

## Requirements

- Python 3.7+
- MySQL server and `mysqldump` utility
- Google Cloud project with Drive API enabled
- `credentials.json` file from Google Cloud Console

## Setup

1. **Install dependencies:**
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. **Place your `credentials.json`** in the project folder.

3. **Edit `main.py`:**
   - Set your database credentials (`DB_NAME`, `DB_USER`, etc.)
   - Set your Google Drive folder ID (`DRIVE_FOLDER_ID`)

## Usage

Run the backup script:
```
python main.py
```

On first run, a browser window will open for Google authentication.

## Notes

- Backups are stored in the `backups/mysql` directory.
- Only `.sql.gz` files are uploaded to Google Drive.
- Old backups (older than 7 days) are deleted automatically. (Locally)
- Old backups (older than 30 days) are deleted from the google drive automatically.
