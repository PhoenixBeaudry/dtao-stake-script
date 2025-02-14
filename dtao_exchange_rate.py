#!/usr/bin/env python3
import bittensor as bt

config = bt.config()

sub = bt.Subtensor(network="finney")

print(sub)

subnets_to_stake = [19, 4, 51, 9, 1, 8, 34, 64,51, 29]

while(True):
    try:
        for netuid in subnets_to_stake:
            subnet = sub.subnet(netuid)
            print(f"Subnet {netuid} price: {subnet.price}/alpha")
            sub.wait_for_block()
    except:
        print("Network not upgraded, trying again.")
        sub.wait_for_block()