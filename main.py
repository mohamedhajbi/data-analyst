from flask import Flask, jsonify
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pandas as pd

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = 'service.json'
FILE_ID = '1K-dP_S7se5K6h7o6e6ocKdBtetCU2Fyc'

def download_csv(file_id):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

    fh.seek(0)
    return pd.read_csv(fh)

@app.route('/')
def index():
    df = download_csv(FILE_ID)
    return df.head().to_json(orient='records')

if __name__ == '__main__':
    app.run(debug=True)
