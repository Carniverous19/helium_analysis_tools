"""

Functions to print information about a specific hotspot


"""
import argparse
import utils
from classes.Hotspots import Hotspots

def __heading2str__(heading):
    headingstr = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    heading = 5 * round(heading / 5, 0)
    idx = int(round(heading / 45)) % 8

    return f"{heading:3.0f} {headingstr[idx]:>2}"


def pocv10_violations(hotspot, chals):
    """

    :param hotspot: hotspot object to analyze
    :param chals: list of challenges
    :return:
    """
    H = Hotspots()
    haddr = hotspot['address']
    hlat, hlng = hotspot['lat'], hotspot['lng']
    transmits_w = dict(total=0, bad_rssi=0, bad_snr=0)
    receives_w = dict(total=0, bad_rssi=0, bad_snr=0)
    poc_rcv = dict(total=0, bad_rssi=0, bad_snr=0)
    bad_neighbors = dict()


    for chal in chals:
        transmitter = None
        for p in chal['path']:
            if p['challengee'] == haddr:
                for w in p['witnesses']:
                    dist = utils.haversine_km(
                        hlat, hlng,
                        H.get_hotspot_by_addr(w['gateway'])['lat'], H.get_hotspot_by_addr(w['gateway'])['lng'])
                    if dist < .3:
                        continue
                    rssi_lim = utils.max_rssi(dist)
                    snr_rssi_lim = utils.snr_min_rssi(w['snr'])
                    transmits_w['total'] += 1
                    if w['gateway'] not in bad_neighbors:
                        bad_neighbors[w['gateway']] = dict(rssi=0, snr=0, ttl=0)
                    bad_neighbors[w['gateway']]['ttl'] += 1
                    if w['signal'] > rssi_lim:
                        transmits_w['bad_rssi'] += 1
                        bad_neighbors[w['gateway']]['rssi'] += 1
                    if w['signal'] < snr_rssi_lim:
                        transmits_w['bad_snr'] += 1
                        bad_neighbors[w['gateway']]['snr'] += 1
                if p['receipt'] and transmitter:
                    dist = utils.haversine_km(
                        hlat, hlng,
                        H.get_hotspot_by_addr(transmitter)['lat'], H.get_hotspot_by_addr(transmitter)['lng']
                    )
                    rssi_lim = utils.max_rssi(dist)
                    snr_rssi_lim = utils.snr_min_rssi(p['receipt']['snr'])
                    poc_rcv['total'] += 1
                    if transmitter not in bad_neighbors:
                        bad_neighbors[transmitter] = dict(rssi=0, snr=0, ttl=0)
                    bad_neighbors[transmitter]['ttl'] += 1
                    if p['receipt']['signal'] > rssi_lim:
                        poc_rcv['bad_rssi'] += 1
                        bad_neighbors[transmitter]['rssi'] += 1
                    if p['receipt']['signal'] < snr_rssi_lim:
                        poc_rcv['bad_snr'] += 1
                        bad_neighbors[transmitter]['snr'] += 1
                        print(f"failed snr with lim {snr_rssi_lim}")
                        print(p['receipt'])
            else:
                for w in p['witnesses']:
                    if w['gateway'] != haddr:
                        continue
                    dist = utils.haversine_km(
                        hlat, hlng,
                        H.get_hotspot_by_addr(p['challengee'])['lat'], H.get_hotspot_by_addr(p['challengee'])['lng']
                    )
                    if dist < .3:
                        continue
                    rssi_lim = utils.max_rssi(dist)
                    snr_rssi_lim = utils.snr_min_rssi(w['snr'])
                    receives_w['total'] += 1
                    if p['challengee'] not in bad_neighbors:
                        bad_neighbors[p['challengee']] = dict(rssi=0, snr=0, ttl=0)
                    bad_neighbors[p['challengee']]['ttl'] += 1
                    if w['signal'] > rssi_lim:
                        receives_w['bad_rssi'] += 1
                        bad_neighbors[p['challengee']]['rssi'] += 1
                    if w['signal'] < snr_rssi_lim:
                        receives_w['bad_snr'] += 1
                        bad_neighbors[p['challengee']]['snr'] += 1
            transmitter = p['challengee']
    print(f"analyzed {len(chals)} challenges from {chals[0]['height']}-{chals[-1]['height']}")
    print(f"PoC v10 failures for {hotspot['name']}")

    print(F"SUMMARY")
    print(f"Category                   | Total | bad RSSI (%) | bad SNR (%) |")
    print(f"-----------------------------------------------------------------")
    print(f"Witnesses to hotspot >300m | {transmits_w['total']:5d} | {transmits_w['bad_rssi']:4d} ({transmits_w['bad_rssi']*100/max(1, transmits_w['total']):3.0f}%)  | {transmits_w['bad_snr']:4d} ({transmits_w['bad_snr']*100/max(1, transmits_w['total']):3.0f}%) |")
    print(f"Hotspot witnessing  >300m  | {receives_w['total']:5d} | {receives_w['bad_rssi']:4d} ({receives_w['bad_rssi']*100/max(1, receives_w['total']):3.0f}%)  | {receives_w['bad_snr']:4d} ({receives_w['bad_snr']*100/max(1, receives_w['total']):3.0f}%) |")
    print(f"Hotspot PoC receipts       | {poc_rcv['total']:5d} | {poc_rcv['bad_rssi']:4d} ({poc_rcv['bad_rssi']*100/max(1, poc_rcv['total']):3.0f}%)  | {poc_rcv['bad_snr']:4d} ({poc_rcv['bad_snr']*100/max(1, poc_rcv['total']):3.0f}%) |")

    print()
    print()
    print(f'BY "BAD" NEIGHBOR')
    print(f"Neighboring Hotspot           | dist km | heading | bad RSSI (%)  | bad SNR (%)   |")
    print(f"------------------------------+---------+---------+---------------+---------------|")
    hlat, hlng = hotspot['lat'], hotspot['lng']
    for n in bad_neighbors:
        if bad_neighbors[n]['rssi'] or bad_neighbors[n]['snr']:
            bad_h = H.get_hotspot_by_addr(n)
            dist_km, heading = utils.haversine_km(
                hlat,
                hlng,
                bad_h['lat'],
                bad_h['lng'],
                return_heading=True
            )

            print(f"{H.get_hotspot_by_addr(n)['name']:29} | {dist_km:5.1f}   | {__heading2str__(heading):7} | {bad_neighbors[n]['rssi']:2d}/{bad_neighbors[n]['ttl']:3d} ({bad_neighbors[n]['rssi']*100/bad_neighbors[n]['ttl']:3.0f}%) | {bad_neighbors[n]['snr']:2d}/{bad_neighbors[n]['ttl']:3d} ({bad_neighbors[n]['snr']*100/bad_neighbors[n]['ttl']:3.0f}%) |")

def poc_reliability(hotspot, challenges):
    """

    :param hotspot:
    :param challenges: list of challenges
    :return:
    """
    H = Hotspots()
    haddr = hotspot['address']

    days, remainder = divmod(challenges[0]['time'] - challenges[-1]['time'], 3600 * 24)
    hours = int(round(remainder / 3600, 0))
    print(f"analyzing {len(challenges)} challenges from block {challenges[0]['height']}-{challenges[-1]['height']} over {days} days, {hours} hrs")


    # iterate through challenges finding actual interactions with this hotspot
    results_tx = dict()  # key = tx addr, value = [pass, fail]
    results_rx = dict()  # key = rx addr, value = [pass, fail]
    for chal in challenges:
        pnext = chal['path'][-1]
        pnext_pass = pnext['witnesses'] or pnext['receipt']

        for p in chal['path'][:-1][::-1]:
            if pnext_pass or p['witnesses'] or p['receipt']:
                if pnext['challengee'] == haddr:
                    if p['challengee'] not in results_rx:
                        results_rx[p['challengee']] = [0, 0]
                    results_rx[p['challengee']][0 if pnext_pass else 1] += 1
                if p['challengee'] == haddr:
                    if pnext['challengee'] not in results_tx:
                        results_tx[pnext['challengee']] = [0, 0]
                    results_tx[pnext['challengee']][0 if pnext_pass else 1] += 1
                pnext_pass = True
            pnext = p

    hlat = hotspot['lat']
    hlon = hotspot['lng']

    def summary_table(results, hotspot_transmitting=False):

        other_pass = 0
        other_ttl = 0
        other_cnt = 0
        dist_min = 9999
        dist_max = 0

        if hotspot_transmitting:
            print(f"PoC hops from: {hotspot['name']}")
            print(f"{'to receiving hotspot':30} | {'dist km'} | {'heading'} | recv/ttl | recv % |")
        else:
            print(f"PoC hops to: {hotspot['name']}")
            print(f"{'from transmitting hotspot':30} | {'dist km'} | {'heading'} | recv/ttl | recv % |")
        print("-" * 72)

        for h in results.keys():
            ttl = results[h][0] + results[h][1]

            dist, heading = utils.haversine_km(
                hlat, hlon,
                H.get_hotspot_by_addr(h)['lat'], H.get_hotspot_by_addr(h)['lng'],
                return_heading=True
            )

            heading = 5 * round(heading / 5, 0)
            idx = int(round(heading / 45)) % 8
            headingstr = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
            if ttl == 1:
                other_ttl += ttl
                other_pass += results[h][0]
                other_cnt += 1
                dist_min = min(dist_min, dist)
                dist_max = max(dist_max, dist)
                continue

            print(f"{H.get_hotspot_by_addr(h)['name']:30} | {dist:6.1f}  | {heading:4.0f} {headingstr[idx]:>2} | {results[h][0]:3d}/{ttl:3d}  | {results[h][0] / ttl * 100:5.0f}% |")

        if other_ttl:
            print(f"other ({other_cnt:2}){' ' * 20} | {dist_min:4.1f}-{dist_max:2.0f} |   N/A   | {other_pass:3d}/{other_ttl:3d}  | {other_pass / other_ttl * 100:5.0f}% | ")

    summary_table(results_tx, hotspot_transmitting=True)
    print()
    print()
    summary_table(results_rx, hotspot_transmitting=False)

def main():
    parser = argparse.ArgumentParser("analyze hotspots", add_help=True)
    parser.add_argument('-x', help='report to run', choices=['poc_reliability', 'poc_v10'])

    parser.add_argument('-c', '--challenges', help='number of challenges to analyze, default:500', default=500, type=int)
    parser.add_argument('-n', '--name', help='hotspot name to analyze with dashes-between-words')
    parser.add_argument('-a', '--address', help='hotspot address to analyze')

    args = parser.parse_args()

    H = Hotspots()
    hotspot = None
    if args.name:
        hotspot = H.get_hotspot_by_name(args.name)
        if hotspot is None:
            raise ValueError(f"could not find hotspot named '{args.name}' use dashes between words")
    elif args.address:
        hotspot = H.get_hotspot_by_addr(args.address)
        if hotspot is None:
            raise ValueError(f"could not find hotspot address '{args.address}' ")
    else:
        raise ValueError("must provide hotspot address '--address' or name '--name'")

    challenges = utils.load_challenges(hotspot['address'], args.challenges)
    if args.x == 'poc_reliability':
        poc_reliability(hotspot, challenges)
    elif args.x == 'poc_v10':
        pocv10_violations(hotspot, challenges)


if __name__ == '__main__':
    main()



