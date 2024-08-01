import re
import plotly.express as px
import plotly.graph_objects as go
import json
from urllib.request import urlopen
import pandas as pd
import folium
import plotly.express as px
import geopandas as gpd
import shapely.geometry
import numpy as np
import wget
import dash_leaflet as dl
from dash import Dash, html, dcc

def generate_visualizations(dfO, dfR, traffic_name, traffic, time_intervals_seconds, dict_names, time_intervals):
    if bool(dict_names):
        if len(dict_names) == 1:
            fig = generate_figure1(dfO, dfR, traffic_name, traffic, time_intervals, dict_names)
            return fig
        else:
            fig = generate_figure2(dfO, dfR, traffic_name, traffic, time_intervals, dict_names)
            return fig
    else:
        dO = dfO.mean()
        dR = dfR.mean()
        dO.drop(dO.index[-1], inplace=True)
        dR.drop(dR.index[-1], inplace=True)
        fig = generate_figure0(dO, dR, traffic_name, traffic, time_intervals)
        return fig

def generate_figure1(dfO, dfR, traffic_name, traffic, time_intervals, dict_names):
    times = time_intervals[1:]
    name = ''
    fig1 = go.Figure()
    for (key, value) in dict_names.items():
        k = key
        name = value + ' (id:' + key + ')'
        ddO = dfO.loc[k]
        ddR = dfR.loc[k]
        ddO.drop(ddO.index[-1], inplace=True)
        ddR.drop(ddR.index[-1], inplace=True)
    fig1.add_trace(go.Scatter(x=ddO.index, y=ddO.values,
                                  mode='lines+markers',
                                  name='without deviations'))
    fig1.add_trace(go.Scatter(x=ddR.index, y=ddR.values,
                                  mode='lines+markers',
                                  name='with deviations'))
    fig1.update_layout(yaxis_title=traffic)
    fig1.update_layout(
        title_text='Comparing the ' + traffic_name + ' for the vehicles that originally passed<br>through ' + name + ' <br>for all the time intervals',
        xaxis_title_text='Time interval',
    )
    fig1.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=ddO.index,
            ticktext=times)
    )
    fig1.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return fig1

def generate_figure2(dfO, dfR, traffic_name, traffic, time_intervals, dict_names):
    times = time_intervals[1:]
    name = ''
    fig1 = go.Figure()
    for (key, value) in dict_names.items():
        k = key
        name = value + ' (id:' + key + ')'
        ddO = dfO.loc[k]
        ddR = dfR.loc[k]
        ddO.drop(ddO.index[-1], inplace=True)
        ddR.drop(ddR.index[-1], inplace=True)
        fig1.add_trace(go.Scatter(x=ddO.index, y=ddO.values,
                                  mode='lines+markers',
                                  name=name+'<br>without deviations'))
        fig1.add_trace(go.Scatter(x=ddR.index, y=ddR.values,
                                  mode='lines+markers',
                                  name=name+'<br>with deviations'))
    fig1.update_layout(yaxis_title=traffic)
    fig1.update_layout(
        title_text='Comparing the ' + traffic_name + ' for the vehicles that originally passed<br>through some streets for all the time intervals',
        xaxis_title_text='Time interval',
    )
    fig1.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=ddO.index,
            ticktext=times)
    )
    fig1.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return fig1

def generate_figure0(dfO, dfR, traffic_name, traffic, time_intervals):
    times = time_intervals[1:]
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dfO.index, y=dfO.values,
                              mode='lines+markers',
                              name='without deviations'))
    fig1.add_trace(go.Scatter(x=dfR.index, y=dfR.values,
                              mode='lines+markers',
                              name='with deviations'))

    fig1.update_layout(yaxis_title=traffic)
    fig1.update_layout(
        title_text='Comparing the average ' + traffic_name + ' for the vehicles on all the streets<br>for all the time intervals',
        xaxis_title_text='Time interval',
    )
    fig1.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=dfO.index,
            ticktext=times)
    )
    fig1.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return fig1

# def generate_figure2(VO, VR, vehicle, edge_id):
#     vehicle_indicator = 'tripinfo_' + vehicle
#
#     vO = VO.loc[:,
#          ['tripinfo_id',
#           vehicle_indicator]]
#
#     vR = VR.loc[:,
#          ['tripinfo_id',
#           vehicle_indicator]]
#     veh = []
#     with open("./osm.passenger.rou.xml", 'r') as file:
#         lines = file.readlines()
#         for i in range(len(lines)):
#             if edge_id in lines[i]:
#                 r = re.split('\"', lines[i - 1])
#                 veh.append(int(r[1]))
#
#     dvO = vO[vO['tripinfo_id'].isin(veh)]
#     dvR = vR[vR['tripinfo_id'].isin(veh)]
#     dvO = dvO.set_index('tripinfo_id')
#     dvR = dvR.set_index('tripinfo_id')
#     dvO_aligned, dvR_aligned = dvO.align(dvR, fill_value=0)
#     df = dvR_aligned - dvO_aligned
#     value = ''
#     if vehicle == 'duration':
#         value = 'duration of the trips (s)'
#     if vehicle == 'routeLength':
#         value = 'length of the route (m)'
#     if vehicle == 'timeLoss':
#         value = 'time loss (s)'
#     if vehicle == 'waitingTime':
#         value = 'waiting time (s)'
#     fig2 = px.strip(df, orientation="h")
#     fig2.update_yaxes(showticklabels=False)
#     fig2.update_layout(
#         title_text='Difference in the ' + value + ' with and without deviations for the vehicles that originally passed through ' + edge_id,
#         xaxis_title_text=value,
#         yaxis_title_text='Vehicles',  # yaxis label
#         bargap=0.2,  # gap between bars of adjacent location coordinates
#         bargroupgap=0.1  # gap between bars of the same location coordinates
#     )
#     fig2.update_layout(template='plotly_dark', font=dict(color='yellow'))
#
#     return fig2
#
#
# def generate_figure3(dfO, dfR, name, traffic_name):
#     dO = dfO.loc[:,
#          [name]]
#     dR = dfR.loc[:,
#          [name]]
#     df = dO.merge(dR, left_index=True, right_index=True, how="left")
#     value_x = name + '_x'
#     value_y = name + '_y'
#     df['diff'] = df[value_y].sub(df[value_x], axis=0)
#     df = df.sort_values(by=['diff'], ascending=False).head(15)
#     fig3 = px.bar(df, y='diff', x=df.index, orientation='v',
#                   color='diff', text='diff',
#                   title='15 most impacted steets in terms of ' + traffic_name + ' comparing with and without deviations for time interval ' + name,
#                   labels={'id': 'Id of the street', 'diff': 'Difference'}
#                   )
#     fig3.update_traces(texttemplate='%{text}', textposition='outside')
#     fig3.update_layout(yaxis=dict(categoryorder='total ascending'))
#     fig3.update_layout(xaxis_title_text='Id of the street')
#     fig3.update_layout(template='plotly_dark', font=dict(color='yellow'))
#     return fig3
