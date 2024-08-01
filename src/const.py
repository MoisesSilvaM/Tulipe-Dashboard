import pandas as pd


def get_constants(movies, series, movies_splits, series_splits):
    num_of_works = movies.shape[0] + series.shape[0]

    countries_movies = movies_splits["country"]["country"].groupby(
        movies_splits["country"]["country"]).count().sort_values(ascending=False).index
    countries_series = series_splits["country"]["country"].groupby(
        movies_splits["country"]["country"]).count().sort_values(ascending=False).index
    num_of_countries = len(countries_movies.append(countries_series).unique())

    languages_movies = movies_splits["language"]["language"].groupby(
        movies_splits["language"]["language"]).count().sort_values(ascending=False).index
    language_series = series_splits["language"]["language"].groupby(
        movies_splits["language"]["language"]).count().sort_values(ascending=False).index
    num_of_lang = len(languages_movies.append(language_series).unique())
    avg_votes = int((movies["votes"].mean() + series["votes"].mean()) / 2)

    return num_of_works, num_of_countries, num_of_lang, avg_votes


def detectors_out_to_table(sim_data_df, field_name):
    # parse all the intervals in the edgedata file
    traffic_indicator = "edge_" + field_name
    time_intervals = sim_data_df['interval_id'].unique()
    data_dict = {}
    for time_interval in time_intervals:
        # get the DF related to time_interval
        data_interval = sim_data_df.loc[sim_data_df['interval_id'] == time_interval]
        # get the IDs of the edges that has an edgedata output value in the current time interval
        list_edges = data_interval['edge_id'].unique()
        for edge_id in list_edges:
            # get the data for all the edges
            data = data_interval.loc[data_interval['edge_id'] == edge_id][traffic_indicator]
            if time_interval not in data_dict:
                data_dict[time_interval] = {}
            data_dict[time_interval][edge_id] = data.item()
    return pd.DataFrame.from_dict(data_dict)
