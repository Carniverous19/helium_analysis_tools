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

## analyze_hotspots.py
This file provides useful reports on an individual hotspot's PoC activity.  Note this code allows you to specify either hotspot name (with dashes) or hotspot address.
It is suggested to always use the hotspot address as there is no guarantee that a hotspot has a unique name (there are already 3 conflicts among ~8,500 hotspots)
If there is a hotspot naming conflict only the last hotspot with that name returned will be considered.

see

    python3 analyze_hotpsots.py -h
    
for more details on arguments.

### poc_v10

First is `poc_v10` which looks at recent challenge activity for the selected hotspot and reports the total number of witness and PoC hops that violate PoCv10 requirements.
For information on PoC v10 requirements see the blog post [Blockchain PoC v10](https://engineering.helium.com/2020/09/21/blockchain-poc-v10.html).

to run the `poc_v10` report run:

    python3 analyze_hotspot.py -x poc_v10 -a {hotspot address}

An example output table is shown below:

    analyzed 202 challenges from 516276-513758
    PoC v10 failures for name-name-name
    Category                   | Total | bad RSSI (%) | bad SNR (%) |
    -----------------------------------------------------------------
    Witnesses to hotspot >300m |   154 |    0 (  0%)  |   13 (  8%) |
    Hotspot witnessing  >300m  |    66 |    0 (  0%)  |    0 (  0%) |
    Hotspot PoC receipts       |    24 |    0 (  0%)  |    0 (  0%) |
    
As indicated in the first row, witnesses within 300m meters are ignored as these shouldnt (arent?) be rewarded anyway.
The column "bad RSSI" means the signal violated Free Space Path Loss estimation.  
The column "bad SNR" means the RSSI was too low for the given SNR.  High SNR but low RSSI means noise is very very low which is suspect.

### poc_reliability
Second is a report `poc_reliability` which analyzes the reliability of the specified hotsot receiving PoCs from its neighbors as well as transmitting to neighbors.
With the current PoC reward system transmitting to the following hotspot is less important since transmissions are rewarded as long as any hotspot receives the transmission (witness or next hop).
If your hotspot cannot reliably receive challenges from its neighbors it is losing out on rewards.

To run the `poc_reliability` report run:

    python3 analyze_hotspot.py -x poc_reliability -a {hotspot address}
    
    
An example output table is:

    analyzing 500 challenges from block 516256-498146 over 11 days, 11 hrs
    PoC hops from: name-name-name
    to receiving hotspot           | dist km | heading | pass/ttl | pass % |
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
    from transmitting hotspot      | dist km | heading | pass/ttl | pass % |
    ------------------------------------------------------------------------
    warm-hotpink-monkey            |    0.5  |  340  N |  16/ 26  |    62% |
    trendy-fleece-cobra            |    2.5  |  100  E |   2/  6  |    33% |
    fluffy-aqua-stallion           |    1.6  |  315 NW |   2/ 64  |     3% |
    tangy-aegean-grasshopper       |    0.4  |   15  N |  22/ 23  |    96% |
    other (10)                     |  2.2-33 |   N/A   |   1/ 10  |    10% | 
    
 
These tables count the total number of times the hotspot failed to receive an RF transmission (meaning previous hop passed) as well as the number of times the target hotspot passed and the following hop failed to receive.
For hotspots with lots of interactions, any neighbor with a total of 1 interaction is pooled together into an "other" category.
The columns in this table give the distance between the two hotspots in km, the heading from the reference hotspot to neighbor in degrees and compass heading as well as the total interaction counts and pass percentage.