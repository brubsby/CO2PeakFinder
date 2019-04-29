import argparse
import time
import numpy as np

import requests
import os


def above_five_minutes(seconds_string):
    value = int(seconds_string)
    above = max(value, 300)
    return above


parser = argparse.ArgumentParser(description='')
parser.add_argument('-c', '--country-code', dest='country_code', help='country code to build a peak hours chart for')
parser.add_argument('-s', '--seconds-between-requests', dest='seconds_between_requests', type=above_five_minutes,
                    help='seconds to wait between calling the co2signal API, must be above 300 (5 minutes)',
                    default=300)
args = parser.parse_args()

measurements = np.ndarray((0, 0))


while True:
    request_time = time.time()

    response = requests.get('https://api.co2signal.com/v1/latest?countryCode={country_code}'.format(
        country_code=args.country_code), headers={'auth-token': os.environ['CO2SIGNAL_API_KEY']})
    if response.ok:
        json_response = response.json()
        data = json_response['data']
        data_list = [request_time, data['carbonIntensity'], data['fossilFuelPercentage']]
        print(data_list)
        measurements = np.append(measurements, data_list)
        np.save(args.country_code, measurements)
    else:
        raise ValueError(response.content)

    time_elapsed = time.time() - request_time
    sleep_time = args.seconds_between_requests - time_elapsed
    time.sleep(sleep_time)
