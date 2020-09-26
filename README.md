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
    Neighboring Hotspot           | dist km | heading | bad RSSI (%)  | bad SNR (%)   |
    ------------------------------+---------+---------+---------------+---------------|
    tricky-carbon-pheasant        |   4.5   |  10  N  |  0/ 10 (  0%) |  5/ 10 ( 50%) |
    polite-silver-bat             |   0.6   |  30 NE  |  0/ 24 (  0%) |  1/ 24 (  4%) |
    faint-pearl-mantis            |   0.5   |  60 NE  |  0/ 25 (  0%) |  1/ 25 (  4%) |
    big-gunmetal-blackbird        |   4.5   |  10  N  |  0/  6 (  0%) |  5/  6 ( 83%) |
    shallow-parchment-copperhead  |   4.5   |  10  N  |  0/ 12 (  0%) |  5/ 12 ( 42%) |
    skinny-fiery-wallaby          |   3.4   | 350  N  |  0/ 11 (  0%) |  2/ 11 ( 18%) |
    swift-purple-griffin          |   2.1   | 270  W  |  0/  6 (  0%) |  5/  6 ( 83%) |
    clean-leather-stallion        |   1.3   | 310 NW  |  0/ 20 (  0%) |  3/ 20 ( 15%) |
    innocent-maroon-swift         |   1.0   | 315 NW  |  0/ 11 (  0%) |  1/ 11 (  9%) |
    uneven-banana-peacock         |   4.5   |  10  N  |  0/  3 (  0%) |  2/  3 ( 67%) |
    large-mercurial-coyote        |   2.6   | 285  W  |  0/  7 (  0%) |  1/  7 ( 14%) |

 This table gives distance between hotspots, heading (degrees and compass) from reference hotspot and the breakdown of RSSI or SNR failures.


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
    to receiving hotspot           | dist km | heading | recv/ttl | recv % |
    ------------------------------------------------------------------------
    tangy-aegean-grasshopper       |    0.4  |   15  N |  26/ 29  |    90% |
    warm-hotpink-monkey            |    0.5  |  340  N |   5/  6  |    83% |
    sweet-citron-stork             |    0.8  |   60 NE |   0/ 13  |     0% |
    trendy-fleece-cobra            |    2.5  |  100  E |   3/  4  |    75% |
    fluffy-aqua-stallion           |    1.6  |  315 NW |   6/ 11  |    55% |
    bright-aquamarine-seal         |    2.0  |  110  E |   0/  9  |     0% |
    scrawny-sable-cat              |    1.8  |  135 SE |   0/  5  |     0% |
    other ( 9)                     |  5.3-31 |   N/A   |   0/  9  |     0% | 
    
    
    PoC hops to: name-name-name
    from transmitting hotspot      | dist km | heading | recv/ttl | recv % |
    ------------------------------------------------------------------------
    warm-hotpink-monkey            |    0.5  |  340  N |  16/ 26  |    62% |
    trendy-fleece-cobra            |    2.5  |  100  E |   2/  6  |    33% |
    fluffy-aqua-stallion           |    1.6  |  315 NW |   2/ 64  |     3% |
    tangy-aegean-grasshopper       |    0.4  |   15  N |  22/ 23  |    96% |
    other (10)                     |  2.2-33 |   N/A   |   1/ 10  |    10% | 
    
 
These tables count the total number of times the hotspot failed to receive an RF transmission (meaning previous hop passed) as well as the number of times the target hotspot transmitted and the following hop failed to receive.
For hotspots with lots of interactions, any neighbor with a total of 1 interaction is pooled together into an "other" category.
The columns in this table give the distance between the two hotspots in km, the heading from the reference hotspot to neighbor in degrees and compass heading as well as the total interaction counts and pass percentage.
