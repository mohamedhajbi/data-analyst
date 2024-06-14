import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pandas as pd
import plotly.graph_objects as go

SERVICE_ACCOUNT_FILE = 'service.json'

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
    df = pd.read_csv(fh)

    columns_to_drop = ['tags', 'thumbnail_link', 'comments_disabled', 'ratings_disabled', 'description']

    # Drop only the columns that exist in the DataFrame
    df.drop(columns=[col for col in columns_to_drop if col in df.columns], axis=1, inplace=True)

    # Further processing
    df['publishedAt'] = pd.to_datetime(df['publish_time'], format='%Y-%m-%dT%H:%M:%S.%fZ')
    df['published_year'] = df['publishedAt'].dt.year
    df['published_hour'] = df['publishedAt'].dt.hour
    df['published_day'] = df['publishedAt'].dt.strftime('%A')
    df['ratio'] = df['likes'] / (df['likes'] + df['dislikes'])

    return df

def top_20(df):
    grouped = pd.pivot_table(df, index='channel_title', columns='published_year', values='video_id', aggfunc='count', margins=True, margins_name='All')
    grouped = grouped.sort_values(by='All', ascending=False).head(21)
    grouped = grouped.sort_values(by='All', ascending=True)
    grouped = grouped.drop(['All'])
    grouped.drop(['All'], axis=1, inplace=True)

    figure = go.Figure()
    colors = {
        2006: '#1f77b4',
        2008: '#ff7f0e',
        2009: '#2ca02c',
        2010: '#d62728',
        2011: '#9467bd',
        2012: '#8c564b',
        2013: '#e377c2',
        2014: '#7f7f7f',
        2015: '#bcbd22',
        2016: '#17becf',
        2017: '#1f77b4',
        2018: '#ff7f0e'
    }

    for year in grouped.columns:
        if year != 'All':
            figure.add_trace(go.Bar(
                y=grouped.index,
                x=grouped[year],
                name=str(year),
                orientation='h',
                marker_color=colors.get(year, '#000000') 
            ))

    figure.update_layout(
        barmode='stack',
        title='The 20 Top performing channels ordered by their appearance on the trending page',
        xaxis_title='Number of appearances',
        yaxis=dict(
            title='Channel Title'
        ),
        height=800,
        width=1200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='black'
        )
    )

    return figure
