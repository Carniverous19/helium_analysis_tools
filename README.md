# Helium Analysis Tools
This repo contains generic tools for analyzing PoC activity.
These are provided for information only, there is no guarantee of accuracy.

## Installation
To install simply run

    git clone https://github.com/Carniverous19/helium_analysis_tools.git
    
At time of writing only Python3.6+ is required but you may want to install `numpy` and `matplotlib` for additional tools that may be added.

# Tools
A lot of these tools require a cache of hotspots from Helium's hotspot API.  
This cache will be created automatically if not present in the `helium_analysis_tools` folder called `hotspots.json`.
The file is not updated on each run so may get stale.  
A warning message will be printed if it is >48 hours old and you may get runtime errors if a hotspot appears in challenge activity that is not in the cache.
To refresh the cache run

    python3 utils.py -x refresh_hotspots

A list of tools and brief description is provided below

## analyze_hotspot.py
This file provides useful reports on an individual hotspot's PoC activity.  Note this code allows you to specify either hotspot name (with dashes) or hotspot address.
It is suggested to always use the hotspot address as there is no guarantee that a hotspot has a unique name (there are already 3 conflicts among ~8,500 hotspots)
If there is a hotspot naming conflict only the last hotspot with that name returned will be considered.

see

    python3 analyze_hotspot.py -h
    
for more details on arguments.

### poc_v10

First is `poc_v10` which looks at recent challenge activity for the selected hotspot and reports the total number of witness and PoC hops that violate PoCv10 requirements.
For information on PoC v10 requirements see the blog post [Blockchain PoC v10](https://engineering.helium.com/2020/09/21/blockchain-poc-v10.html).

to run the `poc_v10` report run:

    python3 analyze_hotspot.py -x poc_v10 --address {hotspot address}

There are two tables in this report.  The first output table gives a summary overview with an example shown below:

    analyzed 202 challenges from 516276-513758
    PoC v10 failures for name-name-name
    SUMMARY
    Category                   | Total | bad RSSI (%) | bad SNR (%) |
    -----------------------------------------------------------------
    Witnesses to hotspot >300m |   154 |    0 (  0%)  |   13 (  8%) |
    Hotspot witnessing  >300m  |    66 |    0 (  0%)  |    0 (  0%) |
    Hotspot PoC receipts       |    24 |    0 (  0%)  |    0 (  0%) |
    
As indicated in the first row, witnesses within 300m meters are ignored as these shouldnt (arent?) be rewarded anyway.
The column "bad RSSI" means the signal violated Free Space Path Loss estimation.  
The column "bad SNR" means the RSSI was too low for the given SNR.  High SNR but low RSSI means noise is very very low which is suspect.

A second table gives more detail breaking down results by hotspot.
This doesnt differentiate between types of interaction (witness or PoC hop) but helps to identify if failures are isolated to a few neighbors or across all neighbors (meaning its likely a problem with your hotspot).  
**Note:** Although I say "bad neighbor" that doesnt mean the hotspot listed is actually gaming, it could be false positives, bad signal between two hotspots due to environmental factors or the reference hotspot that is not at asserted location.

An example table is shown below:
    
    BY "BAD" NEIGHBOR
    Neighboring Hotspot           | owner | dist km | heading |  bad RSSI (%)  |  bad SNR (%)   |
    ------------------------------+-------+---------+---------+----------------+----------------|
    colossal-aquamarine-okapi     | same  |   4.0   | 280  W  |  30/ 30 (100%) |   0/ 30 (  0%) |
    keen-navy-seagull             | same  |   4.3   | 285  W  |  25/ 48 ( 52%) |   0/ 48 (  0%) |
    dizzy-magenta-haddock         | same  |   3.5   | 285  W  |  73/ 73 (100%) |   0/ 73 (  0%) |
    faithful-tiger-crab           | to5cr |  19.2   | 145 SE  |   0/ 24 (  0%) |   4/ 24 ( 17%) |
    quaint-mulberry-raccoon       | same  |   4.3   | 295 NW  |  40/ 40 (100%) |   0/ 40 (  0%) |
    harsh-spruce-fox              | 49CDa |   3.8   | 285  W  |   7/ 60 ( 12%) |   0/ 60 (  0%) |
    cuddly-scarlet-walrus         | 7xMGF |   7.7   | 130 SE  |   0/ 25 (  0%) |   1/ 25 (  4%) |
    strong-tin-hare               | yjksQ | 186.6   | 140 SE  |   2/  2 (100%) |   0/  2 (  0%) |

The second column "owner" indicates whether the hotspot has the same owner as the reference hotspot or gives the last 5 digits of the base58 encoded owner field.
The additional columns in the table are distance between hotspots, heading (degrees and compass) from reference hotspot and the breakdown of RSSI or SNR failures.


### poc_reliability
Second is a report `poc_reliability` which analyzes the reliability of the specified hotpsot receiving PoCs from its neighbors as well as transmitting to neighbors.
With the current PoC reward system transmitting to the following hotspot is less important since transmissions are rewarded as long as any hotspot receives the transmission (witness or next hop).
If your hotspot cannot reliably receive challenges from its neighbors it is losing out on rewards.  

**Note**: This does not take into account receives that fail PoCv10 thresholds.  "recv" means the signal was received, not that the receipt contains valid rssi/snr.

To run the `poc_reliability` report run:

    python3 analyze_hotspot.py -x poc_reliability --address {hotspot address}
    
An example output table is:

    analyzing 500 challenges from block 516256-498146 over 11 days, 11 hrs
    PoC hops from: name-name-name
    to receiving hotspot           | owner | dist km | heading | recv/ttl | recv % |
    --------------------------------------------------------------------------------

    boxy-green-copperhead          | wuMEh |    8.3  |  145 SE |   2/  4  |    50% |
    acidic-lime-manatee            | dwZfH |    8.8  |  145 SE |   3/  6  |    50% |
    joyous-grape-chicken           | wuMEh |    6.7  |  120 SE |   2/  2  |   100% |
    merry-sage-baboon              | same  |    8.7  |  135 SE |   0/  4  |     0% |
    cuddly-scarlet-walrus          | 7xMGF |    7.7  |  130 SE |   2/  4  |    50% |
    flaky-magenta-pigeon           | GcK64 |   13.6  |  125 SE |   1/  6  |    17% |
    bouncy-neon-cottonmouth        | same  |    3.2  |  290  W |   2/  2  |   100% |
    other ( 7)                     |       |  2.3-33 |   N/A   |   5/  7  |    71% |
                                                               ---------------------
                                                         TOTAL |  17/  35 |    49% |


    
    PoC hops to: name-name-name
    from transmitting hotspot      | owner | dist km | heading | recv/ttl | recv % |
    --------------------------------------------------------------------------------
    rapid-lemon-aardvark           | xHq7t |   22.3  |  150 SE |   2/  9  |    22% |
    fast-aqua-jellyfish            | pNiHj |    7.2  |  130 SE |   0/  2  |     0% |
    keen-navy-seagull              | same  |    4.3  |  285  W |  13/ 16  |    81% |
    merry-sage-baboon              | same  |    8.7  |  135 SE |   0/  3  |     0% |
    boxy-green-copperhead          | wuMEh |    8.3  |  145 SE |   3/  3  |   100% |
    joyous-grape-chicken           | wuMEh |    6.7  |  120 SE |   2/  5  |    40% |
    energetic-eggshell-hippo       | B2gu4 |    3.1  |  285  W |   2/  3  |    67% |
    bright-brick-alligator         | 3oHpr |   10.7  |  145 SE |   0/  3  |     0% |
    other ( 7)                     |       |  2.6-30 |   N/A   |   3/  7  |    43% |
                                                               ---------------------
                                                         TOTAL |  25/  51 |    49% |

    
 
These tables count the total number of times the hotspot failed to receive an RF transmission (meaning previous hop passed) as well as the number of times the target hotspot transmitted and the following hop failed to receive.
For hotspots with lots of interactions, any neighbor with a total of 1 interaction is pooled together into an "other" category.
The second column "owner" indicates whether the hotspot has the same owner as the reference hotspot or gives the last 5 digits of the base58 encoded owner field.
The remaining columns give the distance between the two hotspots in km, the heading from the reference hotspot to neighbor in degrees and compass heading as well as the total interaction counts and pass percentage.
