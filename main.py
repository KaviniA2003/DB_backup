#!/usr/bin/env python3
import subprocess
import datetime
import gzip
import shutil
import os
import time
import requests

# ===== CONFIGURATION =====
DB_NAME = "qa_care_db"
DB_USER = "root"
DB_PASSWORD = ""  
DB_HOST = "127.0.0.1"
DB_PORT = 3306

BACKUP_DIR = "backups/mysql"
KEEP_DAYS_LOCAL = 7  # keep local backups for 7 days

# Google Apps Script WebApp URL
WEBAPP_URL = "YOUR_WEBAPP_URL_HERE"  

# =========================

def upload_to_drive(filename):
    """Upload backup file to Google Drive via Apps Script WebApp."""
    try:
        params = {"name": os.path.basename(filename)}  
        with open(filename, 'rb') as file:
            response = requests.post(
                WEBAPP_URL,
                params=params,
                data=file,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=600
            )

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"Successfully Uploaded {filename} to Drive")
                print(f"File URL: {result.get('fileUrl')}")
            else:
                print(f"Script error: {result.get('error')}")
        else:
            print(f"HTTP error {response.status_code} while uploading")
    except Exception as e:
        print(f"Error uploading to Drive: {e}")

def cleanup_old_backups():
    """Delete local backups older than KEEP_DAYS_LOCAL."""
    now = time.time()
    for f in os.listdir(BACKUP_DIR):
        f_path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(f_path) and f.endswith(".sql.gz"):
            if now - os.path.getmtime(f_path) > KEEP_DAYS_LOCAL * 86400:
                os.remove(f_path)
                print(f"🗑 Deleted old local backup: {f}")

def backup_database():
    """Create MySQL backup, compress, upload, clean old backups."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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

        # Compress SQL file
        with open(sql_filename, 'rb') as f_in:
            with gzip.open(gz_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(sql_filename)  # remove uncompressed file

        if not os.path.exists(gz_filename) or os.path.getsize(gz_filename) == 0:
            print("Error: Backup file empty or not created")
            return

        print(f"Backup completed: {gz_filename}")

        # Upload to Drive
        upload_to_drive(gz_filename)

        # Cleanup old local backups
        cleanup_old_backups()

    except subprocess.CalledProcessError as e:
        print(f"mysqldump failed: {e.stderr.decode()}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")

if __name__ == "__main__":
    backup_database()
