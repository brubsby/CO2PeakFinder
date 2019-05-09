import argparse
import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from tzlocal import get_localzone

MINUTE_RESOLUTION = 5  # minutes


def is_weekend(date):
    return date.weekday() > 4


is_weekend_vectorized = np.vectorize(is_weekend)


def create_data_frames(measurements_array):
    data_frame = pd.DataFrame(index=pd.DatetimeIndex(pd.to_datetime(measurements_array[:, 0], unit='s')
                                                     .tz_localize('UTC').tz_convert(get_localzone().zone)),
                              data={"carbon_intensity": measurements_array[:, 1]})
    data_frame['is_weekend'] = is_weekend_vectorized(data_frame.index.date)
    average_data_frame = pd.DataFrame(
        index=pd.date_range(start=np.datetime64('2020-01-01'), periods=24 * (60 / MINUTE_RESOLUTION),
                            freq='{} min'.format(MINUTE_RESOLUTION)),
        data={'weekday_avg': None, 'weekend_avg': None})
    for start_datetime in average_data_frame.index:
        start_time = start_datetime.time()
        end_time = (start_datetime + datetime.timedelta(minutes=MINUTE_RESOLUTION)).time()
        between = data_frame.between_time(start_time, end_time, True, False)
        weekend = between.where(data_frame['is_weekend']).dropna()
        weekday = between.where(~data_frame['is_weekend']).dropna()
        average_data_frame.ix[start_datetime, 'weekday_avg'] = weekday.mean(0)['carbon_intensity']
        average_data_frame.ix[start_datetime, 'weekend_avg'] = weekend.mean(0)['carbon_intensity']

    return data_frame, average_data_frame


def load_measurements_file(filename):
    try:
        measurements_array = np.load(filename)
        measurements_array = measurements_array.reshape((-1, 3))
        print("{} loaded from disk.".format(filename))
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "Existing {} not found, you must collect data first to graph it.".format(filename)) from e
    return measurements_array


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', '--country-code', dest='country_code',
                        help='country code to build a peak hours chart for')
    args = parser.parse_args()

    data_filename = "{}.npy".format(args.country_code)

    measurements = load_measurements_file(data_filename)

    data, average_data = create_data_frames(measurements)

    plt.subplot(3, 1, 1)
    plt.title("{} Carbon Intensity".format(args.country_code))
    plt.ylabel("Weekday Avg")
    plt.plot(average_data.index.time, average_data.weekday_avg)

    plt.subplot(3, 1, 2)
    plt.ylabel("Weekend Avg")
    plt.plot(average_data.index.time, average_data.weekend_avg)

    plt.subplot(3, 1, 3)
    plt.xlabel("Time of Day")
    plt.ylabel("All Measurements")
    for _, frame in data.groupby(data.index.day):
        plt.plot(frame.index.time, frame.carbon_intensity, ".", markersize=1)
    plt.show()
