
import argparse
import statistics
import datetime as dt
from classes.Hotspots import Hotspots
import utils



def transmit_details(hotspot, challenges, smry_only=False):
    """
    Prints a list of all transmits, and number of valid / invalid witnesses
    :param hotspot:
    :param challenges:
    :return:
    """
    results = []
    vars = utils.api_call(path='vars').get('data', dict())
    haddr = hotspot['address']
    H = Hotspots()
    H.update_reference_hspot(address=haddr)
    hotspot = H.get_hotspot_by_addr(haddr)
    print(f"Beacons FROM: {hotspot['name']}")

    if not smry_only:
        print(f"Individual Beacons ==========")
        print(f"{'Beacon Time':14} | {'block':7} | blck Δ | Valid | inval | near | RU's | witness bar chart")
    block_deltas = []
    last_block = None
    for c in challenges:
        if c['path'][0]['challengee'] != hotspot['address']:
            continue  # I am not transmitter
        block_delta_str = 'N/A'
        if last_block:
            block_delta = last_block - c['height']
            block_deltas.append(block_delta)
            block_delta_str = f"{block_delta}"
        last_block = c['height']

        beacon = dict(date=None, height=c['height'], valid=0, invalid=0, close=0, RUs=0)
        ts = c['time']
        if c['path'][0]['receipt']:
            ts = c['path'][0]['receipt']['timestamp'] / 1e9
        elif c['path'][0]['witnesses']:
            # if receipt missing and witnesses use first witness ts
            ts = c['path'][0]['witnesses'][0]['timestamp'] / 1e9
            # print(f"No challengee receipt")
        else:
            continue
            # should be unreachble, cant have a poc_receipt with no witness or challengee receipt
        beacon['date'] = dt.datetime.fromtimestamp(ts).isoformat()[5:19].replace('T', ' ')
        for w in c['path'][0]['witnesses']:
            w_hspot = H.get_hotspot_by_addr(w['gateway'])
            if not w_hspot:
                continue
            dist_km = utils.haversine_km(w_hspot['lat'], w_hspot['lng'], hotspot['lat'], hotspot['lng'])
            if w['is_valid']:
                beacon['valid'] += 1
            else:
                if dist_km <= .32:
                    beacon['close'] += 1
                else:
                    beacon['invalid'] += 1
        tx = 0
        if beacon['valid']:
            tx, _ = utils.hip15_rewards(beacon['valid'] + beacon['invalid'], vars)
            tx = tx * beacon['valid'] / (beacon['valid'] + beacon['invalid']) * hotspot['reward_scale']
        beacon['RUs'] = tx
        results.append(beacon)
        if not smry_only:
            print(f"{beacon['date']} | {beacon['height']:7} | {block_delta_str:6} | {beacon['valid']:5} | {beacon['invalid']:5} | {beacon['close']:4} | {beacon['RUs']:4.2f} | {'V' * beacon['valid'] + 'i' * beacon['invalid'] + 'c' * beacon['close']}")  # + '-' * (25 - beacon['valid'] - beacon['invalid'] - beacon['close'])}")
        #print(beacon)


    print()
    print(f"summary stats")
    print(f"challenger address:        {hotspot['address']}")
    print(f"challenger listening_addr: {hotspot['status']['listen_addrs'][0]}")
    print(f"blocks between chalng avg: {statistics.mean(block_deltas):.0f}")
    print(f"                   median: {statistics.median(block_deltas):.0f}")
    print(f"          75th-percentile: {statistics.quantiles(block_deltas)[-1]:.0f}")
    print(f"        range (min - max): {min(block_deltas)} - {max(block_deltas)}")

    if smry_only:

        print()
        print(f" Beacons by Day ==========")
        print(f"note may be partial first and last day")
        day_dict = dict()
        for res in results:
            date = res['date'][:5]
            if date not in day_dict:
                day_dict[date] = dict(count=0, RUs=0, valid=0, invalid=0, close=0)
            day_dict[date]['count'] += 1
            day_dict[date]['RUs'] += res['RUs']
            day_dict[date]['valid'] += res['valid']
            day_dict[date]['invalid'] += res['invalid']
            day_dict[date]['close'] += res['close']

        print(f"{'Date':5} | bcns | valid | inval | near |  RU's | bcn bar chart")
        for k in day_dict.keys():
            print(f"{k:5} | {day_dict[k]['count']:4} | {day_dict[k]['valid']:5} | {day_dict[k]['invalid']:5} | {day_dict[k]['close']:4} | {day_dict[k]['RUs']:5.2f} | {'X' * day_dict[k]['count']} ")

        print()


        block_interval = 3000
        print(f"Beacons by {block_interval} blocks ========")
        print(f"note may be partial last set of blocks")
        start_block = results[0]['height']
        block_dict = dict()
        for res in results:
            date = int((start_block - res['height']) / block_interval)
            if date not in block_dict:
                block_dict[date] = dict(count=0, RUs=0, valid=0, invalid=0, close=0)
            block_dict[date]['count'] += 1
            block_dict[date]['RUs'] += res['RUs']
            block_dict[date]['valid'] += res['valid']
            block_dict[date]['invalid'] += res['invalid']
            block_dict[date]['close'] += res['close']

        print(f"{'Block age':9} | bcns | valid | inval | near |  RU's | bcn bar chart")
        for k in block_dict.keys():
            block_age = f"{k * block_interval:5}+"
            print(
                f"{block_age:>9} | {block_dict[k]['count']:4} | {block_dict[k]['valid']:5} | {block_dict[k]['invalid']:5} | {block_dict[k]['close']:4} | {block_dict[k]['RUs']:5.2f} | {'X' * block_dict[k]['count']} ")


def challenger_details(hotspot, chals, smry_only=False):
    haddr = hotspot['address']
    H = Hotspots()
    H.update_reference_hspot(address=haddr)
    hotspot = H.get_hotspot_by_addr(haddr)
    print(f"Hotspot: {hotspot['name']}")
    if not smry_only:
        print(f"{'time':14} | {'block':7} | blck Δ | {'challengee':25} | scale | rct | wtns ")
        # print("=" * 82)
    vars = utils.api_call(path='vars')['data']
    max_rct_age = vars['poc_v4_target_challenge_age']
    unsuspected_lone_wolfs = 0
    dense_challenges = 0

    num_poc_rcts = 0
    newest_block = 0
    oldest_block = 1e8
    prev_rct_block = None
    max_block_delta = 0
    block_deltas = []
    for c in chals:
        if c['challenger'] != hotspot['address']:
            continue

        newest_block = max(newest_block, c['height'])
        oldest_block = min(oldest_block, c['height'])
        transmitter = H.get_hotspot_by_addr(c['path'][0]['challengee'])
        num_poc_rcts += 1
        # time, transmitter, distance, val/inval, RU, reason inval
        time_str = dt.datetime.fromtimestamp(c['time']).isoformat()[5:19]
        time_str = time_str.replace('T', ' ')
        transmitter_name = transmitter['name']
        num_ws = len(c['path'][0]['witnesses'])
        w_str = 'NONE' if num_ws == 0 else f'{num_ws} '
        if transmitter['reward_scale'] <= 0.9:
            dense_challenges += 1
            if num_ws == 0:
                unsuspected_lone_wolfs += 1
        block_delta = 0
        block_delta_str = 'N/A'
        if prev_rct_block:
            block_delta = prev_rct_block - c['height']
            block_deltas.append(block_delta)
            block_delta_str = f"{block_delta}" + ('**' if block_delta > max_rct_age else '')
        max_block_delta = max(block_delta, max_block_delta)
        if not smry_only:
            print(f"{time_str:14} | {c['height']:7} | {block_delta_str:6} | {transmitter_name[:25]:25} | {transmitter['reward_scale']:5.2f} | {'YES' if c['path'][0]['receipt'] else 'no' :3} | {w_str:>4}")

        prev_rct_block = c['height']
    print()
    print(f"summary stats")
    print(f"challenger address:        {hotspot['address']}")
    print(f"challenger listening_addr: {hotspot['status']['listen_addrs'][0]}")
    # print(f'lone wolfs in dense areas: {unsuspected_lone_wolfs:<3d}/{dense_challenges:3d}')
    print(f"blocks between chalng avg: {(newest_block - oldest_block) / num_poc_rcts:.0f}")
    print(f"                   median: {statistics.median(block_deltas):.0f}")
    print(f"          75th-percentile: {statistics.quantiles(block_deltas)[-1]:.0f}")
    print(f"        range (min - max): {min(block_deltas)} - {max(block_deltas)}")

def witness_detail(hotspot, chals, smry_only=False):
    haddr = hotspot['address']
    H = Hotspots()
    H.update_reference_hspot(address=haddr)
    hotspot = H.get_hotspot_by_addr(haddr)
    vars = utils.api_call(path='vars')['data']
    print()
    print(f"Witnesses for: {hotspot['name']}")
    if not smry_only:
        print(f"{'time':14} | {'block':7} | {'transmitting hotspot':25} | dist km | valid? |  snr  | rssi | RUs  | inval reason")

    tx_smry = dict()
    for c in chals:
        p = c['path'][0]
        for w in p['witnesses']:
            if w['gateway'] == haddr:
                transmitter = H.get_hotspot_by_addr(p['challengee'])

                # time, transmitter, distance, val/inval, RU, reason inval
                time_str = dt.datetime.fromtimestamp(w['timestamp']/1e9).isoformat()[5:19]
                time_str = time_str.replace('T', ' ')
                transmitter_name = transmitter['name']
                reward_units = 0
                valid = 'INVAL'
                reason = ''
                dist_km = utils.haversine_km(transmitter['lat'], transmitter['lng'], hotspot['lat'], hotspot['lng'])
                max_rssi = utils.max_rssi(dist_km)
                min_rssi = utils.snr_min_rssi(w['snr'])
                if w['is_valid']:
                    valid = 'valid'
                    hip15_rus = 1
                    if len(p['witnesses']) > vars['witness_redundancy']:
                        hip15_rus = (vars['witness_redundancy'] - (1 - pow(vars['poc_reward_decay_rate'], len(p['witnesses']) - vars['witness_redundancy']))) / len(p['witnesses'])
                    reward_units = transmitter['reward_scale'] * hip15_rus
                else:
                    if dist_km < 0.3:
                        reason = 'too close'
                    elif w['signal'] > max_rssi:
                        reason = f'rssi too high ({w["signal"]}dbm,{w["snr"]:.1f}snr)'
                    elif w['signal'] < min_rssi:
                        reason = f'snr too high (snr:{w["snr"]:.1f}, rssi: {w["signal"]}<{min_rssi})'
                    else:
                        reason = 'unknown'
                if not smry_only:
                    print(f"{time_str:14} | {c['height']:7} | {transmitter_name[:25]:25} | {dist_km:6.1f}  | {valid:6} | {w['snr']:5.1f} | {w['signal']:4d} | {reward_units:4.2f} | {reason}")

                if transmitter['address'] not in tx_smry:
                    tx_smry[transmitter['address']] = dict(valid_cnt=0, invalid_cnt=0, RUs=0)
                tx_smry[transmitter['address']]['RUs'] += reward_units
                tx_smry[transmitter['address']]['valid_cnt'] += valid == 'valid'
                tx_smry[transmitter['address']]['invalid_cnt'] += valid != 'valid'

    if smry_only:
        idx_sort = []
        for k in tx_smry.keys():
            idx_sort.append((tx_smry[k]['RUs'], k))
        idx_sort.sort()
        idx_sort = [x[1] for x in idx_sort[::-1]]
        print(f"{'transmitting hotspot':25} | scale | owner | dist km | heading | valids | invlds | RUs")

        earning_by_compass = dict()

        for addr in idx_sort:
            txer = H.get_hotspot_by_addr(addr)
            dist, heading = utils.haversine_km(hotspot['lat'], hotspot['lng'], txer['lat'], txer['lng'], return_heading=True)
            compass = utils.heading_to_compass(heading)
            if compass not in earning_by_compass:
                earning_by_compass[compass] = 0
            earning_by_compass[compass] += tx_smry[addr]['RUs']
            heading = round(heading / 15, 0) * 15
            owner = 'same'
            if hotspot['owner'] != txer['owner']:
                owner = txer['owner'][-5:]
            heading_str = f"{heading:3.0f}  {compass:2}"
            print(f"{txer['name'][:25]:25} | {txer['reward_scale']:5.2f} | {owner:5} | {dist:7.1f} | {heading_str:7} | {tx_smry[addr]['valid_cnt']:6} | {tx_smry[addr]['invalid_cnt']:6} | {tx_smry[addr]['RUs']:.2f}")

        print()
        print(f"Earnings by compass heading")
        print(f"heading |   RUs  | bar chart")
        max_compass = max(list(earning_by_compass.values()))
        for h in earning_by_compass:
            print(f"   {h:4} | {earning_by_compass[h]:6.2f} | {'X' * round(32 * earning_by_compass[h] / max_compass) }")


def main():
    parser = argparse.ArgumentParser("analyze hotspots", add_help=True)
    parser.add_argument('-x', help='report to run', choices=['beacons', 'witnesses', 'challenges'], required=True)
    parser.add_argument('-c', '--challenges', help='number of challenges to analyze, default:500', default=400, type=int)
    parser.add_argument('-n', '--name', help='hotspot name to analyze with dashes-between-words')
    parser.add_argument('-a', '--address', help='hotspot address to analyze')
    parser.add_argument('-d', '--details', help='return detailed report (listing each activity)', action='store_true')

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
    if len(challenges) < 2:
        print(f"ERROR could not load challenges, either hotspot has been offline too long or you need to increase --challenge arguement")
        return
    days, remainder = divmod(challenges[0]['time'] - challenges[-1]['time'], 3600 * 24)
    hours = int(round(remainder / 3600, 0))
    print(f"analyzing {len(challenges)} challenges from block {challenges[0]['height']}-{challenges[-1]['height']} over {days} days, {hours} hrs")

    if args.x == 'beacons':
        transmit_details(hotspot, challenges, smry_only=not args.details)
    elif args.x == 'witnesses':
        witness_detail(hotspot, challenges, smry_only=not args.details)
    elif args.x == 'challenges':
        challenger_details(hotspot, challenges, smry_only=not args.details)
    else:
        print(f"unsupported report")



if __name__ == '__main__':
    main()