# import necessary libraries
import math
from dash import Dash, html, dcc, dash_table
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State

# read in data
df = pd.read_csv('data/data.csv')

# get stylesheet
stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] # load the CSS stylesheet

# initialize app
app = Dash(__name__, external_stylesheets=stylesheets)
server=app.server

category_options = [{'label': col, 'value': col} for col in df.columns[1:]]
# category_options[1]['label'] = 'Artist Name' # Change from name(s) to name
# category_options[1]['value'] = 'Artist Name'
category_options.remove({'label': 'Popularity', 'value': 'Popularity'})
category_options.remove({'label': 'Artist Name(s)', 'value': 'Artist Name(s)'})
category_options.remove({'label': 'Album Name', 'value': 'Album Name'})

track_name_options = [{'label': item, 'value': item} for item in pd.unique(df['Track Name'])]

# ensure only 1 artist name appears in each option
artist_name_options = []
for val in pd.unique(df['Artist Name(s)']):
    if ',' in val:
        val_split = val.split(',')
        for i in val_split:
            if {'label': i, 'value': i} not in artist_name_options:
                artist_name_options.append({'label': i, 'value': i})
    elif {'label': val, 'value': val} not in artist_name_options:
                artist_name_options.append({'label': val, 'value': val})

df.rename(columns={"Arist Name(s)": "Artist Name"}, inplace=True)

album_name_options = [{'label': item, 'value': item} for item in pd.unique(df['Album Name'])]

# Clean release date to just year
album_release_date_options = [{'label': item, 'value': item} for item in pd.unique(df['Album Release Date'])]

def convert_to_year(x):
    x_split = x.split('-')
    x_cleaned = int(x_split[0])
    return x_cleaned

year_df = df.copy()
year_df['Album Release Date'] = year_df['Album Release Date'].apply(convert_to_year)

# get min and max release dates
min_release_date = year_df['Album Release Date'].min()
max_release_date = year_df['Album Release Date'].max()

track_duration_options = [{'label': item, 'value': item} for item in pd.unique(df['Track Duration (s)'])]
# get min track duration
min_track_duration = df['Track Duration (s)'].min()

explicit_options = [{'label': item, 'value': item} for item in pd.unique(df['Explicit'])]

# ensure only 1 genre appears in each option
artist_genres_options = []
for val in pd.unique(df['Artist Genres']):
    if ',' in val:
        val_split = val.split(',')
        for i in val_split:
            if {'label': i, 'value': i} not in artist_genres_options:
                artist_genres_options.append({'label': i, 'value': i})
    elif {'label': val, 'value': val} not in artist_genres_options:
                artist_genres_options.append({'label': val, 'value': val})

# get rid of useless column (thought I already did but I guess not)
df.drop(columns=['Unnamed: 0'], inplace=True)

'''
genres_expanded = df['Artist Genres'].str.split(',').explode()
# count each genre's occurrence
genre_counts = genres_expanded.value_counts().reset_index()
genre_counts.columns = ['Genre', 'Count']
'''

# change true and false to explicit and clean for graph
explicit_counts = df['Explicit'].value_counts().reset_index()
explicit_counts.columns = ['Explicit', 'Count']
explicit_counts.loc[0,'Explicit'] = 'Clean'
explicit_counts.loc[1,'Explicit'] = 'Explicit'

# filter outliers just for track duration graph (thought I already did in Sprint 2 but they are back for some reason)
Q1 = df['Track Duration (s)'].quantile(0.25)
Q3 = df['Track Duration (s)'].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR + 180 # added 120 because lot of longer songs left out doing basic outlier removal
track_duration_df = df[(df['Track Duration (s)'] <= upper_bound)]

# convert to datetime and work around invalid dates
df['Album Release Date'] = df['Album Release Date'].astype(str)
has_dash = df['Album Release Date'].str.contains("-")
df.loc[~has_dash, 'Album Release Date'] = df.loc[~has_dash, 'Album Release Date'].str.split('.').str[0] + "-01-01"
df['Album Release Date'] = pd.to_datetime(df['Album Release Date'], errors='coerce')

range_slider_marks = {str(year): str(year) for year in range(min_release_date, max_release_date + 1, 5)}
range_slider_marks['2023'] = '2023'
# build app
app.layout = html.Div([
    html.Div([
        html.Nav([
            html.Div([
                html.H1('Top 10,000 Songs on Spotify Released from 1956-2023', style={'text-align': 'center', 'color': 'black'})
            ], className='container-fluid')
        ], style={'background-color': 'green'})  
    ], className='navbar navbar-default'),
    html.Div([
        html.H5('Create Graph:'),
        dcc.Dropdown(
        id='category-dropdown',
        options=category_options,
        multi=False,
        value=[df.columns[0]]
    ),
    ], className='row'),
    html.Div([
        dcc.Graph(id='graph-output'),
        dcc.RangeSlider(
            id='year-slider',
            min=min_release_date,
            max=max_release_date,
            value=[min_release_date, max_release_date],
            marks=range_slider_marks,
            step=None
        ),
    ]),
    html.Div([
        dash_table.DataTable(
        df.to_dict('records'),
        [{"name": df.columns[i], "id": df.columns[i]} for i in range(len(df.columns))],
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        style_table={"overflowX": "auto"},
    )]   
)
])

def simplify_genre(genre_list):
    # Get the first genre in the list
    first_genre = genre_list.split(',')[0].strip().lower()
    genre_mappings = {
        'hip hop': ['hip hop', 'rap', 'drill'],
        'pop': ['pop'],
        'rock': ['rock', 'beatlesque'],
        'jazz': ['jazz'],
        'blues': ['blues'],
        'country': ['country'],
        'folk': ['folk'],
        'electronic': ['electro', 'house', 'techno', 'edm', 'trance', 'dubstep', 'freestyle', 'big room'],
        'r&b': ['r&b', 'soul', 'funk'],
        'reggae': ['reggae', 'dancehall'],
        'classical': ['classical', 'orchestral', 'opera'],
        'metal': ['metal', 'death metal', 'heavy metal'],
        'punk': ['punk', 'hardcore punk', 'emo', 'new romantic'],
        'latin': ['latin', 'reggaeton', 'salsa'],
        'world music': ['k-pop', 'afrobeats', 'bollywood', 'celtic', 'australian', 'british', 'german', 'french', 'afrikaans', 
                        'jamaican', 'belgian', 'irish', ],
        'indie': ['indie'],
        'alternative': ['alternative', 'alt rock'],
        'disco': ['disco'],
        'dance': ['dance'],
        'girl': ['girl'],
        'mellow': ['mellow'],
        'band': ['band', 'hollywood']
    }
    
    for base_genre, subgenres in genre_mappings.items():
        if any(sub in first_genre for sub in subgenres):
            return base_genre
    
    # Return the first genre if no simplification matches
    return 'other'
    
df['Artist Genres'] = df['Artist Genres'].apply(simplify_genre)
genre_counts = df['Artist Genres'].value_counts()
genre_df = genre_counts.reset_index()
genre_df.columns = ['Genre', 'Count'] 
sorted_genre_df = genre_df.sort_values(by='Count', ascending=False)

# Move the 'other' row to the end of the DataFrame
other_row = sorted_genre_df[sorted_genre_df['Genre'] == 'other']
sorted_genre_df = pd.concat([sorted_genre_df[sorted_genre_df['Genre'] != 'other'], other_row])


@app.callback(
    Output('graph-output', 'figure'),
    Input('category-dropdown', 'value'),
    Input('year-slider', 'value')
)
def create_graph(category, selected_years):
    fig = {
    "layout": {
        "xaxis": {
            "visible": False
        },
        "yaxis": {
            "visible": False
        },
        "annotations": [
            {
                "text": "No category selected",
                "text": "No Category Selected",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 28
                }
            }
        ]
        }
    }
    
    if category == 'Album Release Date':
        year_rs_df = year_df[(year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])]
        fig = px.histogram(year_rs_df, x="Album Release Date")
        fig.update_layout(title_text='Album Release Date Distribution', xaxis_title='Album Release Date', yaxis_title='Track Duration (s)')
    if category == 'Artist Genres':
        #genre_counts_adjusted = genre_counts.drop(genre_counts[genre_counts.Count <= 2].index)
        #fig = px.bar(genre_counts_adjusted, x='Genre', y='Count', text='Count')
        fig = px.bar(sorted_genre_df, x='Genre', y='Count', text='Count')
        fig.update_layout(title_text='Genre Popularity', xaxis_title='Genre', yaxis_title='Count')
    if category == 'Explicit':
        fig = px.pie(explicit_counts, names='Explicit', values='Count', title='Distribution of Explicit Songs', labels={'true': 'Explicit', 'false': 'Clean'})
        fig.update_layout(title_text='Distribution of Explicity')
    if category == 'Track Duration (s)':
        Q1 = df['Track Duration (s)'].quantile(0.25)
        Q3 = df['Track Duration (s)'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR + 180 # added 120 because lot of longer songs left out doing basic outlier removal
        track_duration_df = df[(df['Track Duration (s)'] <= upper_bound)]
        track_duration_rs_df = track_duration_df[(track_duration_df['Album Release Date'].dt.year >= selected_years[0]) & (track_duration_df['Album Release Date'].dt.year <= selected_years[1])]
        fig = px.histogram(track_duration_rs_df, x='Track Duration (s)')
        fig.update_layout(title_text='Track Duration Distribution', xaxis_title='Track Duration (s)', yaxis_title='Count')
    if category == 'Track Name':
        rs_df = df[(df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])]
        # Q1 = rs_df['Track Duration (s)'].quantile(0.25)
        # Q3 = rs_df['Track Duration (s)'].quantile(0.75)
        # IQR = Q3 - Q1
        # upper_bound = Q3 + 1.5 * IQR + 180 # added 180 because lot of longer songs left out doing basic outlier removal
        # track_duration_rs_df = rs_df[(rs_df['Track Duration (s)'] <= upper_bound)]
        fig = px.scatter(rs_df, x='Album Release Date', y='Popularity', hover_name='Track Name', 
                         hover_data=["Artist Name(s)", "Album Name", "Artist Genres"], color='Artist Genres', opacity=0.5)
        fig.update_layout(title={
                'text': "Tracks",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Album Release Date', yaxis_title='Popularity'
        )
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            )
        )
        fig.add_annotation(
            xref='paper', yref='paper',  # Positions footnote relative to the edges of the plotting area
            x=0, y=-0.2,  # Adjust these values to move the footnote position
            text="*Tracks without 'Popularity' value are set to 0 by default.\nToggle on or off if you want them displayed*",  # Your footnote text here
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )
    # if category == 'Album Name':
    #     rs_df = df[(df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])]
    #     Q1 = rs_df['Track Duration (s)'].quantile(0.25)
    #     Q3 = rs_df['Track Duration (s)'].quantile(0.75)
    #     IQR = Q3 - Q1
    #     upper_bound = Q3 + 1.5 * IQR + 180 # added 180 because lot of longer songs left out doing basic outlier removal
    #     track_duration_rs_df = rs_df[(rs_df['Track Duration (s)'] <= upper_bound)]
    #     fig = px.scatter(track_duration_rs_df, x='Album Release Date', y='Track Duration (s)', hover_name='Album Name', opacity=0.5)
    #     fig.update_layout(title_text='Albums', xaxis_title='Album Release Date', yaxis_title='Track Duration (s)')

    # Condition not being met for Artist Name in dropdown for some reason
    # if category == 'Artist Name':
    #     rs_df = df[(df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])]
    #     Q1 = rs_df['Track Duration (s)'].quantile(0.25)
    #     Q3 = rs_df['Track Duration (s)'].quantile(0.75)
    #     IQR = Q3 - Q1
    #     upper_bound = Q3 + 1.5 * IQR + 180 # added 180 because lot of longer songs left out doing basic outlier removal
    #     track_duration_rs_df = rs_df[(rs_df['Track Duration (s)'] <= upper_bound)]
    #     fig = px.scatter(track_duration_rs_df, x='Album Release Date', y='Track Duration (s)', hover_name='Artist Name(s)', opacity=0.5)
    #     fig.update_layout(title_text='Artists', xaxis_title='Album Release Date', yaxis_title='Track Duration (s)')


    return fig

# run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)