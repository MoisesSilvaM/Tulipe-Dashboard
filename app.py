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
from src.generate_visualizations_interval import generate_visualizations as generate_visualizations_byinterval
from src.generate_visualizations_streets import generate_visualizations as generate_visualizations_bystreets
from src.generate_visualizations_vehicles import generate_visualizations as generate_visualizations_byvehicles
from src.generate_visualizations_impacted import generate_visualizations as generate_visualizations_impacted
from src.const import map_to_geojson as map_to_geojson
import datetime


def load_vehicles_data():
    vehicle_outputs_without = pd.read_csv('./Ofile.veh.csv', sep=";")
    vehicle_outputs_with = pd.read_csv('./Rfile.veh.csv', sep=";")
    return vehicle_outputs_without, vehicle_outputs_with


def read_geojson():
    with open('./bxl_Tulipe.geojson', encoding='utf-8') as f:
        gj = geojson.load(f)
    return gj


def read_geojson_deviations():
    with open('./map_plot.geojson', encoding='utf-8') as f:
        gj = geojson.load(f)
    return gj


def define_quantile(edgedata_df, interval, traffic):
    street_data = edgedata_df.loc[edgedata_df['interval_id'].isin(interval)].copy()
    street_data = street_data.set_index('edge_id').fillna(0)
    street_data = street_data.groupby('edge_id')[traffic].mean()

    p1 = street_data.quantile(q = 0.4)
    p2 = street_data.quantile(q=0.6)
    p3 = street_data.quantile(q=0.8)
    p4 = street_data.quantile(q=0.9)

    minim = street_data.min()
    maxim = street_data.max()
    list_intervals = [minim, p1, p2, p3, p4, maxim]
    return list_intervals


def load_street_data(traffic):
    dO = pd.read_csv('./Ofile.out.csv', sep=";")
    dR = pd.read_csv('./Rfile.out.csv', sep=";")
    dfO = detectors_out_to_table(dO, traffic)
    dfR = detectors_out_to_table(dR, traffic)
    dfO = dfO.fillna(0)
    dfR = dfR.fillna(0)
    street_data_without, street_data_with = dfO.align(dfR, fill_value=0)
    return street_data_without, street_data_with


def get_from_time_intervals_string(time_intervals_seconds):
    interval_time = re.split(" to ", time_intervals_seconds[0])
    return interval_time[0]


def get_to_time_intervals_string(time_intervals_seconds):
    interval_time = re.split(" to ", time_intervals_seconds[-1])
    return interval_time[1]


def get_time_intervals_string():
    time_intervals_string = []
    time_intervals_seconds = get_time_intervals_seconds()
    for elem in time_intervals_seconds:
        res = re.split("_to_", elem)
        interval_time = str(datetime.timedelta(seconds=int(res[0]))) + ' to ' + str(
            datetime.timedelta(seconds=int(res[1])))
        time_intervals_string.append(interval_time)
    return time_intervals_string[:-1]


def get_time_intervals_marks():
    time_intervals_marks = []
    time_intervals_seconds = get_time_intervals_seconds()
    for elem in time_intervals_seconds[:-1]:
        res = re.split("_to_", elem)
        interval_time = str(datetime.timedelta(seconds=int(res[0])))
        time_intervals_marks.append(interval_time)
    res = re.split("_to_", time_intervals_seconds[-1])
    interval_time = str(datetime.timedelta(seconds=int(res[1])))
    time_intervals_marks.append(interval_time)
    return time_intervals_marks


def get_time_intervals_seconds():
    dO = pd.read_csv('./Ofile.out.csv', sep=";")
    time_intervals_seconds = dO['interval_id'].unique()
    return time_intervals_seconds

# Initialize the app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css], title='TULIPE - Traffic management')
server = app.server

geo_data = None
dict_names = {}
dict_closeds_treets = {}
time_intervals_seconds = get_time_intervals_seconds()
time_intervals_string = get_time_intervals_string()
time_intervals_marks = get_time_intervals_marks()
len_time_intervals_string = len(time_intervals_string)
closed_roads = ["231483314", "832488061", "616545123", "150276002", "8384928", "606127853", "4730627", "4726710#0", "627916937", "4726681#0"] #This list has to come from the App (for now I left it like this)


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


style_color = assign("""function(feature, context){
    const {selected} = context.hideout;
    if(selected.includes(feature.properties.id)){   
        return {fillColor: '#3f3f3f', color: '#3f3f3f'} 
    }
    return {fillColor: '#1a73e8', color: '#1a73e8'}
}""")


on_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`${feature.properties.name} (id:${feature.properties.id})`)
}""")


on_each_feature_closed = assign("""function(feature, layer, context){
    const {colorProp, tname, closed} = context.hideout;
    if(closed.includes(feature.properties.id)){   
        layer.bindTooltip(`${feature.properties.name} (Closed street)`)
    }
    else{
        layer.bindTooltip(`${feature.properties.name} (${tname}: ${feature.properties[colorProp].toFixed()})`)
    }
}""")


style_color_closed = assign("""function(feature, context)
{
    const {colorscale, classes, colorProp, closed} = context.hideout;
    const value = feature.properties[colorProp];
    
    let fillColor;
    for (let i = 0; i < classes.length; ++i) {
        if (value > classes[i]) {
            fillColor = colorscale[i];  // set the fill color according to the class
        }
    }
    if(closed.includes(feature.properties.id)){   
        return {fillColor: '#a8a8a8', color: '#a8a8a8'} 
    }
    return {fillColor: fillColor, color: fillColor};
}
""")


modal_body = html.Div([
    html.Br(),
    html.B("Team: "), "Moisés Silva-Muñoz | Davide Andrea Guastella | Gianluca Bontempi",
    html.Br(),html.Br(),
    html.B("About: "), "The Machine Learning Group (MLG), founded in 2004 by G. Bontempi,  is a research unit of the Computer Science Department of the ULB (Université Libre de Bruxelles, Brussels, Belgium), Faculty of Sciences, currently co-headed by Prof. Gianluca Bontempi and Prof. Tom Lenaerts. MLG targets machine learning and behavioral intelligence research focusing on time series analysis, big data mining, causal inference, network inference, decision-making models and behavioral analysis with applications in data science, medicine, molecular biology, cybersecurity and social dynamics related to cooperation, emotions and others.",
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


collapse = html.Div(
    [
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    html.Div(id='map_plot')
                )
            ),
            id="collapse",
            is_open=True,
        ),
        html.Div(id='description_map_plot'),
        dbc.Button(
            "Closed streets", id="collapse-button", size="sm", className="mb-3", outline=True, color="warning", n_clicks=0, style={'marginTop': '1px'}),
    ]
)


@app.callback(
    Output('map_plot', 'children'),
    Output('description_map_plot', 'children'),
    [Input('traffic-dropdown', 'value'), Input('my-range-slider', 'value')])
def update_map_plot(traffic, timeframes):
    list_timeframe_string = []
    list_timeframe_split = []
    list_timeframe_in_seconds = []
    if timeframes[0] != timeframes[1]:
        time_frames = list(range(timeframes[0], timeframes[1]))
    else:
        time_frames = list(range(0, len_time_intervals_string))

    [list_timeframe_string.append(time_intervals_string[i]) for i in time_frames]
    timeframe_from = get_from_time_intervals_string(list_timeframe_string)
    timeframe_to = get_to_time_intervals_string(list_timeframe_string)

    [list_timeframe_split.append(re.split(" ", list_timeframe_string[i])) for i in range(len(list_timeframe_string))]
    [list_timeframe_in_seconds.append(selected_timeframe_in_seconds(list_timeframe_split[i])) for i in range(len(list_timeframe_split))]

    timeframe_from = get_from_time_intervals_string(list_timeframe_string)
    timeframe_to = get_to_time_intervals_string(list_timeframe_string)

    traffic_indicator = "edge_" + get_traffic_name(traffic)
    edgedata_df = pd.read_csv('./Rfile.out.csv', sep=";")

    map_to_geojson(edgedata_df, list_timeframe_in_seconds, traffic_indicator)
    classes = define_quantile(edgedata_df, list_timeframe_in_seconds, traffic_indicator)
    colorscale = ["#0F9D58", "#fff757", "#fbbc09", "#E94335", "#822F2B"]
    return html.Div([
                        dl.Map([
                            dl.TileLayer(),
                            dl.GeoJSON(data=read_geojson_deviations(), id="closed_roads_maps", hideout=dict(colorscale=colorscale, classes=classes, colorProp=traffic_indicator, tname=traffic, closed=closed_roads),
                                       style=style_color_closed, onEachFeature=on_each_feature_closed)
                        ], center=(50.83401264776447, 4.366035991425782), zoomControl=False, minZoom=15,
                            zoom=15, style={'height': '60vh', 'width': '100%'})
                    ], style={'backgroundColor': 'black', 'display': 'block'}), html.Div(['Showing results for ' + traffic + ' for the time interval: ' + timeframe_from + ' to '+ timeframe_to], style={'color':'#deb522'})


@app.callback(
    Output('collapse-button', 'children'),
    Input('collapse-button', 'n_clicks'))
def update_button(n_clicks):
    bool_disabled = n_clicks % 2
    if bool_disabled:
        return "Show map"
    else:
        return "Hide map"


MAX_OPTIONS_DISPLAY = 3300
# Generate options for the dropdown
dropdown_options = [{'label': title, 'value': title} for title in ['Travel time (seconds)', 'Density (vehicles/kilometres)','Occupancy (%)', 'Time loss (seconds)', 'Waiting time (seconds)', 'Speed (meters/seconds)', 'Speed relative (average speed / speed limit)', 'Sampled seconds (vehicles/seconds)']]
dropdown_options_vehicles = [{'label': title, 'value': title} for title in ['Duration (seconds)', 'Route length (meters)', 'Time loss (seconds)', 'Waiting time (seconds)']]
dropdown_options_timeframes = [{'label': title, 'value': title} for title in time_intervals_string]

offcanvas = html.Div([
            html.Div(id="filters",
                children=[html.H6("Filters")],
                style={'marginTop': '50px'},
            ),
            html.Div(id="street-ind",
                children="Street indicators",
                style={'marginTop': '15px'},
            ),
            dcc.Dropdown(
            id='traffic-dropdown',
            options=dropdown_options,
            value='Travel time (seconds)',
            placeholder='Select a traffic indicator...',
            searchable=True,
            style={'color':'black'}
            ),
            html.Div(id="time-frames",
                     children="Time frames",
                     style={'marginTop': '25px'},
                     ),
            html.Div([
                dcc.RangeSlider(min = 0, max= len(time_intervals_marks)-1, step=1, allowCross=False,
                                marks= {(i):{'label':str(time_intervals_marks[i]), 'style':{'transform': 'translateX(-20%) rotate(45deg)', "white-space": "nowrap", 'margin-top':'10px', "fontSize": "14px", 'color': '#deb522'}} for i in range(len(time_intervals_marks))},
                                value=[0, len(time_intervals_marks)-1], id='my-range-slider'
                                ),
                html.Div(id='output-container-range-slider')
            ], className="dbc", style={'padding':'10px 20px 45px 0px'}
            ),
            html.Div(id='string_names',
                     style={'marginTop': '15px'}),
            html.Div(id="select-street",
                     children="Select the streets to analyze",
                     style={'marginTop': '15px'},
                     ),
            html.Div([
                dl.Map([
                    dl.TileLayer(),
                    # From hosted asset (best performance).
                    dl.GeoJSON(data=read_geojson(), id="geojson", hideout=dict(selected=[]), style=style_color, hoverStyle=arrow_function(dict(weight=5, color='#00FFF7', dashArray='')), onEachFeature=on_each_feature,)
                ], center=(50.83401264776447, 4.366035991425782), zoomControl=False, minZoom=14, zoom=15, style={'height': '50vh', 'width': '100%'}), #window height
            ], style={'border':'3px'}),
            dcc.Store(id='dict_names'),
            ], style={'backgroundColor':"black",'color':'#deb522', 'width': '28%', "position": "fixed"} #FIXING
        )  #, 'width': '50vh' #width left column

@app.callback(Output("modal", "is_open"),
              [Input("open", "n_clicks"),
               #Input("close", "n_clicks")
               ],
              [State("modal", "is_open")])
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

@app.callback(Output("indicators_modal", "is_open"),
              [Input("indicators_open", "n_clicks"),
               #Input("indicators_close", "n_clicks")
               ],
              [State("indicators_modal", "is_open")])
def toggle_indicators_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.Div(id="Tulipe",
                children=[html.H5("Tulipe - Traffic management")],
                style={'marginTop': '5px', 'backgroundColor':"black",'color':'#deb522', 'width': '28%', "position": "fixed"}, #style={'marginTop': '5px', 'color': '#deb522'},
            ), width=5),
            dbc.Col(html.Div([' ']), width=5), #Hasta aqui
            dbc.Col(html.Div([
                html.Div(["", dbc.Button("About as", outline=True, color="link", size="sm", className="me-1", id="open", n_clicks=0, style={'color': '#deb522'}),
                          "  ",
                          dbc.Button("Indicators", outline=True, color="link", size="sm", className="me-1", id="indicators_open", n_clicks=0, style={'color': '#deb522'})],
                         style={'text-align': 'right'}),
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Machine Learning Group")),
                    dbc.ModalBody([modal_body]),
                ],
                    id="modal",
                    is_open=False,
                ),
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Indicator description")),
                    dbc.ModalBody([traffic_body]),
                ],
                    id="indicators_modal",
                    is_open=False
                )]
                ),width=2)
        ]),
        dbc.Row([
            dbc.Col(offcanvas, width=5),
            dbc.Col(
                html.Div([
                    html.Div([
                        html.Div(id="summary",
                        children=[html.H5("Summary")],
                        style={'marginTop': '0px', 'color': '#deb522'},
                        ),
                        html.Div(id="traffic_level",
                        children=["Traffic level   : Medium traffic"],
                        style={'marginTop': '5px', 'color': '#deb522'},
                        ),
                        html.Div(id="time_intervals",
                        children=["Time intervals: 12"],
                        style={'marginTop': '5px', 'color': '#deb522'},
                        ),
                        html.Div(id="street-deviations-results",
                        children=["Map of Street Deviations Results"],
                        style={'marginTop': '5px', 'color': '#deb522'},
                        ),
                        collapse,
                      ]),
                html.Hr(
                    style={'borderWidth': "0.2vh", "width": "100%", "borderColor": "#deb522", "opacity": "unset"}),
                html.Div(id="bystreets",
                         children=[html.H5("Results by streets")],
                         style={'marginTop': '5px', 'color': '#deb522'}
                         ),
                dcc.Loading([html.Div(id='tabs-content')],type='default',color='#deb522'),
                html.Br(),
                html.Hr(
                    style={'borderWidth': "0.2vh", "width": "100%", "borderColor": "#deb522", "opacity": "unset"}),
                html.Div(id="byvehicles",
                         children=[html.H5("Results by vehicles")],
                         style={'marginTop': '5px', 'color': '#deb522'}
                         ),
                html.Div(id="vehicle-ind",
                         children="Vehicle indicators",
                         style={'marginTop': '15px', 'color': '#deb522'},
                         ),
                dcc.Dropdown(
                    id='vehicle-dropdown',
                    options=dropdown_options_vehicles,
                    value='Duration (seconds)',
                    placeholder='Select a vehicular traffic indicator...',
                    searchable=True,
                    style={'color': 'black'}
                ),
                dcc.Loading([html.Div(id='tabs-content_vehicles')],type='default',color='#deb522')
                ]), width=7)
        ])
    ], style={'backgroundColor': 'black', 'padding': '0px'})
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
    [Input('traffic-dropdown', 'value'), Input('my-range-slider', 'value'), Input("geojson", "hideout"), Input("geojson", "n_clicks")]
)
def update_tab(traffic, timeframes, hideout, string_names):
    list_timeframe_string = []
    list_timeframe_split = []
    list_timeframe_in_seconds = []
    if timeframes[0] != timeframes[1]:
        time_frames = list(range(timeframes[0], timeframes[1]))
    else:
        time_frames = list(range(0, len_time_intervals_string))
    [list_timeframe_string.append(time_intervals_string[i]) for i in time_frames]
    geo_data = read_geojson()
    street_data_without, street_data_with = load_street_data(get_traffic_name(traffic))
    traffic_name = get_traffic(traffic)
    traffic_lowercase = get_traffic_lowercase(traffic)
    timeframe_from = get_from_time_intervals_string(list_timeframe_string)
    timeframe_to = get_to_time_intervals_string(list_timeframe_string)

    [list_timeframe_split.append(re.split(" ", list_timeframe_string[i])) for i in  range(len(list_timeframe_string))]
    [list_timeframe_in_seconds.append(selected_timeframe_in_seconds(list_timeframe_split[i])) for i in range(len(list_timeframe_split))]

    figure_bystreets = generate_visualizations_bystreets(street_data_without, street_data_with, traffic_name, traffic, dict_names, list_timeframe_in_seconds, list_timeframe_string, len_time_intervals_string, timeframe_from, timeframe_to)
    figure_impacted = generate_visualizations_impacted(street_data_without, street_data_with, traffic_name, traffic_lowercase, list_timeframe_in_seconds, list_timeframe_string, len_time_intervals_string, geo_data, hideout, dict_names, timeframe_from, timeframe_to)
    figure_byinterval = generate_visualizations_byinterval(street_data_without, street_data_with, traffic_name, traffic, list_timeframe_in_seconds, timeframe_from, timeframe_to, hideout, dict_names)

    return (
        html.Div([
            dcc.Graph(id='graph1', figure=figure_bystreets),
        ], style={'width': '100%', 'display': 'inline-block'}),
        html.Div(
            id="histogram_bystreet",
            children=[
                html.Div(
                    id="expl_bystreet_results",
                    children="Here I will include a short explanation of how to read the results.",
                ),
            ], style={'color': '#deb522'}),
        html.Br(),
        html.Div([
            dcc.Graph(id='graph1', figure=figure_impacted, style={'height': '800px'}),
        ], style={'width': '100%', 'display': 'inline-block'}),
        html.Div(
            id="histogram5",
            children=[
                html.Div(
                    id="intro5_histogram",
                    children="Here I will include a short explanation of how to read the results.",
                ),
            ], style={'color': '#deb522'}),
        html.Br(),
        html.Hr(style={'borderWidth': "0.2vh", "width": "100%", "borderColor": "#deb522", "opacity": "unset"}),
        html.Div(id="byinterval",
            children=[html.H5("Results by time interval")],
            style = {'marginTop': '5px', 'color': '#deb522'}
            ),
        html.Div([
            dcc.Graph(id='graph1', figure=figure_byinterval),
        ], style={'width': '100%', 'display': 'inline-block'}),
        html.Div(
            id="byinterval",
            children=[
                html.Div(
                    id="expl_byinterval_results",
                    children="Here I will include a short explanation of how to read the results.",
                ),
            ], style={'color': '#deb522'}),
    )


@app.callback(
    Output('tabs-content_vehicles', 'children'),
    [Input('vehicle-dropdown', 'value')]
    )
def update_tab(vehicle):
    vehicle_data_without, vehicle_data_with = load_vehicles_data()
    veh_traffic = get_veh_traffic(vehicle)
    figure_byvehicles = generate_visualizations_byvehicles(vehicle_data_without, vehicle_data_with, get_vehicle_name(vehicle), veh_traffic)
    return (
        html.Div([
            dcc.Graph(id='graph1', figure=figure_byvehicles),
        ], style={'width': '100%', 'display': 'inline-block'}),
        html.Div(
            id="byvehicles",
            children=[
                html.Div(
                    id="intro4_histogram",
                    children="Here I will include a short explanation of how to read the results.",
                ),
            ], style={'color': '#deb522'})
    )


if __name__ == '__main__':
    app.run_server(debug=False)