import argparse
from datetime import datetime
import time
import numpy as np

import requests
import os

from requests.adapters import HTTPAdapter
from urllib3 import Retry

MAX_RETRIES = 5
MAX_FAILURES = 6  # number of intervals that are allowed to fail before quitting


def above_five_minutes(seconds_string):
    value = int(seconds_string)
    above = max(value, 300)
    return above


def wait_for_modulo_time(modulo_amount):
    this_modulo_epoch_time = (time.time() // modulo_amount) * modulo_amount
    next_modulo_epoch_time = this_modulo_epoch_time + modulo_amount
    time.sleep(next_modulo_epoch_time - time.time())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', '--country-code', dest='country_code', help='country code to build a peak hours chart for')
    parser.add_argument('-s', '--seconds-between-requests', dest='seconds_between_requests', type=above_five_minutes,
                        help='seconds to wait between calling the co2signal API, must be above 300 (5 minutes)',
                        default=300)
    args = parser.parse_args()

    data_filename = "{}.npy".format(args.country_code)

    try:
        measurements = np.load(data_filename)
        measurements = measurements.reshape((-1, 3))
        print("{} loaded from disk, continuing.".format(data_filename))
    except FileNotFoundError:
        print("Existing {} not found, starting fresh.".format(data_filename))
        measurements = np.ndarray((0, 0))

    wait_for_modulo_time(args.seconds_between_requests)

    session = requests.Session()

    retries = Retry(total=MAX_RETRIES,
                    backoff_factor=5,
                    status_forcelist=[500, 502, 503, 504])

    session.mount('https://', HTTPAdapter(max_retries=retries))

    failures = 0
    while True:
        success = False
        for retry_count in range(MAX_RETRIES):
            request_time = time.time()
            try:
                response = session.get('https://api.co2signal.com/v1/latest?countryCode={country_code}'.format(
                    country_code=args.country_code), headers={'auth-token': os.environ['CO2SIGNAL_API_KEY']})
                if response.ok:
                    json_response = response.json()
                    data = json_response['data']
                    data_list = [request_time, data['carbonIntensity'], data['fossilFuelPercentage']]
                    print("{}: {}".format(datetime.fromtimestamp(request_time), data_list))
                    measurements = np.append(measurements, data_list)
                    np.save(data_filename, measurements)
                    failures = 0
                    success = True
                    break
                else:
                    backoff_time = pow(2, retry_count)
                    print('Got this response from co2signal:"{error}", exponentially backing off, {time} seconds.'
                          .format(error=getattr(response, "content", None), time=backoff_time))
                    time.sleep(backoff_time)
                    success = False
            except ConnectionError as e:
                backoff_time = pow(2, retry_count)
                print('Got an connection error when trying to query co2signal, exponentially backing off, '
                      '{time} seconds.'.format(error=repr(e), time=backoff_time))
                time.sleep(backoff_time)
        if not success:
            failures += 1
            if failures > MAX_FAILURES:
                raise SystemError('Number of data collection windows missed exceeded maximum failures allowed: {}'
                                  .format(MAX_FAILURES))
        wait_for_modulo_time(args.seconds_between_requests)
