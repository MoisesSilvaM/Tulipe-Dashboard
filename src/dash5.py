import plotly.express as px
import datetime
import plotly.graph_objects as go
from src.const import detectors_out_to_table
import json


def generate_visualizations(dfO, dfR, traffic_name, traffic_3, traffic_lowercase, timeframe_in_seconds, timeframe_split,
                            geojson):
    fig = generate_figure(dfO, dfR, traffic_name, traffic_3, traffic_lowercase, timeframe_in_seconds, timeframe_split,
                          geojson)
    return fig


def generate_figure(dfO, dfR, traffic_name, traffic_3, traffic_lowercase, timeframe_in_seconds, timeframe_split,
                    geojson):
    dO = dfO.loc[:,
         [timeframe_in_seconds]]
    dR = dfR.loc[:,
         [timeframe_in_seconds]]
    df = dO.merge(dR, left_index=True, right_index=True, how="left")
    value_x = timeframe_in_seconds + '_x'
    value_y = timeframe_in_seconds + '_y'
    df['difference'] = df[value_y].sub(df[value_x], axis=0)
    df = df.sort_values(by=['difference'], ascending=False).head(15)
    seconds = get_response(traffic_lowercase)
    if traffic_lowercase == 'time loss (seconds)' or traffic_lowercase == 'travel time (seconds)' or traffic_lowercase == 'waiting time (seconds)':
        print("Si")
        df['diff_dates'] = df['difference'].apply(get_sec_to_date)
    else:
        print("No")
        df['diff_dates'] = df['difference'].apply(get_copy_sec)
    print(df)
    index_names = df.index.values.tolist()
    list_names = []
    for elem in index_names:
        for i in geojson['features']:
            if i["properties"].get("id") == elem:
                list_names.append(i["properties"].get("name") + ' (id:' + i["properties"].get("id") + ')')
    fig = px.bar(df, y='difference', x=df.index, orientation='v', text='diff_dates',
                 # color='diff_dates',
                 title='15 most impacted steets in terms of ' + traffic_name + ' for the time interval<br>' +
                       timeframe_split[0] + ' to ' + timeframe_split[2],
                 # labels={'id': 'Id of the street', 'diff_dates': 'Difference in ' + traffic_lowercase}
                 )
    if traffic_lowercase == 'time loss (seconds)' or traffic_lowercase == 'travel time (seconds)' or traffic_lowercase == 'waiting time (seconds)':
        fig.update_traces(texttemplate='%{text}', textposition='outside')
    else:
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    # fig.update_layout(yaxis=dict(categoryorder='total ascending'))
    fig.update_layout(xaxis_title_text='Street')
    fig.update_layout(yaxis_title_text='Difference in ' + get_traffic_y_axis(traffic_name))
    fig.update_layout(template='plotly_dark', font=dict(color='yellow'))
    fig.update_layout(xaxis=dict(tickmode='array', tickvals=df.index, ticktext=list_names))
    fig.update_layout(yaxis=dict(showticklabels=False))
    return fig


def get_sec_to_date(seconds):
    dates = str(datetime.timedelta(seconds=int(seconds)))
    return dates


def get_copy_sec(seconds):
    return seconds


def get_traffic_y_axis(traffic):
    inf = ''
    if traffic == "vehicle density (vehicles/kilometres)":
        inf = "vehicle density (vehicles/kilometres)"
    elif traffic == "vehicle occupancy (%)":
        inf = "vehicle occupancy (%)"
    elif traffic == "time lost by vehicles due to driving slower than the desired speed (seconds)":
        inf = "time loss (h:mm:ss)"
    elif traffic == "travel time (seconds)":
        inf = "travel time (h:mm:ss)"
    elif traffic == "waiting time (seconds))":
        inf = "waiting time (h:mm:ss)"
    elif traffic == "average speed (meters/seconds)":
        inf = "average speed (meters/seconds)"
    elif traffic == "speed relative (average speed / speed limit)":
        inf = "speed relative (average speed / speed limit)"
    elif traffic == "Sampled seconds (vehicles/seconds)":
        inf = "Sampled seconds (vehicles/seconds)"
    return inf

def get_response(traffic):
    print(traffic)
    inf = False
    if traffic == 'time loss (seconds)':
        inf = True
    elif traffic == 'travel time (seconds)':
        inf = True
    # elif traffic == "waiting time (seconds)":
    #     inf = True
    return inf
