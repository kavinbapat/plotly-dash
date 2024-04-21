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
                html.H1('Top 10,000 Songs on Spotify Released from 1956-2023', style={'text-align': 'center', 'color': 'black', 'font-family': 'Copperplate'})
            ], className='container-fluid')
        ], style={'background-color': 'green'})  
    ], className='navbar navbar-default',),
    html.Div([
        html.P('Below is a graph displaying every song based on its popularity and release date.', 
               style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Garamond', 'font-size': 24})
    ]),
    html.Div([
        html.Div([
            dcc.Checklist(
                id='popularity-checkbox',
                options=[
                    {'label': 'Include tracks with popularity of 0', 'value': 'yes'},
                ],  
                value=[],  # Initial selected values
                labelStyle={'display': 'block'}  # Display checkboxes in block to appear vertically
            )
        ], style={'marginLeft': '10%', 'font-family': 'Garamond'}),
        dcc.Graph(id='graph-output', style={'width': '80%', 'margin': '0 auto'}),
        html.Div([
            dcc.RangeSlider(
                id='year-slider',
                min=min_release_date,
                max=max_release_date,
                value=[min_release_date, max_release_date],
                marks=range_slider_marks,
                step=1,
            ),
        ], style={'width': '80%', 'margin': '0 auto'})
        
    ],),
    html.Div([
        html.H6('Adjust the range of years displayed on the graph', style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Garamond'})
    ]),
    html.Div(style={'border-top': '3px solid #4CAF50', 'width': '100%', 'margin': '20px 0'}),
    html.Div([
        html.P('To look at more information regarding the overall distribution of the most popular songs on this site, including genres, track lengths, etc., create a graph using the dropdown below.', 
               style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Garamond', 'font-size': 24})
    ]),
    html.Div([
        html.Div([
            html.H6('Select Graph:', style={'margin-right': '10px', 'font-family': 'Garamond'}),
        ],style={'display': 'flex', 'alignItems': 'center', 'marginLeft': '10%'}),
        dcc.Dropdown(
            id='category-dropdown',
            options=category_options,
            multi=False,
            value=df.columns[0],
            style={'width': '50%'}
        )
    ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%'}),
    html.Div([
        dcc.Graph(id='graph-output-2', style={'width': '80%', 'margin': '0 auto'}),
        html.Div([
            dcc.RangeSlider(
            id='year-slider-2',
            min=min_release_date,
            max=max_release_date,
            value=[min_release_date, max_release_date],
            marks=range_slider_marks,
            step=1
        ),
        ], style={'width': '80%', 'margin': '0 auto'})
       
    ],),
    html.Div([
        html.H6('Adjust the range of years displayed on the graph', style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Garamond'})
    ]),
    html.Div(style={'border-top': '3px solid #4CAF50', 'width': '100%', 'margin': '20px 0'}),
    html.Div([
        html.P('Below is a data table containing all the original information on each of the tracks. Feel free to sort and filter the data using keywords to find the information you are looking for.', 
               style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Garamond', 'font-size': 24})
    ]),
    html.Div([
        html.H4('Data Table', style={'text-align': 'center', 'color': 'light-blue', 'font-family': 'Georgia'})
    ]),
    html.Div([
        dash_table.DataTable(
        df.to_dict('records'),
        [{"name": df.columns[i], "id": df.columns[i]} for i in range(len(df.columns))],
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        style_cell={'textAlign': 'left', 'backgroundColor': '#ffdea3', 'color': 'black'},
        style_header={
            'backgroundColor': '#c49d56',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_table={"overflowX": "auto"},
    ), ]
)
], style={'backgroundColor': '#b5f5bb'})

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
popularity_df = df.copy()
popularity_df = popularity_df[popularity_df['Popularity'] > 0]


@app.callback(
    Output('graph-output', 'figure'),
    Input('year-slider', 'value'),
    Input('popularity-checkbox', 'value')
)
def create_graph_1(selected_years, show_popularity):
    if len(show_popularity) > 0:
        pop_rs_df = df[(df['Album Release Date'].dt.year >= selected_years[0]) & (df['Album Release Date'].dt.year <= selected_years[1])]
        fig_pop = px.scatter(pop_rs_df, x='Album Release Date', y='Popularity', hover_name='Track Name', 
                         hover_data=["Artist Name(s)", "Album Name", "Artist Genres"], color='Artist Genres', opacity=0.5)
        fig_pop.update_layout(title={
                'text': "Tracks",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Album Release Date', yaxis_title='Popularity'
        )
        fig_pop.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            )
        )
        fig_pop.add_annotation(
            xref='paper', yref='paper',
            x=0, y=-0.2,
            text="*Tracks without 'Popularity' value are set to 0 by default. Toggle on or off above if you want them displayed*",
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )
        fig_pop.update_layout(
            xaxis=dict(showgrid=False),  
            yaxis=dict(showgrid=False) 
        )
        fig_pop.update_layout(paper_bgcolor='#b5f5bb')
        fig_pop.update_layout(plot_bgcolor='#f0fcf4')

        return fig_pop
    else:
        nopop_rs_df = popularity_df[(popularity_df['Album Release Date'].dt.year >= selected_years[0]) & (popularity_df['Album Release Date'].dt.year <= selected_years[1])]
        fig_nopop = px.scatter(nopop_rs_df, x='Album Release Date', y='Popularity', hover_name='Track Name', 
                         hover_data=["Artist Name(s)", "Album Name", "Artist Genres"], color='Artist Genres', opacity=0.5)
        fig_nopop.update_layout(title={
                'text': "Tracks",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Album Release Date', yaxis_title='Popularity'
        )
        fig_nopop.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            )
        )
        fig_nopop.add_annotation(
            xref='paper', yref='paper',
            x=0, y=-0.2,
            text="*Tracks without 'Popularity' value are set to 0 by default.\nToggle on or off if you want them displayed*",
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )
        fig_nopop.update_layout(
            xaxis=dict(showgrid=False),  
            yaxis=dict(showgrid=False) 
        )
        fig_nopop.update_layout(paper_bgcolor='#b5f5bb')
        fig_nopop.update_layout(plot_bgcolor='#f0fcf4')

        return fig_nopop




@app.callback(
    Output('graph-output-2', 'figure'),
    Input('category-dropdown', 'value'),
    Input('year-slider-2', 'value'),
)
def create_graph_2(category, selected_years):
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
                    "size": 48,
                    "family": 'Garamond'
                }
            }
        ],
        "plot_bgcolor": "#b5f5bb",
        "paper_bgcolor": "#b5f5bb"
        }
    }
    
    if category == 'Album Release Date':
        year_rs_df = year_df[(year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])]
        fig = px.histogram(year_rs_df, x="Album Release Date")
        fig.update_layout(title_text='Album Release Date Distribution', xaxis_title='Album Release Date', yaxis_title='Track Duration (s)')
        fig.update_layout(paper_bgcolor='#b5f5bb')
        fig.update_layout(plot_bgcolor='#f0fcf4')
        fig.update_traces(marker_color='#b07205')
        fig.update_layout(  
            yaxis=dict(showgrid=False) 
        )
        fig.update_layout(title={
                'text': "Album Release Date Distribution",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Album Release Date', yaxis_title='Track Duration (s)'
        )

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
        fig.update_layout(paper_bgcolor='#b5f5bb')
        fig.update_layout(plot_bgcolor='#f0fcf4')
        fig.update_traces(marker_color='#b07205')
        fig.update_layout(
            xaxis=dict(showgrid=False),  
            yaxis=dict(showgrid=False) 
        )
        fig.update_layout(title={
                'text': "Most Popular Genres",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Genre', yaxis_title='Count'
        )
        fig.add_annotation(
            xref='paper', yref='paper',
            x=0, y=-0.2,
            text="*Genres were consolidated into broad categories. Original genre data can be seen in the table below*",
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )

    if category == 'Explicit':
        rs_df = (year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])
        explicit_rs_df = df[rs_df]
        counts = explicit_rs_df['Explicit'].value_counts()
        fig = px.pie(counts, values=counts, names=counts.index, title='Explicit vs Non-Explicit Track Percentages')
        fig.update_layout(paper_bgcolor='#b5f5bb')
        fig.update_layout(title={
                'text': "Explicit vs Non-Explicit Track Percentages",
                'x':0.5,
                'xanchor': 'center',
            }
        )

    if category == 'Track Duration (s)':
        Q1 = df['Track Duration (s)'].quantile(0.25)
        Q3 = df['Track Duration (s)'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR + 180 # added 120 because lot of longer songs left out doing basic outlier removal
        track_duration_df = df[(df['Track Duration (s)'] <= upper_bound)]
        track_duration_rs_df = track_duration_df[(track_duration_df['Album Release Date'].dt.year >= selected_years[0]) & (track_duration_df['Album Release Date'].dt.year <= selected_years[1])]
        fig = px.histogram(track_duration_rs_df, x='Track Duration (s)')
        fig.update_layout(paper_bgcolor='#b5f5bb')
        fig.update_layout(plot_bgcolor='#f0fcf4')
        fig.update_traces(marker_color='#b07205')
        fig.update_layout(
            xaxis=dict(showgrid=False),  
            yaxis=dict(showgrid=False) 
        )
        fig.update_layout(title={
                'text': "Track Duration Distribution",
                'x':0.5,
                'xanchor': 'center',
            }, xaxis_title='Track Duration (s)', yaxis_title='Count'
        )

    if category == 'Artist Genres %':
        rs_df = (year_df['Album Release Date'] >= selected_years[0]) & (year_df['Album Release Date'] <= selected_years[1])
        genres_percentage_rs_df = df[rs_df]
        counts = genres_percentage_rs_df['Artist Genres'].value_counts()
        fig = px.pie(counts, values=counts, names=counts.index, title='Distribution of Artist Genres')
        fig.update_layout(paper_bgcolor='#b5f5bb')
        fig.update_layout(title={
                'text': "Distribution of Artist Genres",
                'x':0.5,
                'xanchor': 'center',
            }
        )
        fig.add_annotation(
            xref='paper', yref='paper',
            x=-.3, y=-.5,
            text="*Genres were consolidated into broad categories. Original genre data can be seen in the table below*",
            showarrow=False,
            font=dict(size=12, color="grey"),
            align="center"
        )
    
    
    return fig
    

# run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)