import plotly.express as px
import plotly.graph_objects as go
#from src.const import detectors_out_to_table



def generate_visualizations(dfO, dfR, VO, VR, traffic_name, vehicle, time_intervals, dict_names):
    vehicle_indicator = "tripinfo_" + vehicle
    #fig1 = generate_figure1(dfO, dfR, time_intervals[-1], traffic_name)
    fig2 = generate_figure2(dfO, dfR, traffic_name)
    #fig3 = generate_figure3(dfO, dfR, time_intervals[-1], traffic_name)
    #fig4 = generate_visualizations4(VO, VR, vehicle, vehicle_indicator)
    return fig2


def generate_figure1(dfO, dfR, name, traffic_name):
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(x=dfO[name], name="Without deviations"))
    fig1.add_trace(go.Histogram(x=dfR[name], name="With deviations"))
    fig1.update_layout(
        title_text='Distribution of the results for time interval ' + name + 'in terms of<br>' + traffic_name,  # title of plot
        xaxis_title_text=traffic_name,  # xaxis label
        yaxis_title_text='Number of vehicles',  # yaxis label
        bargap=0.2,  # gap between bars of adjacent location coordinates
        bargroupgap=0.1  # gap between bars of the same location coordinates
    )
    fig1.update_layout(template='plotly_dark', font=dict(color='yellow'))
    return fig1


def generate_figure2(dfO, dfR, traffic_name):
    df = dfR - dfO
    fig2 = px.strip(df, orientation="h")
    fig2.update_layout(template='plotly_dark', font=dict(color='yellow'))
    fig2.update_layout(
        title_text='Difference of streets with and without deviations in terms of<br>' + traffic_name,  # title of plot
        xaxis_title_text="Difference in terms of " + traffic_name,  # xaxis label
        yaxis_title_text='Time intervals',  # yaxis label
        bargap=0.2,  # gap between bars of adjacent location coordinates
        bargroupgap=0.1  # gap between bars of the same location coordinates
    )
    return fig2


# def generate_figure3(dfO, dfR, name, traffic):
#     dO = dfO.loc[:,
#          [name]]
#
#     dR = dfR.loc[:,
#          [name]]
#     df = dO.merge(dR, left_index=True, right_index=True, how="left")
#     value_x = name + '_x'
#     value_y = name + '_y'
#     df['diff'] = df[value_y].sub(df[value_x], axis=0)
#     df = df.sort_values(by=['diff'], ascending=False).head(15)
#     inf = ''
#     if traffic == "density":
#         inf = "Vehicle density (veh/km)"
#     elif traffic == "occupancy":
#         inf = "Occupancy (%)"
#     elif traffic == "timeLoss":
#         inf = "Time loss due to driving slower than desired (s)"
#     elif traffic == "traveltime":
#         inf = "Travel time (s)"
#     elif traffic == "waitingTime":
#         inf = "Waiting time (s)"
#     elif traffic == "speed":
#         inf = "Average speed (m/s)"
#     elif traffic == "speedRelative":
#         inf = "Speed relative (average speed / speed limit)"
#     elif traffic == "sampledSeconds":
#         inf = "Sampled seconds (veh/s)"
#     fig_bar = px.bar(df, y='diff', x=df.index, orientation='v',
#                      color='diff', text='diff',
#                      title='15 most impacted steets in terms of ' + inf + ' comparing with and without deviations for time interval ' + name,
#                      labels={'id': 'Id of the street', 'diff': 'Difference'}
#                      )
#     fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
#     fig_bar.update_layout(yaxis=dict(categoryorder='total ascending'))
#     fig_bar.update_layout(template='plotly_dark', font=dict(color='yellow'))
#     return fig_bar
