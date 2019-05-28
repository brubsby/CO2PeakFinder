import argparse
import datetime

from graph_data import create_data_frames, load_measurements_file

import numpy as np

MINUTE_RESOLUTION = 5  # minutes
TERTILE_Z_SCORE = 0.43073
PEAKEDNESS_NAMES_DICT = {
    1: "Off-Peak",
    2: "Mid-Peak",
    3: "Peak"
}


class TimeRange(object):
    """An object encapsulating a start time and an end time"""

    def __init__(self, start, end, name=None):
        self.start = start
        self.end = end
        self.name = name

    def __str__(self):
        return "{}-{} {}".format(self.start, self.end, self.name)

    def span(self):
        return self.end - self.start


def boolean_list_to_number(boolean_list):
    counter = 1
    for boolean in boolean_list:
        if boolean:
            return counter
        counter += 1
    raise AssertionError("Internal error, peakedness arrays malformed")


def time_of_day_seconds(time):
    return time.hour * 3600 + time.minute * 60 + time.second


def create_ranges(aggregated_list):
    ranges = []
    start_time = None
    last_peakedness = None
    for i, time in enumerate(interval_times):
        if start_time is None:
            start_time = time
            last_peakedness = aggregated_list[i]
            continue
        if last_peakedness != aggregated_list[i]:
            end_time = time
            ranges.append(TimeRange(start_time, end_time, PEAKEDNESS_NAMES_DICT[last_peakedness]))
            start_time = time
            last_peakedness = aggregated_list[i]
    return ranges


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

    weekday_stacked = np.stack([weekday_off_peak_mask, weekday_mid_peak_mask, weekday_peak_mask])
    weekday_aggregated = np.apply_along_axis(boolean_list_to_number, 0, weekday_stacked)

    weekend_stacked = np.stack([weekend_off_peak_mask, weekend_mid_peak_mask, weekend_peak_mask])
    weekend_aggregated = np.apply_along_axis(boolean_list_to_number, 0, weekend_stacked)

    weekday_ranges = create_ranges(weekday_aggregated)
    weekend_ranges = create_ranges(weekend_aggregated)

    # weekday_ranges = delete_small_ranges(weekday_aggregated)
    # weekend_ranges = delete_small_ranges(weekend_aggregated)

    print("Weekday Ranges:")
    for weekday_range in weekday_ranges:
        print(weekday_range)
    print()
    print("Weekend Ranges:")
    for weekend_range in weekend_ranges:
        print(weekend_range)

