import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
    df.drop(columns=[col for col in columns_to_drop if col in df.columns], axis=1, inplace=True)

    # Further processing
    df['publishedAt'] = pd.to_datetime(df['publish_time'], format='%Y-%m-%dT%H:%M:%S.%fZ')
    df['published_year'] = df['publishedAt'].dt.year
    df['published_hour'] = df['publishedAt'].dt.hour
    df['published_day'] = df['publishedAt'].dt.strftime('%A')
    df['views_cat'] = df.views.apply(views_cat)

    return df

def views_cat(views):
    if views <= 10000: return 'less than 10k'
    if views <= 25000: return '25k'
    if views <= 50000: return '50k'
    if views <= 75000: return '75k'
    if views <= 100000: return '100k'
    if views <= 250000: return '250k'
    if views <= 500000: return '500k'
    if views <= 750000: return '750k'
    if views <= 1000000: return '1m'
    if views <= 2500000: return '2.5m'
    if views <= 5000000: return '5m'
    if views <= 7500000: return '7.5m'
    if views <= 10000000: return '10m'
    return '15m' if views <= 15000000 else 'more than 15m'

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

    # Customize layout
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

def pie_chart(df):
    df['views_cat'] = df.views.apply(views_cat)
    appreanf_f_view = df.groupby('views_cat').size().reset_index(name='counts').sort_values(by='counts', ascending=True)
    sorter = ['less than 10k', '25k', '50k', '75k', '100k', '250k', '500k', '750k', '1m', '2.5m', '5m', '7.5m', '10m', '15m', 'more than 15m']
    sorterIndex = dict(zip(sorter, range(len(sorter))))
    appreanf_f_view['rank'] = appreanf_f_view['views_cat'].map(sorterIndex)
    appreanf_f_view = appreanf_f_view.sort_values(by='rank')
    appreanf_f_view.drop(['rank'], axis=1, inplace=True)

    fig = px.pie(appreanf_f_view, values='counts', names='views_cat', title='Percentage of appearance as a function of views category')
    
    return fig

def ratio(df):
    df['ratio'] = df['likes'] / (df['likes'] + df['dislikes'])
    ratio_cat = df['ratio'].value_counts().sort_index()
    figs = px.scatter(x=ratio_cat.index, y=ratio_cat.values, labels={'x': 'Like/Dislike Ratio', 'y': 'Count'}, title='Number of appearance as a function of likes dislikes ratio')
    return figs

def best_day_to_publish(df):
    day_cat = df.groupby('published_day').size().reset_index(name='counts').sort_values(by='counts', ascending=True)
    sorter = ['Monday','Tueday','Wednesday','Thursday','Friday','Saturday','Sunday']
    sorterIndex = dict(zip(sorter, range(len(sorter))))
    day_cat['rank'] = day_cat['published_day'].map(sorterIndex)
    day_cat = day_cat.sort_values(by='rank')
    day_cat.drop(['rank'], axis=1, inplace=True)
    fig_days = px.bar(x=day_cat.published_day, y=day_cat.counts, labels={'x': 'Day of publication', 'y': 'Number of appearance'}, title='Probability of apparition as a function of the day of publication') 
    return fig_days
