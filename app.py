from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from src.const import detectors_out_to_table
import json
import geopandas as gpd
import geojson
import dash_leaflet as dl
import re
from dash_extensions.javascript import assign
from dash_extensions.javascript import arrow_function
from src.dash1 import generate_visualizations as generate_visualizations1
from src.dash2 import generate_visualizations as generate_visualizations2
from src.dash3 import generate_visualizations as generate_visualizations3
from src.dash4 import generate_visualizations as generate_visualizations4
from src.dash5 import generate_visualizations as generate_visualizations5
import datetime
d = pd.read_csv('./Ofile.out.csv')
dO = pd.read_csv('./Ofile.out.csv', sep=";")
dR = pd.read_csv('./Rfile.out.csv', sep=";")
VO = pd.read_csv('./Ofile.veh.csv', sep=";")
VR = pd.read_csv('./Rfile.veh.csv', sep=";")
geo_data = None
dict_names = {}
time_intervals_seconds = dO['interval_id'].unique()
time_intervals = []
def read_geojson():
    with open('./bxl_Tulipe.geojson', encoding='utf-8') as f:
        gj = geojson.load(f)
    return gj


# Define function to load data based on tab selection
def load_data(traffic):
    dfO = detectors_out_to_table(dO, traffic)
    dfR = detectors_out_to_table(dR, traffic)
    dfO = dfO.fillna(0)
    dfR = dfR.fillna(0)
    dfO_aligned, dfR_aligned = dfO.align(dfR, fill_value=0)
    return dfO_aligned, dfR_aligned


# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title='TULIPE - Traffic management')
server = app.server

def generate_stats_card (title, value, image_path):
    return html.Div(
        dbc.Card([
            dbc.CardImg(src=image_path, top=True, style={'width': '50px','alignSelf': 'center'}),
            dbc.CardBody([
                html.P(value, className="card-value", style={'margin': '0px','fontSize': '22px','fontWeight': 'bold'}),
                html.H4(title, className="card-title", style={'margin': '0px','fontSize': '18px','fontWeight': 'bold'})
            ], style={'textAlign': 'center'}),
        ], style={'paddingBlock':'10px',"backgroundColor":'#deb522','border':'none','borderRadius':'10px'})
    )


tab_style = {
    'idle':{
        'borderRadius': '10px',
        'padding': '0px',
        'marginInline': '5px',
        'display':'flex',
        'alignItems':'center',
        'justifyContent':'center',
        'fontWeight': 'bold',
        'backgroundColor': '#deb522',
        'border':'none'
    },
    'active':{
        'borderRadius': '10px',
        'padding': '0px',
        'marginInline': '5px',
        'display':'flex',
        'alignItems':'center',
        'justifyContent':'center',
        'fontWeight': 'bold',
        'border':'none',
        'textDecoration': 'underline',
        'backgroundColor': '#deb522'
    }
}
##D3D3D3
#00FFF7
style_handle = assign("""function(feature, context){
    const {selected} = context.hideout;
    if(selected.includes(feature.properties.id)){   
        return {fillColor: '#3f3f3f', color: '#3f3f3f'} 
    }
    //console.log(feature.properties.id)
    return {fillColor: '#1a73e8', color: '#1a73e8'}
}""")

on_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`${feature.properties.name} (id:${feature.properties.id})`)
}""")

modal_body = html.Div([
    html.Br(),
    html.B("Team: "), "Moisés Silva-Muñoz | Davide Andrea Guastella | Gianluca Bontempi",
    html.Br(),html.Br(),
    html.B("About: "), "The Machine Learning Group (MLG), founded in 2004 by G. Bontempi,  is a research unit of the Computer Science Department of the ULB (Université Libre de Bruxelles, Brussels, Belgium), Faculty of Sciences, currently co-headed by Prof. Gianluca Bontempi and Prof. Tom Lenaerts. MLG targets machine learning and behavioral intelligence research focusing on time series analysis, big data mining, causal inference, network inference, decision-making models and behavioral analysis with applications in data science, medicine, molecular biology, cybersecurity and social dynamics related to cooperation, emotions and others.",
    #html.Br(), html.Br(),
    #"His main areas of interest are AI, Machine Learning, Data Visualization, and Concurrent Programming. He has good hands-on with Python and its ecosystem libraries.",
    #html.Br(),html.Br(),
    #html.B("Email: "), "sunny.2309@yahoo.in",
    html.Br(),html.Br(),
    html.Div([
        html.A([html.Img(src="assets/mlg.png", height=50, className="rounded m-1")], href="https://mlg.ulb.ac.be/wordpress/", target="_blank"),
        html.A([html.Img(src="assets/ulb.png", height=50, className="rounded m-1")], href="https://www.ulb.be", target="_blank"),
    ])
])

traffic_body = html.Div([
    html.B("Traveltime: "), "Time in seconds needed to pass the street.",
    html.Br(),
    html.B("Density: "), "Vehicle density on the street (vehicles per km).",
    html.Br(),
    html.B("Occupancy: "), "Occupancy of the street in %. A value of 100 would indicate vehicles standing bumper to bumper on the whole street (minGap=0).",
    html.Br(),
    html.B("TimeLoss: "), "The average time lost due to driving slower than desired (includes waitingTime).",
    html.Br(),
    html.Br("WaitingTime: "), "Sum of the time (in seconds) that vehicles are considered to be stopped.",
    html.Br(),
    html.B("Speed: "), "The mean speed (meters/seconds) on the street within the reported interval.",
    html.Br(),
    html.B("SpeedRelative: "), "Quotient of the average speed and the speed limit of the streets.",
    html.Br(),
    html.B("SampledSeconds: "), "Sum of vehicles on the street every second during the time interval.",
    html.Br(),
    html.B("Duration: "), "The average trip duration.",
    html.Br(),
    html.B("RouteLength: "), "The average route length.",
])


MAX_OPTIONS_DISPLAY = 3300
# Generate options for the dropdown
dropdown_options = [{'label': title, 'value': title} for title in ['Travel time (seconds)', 'Density (vehicles/kilometres)','Occupancy (%)', 'Time loss (seconds)', 'Waiting time (seconds)', 'Speed (meters/seconds)', 'Speed relative (average speed / speed limit)', 'Sampled seconds (vehicles/seconds)']]
dropdown_options_vehicles = [{'label': title, 'value': title} for title in ['Duration (seconds)', 'Route length (meters)', 'Time loss (seconds)', 'Waiting time (seconds)']]
for elem in time_intervals_seconds:
    res = re.split("_to_", elem)
    interval_time = str(datetime.timedelta(seconds=int(res[0]))) + ' to ' + str(datetime.timedelta(seconds=int(res[1])))
    time_intervals.append(interval_time)
time_intervals.insert(0, time_intervals.pop())
dropdown_options_timeframes = [{'label': title, 'value': title} for title in time_intervals]

offcanvas = html.Div(
    [
        dbc.Button("Traffic indicators", id="open-movie-offcanvas", n_clicks=0, style={'backgroundColor':'#deb522','color':'black','fontWeight': 'bold','border':'none'}),
        dbc.Offcanvas(html.Div([
            html.Div(id="street-ind",
                children="Street indicators",
                style={'marginTop': '-15px'},
            ),
            dcc.Dropdown(
            id='traffic-dropdown',
            options=dropdown_options,
            value='Travel time (seconds)',
            placeholder='Select a traffic indicator...',
            searchable=True,
            style={'color':'black'}
            ),
            html.Div(id="vehicle-ind",
                children="Vehicle indicators",
                style={'marginTop': '15px'},
            ),
            dcc.Dropdown(
            id='vehicle-dropdown',
            options=dropdown_options_vehicles,
            value='Duration (seconds)',
            placeholder='Select a vehicular traffic indicator...',
            searchable=True,
            style={'color':'black'}
            ),
            html.Div(id="time-frames",
                     children="Time frames",
                     style={'marginTop': '15px'},
                     ),
            dcc.Dropdown(
                id='timeframes-dropdown',
                options=dropdown_options_timeframes,
                value=time_intervals[0],
                placeholder='Select a time frame...',
                searchable=True,
                style={'color': 'black'}
            ),
            html.Div(id='string_names',
                     style={'marginTop': '15px'}),
            html.Div(id="select-street",
                     children="Select one street to analyze",
                     style={'marginTop': '15px'},
                     ),
            html.Div([
                dl.Map([
                    dl.TileLayer(),
                    # From hosted asset (best performance).
                    dl.GeoJSON(data=read_geojson(), id="geojson", hideout=dict(selected=[]), style=style_handle, hoverStyle=arrow_function(dict(weight=5, color='#00FFF7', dashArray='')), onEachFeature=on_each_feature,)
                ], center=(50.83401264776447, 4.366035991425782), zoomControl=False, minZoom=14, zoom=15, style={'height': '50vh'}), #window height
            ], style={'border':'3px'}),
            html.Br(),
            html.Div(["", dbc.Button("About as", outline=True, color="warning", size="sm", className="me-1", id="open", n_clicks=0), "  ", dbc.Button("Indicators", outline=True, size="sm", color="warning", className="me-1", id="indicators_open", n_clicks=0)]),
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Machine Learning Group")),
                dbc.ModalBody([modal_body]),
                dbc.ModalFooter(dbc.Button("Close", id="close", className="ms-auto", n_clicks=0))
            ],
                id="modal",
                is_open=False,
            ),
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Indicator description")),
                dbc.ModalBody([traffic_body]),
                dbc.ModalFooter(dbc.Button("Close", id="indicators_close", className="ms-auto", n_clicks=0))
            ],
                id="indicators_modal",
                is_open=False,
                #style={'width': '72vh'}
            ),
            dcc.Store(id='dict_names')
            ]),
            id="traffic-offcanvas",
            title="Filters",
            is_open=False,
            style={'backgroundColor':"black",'color':'#deb522', 'width': '68vh'}, #window width
        )
    ],
    style={'display': 'flex', 'justifyContent': 'space-between','marginTop': '20px'}
)
@app.callback(Output("modal", "is_open"), [Input("open", "n_clicks"), Input("close", "n_clicks")], [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
@app.callback(Output("indicators_modal", "is_open"), [Input("indicators_open", "n_clicks"), Input("indicators_close", "n_clicks")], [State("indicators_modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Define the layout of the app
app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.Img(src="./assets/imdb.png",width=150), width=2),
            dbc.Col(
                dcc.Tabs(id='graph-tabs', value='overview', children=[
                    dcc.Tab(label='Overview', value='overview',style=tab_style['idle'],selected_style=tab_style['active']),
                    dcc.Tab(label='By time intervals', value='intervals',style=tab_style['idle'],selected_style=tab_style['active']),
                    dcc.Tab(label='By streets', value='streets',style=tab_style['idle'],selected_style=tab_style['active']),
                    dcc.Tab(label='By vehicles', value='vehicles',style=tab_style['idle'],selected_style=tab_style['active']),
                    dcc.Tab(label='Most impacted', value='impacted',style=tab_style['idle'],selected_style=tab_style['active'])
                ], style={'marginTop': '15px', 'width':'750px','height':'50px'})
            ,width=8),
            dbc.Col(offcanvas, width=2)
        ]),
        dbc.Row([
            dcc.Loading([
                html.Div(id='tabs-content')
            ],type='default',color='#deb522')
        ])
    ], style={'padding': '0px'})
],style={'backgroundColor': 'black', 'minHeight': '100vh'})


@app.callback(
    Output("geojson", "hideout"),
    Output('string_names', 'children'),
    Output('dict_names', 'data'),
    Input("geojson", "n_clicks"),
    State("geojson", "clickData"),
    State("geojson", "hideout"),
    prevent_initial_call=True)

def toggle_select(_, feature, hideout):
    selected = hideout["selected"]
    id = feature["properties"]["id"]
    name = feature["properties"]["name"]
    if id in selected:
        selected.remove(id)
        del dict_names[id]
    else:
        selected.append(id)
        dict_names[id] = name
    return hideout, html.Div(['Selected street:'] + [html.Div(f"{value} (id:{key})") for (key, value) in dict_names.items()]), dict_names

@app.callback(
    Output("traffic-offcanvas", "is_open"),
    Input("open-movie-offcanvas", "n_clicks"),
    [State("traffic-offcanvas", "is_open")],
)
def toggle_offcanvas_movie(n1, is_open):
    if n1:
        return not is_open
    return is_open

def selected_timeframe_in_seconds(timeframe_split):
    h1, m1, s1 = timeframe_split[0].split(':')
    starting = int(datetime.timedelta(hours=int(h1), minutes=int(m1), seconds=int(s1)).total_seconds())
    h2, m2, s2 = timeframe_split[2].split(':')
    end = int(datetime.timedelta(hours=int(h2), minutes=int(m2), seconds=int(s2)).total_seconds())
    interval_seconds = str(starting) + "_to_" + str(end)
    return interval_seconds

def get_veh_traffic(traffic):
    value = ''
    if traffic == 'Duration (seconds)':
        value = 'duration of the trip (seconds) '
    if traffic == 'Route length (seconds)':
        value = 'length of the route (meters)'
    if traffic == 'Time loss (seconds)':
        value = 'time loss (seconds)'
    if traffic == 'Waiting time (seconds)':
        value = 'waiting time (seconds)'
    return value

def get_traffic_2(traffic):
    inf = ''
    if traffic == "Density (vehicles/kilometres)":
        inf = "vehicle density (vehicles/kilometres)"
    elif traffic == "Occupancy (%)":
        inf = "vehicle occupancy (%)"
    elif traffic == "Time loss (minutes)":
        inf = "time lost by vehicles due to driving slower than the desired speed (minutes)"
    elif traffic == "Travel time (seconds)":
        inf = "travel time (minutes)"
    elif traffic == "Waiting time (seconds)":
        inf = "waiting time (minutes)"
    elif traffic == "Speed (meters/seconds)":
        inf = "average speed (meters/seconds)"
    elif traffic == "Speed relative (average speed / speed limit)":
        inf = "speed relative (average speed / speed limit)"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        inf = "sampled seconds (vehicles/seconds)"
    return inf

def get_traffic_3(traffic):
    inf = ''
    if traffic == "Density (vehicles/kilometres)":
        inf = "vehicle density (vehicles/kilometres)"
    elif traffic == "Occupancy (%)":
        inf = "vehicle occupancy (%)"
    elif traffic == "Time loss (seconds)":
        inf = "time lost by vehicles due to driving slower than the desired speed (seconds)"
    elif traffic == "Travel time (seconds)":
        inf = "travel time (seconds)"
    elif traffic == "Waiting time (seconds)":
        inf = "waiting time (seconds)"
    elif traffic == "Speed (meters/seconds)":
        inf = "average speed (meters/seconds)"
    elif traffic == "Speed relative (average speed / speed limit)":
        inf = "speed relative (average speed / speed limit)"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        inf = "sampled seconds (vehicles/seconds)"
    return inf

def get_traffic(traffic):
    inf = ''
    if traffic == "Density (vehicles/kilometres)":
        inf = "vehicle density (vehicles/kilometres)"
    elif traffic == "Occupancy (%)":
        inf = "vehicle occupancy (%)"
    elif traffic == "Time loss (seconds)":
        inf = "time lost by vehicles due to driving slower than the desired speed (seconds)"
    elif traffic == "Travel time (seconds)":
        inf = "travel time (seconds) of the vehicles"
    elif traffic == "Waiting time (seconds)":
        inf = "waiting time (seconds) of the vehicles"
    elif traffic == "Speed (meters/seconds)":
        inf = "average speed (meters/seconds) of the vehicles"
    elif traffic == "Speed relative (average speed / speed limit)":
        inf = "speed relative (average speed / speed limit) of the vehicles"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        inf = "sampled seconds (vehicles/seconds) of the vehicles"
    return inf

def get_traffic_lowercase(traffic):
    traffic_df = ''
    if traffic == "Density (vehicles/kilometres)":
        traffic_df = "density (vehicles/kilometres)"
    elif traffic == "Occupancy (%)":
        traffic_df = "occupancy (%)"
    elif traffic == "Time loss (seconds)":
        traffic_df = "time loss (seconds)"
    elif traffic == "Travel time (seconds)":
        traffic_df = "travel time (seconds)"
    elif traffic == "Waiting time (seconds)":
        traffic_df = "waiting time (seconds)"
    elif traffic == "Speed (meters/seconds)":
        traffic_df = "speed (meters/seconds)"
    elif traffic == "Speed relative (average speed / speed limit)":
        traffic_df = "speed relative (average speed / speed limit)"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        traffic_df = "sampled seconds (vehicles/seconds)"
    return traffic_df

def get_traffic_name(traffic):
    traffic_df = ''
    if traffic == "Density (vehicles/kilometres)":
        traffic_df = "density"
    elif traffic == "Occupancy (%)":
        traffic_df = "occupancy"
    elif traffic == "Time loss (seconds)":
        traffic_df = "timeLoss"
    elif traffic == "Travel time (seconds)":
        traffic_df = "traveltime"
    elif traffic == "Waiting time (seconds)":
        traffic_df = "waitingTime"
    elif traffic == "Speed (meters/seconds)":
        traffic_df = "speed"
    elif traffic == "Speed relative (average speed / speed limit)":
        traffic_df = "speedRelative"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        traffic_df = "sampledSeconds"
    return traffic_df

def get_vehicle_name(traffic):
    vehicle_df = ''
    if traffic == "Duration (seconds)":
        vehicle_df = "duration"
    elif traffic == "Route length (meters)":
        vehicle_df = "routeLength"
    elif traffic == "Time loss (seconds)":
        vehicle_df = "timeLoss"
    elif traffic == "Waiting time (seconds)":
        vehicle_df = "waitingTime"
    return vehicle_df


@app.callback(
    Output('tabs-content', 'children'),
    [Input('graph-tabs', 'value'), Input('traffic-dropdown', 'value'), Input('vehicle-dropdown', 'value'), Input('timeframes-dropdown', 'value'), Input("geojson", "hideout"), Input("geojson", "n_clicks")]
)
def update_tab(tab, traffic, vehicle, timeframes, hideout, string_names):
    traffic_lowercase = get_traffic_lowercase(traffic)
    geo_data = read_geojson()
    dfO, dfR = load_data(get_traffic_name(traffic))
    traffic_name = get_traffic(traffic)
    traffic_3 = get_traffic_3(traffic)
    veh_traffic = get_veh_traffic(vehicle)
    timeframe_split = re.split(" ", timeframes)
    timeframe_in_seconds = selected_timeframe_in_seconds(timeframe_split)
    if tab == 'overview':
        fig2 = generate_visualizations1(dfO, dfR, VO, VR, traffic_name, vehicle, time_intervals_seconds, dict_names)
        return html.Div([
        html.Div([
                dcc.Graph(id='graph2', figure=fig2),
            ], style={'width': '49%', 'display': 'inline-block'})
        # html.Div([
        #     dcc.Graph(id='graph4', figure=fig4),
        # ], style={'width': '97%', 'display': 'inline-block'})
    ])
    elif tab == 'intervals':
        figure = generate_visualizations2(dfO, dfR, traffic_3, traffic, timeframe_in_seconds, timeframe_split[0], timeframe_split[2], hideout, dict_names)
        return (
            # html.Div(
            #     id="title_histogram",
            #     children=[
            #         html.H4("Histograms with integrated results for the time frame "+ timeframe_split[0] + " to "
            #                 + timeframe_split[2] + " comparing the streets with and without deviations"),
            #     ],style={'color': 'yellow'}),
            html.Div([
                dcc.Graph(id='graph1', figure=figure, style={'height': '450px'}),
            ], style={'width': '55%', 'display': 'inline-block'}),
            html.Div(
                id="histogram",
                children=[
                    html.Div(
                        id="intro_histogram",
                        children="A histogram is a graph that shows the frequency of numerical data using rectangles. "
                                 "The height of a rectangle (the vertical axis) represents the distribution frequency "
                                 "of a variable (the amount, or how often that variable appears). The width of the "
                                 "rectangle (horizontal axis) represents the value of the variable (" + traffic_3 + ").",
                    ),
                ], style={'color': 'yellow'})
        )
    elif tab == 'streets':
        fig1 = generate_visualizations3(dfO, dfR, traffic_3, traffic, time_intervals_seconds, dict_names,time_intervals)
        if fig1 is not None:
            return html.Div([
            html.Div([
                dcc.Graph(id='graph1', figure=fig1, style={'height': '450px'}),
                ], style={'width': '55%', 'display': 'inline-block'})
            ])
        else:
            return html.Div(
                    id="select_one_street",
                    children = [
                        html.H1('Select one street on the map to analyze')
                    ], style={'color': 'yellow'}
            )
    elif tab == 'vehicles':
        fig1 = generate_visualizations4(VO, VR, get_vehicle_name(vehicle), veh_traffic)
        return html.Div([
            # html.Div(
            #     id="title_histogram_4",
            #     children=[
            #         html.H4('Histograms with integrated results obtained for the whole simulation considering the ' + veh_traffic + ' of the vehicles, comparing the results with and without deviations.'),
            #     ], style={'color': 'yellow'}),
        html.Div([
            dcc.Graph(id='graph1', figure=fig1, style={'height': '450px'}),
        ], style={'width': '55%', 'display': 'inline-block'}),
            html.Div(
                id="histogram4",
                children=[
                    html.Div(
                        id="intro4_histogram",
                        children="A histogram is a graph that shows the frequency of numerical data using rectangles. "
                                 "The height of a rectangle (the vertical axis) represents the distribution frequency "
                                 "of a variable (the amount, or how often that variable appears). The width of the "
                                 "rectangle (horizontal axis) represents the value of the variable (" + traffic_3 + ").",
                    ),
                ], style={'color': 'yellow'})
        ])
    elif tab == 'impacted':
        fig = generate_visualizations5(dfO, dfR, traffic_name, traffic_3, traffic_lowercase, timeframe_in_seconds, timeframe_split, geo_data)
        return html.Div([
            html.Div(
                id="title_histogram_5",
                children=[
                    html.H4('Difference obtained by comparing the streets with and without deviations.'),
                ], style={'color': 'yellow'}),
        html.Div([
            dcc.Graph(id='graph1', figure=fig, style={'height': '650px'}),
        ], style={'width': '70%', 'display': 'inline-block'}),
            html.Div(
                id="histogram5",
                children=[
                    html.Div(
                        id="intro5_histogram",
                        children="A bar chart is a graphical representation used to display and compare discrete "
                                 "categories of data through rectangular bars, where the length or height of each bar "
                                 "is proportional to the value of the corresponding category (" + traffic_3 + " in this case).",
                    ),
                ], style={'color': 'yellow'})
        ])


if __name__ == '__main__':
    app.run_server(debug=False)