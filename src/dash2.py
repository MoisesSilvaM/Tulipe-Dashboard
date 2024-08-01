import plotly.express as px
import plotly.graph_objects as go
import os
from src.const import detectors_out_to_table
import re
import datetime
import time

def generate_visualizations(dfO, dfR, traffic_3, traffic, timeframe_in_seconds, timeframe_from, timeframe_to, hideout, dict_names):
    if bool(dict_names):
        my_list = [*hideout.values()]
        fig = generate_figure(dfO[timeframe_in_seconds], dfR[timeframe_in_seconds], traffic_3, traffic, timeframe_from, timeframe_to, my_list)
        return fig
    else:
        fig = generate_figure_all(dfO[timeframe_in_seconds], dfR[timeframe_in_seconds], traffic_3, traffic, timeframe_from, timeframe_to)
        return fig

def generate_figure_all(dfO, dfR, traffic_3, traffic, timeframe_from, timeframe_to):
    figures = go.Figure()
    figures.add_trace(go.Histogram(x=dfO, name="Without deviations"))
    figures.add_trace(go.Histogram(x=dfR, name="With deviations"))
    figures.update_layout(
        title_text='Frequency distribution of the results obtained by the vehicles in terms <br>of ' + traffic_3 + ' for the time interval ' + timeframe_from + ' to ' + timeframe_to,
        xaxis_title_text=traffic,  # xaxis label
        yaxis_title_text='Number of vehicles',  # yaxis label
        bargap=0.2,  # gap between bars of adjacent location coordinates
        bargroupgap=0.1  # gap between bars of the same location coordinates
    )
    figures.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return figures

def generate_figure(dfO, dfR, traffic_3, traffic, timeframe_from, timeframe_to, my_list):
    dO = dfO[dfO.index.isin(my_list[0])]
    dR = dfR[dfR.index.isin(my_list[0])]
    figures = go.Figure()
    figures.add_trace(go.Histogram(x=dO, name="Without deviations"))
    figures.add_trace(go.Histogram(x=dR, name="With deviations"))
    figures.update_layout(
        title_text='Frequency distribution of the results obtained by the vehicles in terms <br>of ' + traffic_3 + ' for the time interval ' + timeframe_from + ' to ' + timeframe_to,
        xaxis_title_text=traffic,  # xaxis label
        yaxis_title_text='Number of vehicles',  # yaxis label
        bargap=0.2,  # gap between bars of adjacent location coordinates
        bargroupgap=0.1  # gap between bars of the same location coordinates
    )
    figures.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return figures

def get_sec_to_date(seconds):
    min = seconds / 60
    return min