import argparse
from datetime import datetime
import time
import numpy as np

import requests
import os


def above_five_minutes(seconds_string):
    value = int(seconds_string)
    above = max(value, 300)
    return above


def wait_for_modulo_time(modulo_amount):
    this_modulo_epoch_time = (time.time() // modulo_amount) * modulo_amount
    next_modulo_epoch_time = this_modulo_epoch_time + modulo_amount
    time.sleep(next_modulo_epoch_time - time.time())


parser = argparse.ArgumentParser(description='')
parser.add_argument('-c', '--country-code', dest='country_code', help='country code to build a peak hours chart for')
parser.add_argument('-s', '--seconds-between-requests', dest='seconds_between_requests', type=above_five_minutes,
                    help='seconds to wait between calling the co2signal API, must be above 300 (5 minutes)',
                    default=300)
args = parser.parse_args()

data_filename = "{}.npy".format(args.country_code)

try:
    measurements = np.load(data_filename)
    measurements = measurements.reshape((-1,3))
    print("{} loaded from disk, continuing.".format(data_filename))
except FileNotFoundError:
    print("Existing {} not found, starting fresh.".format(data_filename))
    measurements = np.ndarray((0, 0))

wait_for_modulo_time(args.seconds_between_requests)

while True:
    request_time = time.time()

    response = requests.get('https://api.co2signal.com/v1/latest?countryCode={country_code}'.format(
        country_code=args.country_code), headers={'auth-token': os.environ['CO2SIGNAL_API_KEY']})
    if response.ok:
        json_response = response.json()
        data = json_response['data']
        data_list = [request_time, data['carbonIntensity'], data['fossilFuelPercentage']]
        print("{}: {}".format(datetime.fromtimestamp(request_time), data_list))
        measurements = np.append(measurements, data_list)
        np.save(data_filename, measurements)
    else:
        raise ValueError(response.content)

    wait_for_modulo_time(args.seconds_between_requests)
