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
category_options.remove({'label': 'Popularity', 'value': 'Popularity'})
category_options.remove({'label': 'Artist Name(s)', 'value': 'Artist Name(s)'})
category_options.remove({'label': 'Album Name', 'value': 'Album Name'})
category_options.remove({'label': 'Track Name', 'value': 'Track Name'})
category_options.insert(4, {'label': 'Artist Genres %', 'value': 'Artist Genres %'})

# get rid of useless column (thought I already did but I guess not)
df.drop(columns=['Unnamed: 0'], inplace=True)

# filter outliers just for track duration graph (thought I already did in Sprint 2 but they are back for some reason)
Q1 = df['Track Duration (s)'].quantile(0.25)
Q3 = df['Track Duration (s)'].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR + 180 # added 180 because lot of longer songs left out doing basic outlier removal
track_duration_df = df[(df['Track Duration (s)'] <= upper_bound)]

def convert_to_year(x):
    x_split = x.split('-')
    x_cleaned = int(x_split[0])
    return x_cleaned

year_df = df.copy()
year_df['Album Release Date'] = year_df['Album Release Date'].apply(convert_to_year)

# get min and max release dates
min_release_date = year_df['Album Release Date'].min()
max_release_date = year_df['Album Release Date'].max()

# convert to datetime and work around invalid dates
df['Album Release Date'] = df['Album Release Date'].astype(str)
has_dash = df['Album Release Date'].str.contains("-")
df.loc[~has_dash, 'Album Release Date'] = df.loc[~has_dash, 'Album Release Date'].str.split('.').str[0] + "-01-01"
df['Album Release Date'] = pd.to_datetime(df['Album Release Date'], errors='coerce')

# create marks for range
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
    ], className='navbar navbar-default', style={'backgroundColor': '#e3faf6'}),
    html.Div([
        dcc.Checklist(
        id='popularity-checkbox',
        options=[
            {'label': 'Include tracks with popularity of 0', 'value': 'yes'},
        ],  
        value=[],  # Initial selected values
        labelStyle={'display': 'block'}  # Display checkboxes in block to appear vertically
        ),
        dcc.Graph(id='graph-output'),
        dcc.RangeSlider(
            id='year-slider',
            min=min_release_date,
            max=max_release_date,
            value=[min_release_date, max_release_date],
            marks=range_slider_marks,
            step=1
        ),
    ], style={'backgroundColor': '#e3faf6'}),
    html.Div([
        html.H5('Display Secondary Graph Below:'),
        dcc.Dropdown(
        id='category-dropdown',
        options=category_options,
        multi=False,
        value=[df.columns[0]]
    ),
    ], className='row', style={'backgroundColor': '#e3faf6'}),
    html.Div([
        dcc.Graph(id='graph-output-2'),
        dcc.RangeSlider(
            id='year-slider-2',
            min=min_release_date,
            max=max_release_date,
            value=[min_release_date, max_release_date],
            marks=range_slider_marks,
            step=1
        ),
    ], style={'backgroundColor': '#e3faf6'}),
    html.Div([
        dash_table.DataTable(
        df.to_dict('records'),
        [{"name": df.columns[i], "id": df.columns[i]} for i in range(len(df.columns))],
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        style_table={"overflowX": "auto"},
    ), ]   , style={'backgroundColor': '#e3faf6'}
)
], style={'backgroundColor': '#e3faf6'})

def simplify_genre(genre_list):
    # simplify genre lists to first genre
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
        'metal': ['metal', 'death metal', 'heavy metal'],
        'punk': ['punk', 'hardcore punk', 'emo', 'new romantic'],
        'world music': ['k-pop', 'afrobeats', 'bollywood', 'celtic', 'australian', 'british', 'german', 'french', 'afrikaans', 
                        'jamaican', 'belgian', 'irish', 'latin', 'reggaeton', 'salsa'],
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
    
    # categorize extraneous genres as 'other'
    return 'other'

# broadly categorize genres
df['Artist Genres'] = df['Artist Genres'].apply(simplify_genre)

# only contain tracks where there is a popularity value
popularity_df = df[df['Popularity'] > 0]

@app.callback(
    Output('graph-output', 'figure'),
    Input('year-slider', 'value'),
    Input('popularity-checkbox', 'value')
)
def create_graph(selected_years, show_popularity):
    if show_popularity:
        rs_df = df[(df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])]
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
            text="*Tracks without 'Popularity' value are set to 0 by default. Toggle on or off above if you want them displayed*",  # Your footnote text here
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )
    else:
        rs_df = popularity_df[(popularity_df['Album Release Date'].dt.year >= selected_years[0]) & (popularity_df['Album Release Date'].dt.year <= selected_years[1])]
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
         

    return fig




@app.callback(
    Output('graph-output-2', 'figure'),
    Input('category-dropdown', 'value'),
    Input('year-slider-2', 'value'),
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
        rs_df = (df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])
        genre_counts_rs_df = df[rs_df]
        counts = genre_counts_rs_df['Artist Genres'].value_counts().reset_index()
        counts.columns = ['Artist Genres', 'Count']

        # sort genres by descending order and move 'other' row to the end of the df
        sorted_genre_counts_rs_df = counts.sort_values(by='Count', ascending=False)
        other_row = sorted_genre_counts_rs_df[sorted_genre_counts_rs_df['Artist Genres'] == 'other']
        sorted_genre_counts_rs_df = pd.concat([sorted_genre_counts_rs_df[sorted_genre_counts_rs_df['Artist Genres'] != 'other'], other_row])

        fig = px.bar(sorted_genre_counts_rs_df, x='Artist Genres', y='Count', title='Most Popular Genres')

    if category == 'Explicit':
        rs_df = (year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])
        explicit_rs_df = df[rs_df]
        counts = explicit_rs_df['Explicit'].value_counts()
        fig = px.pie(counts, values=counts, names=counts.index, title='Explicit vs Non-Explicit Track Percentages')

    if category == 'Track Duration (s)':
        Q1 = df['Track Duration (s)'].quantile(0.25)
        Q3 = df['Track Duration (s)'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR + 180 # added 120 because lot of longer songs left out doing basic outlier removal
        track_duration_df = df[(df['Track Duration (s)'] <= upper_bound)]
        track_duration_rs_df = track_duration_df[(track_duration_df['Album Release Date'].dt.year >= selected_years[0]) & (track_duration_df['Album Release Date'].dt.year <= selected_years[1])]
        fig = px.histogram(track_duration_rs_df, x='Track Duration (s)')
        fig.update_layout(title_text='Track Duration Distribution', xaxis_title='Track Duration (s)', yaxis_title='Count')

    if category == 'Artist Genres %':
        rs_df = (year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])
        genres_percentage_rs_df = df[rs_df]
        counts = genres_percentage_rs_df['Artist Genres'].value_counts()
        fig = px.pie(counts, values=counts, names=counts.index, title='Distribution of Artist Genres')
    
    return fig
    

# run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)