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


def poc_summary(hotspot, chals, expected_chal_interval=120):

    haddr = hotspot['address']
    init_target = 0
    challenger_count = 0
    last_target = None
    last_challenger = None
    max_target_delta = 0
    max_challenger_delta = 0
    untargetable_count = 0
    print(f"PoC Summary Report for: {hotspot['name']}")
    planned_count = [0] * 5
    tested_count = [0] * 5
    passed_count = [0] * 5
    for c in chals:
        if c['path'][0]['challengee'] == haddr:
            if last_target is None:
                last_target = c['height']
            else:
                max_target_delta = max(max_target_delta, last_target - c['height'])
                last_target = c['height']
            init_target += 1
        elif c['challenger'] == haddr:
            if last_challenger is None:
                last_challenger = c['height']
            else:
                challenger_delta = last_challenger - c['height']
                if challenger_delta > 300:
                    untargetable_count += challenger_delta - 300
                max_challenger_delta = max(max_challenger_delta, challenger_delta)
                last_challenger = c['height']
            challenger_count += 1

        next_passed = False
        next_addr = ''
        for i in range(len(c['path'])-1, -1, -1):

            passed = c['path'][i]['witnesses'] or (c['path'][i]['receipt'] and i > 0) or next_passed
            if c['path'][i]['challengee'] == hotspot['address']:
                planned_count[i] += 1
                if passed:
                    passed_count[i] += 1

            if passed and next_addr == hotspot['address']:
                tested_count[i + 1] += 1

            next_addr = c['path'][i]['challengee']
            next_passed = passed
        if c['path'][0]['challengee'] == hotspot['address']:
            tested_count[0] += 1

    print()
    print('PoC Eligibility:')
    print(f"successfully targeted   {init_target} times in {(chals[0]['height']-chals[-1]['height'])} blocks (every {(chals[0]['height']-chals[-1]['height'])/init_target:.0f} blocks)")
    print(f"\tlongest untargeted stretch: {max_target_delta:4d} blocks")
    print(f"challenger receipt txn  {challenger_count} times in {(chals[0]['height']-chals[-1]['height'])} blocks (every {(chals[0]['height']-chals[-1]['height'])/challenger_count:.0f} blocks)")
    print(f"\tlongest stretch without challenger receipt: {max_challenger_delta:4d} blocks")
    print(f"\thotspot was untargetable for: {untargetable_count} blocks ({untargetable_count*100/(chals[0]['height']-chals[-1]['height']):.1f}% of blocks)")

    print()
    print(f"PoC Hop Summary:")
    print(f"Hop | planned | tested (%) | passed (%) |")
    print(f'-----------------------------------------')
    for i in range(0, 5):
        print(f"{i+1:3} | {planned_count[i]:6d}  | {tested_count[i]:3d} ({tested_count[i]*100/planned_count[i]:3.0f}%) | {passed_count[i]:3d} ({passed_count[i]*100/planned_count[i]:3.0f}%) |")

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
    print(f"Neighboring Hotspot           | owner | dist km | heading |  bad RSSI (%)  |  bad SNR (%)   |")
    print(f"------------------------------+-------+---------+---------+----------------+----------------|")
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
            own = 'same' if hotspot['owner'] == bad_h['owner'] else bad_h['owner'][-5:]
            print(f"{H.get_hotspot_by_addr(n)['name']:29} | {own:5} | {dist_km:5.1f}   | {__heading2str__(heading):7} | {bad_neighbors[n]['rssi']:3d}/{bad_neighbors[n]['ttl']:3d} ({bad_neighbors[n]['rssi']*100/bad_neighbors[n]['ttl']:3.0f}%) | {bad_neighbors[n]['snr']:3d}/{bad_neighbors[n]['ttl']:3d} ({bad_neighbors[n]['snr']*100/bad_neighbors[n]['ttl']:3.0f}%) |")

def poc_reliability(hotspot, challenges):
    """

    :param hotspot:
    :param challenges: list of challenges
    :return:
    """
    H = Hotspots()
    haddr = hotspot['address']

    # days, remainder = divmod(challenges[0]['time'] - challenges[-1]['time'], 3600 * 24)
    # hours = int(round(remainder / 3600, 0))
    # print(f"analyzing {len(challenges)} challenges from block {challenges[0]['height']}-{challenges[-1]['height']} over {days} days, {hours} hrs")
    #

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
        all_ttl = 0
        all_pass = 0
        dist_min = 9999
        dist_max = 0

        if hotspot_transmitting:
            print(f"PoC hops from: {hotspot['name']}")
            print(f"{'to receiving hotspot':30} | owner | {'dist km'} | {'heading'} | recv/ttl | recv % |")
        else:
            print(f"PoC hops to: {hotspot['name']}")
            print(f"{'from transmitting hotspot':30} | owner | {'dist km'} | {'heading'} | recv/ttl | recv % |")
        print("-" * 80)

        for h in results.keys():
            ttl = results[h][0] + results[h][1]
            all_ttl += ttl
            all_pass += results[h][0]
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
            ownr = 'same' if hotspot['owner'] == H.get_hotspot_by_addr(h)['owner'] else H.get_hotspot_by_addr(h)['owner'][-5:]
            print(f"{H.get_hotspot_by_addr(h)['name']:30} | {ownr:5} | {dist:6.1f}  | {heading:4.0f} {headingstr[idx]:>2} | {results[h][0]:3d}/{ttl:3d}  | {results[h][0] / ttl * 100:5.0f}% |")

        if other_ttl:
            print(f"other ({other_cnt:2}){' ' * 20} |  N/A  | {dist_min:4.1f}-{dist_max:2.0f} |   N/A   | {other_pass:3d}/{other_ttl:3d}  | {other_pass / other_ttl * 100:5.0f}% | ")

        print(f"{' ' * 40}{' ' * 10}         ---------------------")
        print(f"{' ' * 40}{' '*10}   TOTAL | {all_pass:3d}/{all_ttl:4d} | {all_pass / all_ttl * 100:5.0f}% | ")

    summary_table(results_tx, hotspot_transmitting=True)
    print()
    print()
    summary_table(results_rx, hotspot_transmitting=False)

def main():
    parser = argparse.ArgumentParser("analyze hotspots", add_help=True)
    parser.add_argument('-x', help='report to run', choices=['poc_reliability', 'poc_v10', 'poc_summary'], required=True)

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
    challenges = challenges[:args.challenges]
    days, remainder = divmod(challenges[0]['time'] - challenges[-1]['time'], 3600 * 24)
    hours = int(round(remainder / 3600, 0))
    print(
        f"analyzing {len(challenges)} challenges from block {challenges[0]['height']}-{challenges[-1]['height']} over {days} days, {hours} hrs")

    if args.x == 'poc_reliability':
        poc_reliability(hotspot, challenges)
    elif args.x == 'poc_v10':
        pocv10_violations(hotspot, challenges)
    elif args.x == 'poc_summary':
        poc_summary(hotspot, challenges)


if __name__ == '__main__':
    main()



