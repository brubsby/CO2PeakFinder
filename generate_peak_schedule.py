import argparse
import datetime

import math
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from graph_data import create_data_frames, load_measurements_file

MINUTE_RESOLUTION = 15  # minutes
TERTILE_Z_SCORE = 0.43073
PEAKEDNESS_NAMES_DICT = {
    1: "Off-Peak",
    2: "Mid-Peak",
    3: "Peak"
}
PEAKEDNESS_COLOR_DICT = {
    1: "g",
    2: "y",
    3: "r"
}


class TimeRange(object):
    """An object encapsulating a start time and an end time"""

    def __init__(self, start, end, intensity_category):
        self.start = start
        self.end = end
        self.intensity_category = intensity_category

    def __str__(self):
        return "{}-{} {}".format(self.start, self.end, self.name())

    def span(self):
        return time_diff(self.end, self.start).seconds / 60

    def name(self):
        return PEAKEDNESS_NAMES_DICT[self.intensity_category]

    def color(self):
        return PEAKEDNESS_COLOR_DICT[self.intensity_category]


def boolean_list_to_number(boolean_list):
    counter = 1
    for boolean in boolean_list:
        if boolean:
            return counter
        counter += 1
    raise AssertionError("Internal error, peakedness arrays malformed")


def time_diff(t1, t2):
    return datetime.datetime.combine(datetime.date.min, t1) - datetime.datetime.combine(datetime.date.min, t2)


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
            ranges.append(TimeRange(start_time, end_time, last_peakedness))
            start_time = time
            last_peakedness = aggregated_list[i]
    ranges.append(TimeRange(start_time, datetime.time.max, aggregated_list[-1]))
    return ranges


def is_weekend(date):
    return date.weekday() > 4


def smooth(x, window_len=11, window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s = np.r_[x[window_len - 1:0:-1], x, x[-2:-window_len - 1:-1]]
    # print(len(s))
    if window == 'flat':  # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')
    return y[math.floor(window_len/2-1):math.floor(-window_len/2)]


def smooth_data(data):
    new_dataframe = pd.DataFrame(index=data.index)
    columns = list(data)
    for column in columns:
        new_dataframe[column] = smooth(data[column])
    return new_dataframe


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

    weekday_days = len(np.unique(data.loc[data['is_weekend']].index.date))
    weekend_days = len(np.unique(data.loc[~data['is_weekend']].index.date))

    average_data = smooth_data(average_data)

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

    print("Data from {} weekdays and {} weekend days.".format(weekday_days, weekend_days))

    print()

    print("Weekday Ranges:")
    for weekday_range in weekday_ranges:
        print(weekday_range)
    print()
    print("Weekend Ranges:")
    for weekend_range in weekend_ranges:
        print(weekend_range)

    plt.subplot(2, 1, 1)
    plt.title("{} Carbon Intensity".format(args.country_code))
    plt.ylabel("Weekday Avg")
    plt.plot(average_data.index.time, average_data.weekday_avg)
    for weekday_range in weekday_ranges:
        plt.axvspan(weekday_range.start, weekday_range.end, alpha=0.5, facecolor=weekday_range.color())

    plt.subplot(2, 1, 2)
    plt.ylabel("Weekend Avg")
    plt.plot(average_data.index.time, average_data.weekend_avg)
    for weekend_range in weekend_ranges:
        plt.axvspan(weekend_range.start, weekend_range.end, alpha=0.5, facecolor=weekend_range.color())

    plt.show()

