import argparse
import datetime

from graph_data import create_data_frames, load_measurements_file

import numpy as np

MINUTE_RESOLUTION = 5  # minutes
TERTILE_Z_SCORE = 0.43073


def time_of_day_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


def is_weekend(date):
    return date.weekday() > 4


time_of_day_seconds_vectorized = np.vectorize(time_of_day_seconds)
is_weekend_vectorized = np.vectorize(is_weekend)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', '--country-code', dest='country_code',
                        help='country code to build a peak hours chart for')
    parser.add_argument('-f', '--filter-decimal', dest='filter_percent',
                        help='filter days out if they have less than (<f>*100)% of samples')
    args = parser.parse_args()

    data_filename = "{}.npy".format(args.country_code)

    measurements = load_measurements_file(data_filename)

    data, average_data = create_data_frames(measurements)

    weekday_mean = average_data['weekday_avg'].mean()
    weekday_std_dev = average_data['weekday_avg'].std()
    weekday_low_tertile = weekday_mean - (weekday_std_dev * TERTILE_Z_SCORE)
    weekday_high_tertile = weekday_mean + (weekday_std_dev * TERTILE_Z_SCORE)

    weekend_mean = average_data['weekend_avg'].mean()
    weekend_std_dev = average_data['weekend_avg'].std()
    weekend_low_tertile = weekend_mean - (weekend_std_dev * TERTILE_Z_SCORE)
    weekend_high_tertile = weekend_mean + (weekend_std_dev * TERTILE_Z_SCORE)

    weekday_off_peak_times = average_data[average_data['weekday_avg'] <= weekday_low_tertile].dropna().index.time
    weekday_mid_peak_times = average_data[average_data['weekday_avg'] > weekday_low_tertile].dropna()[
        average_data['weekday_avg'] < weekday_high_tertile].dropna().index.time
    weekday_peak_times = average_data[average_data['weekday_avg'] >= weekday_high_tertile].dropna().index.time

    weekend_off_peak_times = average_data[average_data['weekend_avg'] <= weekend_low_tertile].dropna().index.time
    weekend_mid_peak_times = average_data[average_data['weekend_avg'] > weekend_low_tertile].dropna()[
        average_data['weekend_avg'] < weekend_high_tertile].dropna().index.time
    weekend_peak_times = average_data[average_data['weekend_avg'] >= weekend_high_tertile].dropna().index.time

    interval_times = np.array(
        [datetime.time(hour=minute // 60, minute=minute % 60) for minute in range(0, 60 * 24, MINUTE_RESOLUTION)])
    
    weekday_off_peak_mask = np.isin(interval_times, weekday_off_peak_times)
    weekday_mid_peak_mask = np.isin(interval_times, weekday_mid_peak_times)
    weekday_peak_mask = np.isin(interval_times, weekday_peak_times)

    weekend_off_peak_mask = np.isin(interval_times, weekend_off_peak_times)
    weekend_mid_peak_mask = np.isin(interval_times, weekend_mid_peak_times)
    weekend_peak_mask = np.isin(interval_times, weekend_peak_times)

    for i, time in enumerate(interval_times):
        # TODO aggregate time intervals from masks
        pass
