# Helium Analysis Tools
This repo contains generic tools for analyzing PoC activity.
These are provided for information only, there is no guarantee of accuracy.

## Installation
To install simply run

    git clone https://github.com/Carniverous19/helium_analysis_tools.git
    
At time of writing only Python3.8+ is required.

# Tools
A lot of these tools require a cache of hotspots from Helium's hotspot API.  
This cache will be created automatically if not present in the `helium_analysis_tools` folder called `hotspots.json`.
The file is not updated on each run so may be a few days stale but will auto-refresh if its older than 72-hours.

To force refresh the cache run:

    python3 utils.py -x refresh_hotspots

Note the hotspot you specify to be analyzed is pulled from the API on every function call so it has fresh information but its neighbors or witnesses may be stale.
None of these tools are useful for quick changes and its assumed hotspots and their neighbors are fairly stationary over the period of time analyzed.

A list of tools and brief description is provided below.

## analyze_hotspot.py
This is the old set of tools used for multi-hop PoC it is depreciated as beaconing and HIP17 rewards changed a lot of how PoC activity should be analyzed.
Ignore this file and associated reports unless you need to use them for legacy purposes.


## beacon_reports.py
This is the main report generating tool and gives useful reports on an individual hotspots PoC and challenge creation activity.
Note this code allows you to specify either hotspot name (with dashes) or hotspot address.
It is suggested to always use the hotspot address as there is no guarantee that a hotspot has a unique name (there are already 16 conflicts among ~17,500 hotspots).
If there is a hotspot naming conflict only the last hotspot with that name returned will be considered.

see 

    python3 beacon_reports.py -h
    
for more details on arguments.

### witnesses

This report gives a summary of recent witnesses for the specified hotspot.
These are receives by the reference hotspot, to see who can hear the reference hotspot's transmits use the "beacons" report.
There are two main reports the default report and the detailed report.

to run the default `witnesses` report run:

    python3 beacon_reports.py -x witnesses --address {hotspot address}


The first table lists information about each hotspot the reference hotspot (specified in command line) can witness.
hotspots are listed in decending order of reward units (RUs).
A sample table is shown below:

    Witnesses for: dry-daisy-tortoise
    transmitting hotspot      | scale | owner | dist km | heading | valids | invlds | RUs
    active-inky-vulture       |  1.00 | same  |    28.4 | 135  SE |     11 |      0 | 5.76
    flaky-magenta-pigeon      |  1.00 | same  |    18.9 | 135  SE |      5 |      0 | 5.00
    crazy-clear-hippo         |  1.00 | YYsQd |    18.5 | 135  SE |      6 |      0 | 3.58
    droll-fleece-tortoise     |  1.00 | kwpFt |    54.4 | 120  SE |      6 |      0 | 3.24
    shiny-latte-hare          |  0.50 | Dy7JS |     3.3 | 135  SE |      6 |      0 | 2.88
    joyous-grape-chicken      |  1.00 | wuMEh |    12.0 | 135  SE |      6 |      0 | 2.80
    damp-rose-lynx            |  1.00 | yiym9 |    27.4 | 150  SE |      7 |      0 | 2.58

Column descriptions:
 - **transmitting hotspot**: This is the name of the hotspot that beaconed and can be witnessed by the reference hotspot.  Note if the name is longer than 25-characters it will be clipped.
 - **scale**: This is the *transmit_reward_scale* from HIP17 of the transmitting hotspot.  See [HIP17](https://github.com/helium/HIP/blob/master/0017-hex-density-based-transmit-reward-scaling.md) for more details on how this affects witness rewards.
 - **owner**: This is the last 5 digits of the hotspot's owner address if the owner is different from the refrence hotspot.  It will list "same" if the owner is the same.
 - **dist km**: This is the distance between the transmitting hotspot and reference hotspot in km using the cache'd hotspot locations and haversine formula.
 - **heading**: This column lists the heading from reference hotspot to transmitter in degrees and compass heading.
 - **valids**: This is the number of times the reference hotspot witnessed the transmitting hotspot and the witness was valid and earned HNT.
 - **invlds**: This is the number of times the reference hotspot witnessed the transmitting hotspot and the witness was invalid and did not earn HNT.
 - **RUs**: This is the estimated number of reward units earned for witnessing the transmitting hotspot over the number of PoCs analyzed.  Note that reward units do not equal HNT but are proportional to HNT earned.  See [HIP15](https://github.com/helium/HIP/blob/master/0015-beaconing-rewards.md) for a definition of reward units and how they relate to earnings.
 
Another summary table is provided after the list of all hotspots that were witnessed.
This table shows the reward-units earned aggregated by compass heading.
Its useful to determine what directions are providing the most rewards.
A sample table is shown below:

    Earnings by compass heading
    heading |   RUs  | bar chart
       SW   |  10.91 | XXXXXXXXXXXXXXXXX
       W    |   9.69 | XXXXXXXXXXXXXXX
       N    |  16.04 | XXXXXXXXXXXXXXXXXXXXXXXXX
       NE   |  20.35 | XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
       NW   |   8.59 | XXXXXXXXXXXXXX
       S    |   2.93 | XXXXX
       SE   |   1.98 | XXX

Column descriptions:
 - **heading**: This is the compass heading relative to the reference hotspot
 - **RUs**: This is the sum of all reward units from hotspots at the specified compass heading over the PoCs analyzed
 - **bar chart**: This is a crude bar chart showing the same information as "RUs".  The direction with the most earnings will have 32 `X`'s and the others are scaled accordingly

#### witness details

The detailed witness report will list each witness for the reference hotspot of the PoCs analyzed.
This could be hundreds of columns so it is best to use this in combination with the `-c` or `--challenges` argument to limit the challenge history.

to run the detailed `witnesses` report run the same command but specify the `-d` or `--details` flag:

    python3 beacon_reports.py -x witnesses --address {hotspot address} --details
    
A sample table is shown below:

    Witnesses for: dry-daisy-tortoise
    time           | block   | transmitting hotspot      | dist km | valid? |  snr  | rssi | RUs  | inval reason
    02-04 13:22:54 |  705134 | faithful-tiger-crab       |   24.7  | valid  |   5.5 | -109 | 0.21 |
    02-04 10:19:59 |  704949 | hot-chocolate-llama       |   19.8  | valid  |  -5.5 | -114 | 0.76 |
    02-04 08:39:29 |  704856 | cuddly-scarlet-walrus     |   13.2  | valid  |  -1.8 | -113 | 0.76 |
    02-04 07:20:46 |  704783 | soaring-lava-cormorant    |   28.8  | valid  |  -5.0 | -115 | 0.13 |
    02-04 01:45:08 |  704491 | boxy-green-copperhead     |   13.8  | valid  |  -3.0 | -114 | 0.12 |
    02-03 19:48:23 |  704170 | huge-tiger-gazelle        |   48.1  | valid  |  -3.5 | -112 | 0.16 |
    02-03 18:29:43 |  704097 | crazy-clear-hippo         |   18.5  | valid  |  -4.2 | -109 | 0.43 |
    02-03 18:14:51 |  704085 | energetic-pink-tapir      |   23.1  | valid  |  -7.5 | -117 | 0.11 |
    02-03 14:17:36 |  703868 | energetic-pink-tapir      |   23.1  | valid  | -10.2 | -115 | 0.15 |
    02-03 13:38:23 |  703833 | soaring-lava-cormorant    |   28.8  | valid  |  -2.0 | -103 | 0.13 |
    02-03 12:49:11 |  703786 | orbiting-cotton-finch     |   10.4  | INVAL  |   7.2 | -106 | 0.00 | snr too high (snr:7.2, rssi: -106<-105)
    02-03 11:56:25 |  703732 | flaky-magenta-pigeon      |   18.9  | valid  |  -9.2 | -102 | 1.00 |
    02-03 11:52:32 |  703729 | huge-tiger-gazelle        |   48.1  | valid  |   0.2 | -113 | 0.21 |
    02-03 11:54:14 |  703728 | flaky-magenta-pigeon      |   18.9  | valid  |  -9.8 | -115 | 1.00 |
    02-03 11:42:39 |  703720 | shiny-latte-hare          |    3.3  | valid  |   0.5 | -111 | 0.50 |
    02-03 07:34:52 |  703450 | young-corduroy-shell      |   15.6  | valid  |   5.0 | -109 | 0.18 |
    02-03 07:13:09 |  703423 | obedient-flaxen-cat       |    7.8  | INVAL  |  11.0 |  -96 | 0.00 | snr too high (snr:11.0, rssi: -96<-90)

Column descriptions:
 - **time**: This is the time in your local timezone (or the operating systems configured timezone) when the witness occurred
 - **block**: This is the block height reported in the witness transaction
 - **transmitting hotspot**: This is the name of the hotspot that beaconed and can be witnessed by the reference hotspot.  Note if the name is longer than 25-characters it will be clipped.
 - **dist km**: This is the distance between the transmitting hotspot and reference hotspot in km using the cache'd hotspot locations and haversine formula.
 - **valid?**: This will be `valid` if the witness was valid or `INVAL` if the witness was invalid, see `inval reason` fora  description of why a witness was invalid
 - **snr**: This is the signal to noise ratio in dB for the witness
 - **rssi**: This is the signal strength in dBm for the witness
 - **RUs**: This is the number of reward units earned for this specific witness
 - **inval reason**: If the witness was invalid this column will give a brief description of why it was invalid.

### beacons
This report gives a summary of recent beacons from the specified hotspot.
Beacons are the result of being challenged by other hotspots and show up as "challengee" activity in explorer.
The should occur roughly every 240 blocks based on the `poc_challenge_interval` chain variable at the time of this writing.
These are transmits by the reference hotspot, to see who can be received by the reference hotspot use the "witnesses" report.
There are two main reports the default report and the detailed report.

to run the default `beacons` report run:

    python3 beacon_reports.py -x beacons --address {hotspot address}

There are 3 different summary tables from this report.

The first table "summary stats" gives information about the reference hotspot and rough statistics on the beaconing rate over the PoCs analyzed:

    Beacons FROM: bright-cloud-newt
    
    summary stats
    challenger address:        112jegqqkXeENr3GQHvPnYJB8UUUHBR577aXHUvnfvCf1qrotbtn
    challenger listening_addr: /ip4/104.174.111.107/tcp/0
    blocks between chalng avg: 360
                       median: 298
              75th-percentile: 532
            range (min - max): 6 - 1099

The challenger address is either the same as specified or the address of the hotspot name.

The challenger `listening_addr` is the libp2p address recorded on the blockchain where the hotspot can be reached.
This is useful to understand if relaying is used or what port the hotspot is listening on.
Note this is not pulled from the p2p network directly but the hotspot API so it may be stale depending on how frequently the hotspot addresses are updated on chain.

The next four rows are all related to `blocks between chalng`.  This looks at the number of blocks between each challenge received and looks at the average, median, 75th percentile, and range of these differences.

The second table is "Beacons by Day" which summarizes the number of beacons transmitted by day and aggregate info for those beacons.  A sample table is shown below:

     Beacons by Day ==========
    note may be partial first and last day
    Date  | bcns | valid | inval | near |  RU's | bcn bar chart
    02-02 |    2 |    41 |     2 |    1 |  0.67 | XX
    02-01 |    2 |    21 |     1 |    1 |  0.59 | XX
    01-31 |    5 |    81 |     8 |    5 |  1.56 | XXXXX
    01-30 |    3 |    52 |     2 |    3 |  1.01 | XXX
    01-29 |    2 |    29 |     2 |    2 |  0.64 | XX
    01-28 |    4 |    27 |     1 |    3 |  0.85 | XXXX
    01-27 |    2 |    23 |     1 |    2 |  0.62 | XX
    01-26 |    4 |    28 |     1 |    3 |  0.86 | XXXX
    01-25 |    4 |    26 |     3 |    4 |  0.86 | XXXX
    01-24 |    3 |    29 |     5 |    3 |  0.82 | XXX
    01-23 |    8 |    78 |     7 |    9 |  2.09 | XXXXXXXX

Column descriptions:
 - **Date**: This is the date (in local / OS configured timezone) where the beacons occurred
 - **bcns**: This is the number of beacons transmitted on the specified date
 - **valid**: This is the total number of valid witnesses for all of the reference hotspot's beacons
 - **inval**: This is the total number of invalid witnesses for RSSI or SNR PoCv10 violations, *not* invalid for being too close.  There are beacon reward penalties for these.
 - **near**: This is the total number of witnesses that are invalid for being too close to the transmitter.  There are no penalties for these and they are ignored in reward calculations.
 - **RU's**: This is the estimated number of reward units earned on this day for beaconing. See [HIP15](https://github.com/helium/HIP/blob/master/0015-beaconing-rewards.md) for a definition of reward units and how they relate to HNT earnings.
 - **bcn bar chart**: This is a crude bar chart showing the number of beacons on the corresponding date.  Each `X` corresponds to one beacon.
 
The third chart is similar to the beacons by day but is organized by 3000 blocks.
This could be helpful to show regular behavior even if block times speed up and slow down.
Remember "time" for the blockhain is based on blocks not days/hours/minutes.
This chart groups beacon activity in groups of 3000 blocks which would *roughly* correspond to 2 days if blocks are perfectly hitting their 60s interval.
A sample table is shown below:

    Beacons by 3000 blocks ========
    note may be partial last set of blocks
    Block age | bcns | valid | inval | near |  RU's | bcn bar chart
           0+ |    9 |   143 |    11 |    7 |  2.82 | XXXXXXXXX
        3000+ |    7 |   101 |     5 |    7 |  2.23 | XXXXXXX
        6000+ |    8 |    58 |     2 |    6 |  1.74 | XXXXXXXX
        9000+ |   11 |    77 |    10 |   11 |  2.54 | XXXXXXXXXXX
       12000+ |    8 |   101 |     9 |    9 |  2.43 | XXXXXXXX
       15000+ |    4 |    25 |     1 |    3 |  0.81 | XXXX

Column descriptions:
 - **Block age**: This is based on the most recent block with PoC activity from the reference hotspot and counts backwards.  Beacons 0 - 2999 blocks ago will be in the "0+" bucket, beacons 3000 - 5999 blocks ago will be in the "3000+" bucket, etc.
 - **bcns**: This is the number of beacons transmitted within the specified block range
The remaining columns are the same as the above table for the block interval instead of date.

#### beacon details

The detailed beacon report will list each beacon transmitted from the reference hotspot.

to run the detailed `beacons` report run the same command but specify the `-d` or `--details` flag:

    python3 beacon_reports.py -x beacons --address {hotspot address} --details

A sample table is shown below:

    Beacons FROM: slow-burgundy-mandrill
    Individual Beacons ==========
    Beacon Time    | block   | blck Δ | Valid | inval | near | RU's | avg rssi | witness bar chart
    02-04 09:40:52 |  704903 | N/A    |     0 |     1 |    0 | 0.00 |   -106.0 | i
    02-04 04:15:59 |  704612 | 291    |     7 |     3 |    1 | 0.24 |  -108.32 | VVVVVVViiic
    02-04 03:58:43 |  704602 | 10     |     7 |     2 |    1 | 0.26 |   -103.3 | VVVVVVViic
    02-03 22:47:34 |  704324 | 278    |     9 |     2 |    1 | 0.29 |  -109.55 | VVVVVVVVViic
    02-03 22:13:11 |  704290 | 34     |     0 |     0 |    0 | 0.00 |          |
    02-03 20:37:33 |  704199 | 91     |     0 |     0 |    0 | 0.00 |          |
    02-03 16:24:33 |  703975 | 224    |     6 |     2 |    1 | 0.24 |   -110.3 | VVVVVViic
    02-03 09:55:19 |  703614 | 361    |    11 |     2 |    1 | 0.31 |   -103.5 | VVVVVVVVVVViic
    02-03 03:58:31 |  703229 | 385    |     6 |     3 |    1 | 0.22 |   -101.1 | VVVVVViiic
    02-02 22:53:09 |  703008 | 221    |     9 |     2 |    1 | 0.29 |  -108.33 | VVVVVVVVViic
    02-02 21:35:35 |  702940 | 68     |     0 |     0 |    0 | 0.00 |          |
    02-02 19:32:59 |  702800 | 140    |     0 |     0 |    0 | 0.00 |          |
    02-02 15:41:31 |  702530 | 270    |     2 |     2 |    1 | 0.10 |   -110.5 | VViic
    02-02 11:13:18 |  702270 | 260    |     3 |     1 |    0 | 0.15 |   -103.2 | VVVi
    02-02 10:29:05 |  702217 | 53     |     9 |     2 |    0 | 0.29 |  -111.21 | VVVVVVVVVii

Column descriptions:
 - **Beacon Time**: This is the time in your local timezone (or the operating systems configured timezone) when the beacon occurred
 - **block**: This is the block height for the challenge receipt
 - **blck Δ**: This is the block delta or number of blocks between the beacon at the current row and the previous row (in the future). This should average to ~240 blocks but there is no lower or upper limit and randomness means you may see low or high numbers occasionally without it being an bug.
 - **Valid**: This is the number of valid witnesses the beacon had.
 - **inval**: This is the number of invalid witnesses for RSSI or SNR PoCv10 violations, *not* invalid for being too close.  There are beacon reward penalties for these.
 - **near**: This is the number of witnesses that are invalid for being too close to the transmitter.  There are no penalties for these and they are ignored in reward calculations.
 - **RU's**: This is the estimated number of reward units earned for this specific beacon. 
 - **avg rssi**: This is the average RSSI for all witnesses
 - **witness bar chart**: This is a crude bar chart showing the number of witnesses for the beacon.  There will be a `V` for each valid witness, an `i` for each invalid witness, and a `c` for each witness that is to near or close to the transmitter.
 
### challenges
This report gives a summary of recent challenges created by the specified hotspot.
Challenges are created periodically and transmitted to the challengee over p2p.  These show up as "challenger" activity in explorer.
Hotspots need to create challenges to show they are active and participating in the blockchain to be eligible to receive challenges and participate in PoC.
Challenges can be created every 240 blocks based on the `poc_challenge_interval` chain variable at the time of this writing.
Challenges with a challengee or witness receipt (`poc_receipt_v1` transactions) must be submitted every 1,000 blocks based on `poc_v4_target_challenge_age` chain var to be considered active.
Again everything in these reports is done over the reference hotspot's internet / p2p communication and has nothing to do with RF performance.
There are two main reports the default report and the detailed report.

to run the default `challenges` report run:

    python3 beacon_reports.py -x beacons --address {hotspot address}
    
There is one table for this report.  An example is shown below:

Hotspot: bright-cloud-newt

    summary stats
    challenger address:        112jegqqkXeENr3GQHvPnYJB8UUUHBR577aXHUvnfvCf1qrotbtn
    challenger listening_addr: /ip4/104.174.111.107/tcp/0
    blocks between chalng avg: 345
                       median: 258
              75th-percentile: 302
            range (min - max): 245 - 1095

This shows similar statics to the first table for the "beacons" report but from the challenger's perspective.
Note it appears the 240 block or `poc_challenge_interval` variable is a hard limit and you will not be able to create challenges faster than than rate.
Therefore the min interval is likely to be very close but above 240.

#### challenges details

The detailed witness report will list each challenge created by the reference hotspot.

to run the detailed `challenges` report run the same command but specify the `-d` or `--details` flag:

    python3 beacon_reports.py -x challenges --address {hotspot address} --details
    
A sample table is shown below:

    Hotspot: bright-cloud-newt
    time           | block   | blck Δ | challengee                | scale | rct | wtns
    02-04 03:22:55 |  704560 | N/A    | icy-raspberry-worm        |  0.50 | YES | NONE
    02-03 17:11:56 |  704012 | 548    | damp-scarlet-squirrel     |  1.00 | YES | NONE
    02-03 12:06:11 |  703731 | 281    | amusing-tweed-wren        |  0.19 | YES | NONE
    02-02 17:49:45 |  702669 | 1062** | witty-purple-wasp         |  1.00 | YES | NONE
    02-02 13:19:51 |  702403 | 266    | clean-obsidian-cheetah    |  0.17 | YES | NONE
    02-02 08:54:36 |  702095 | 308    | huge-honeysuckle-eagle    |  0.50 | YES | NONE
    02-02 04:54:39 |  701836 | 259    | great-charcoal-dragonfly  |  1.00 | YES | NONE
    02-02 00:50:54 |  701578 | 258    | fluffy-metal-hawk         |  1.00 | YES | NONE
    02-01 20:34:51 |  701331 | 247    | wobbly-quartz-moth        |  1.00 | YES |   1
    02-01 16:09:15 |  701085 | 246    | elegant-magenta-mustang   |  0.01 | YES |  10
    02-01 08:44:41 |  700585 | 500    | cheerful-chili-caterpilla |  1.00 | YES | NONE
    02-01 04:29:43 |  700334 | 251    | young-admiral-nuthatch    |  0.50 | YES | NONE

Column descriptions:
 - **time**: This is the time in your local timezone (or the operating systems configured timezone) when the challenge occurred
 - **block**: This is the block height for the challenge receipt
 - **blck Δ**: This is the block delta or number of blocks between the challenge at the current row and the previous row (in the future).  This number needs to be <1000 or `poc_v4_target_challenge_age` for the hotspot to be eligible to receive challenges.  If this number is above the chain var the block delta will have `**` after it.
 - **challengee**: This is the name of the hotspot that received the challenge and beaconed.
 - **scale**: This is the *transmit_rewards_scale* for the challengee.  If this number is < 1.00 it means there are hotspots nearby the challengee.
 - **rct**: This will be `YES` if the challengee was able to deliver a beacon receipt back to the challenger (reference hotspot) or `no` if it did not deliver a receipt
 - **wtns**: This is the number of witnesses for the beacon (or more importantly the number of witness receipts delivered to the challenger).  This will be `NONE` if there were no receipts.
