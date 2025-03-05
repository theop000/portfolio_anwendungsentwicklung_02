import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.express as px
import json
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import os
import time

# Import the functions from the new data.py
from data import (
    initialize_stations_data,
    download_station_data,
    clean_station_data,
    create_monthly_averages,
    create_yearly_averages
)

# Create the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Initialize the stations data only if it doesn't exist
if not os.path.exists('./data/stations.csv') or os.path.getsize('./data/stations.csv') == 0:
    initialize_stations_data()

# Read the stations data
stations_df = pd.read_csv('./data/stations.csv',
                         usecols=['Station_Name', 'Latitude', 'Longitude', 'FirstYear', 'LastYear', 'Station_ID'])

# Create the map figure using scatter_mapbox
fig = px.scatter_mapbox(stations_df,
                         lat='Latitude',
                         lon='Longitude',
                         hover_name='Station_Name',
                         height=600)

# Set consistent styling
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox=dict(
        center=dict(lat=48.0458, lon=8.4617),
        zoom=4,
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
    clickmode='event+select'
)

# Set consistent marker size for all points
fig.update_traces(
    marker=dict(size=5),  
    selector=dict(type='scattermapbox')  
)

# Define the app layout
app.layout = html.Div([
    # Store component to save the selected stations
    dcc.Store(id='selected-stations-store'),
    # Store for button state
    dcc.Store(id='search-button-state', data={'active': False}),
    # # Store for selected station
    # dcc.Store(id='selected-station')

    dcc.Tabs([
        dcc.Tab(label= 'Karte - Wetterstationen', children= [
            html.H1('Karte - Wetterstationen', 
                    style={'textAlign': 'left', 'marginBottom': 10, 'fontWeight': 'bold'}),
            
            # Flex container for map and sidebar
            html.Div([
                # Map container (left side)
                html.Div([
                    dcc.Graph(id='station-map', 
                              figure=fig,
                              config={
                                  'scrollZoom': True,
                                  'displayModeBar': False
                              }),
                    dcc.Store(id='clicked-coord', data={'lat': None, 'lon': None})
                ], style={'width': '75%', 'display': 'inline-block'}),
                
                # Sidebar container (right side)
                html.Div([
                    html.H3('Sucheinstellungen', style={'marginBottom': '20px'}),
                    
                    # Radius input
                    html.Label('Suchradius (max. 100km)', style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='radius-slider',  
                        type='number',
                        min=1,
                        max=100,
                        value=50,
                        step=1,
                        style={
                            'width': '100%',
                            'padding': '8px',
                            'marginTop': '5px',
                            'marginBottom': '10px',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc'
                        }
                    ),
                    html.Br(),
                    
                    # Station count slider
                    html.Label('Anzahl der Stationen', style={'fontWeight': 'bold'}),
                    dcc.Slider(id='station-count-slider', min=1, max=10, value=5, step=1),
                    html.Br(),
                    
                    # Year range selection
                    html.Label('Zeitraum auswählen', style={'fontWeight': 'bold'}),
                    html.Div([
                        # Left input (Von)
                        html.Div([
                            dcc.Input(
                                id='year-from',
                                type='number',
                                min=0,
                                max=2024,
                                value=2000,
                                step=1,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Von', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block'}),
                        
                        # Right input (Bis)
                        html.Div([
                            dcc.Input(
                                id='year-to',
                                type='number',
                                min=0,
                                max=2024,
                                value=2024,
                                step=1,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Bis', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
                    ]),
                    html.Br(),                    
                    
                    # Coordinate inputs
                    html.Label('Koordinaten eingeben', style={'fontWeight': 'bold'}),
                    html.Div([
                        # Left input (Breitengrad)
                        html.Div([
                            dcc.Input(
                                id='latitude-input',
                                type='number',
                                value=48.0458,
                                min=-90,
                                max=90,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Breitengrad', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block'}),
                        
                        # Right input (Längengrad)
                        html.Div([
                            dcc.Input(
                                id='longitude-input',
                                type='number',
                                value=8.4617,
                                min=-180,
                                max=180,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Längengrad', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
                    ]),
                    html.Br(),                    

                    # Button (Stationen suchen)
                    html.Button('Stationen suchen', 
                            id='search-stations-button',
                            style={
                                'width': '100%',
                                'padding': '10px',
                                'backgroundColor': '#4CAF50',
                                'color': 'white',
                                'border': 'none',
                                'borderRadius': '1px',
                                'cursor': 'pointer'
                            }),
                    
                    # Display chosen coordinates
                    html.Div(id='click-data', 
                            style={'marginTop': '20px', 'textAlign': 'center'})

                # Search Parameter container (right side)
                ], style={
                    'width': '23%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'padding': '20px',
                    'backgroundColor': '#f9f9f9',
                    'borderLeft': '1px solid #ccc',
                    'height': '800px',
                    'marginLeft': '2%'
                })
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'})
        ]),
        # Tab (Stationsdaten)
        dcc.Tab(label='Stationsdaten', children=[
            html.H1('Stationsdaten',
                    style={'textAlign': 'left', 'marginBottom': 20, 'fontWeight': 'bold'}),
            html.Div([
                # Container for the station data table
                html.Div(id='station-data-table'),
                # New divider with loading state
                html.Div([
                    html.Div([  # New wrapper div for horizontal alignment
                        html.Div(id='loading-message', children='Wähle eine Station aus',
                                style={'color': 'white', 'textAlign': 'center', 'padding': '10px', 'marginRight': '10px'}),
                        dcc.Loading(
                            id='loading-spinner',
                            type='circle',
                            color='white',
                            children=html.Div(id='loading-spinner-output'),
                        )
                    ], style={
                        'display': 'flex',
                        'flexDirection': 'row',  
                        'alignItems': 'center',
                        'justifyContent': 'center',
                    })
                ], style={
                    'backgroundColor': 'lightblue',
                    'height': '10vh',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'marginTop': '20px',
                    'marginBottom': '20px'
                }),
                # Container for the yearly data
                html.Div(id='yearly-data-container')
            ])
        ])            
    ])
])



def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# Default settings on startup (Villingen-Schwenningen)
@app.callback(
    Output('click-data', 'children'),
    Output('latitude-input', 'value'),
    Output('longitude-input', 'value'),
    Input('station-map', 'clickData'),
    prevent_initial_call=True
)
def update_click_info(clickData):
    if not clickData:
        return "Click on the map to place a pin", 48.0458, 8.4617
    
    lat = clickData['points'][0]['lat']
    lon = clickData['points'][0]['lon']
    return f'Selected coordinates: {lat:.4f}, {lon:.4f}', lat, lon

# Storing selected stations based on distance
@app.callback(
    Output('station-map', 'figure'),
    Output('selected-stations-store', 'data'),
    Input('search-stations-button', 'n_clicks'),
    Input('radius-slider', 'value'),
    Input('station-count-slider', 'value'),
    Input('year-from', 'value'),
    Input('year-to', 'value'),
    State('latitude-input', 'value'),
    State('longitude-input', 'value'),
    State('station-map', 'figure'),
    prevent_initial_call=False
)
def update_stations_selection(n_clicks, radius_value, count_value, year_from, year_to, lat, lon, figure):
    # Handle the initial call
    if n_clicks is None:
        # Calculate initial stations based on default coordinates (Testing)
        stations_df['Distance'] = stations_df.apply(
            lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
            axis=1
        )
        
        filtered_stations = stations_df[
            (stations_df['FirstYear'] <= year_to) & 
            (stations_df['LastYear'] >= year_from) &
            (stations_df['Distance'] <= radius_value)
        ].nsmallest(count_value, 'Distance')
        
        return figure, filtered_stations.to_dict('records')
    
    # Calculate stations based on chosen coordinates
    stations_df['Distance'] = stations_df.apply(
        lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
        axis=1
    )
    
    filtered_stations = stations_df[
        (stations_df['FirstYear'] <= year_to) & 
        (stations_df['LastYear'] >= year_from) &
        (stations_df['Distance'] <= radius_value)
    ].nsmallest(count_value, 'Distance')
    
    return figure, filtered_stations.to_dict('records')

# Creating the Table based on the selected stations
@app.callback(
    Output('station-data-table', 'children'),
    Input('selected-stations-store', 'data'),
    prevent_initial_call=False
)
def update_station_table(selected_stations):
    if not selected_stations:
        return "No stations selected"
    
    # Convert stored data directly to DataFrame 
    display_df = pd.DataFrame(selected_stations)[
        ['Station_Name', 'Distance', 'FirstYear', 'LastYear', 'Station_ID', 'Latitude'] 
    ]
    
    # Round Distance to 2 decimal places
    display_df['Distance'] = display_df['Distance'].round(2)
    
    return dash.dash_table.DataTable(
        id='stations-table',  
        data=display_df.to_dict('records'),
        columns=[
            {'name': 'Station Name', 'id': 'Station_Name'},
            {'name': 'Distance (km)', 'id': 'Distance'},
            {'name': 'First Year', 'id': 'FirstYear'},
            {'name': 'Last Year', 'id': 'LastYear'},
            {'name': 'Station ID', 'id': 'Station_ID'}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[{
            'cursor': 'pointer'
        }],
        row_selectable='single'
    )

# Prevention of invalid selection (year_to, year_from) in Zeitraum
@app.callback(
    Output('year-to', 'value'),
    Output('year-from', 'value'),
    Input('year-from', 'value'),
    Input('year-to', 'value'),
    prevent_initial_call=True
)
def validate_years(year_from, year_to):
    triggered_id = ctx.triggered_id
    
    # Ensure values are valid
    year_from = max(0, min(2024, year_from if year_from else 0)) 
    year_to = max(0, min(2024, year_to if year_to else 2024))
    
    # If "from" year was changed
    if triggered_id == 'year-from':
        if year_from > year_to:
            year_to = year_from
    # If "to" year was changed
    elif triggered_id == 'year-to':
        if year_to < year_from:
            year_from = year_to
            
    return year_to, year_from

# Creation of data tabel and graph based on a selected station
@app.callback(
    [Output('yearly-data-container', 'children'),
     Output('loading-message', 'children'),
     Output('loading-spinner-output', 'children'),
     Output('loading-message', 'style')],
    Input('stations-table', 'selected_rows'),
    State('stations-table', 'data'),
    State('year-from', 'value'),
    State('year-to', 'value'),
    prevent_initial_call=True
)
def display_yearly_data(selected_rows, table_data, year_from, year_to):
    if not selected_rows:
        return "", "Wähle eine Station aus", "", {
            'color': 'white',
            'textAlign': 'center',
            'padding': '10px',
            'marginRight': '10px'
        }
    
    loading_style = {'color': 'white', 'textAlign': 'center', 'padding': '10px', 'marginRight': '10px'}
    start_time = time.time()
    
    try:
        # Get the selected station's data
        selected_station = table_data[selected_rows[0]]
        station_id = selected_station['Station_ID']
        station_lat = selected_station['Latitude']
        
        # Check if files exist and create if needed
        monthly_file = f"./data/stations/{station_id}_monthly.csv"
        yearly_file = f"./data/stations/{station_id}_yearly.csv"
        raw_file = f"./data/stations/{station_id}.csv"
        
        if time.time() - start_time > 5:
            raise TimeoutError("Data loading timeout")
            
        if not (os.path.exists(monthly_file) and os.path.exists(yearly_file)):
            # Process station files
            station_files = [f for f in os.listdir("./data/stations") if f.endswith('_yearly.csv')]
            if len(station_files) >= 10:
                # Oldest file gets removed
                station_times = []
                for fname in station_files:
                    station_id_from_file = fname.replace('_yearly.csv', '')
                    files_to_check = [
                        f"./data/stations/{station_id_from_file}.csv",
                        f"./data/stations/{station_id_from_file}_monthly.csv",
                        f"./data/stations/{station_id_from_file}_yearly.csv"
                    ]
                    creation_time = min(os.path.getctime(f) for f in files_to_check if os.path.exists(f))
                    station_times.append((station_id_from_file, creation_time))
                
                oldest_station = min(station_times, key=lambda x: x[1])[0]
                for ext in ['', '_monthly', '_yearly']:
                    old_file = f"./data/stations/{oldest_station}{ext}.csv"
                    if os.path.exists(old_file):
                        os.remove(old_file)
            
            # Download and process new data
            if not download_station_data(station_id):
                raise Exception("Failed to download station data")
            if not clean_station_data(station_id):
                raise Exception("Failed to clean station data")
            if not create_monthly_averages(station_id):
                raise Exception("Failed to create monthly averages")
            if not create_yearly_averages(station_id):
                raise Exception("Failed to create yearly averages")
        
        # Read the processed data
        yearly_df = pd.read_csv(yearly_file)
        monthly_df = pd.read_csv(monthly_file)
        
        # Filter data based on selected year range
        monthly_df = monthly_df[
            (monthly_df['Year'] >= year_from) & 
            (monthly_df['Year'] <= year_to)
        ]
        
        # Seasons based on north/south of Equator 
        is_northern = station_lat >= 0
        
        def calculate_seasonal_data(df):
            seasonal_data = []
            
            for year in df['Year'].unique():
                current_year = df[df['Year'] == year]
                prev_year = df[df['Year'] == year - 1]
                
                if is_northern:
                    winter_months = pd.concat([
                        prev_year[prev_year['Month'] == 12] if not prev_year.empty else pd.DataFrame(),
                        current_year[current_year['Month'].isin([1, 2])]
                    ])
                    spring_months = current_year[current_year['Month'].isin([3, 4, 5])]
                    summer_months = current_year[current_year['Month'].isin([6, 7, 8])]
                    fall_months = current_year[current_year['Month'].isin([9, 10, 11])]
                else:
                    summer_months = pd.concat([
                        prev_year[prev_year['Month'] == 12] if not prev_year.empty else pd.DataFrame(),
                        current_year[current_year['Month'].isin([1, 2])]
                    ])
                    fall_months = current_year[current_year['Month'].isin([3, 4, 5])]
                    winter_months = current_year[current_year['Month'].isin([6, 7, 8])]
                    spring_months = current_year[current_year['Month'].isin([9, 10, 11])]
                
                row_data = {
                    'Jahr': year,
                    'Min. (jährlich)': yearly_df[yearly_df['Year'] == year]['TMIN'].iloc[0],
                    'Max. (jährlich)': yearly_df[yearly_df['Year'] == year]['TMAX'].iloc[0],
                    'Winter_Min': winter_months['TMIN'].mean().round(2) if not winter_months.empty else None,
                    'Winter_Max': winter_months['TMAX'].mean().round(2) if not winter_months.empty else None,
                    'Frühling_Min': spring_months['TMIN'].mean().round(2) if not spring_months.empty else None,
                    'Frühling_Max': spring_months['TMAX'].mean().round(2) if not spring_months.empty else None,
                    'Sommer_Min': summer_months['TMIN'].mean().round(2) if not summer_months.empty else None,
                    'Sommer_Max': summer_months['TMAX'].mean().round(2) if not summer_months.empty else None,
                    'Herbst_Min': fall_months['TMIN'].mean().round(2) if not fall_months.empty else None,
                    'Herbst_Max': fall_months['TMAX'].mean().round(2) if not fall_months.empty else None,
                }
                seasonal_data.append(row_data)
            
            return pd.DataFrame(seasonal_data)
        
        combined_df = calculate_seasonal_data(monthly_df)
        
        # Filter combined data for selected year range
        combined_df = combined_df[
            (combined_df['Jahr'] >= year_from) & 
            (combined_df['Jahr'] <= year_to)
        ]
        
        # Header with the stations name
        return [
            html.H3(f"{selected_station['Station_Name']}",
                   style={'marginTop': '20px', 'marginBottom': '10px'}),
            
            # Data Table and styling
            dash.dash_table.DataTable(
                data=combined_df.to_dict('records'),
                columns=[
                    {'name': 'Jahr', 'id': 'Jahr'},
                    {'name': 'Min. (jährlich)', 'id': 'Min. (jährlich)'},
                    {'name': 'Max. (jährlich)', 'id': 'Max. (jährlich)'},
                    {'name': 'Winter Min.', 'id': 'Winter_Min'},
                    {'name': 'Winter Max.', 'id': 'Winter_Max'},
                    {'name': 'Frühling Min.', 'id': 'Frühling_Min'},
                    {'name': 'Frühling Max.', 'id': 'Frühling_Max'},
                    {'name': 'Sommer Min.', 'id': 'Sommer_Min'},
                    {'name': 'Sommer Max.', 'id': 'Sommer_Max'},
                    {'name': 'Herbst Min.', 'id': 'Herbst_Min'},
                    {'name': 'Herbst Max.', 'id': 'Herbst_Max'}
                ],
                style_table={
                    'overflowX': 'auto',
                    'overflowY': 'auto',
                    'maxHeight': '400px'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'minWidth': '80px',
                    'height': '30px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'height': '40px'
                },
                style_header_conditional=(
                    [
                        {
                            'if': {'column_id': 'Jahr'},
                            'color': 'black'
                        }
                    ] + 
                    [
                        {
                            'if': {'column_id': col},
                            'color': '#0000ff'  # Blue for all Min columns
                        } for col in ['Min. (jährlich)', 'Winter_Min', 'Frühling_Min', 'Sommer_Min', 'Herbst_Min']
                    ] + 
                    [
                        {
                            'if': {'column_id': col},
                            'color': '#ff0000'  # Red for all Max columns
                        } for col in ['Max. (jährlich)', 'Winter_Max', 'Frühling_Max', 'Sommer_Max', 'Herbst_Max']
                    ]
                ),
                style_data_conditional=[
                    # Yearly
                    {
                        'if': {'column_id': 'Min. (jährlich)'},
                        'color': '#0000ff'
                    },
                    {
                        'if': {'column_id': 'Max. (jährlich)'},
                        'color': '#ff0000'
                    },
                    # Winter
                    {
                        'if': {'column_id': 'Winter_Min'},
                        'color': '#969696'
                    },
                    {
                        'if': {'column_id': 'Winter_Max'},
                        'color': '#626262'
                    },
                    # Spring
                    {
                        'if': {'column_id': 'Frühling_Min'},
                        'color': '#47D45A'
                    },
                    {
                        'if': {'column_id': 'Frühling_Max'},
                        'color': '#3B7D23'
                    },
                    # Summer
                    {
                        'if': {'column_id': 'Sommer_Min'},
                        'color': '#E97132'
                    },
                    {
                        'if': {'column_id': 'Sommer_Max'},
                        'color': '#CC5316'
                    },
                    # Autumn
                    {
                        'if': {'column_id': 'Herbst_Min'},
                        'color': '#75300D'
                    },
                    {
                        'if': {'column_id': 'Herbst_Max'},
                        'color': '#4C1F08'
                    }
                ],
                sort_action='native'
            ),
            
            # Temperature Graph below the table
            html.Div([
                dcc.Graph(
                    id='temperature-graph',
                    figure={
                        'data': [
                            # Yearly lines
                            {'x': combined_df['Jahr'], 'y': combined_df['Min. (jährlich)'],
                             'name': 'Jährlich Min.', 'line': {'color': '#0000ff', 'width': 2}},
                            {'x': combined_df['Jahr'], 'y': combined_df['Max. (jährlich)'],
                             'name': 'Jährlich Max.', 'line': {'color': '#ff0000', 'width': 2}},
                            # Winter lines
                            {'x': combined_df['Jahr'], 'y': combined_df['Winter_Min'],
                             'name': 'Winter Min.', 'line': {'color': '#969696', 'width': 2}},
                            {'x': combined_df['Jahr'], 'y': combined_df['Winter_Max'],
                             'name': 'Winter Max.', 'line': {'color': '#626262', 'width': 2}},
                            # Spring lines
                            {'x': combined_df['Jahr'], 'y': combined_df['Frühling_Min'],
                             'name': 'Frühling Min.', 'line': {'color': '#47D45A', 'width': 2}},
                            {'x': combined_df['Jahr'], 'y': combined_df['Frühling_Max'],
                             'name': 'Frühling Max.', 'line': {'color': '#3B7D23', 'width': 2}},
                            # Summer lines
                            {'x': combined_df['Jahr'], 'y': combined_df['Sommer_Min'],
                             'name': 'Sommer Min.', 'line': {'color': '#E97132', 'width': 2}},
                            {'x': combined_df['Jahr'], 'y': combined_df['Sommer_Max'],
                             'name': 'Sommer Max.', 'line': {'color': '#CC5316', 'width': 2}},
                            # Autumn lines
                            {'x': combined_df['Jahr'], 'y': combined_df['Herbst_Min'],
                             'name': 'Herbst Min.', 'line': {'color': '#75300D', 'width': 2}},
                            {'x': combined_df['Jahr'], 'y': combined_df['Herbst_Max'],
                             'name': 'Herbst Max.', 'line': {'color': '#4C1F08', 'width': 2}},
                        ],
                        'layout': {
                            'title': 'Temperaturverlauf',
                            'xaxis': {
                                'title': 'Jahr',
                                'tickmode': 'linear',
                                'dtick': 1,
                                'fixedrange': True  
                            },
                            'yaxis': {
                                'title': 'Temperatur in Grad C',
                                'fixedrange': True  
                            },
                            'hovermode': 'x unified',
                            'legend': {
                                'x': 1.05,
                                'y': 1,
                                'xanchor': 'left'
                            },
                            'height': 700,  
                            'uirevision': True,  
                            'dragmode': False,  
                        }
                    },
                    config={
                        'displayModeBar': False,
                        'staticPlot': False
                    },
                    style={'height': '700px'}  # Match container height to figure height
                )
            ], style={
                'marginTop': '20px',
                'marginBottom': '40px'
            })
        ], "", "", loading_style
        
    except TimeoutError:
        return "", "Probleme beim Laden der Stationsdaten, versuche es später erneut", "", loading_style
    except Exception as e:
        print(f"Error processing station data: {str(e)}")
        return "", "Probleme beim Laden der Stationsdaten, versuche es später erneut", "", loading_style

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)