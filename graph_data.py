import numpy as np
import argparse
import pandas as pd
from matplotlib import pyplot as plt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', '--country-code', dest='country_code',
                        help='country code to build a peak hours chart for')
    args = parser.parse_args()

    data_filename = "{}.npy".format(args.country_code)

    try:
        measurements = np.load(data_filename)
        measurements = measurements.reshape((-1, 3))
        print("{} loaded from disk.".format(data_filename))
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "Existing {} not found, you must collect data first to graph it.".format(data_filename)) from e

    data = pd.DataFrame(index=pd.DatetimeIndex(measurements[:, 0].astype('datetime64[s]')),
                        data={"carbon_intensity": measurements[:, 1]})

    plt.title("{} Carbon Intensity".format(args.country_code))
    plt.xlabel("Time of Day")
    plt.ylabel("Carbon Intensity")
    for _, frame in data.groupby(data.index.day):
        plt.plot(frame.index.time, frame.carbon_intensity)
    plt.show()
    input()
