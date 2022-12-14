#!/usr/bin/env python3.8
import json
import urllib.request
import urllib.error
import time
import argparse
from math import radians, cos, sin, asin, sqrt, log10, ceil, degrees, atan2

# compass_headings = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
compass_headings = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]
headers = {"User-Agent": "Helium Analysis Tools"}


def api_call(base="https://api.helium.io/v1/", path=""):
    if base[-1] != "/":
        base += "/"
    url = f"{base}{path}"

    req = urllib.request.Request(url, headers=headers)

    for i in range(0, 3):
        try:
            return json.load(urllib.request.urlopen(req))
        except (urllib.error.HTTPError, json.JSONDecodeError) as e:
            time.sleep(0.25 + 1 * i)


def load_challenges(haddr, numchalls=500, cursor=None):
    chals = []
    if numchalls > 5000:
        raise ValueError(f"invalid number of challenges to load")
    while len(chals) < numchalls:
        path = f"hotspots/{haddr}/challenges"
        if cursor:
            path += f"?cursor={cursor}"
        result = api_call(path=path)
        print(f"-I- loaded {len(result['data'])} challenges")
        cursor = result.get("cursor")

        chals.extend(result["data"])
        if not cursor:
            break
    too_old_idx = None
    for i in range(0, len(chals)):
        if chals[i]["height"] < 430000:
            too_old_idx = i
            break
    if too_old_idx is not None:
        chals = chals[:too_old_idx]

    return chals


def hip15_rewards(nwitnesses, vars):
    """
    Calculates HIP15 rewward units for transmitter and receiver
    :param nwitnesses:
    :param vars: chain variables or a dict contain those used for hip15
    :return:
    """
    if nwitnesses == 0:
        return 0, 0
    tx_ru = 1
    rx_ru = 1
    N = vars.get("witness_redundancy", 4)
    r = vars.get("poc_reward_decay_rate", 0.8)

    hip15_rus = (N - (1 - pow(r, nwitnesses - N))) / nwitnesses
    if nwitnesses <= N:
        rw_tx = nwitnesses / N
        rw_rx = 1
    else:
        rw_tx = 1 + (1 - pow(r, nwitnesses - N))
        rw_rx = (N - (1 - pow(r, nwitnesses - N))) / nwitnesses

    return rw_tx, rw_rx


def load_hotspots(force=False):
    try:
        if force:
            raise FileNotFoundError
        with open("hotspots.json", "r") as fd:
            dat = json.load(fd)
            if time.time() - dat["time"] > 72 * 3600:
                print(
                    f"-W- hotspot cache is over 2 days old consider refreshing 'python3 utils.py -x refresh_hotspots'"
                )
                # raise FileNotFoundError
            if not dat["hotspots"]:
                raise FileNotFoundError
            return dat["hotspots"]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        with open("hotspots.json", "w") as fd:
            cursor = None
            hotspots = []
            while True:
                url = "https://api.helium.io/v1/hotspots"
                if cursor:
                    url += "?cursor=" + cursor

                req = urllib.request.Request(url, headers=headers)

                try:
                    resp = urllib.request.urlopen(req)
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        time.sleep(5)
                        continue
                    elif e.code == 503:
                        # Service Unavailable
                        time.sleep(5)
                        continue
                    elif e.code == 500:
                        print(f"-W- found error 500: "+str(e))
                        time.sleep(10)
                        continue

                json_data = json.load(resp)
                cursor = json_data.get("cursor")

                if not json_data.get("data"):
                    break
                # print(resp.get('data'))
                hotspots.extend(json_data.get("data"))
                print(f"-I- found {len(hotspots)} hotspots")
                if len(json_data.get("data", [])) < 1000 or cursor is None:
                    break

            dat = dict(time=int(time.time()), hotspots=hotspots)
            json.dump(dat, fd, indent=2)
        return hotspots


def heading_to_compass(heading_degrees):

    idx = int(round(heading_degrees / (360 / len(compass_headings)))) % len(
        compass_headings
    )

    return compass_headings[idx]


def compass_to_heading(compass_heading):
    compass_heading = compass_heading.upper()
    idx = None
    try:
        idx = compass_headings.index(compass_heading)
    except ValueError:
        pass

    if idx is None:
        return idx

    return 360 / len(compass_headings) * idx


def haversine_km(lat1, lon1, lat2, lon2, return_heading=False):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles

    X = cos(lat2) * sin(dlon)
    Y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    b_rad = atan2(X, Y)
    b = (degrees(b_rad) + 360) % 360
    if return_heading:
        return c * r, b
    return c * r


def max_rssi(dist_km):
    if dist_km < 0.001:
        return -1000
    return 28 + 1.8 * 2 - (20 * log10(dist_km) + 20 * log10(915) + 32.44)


def snr_min_rssi(snr):
    """
    retuns the minimum rssi valid at given snr
    :param snr:
    :return:
    """
    # ce
    snr = int(ceil(snr))

    snr_table = {
        12: (-90, -35),
        4: (-115, -112),
        -4: (-125, -125),
        16: (-90, -35),
        -15: (-124, -124),
        -6: (-124, -124),
        -1: (-125, -125),
        -2: (-125, -125),
        5: (-115, -100),
        14: (-90, -35),
        -11: (-125, -125),
        9: (-95, -45),
        10: (-90, -40),
        -12: (-125, -125),
        -7: (-123, -123),
        -10: (-125, -125),
        -14: (-125, -125),
        2: (-117, -112),
        6: (-113, -100),
        -5: (-125, -125),
        3: (-115, -112),
        -3: (-125, -125),
        1: (-120, -117),
        7: (-108, -45),
        8: (-105, -45),
        -8: (-125, -125),
        0: (-125, -125),
        13: (-90, -35),
        -16: (-123, -123),
        -17: (-123, -123),
        -18: (-123, -123),
        -19: (-123, -123),
        -20: (-123, -123),
        15: (-90, -35),
        -9: (-125, -125),
        -13: (-125, -125),
        11: (-90, -35),
    }
    if snr not in snr_table:
        return 1000
    return snr_table[snr][0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser("simple utilities")
    parser.add_argument(
        "-x",
        choices=["refresh_hotspots"],
        help="action to take",
        default="refresh_hotspots",
    )
    args = parser.parse_args()
    if args.x == "refresh_hotspots":
        load_hotspots(True)
