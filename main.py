import subprocess
import datetime
import gzip
import shutil
import os
import time
import pickle

# Google Drive API imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone

# ===== CONFIGURATION =====
DB_NAME = "test_backup_db"
DB_USER = "test_user"
DB_PASSWORD = "test_password"
DB_HOST = "127.0.0.1"
DB_PORT = 3306

BACKUP_DIR = "backups/mysql"
KEEP_DAYS_LOCAL = 7       # Keep local backups for 7 days
KEEP_DAYS_DRIVE = 30      # Keep Drive backups for 30 days

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_PICKLE = 'token.pickle'
DRIVE_FOLDER_ID = '1NBrTP2OeMibRfiJfbWAdbvw_-Qinj8Kp'
# =========================


def get_drive_service():
    """Authenticate and return a Google Drive service instance."""
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(filename):
    """Upload a backup file to Google Drive."""
    service = get_drive_service()
    file_metadata = {
        'name': os.path.basename(filename),
        'parents': [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(filename, mimetype='application/gzip')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Uploaded to Google Drive with file ID: {file.get('id')}")


def cleanup_old_backups():
    """Delete local backups older than KEEP_DAYS_LOCAL."""
    now = time.time()
    for f in os.listdir(BACKUP_DIR):
        f_path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(f_path) and f.endswith(".sql.gz"):
            if now - os.path.getmtime(f_path) > KEEP_DAYS_LOCAL * 86400:
                os.remove(f_path)
                print(f"🗑 Deleted old local backup: {f}")


def cleanup_old_drive_backups():
    """Delete Drive backups older than KEEP_DAYS_DRIVE (only matching DB_NAME)."""
    service = get_drive_service()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS_DRIVE)

    query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/gzip'"
    results = service.files().list(q=query, fields="files(id, name, createdTime)").execute()
    files = results.get('files', [])

    for file in files:
        # Only delete backups that match the DB name pattern
        if not file['name'].startswith(DB_NAME):
            continue

        created_time = datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00'))
        if created_time < cutoff_date:
            service.files().delete(fileId=file['id']).execute()
            print(f"🗑 Deleted old Drive backup: {file['name']} (Created: {created_time})")


def backup_database():
    """Create MySQL backup, compress, clean old backups locally and on Drive."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    sql_filename = os.path.join(BACKUP_DIR, f"{DB_NAME}_{timestamp}.sql")
    gz_filename = f"{sql_filename}.gz"

    print(f"Starting backup of database: {DB_NAME}")

    dump_cmd = [
        "mysqldump",
        f"--host={DB_HOST}",
        f"--port={DB_PORT}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        DB_NAME,
    ]

    try:
        # Run mysqldump
        with open(sql_filename, "wb") as f_out:
            subprocess.run(dump_cmd, stdout=f_out, stderr=subprocess.PIPE, check=True)

        # Compress the SQL file
        with open(sql_filename, 'rb') as f_in:
            with gzip.open(gz_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(sql_filename)  # Remove uncompressed file

        # Verify backup
        if not os.path.exists(gz_filename) or os.path.getsize(gz_filename) == 0:
            print("Error: Backup file is empty or was not created")
            return

        print(f"Backup completed: {gz_filename}")

        cleanup_old_backups()          
        upload_to_drive(gz_filename)   
        cleanup_old_drive_backups()    

    except subprocess.CalledProcessError as e:
        print(f"Error during backup: {e.stderr.decode()}")
    except Exception as ex:
        print(f"⚠️ Unexpected error: {ex}")


if __name__ == "__main__":
    backup_database()
