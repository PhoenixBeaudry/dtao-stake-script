#!/usr/bin/env python3
import bittensor as bt

config = bt.config()

sub = bt.Subtensor(network="ws://127.0.0.1:9944")

print(sub)

subnets_to_stake = [19, 4, 51]

for netuid in subnets_to_stake:
    subnet = sub.subnet(netuid)
    print(f"Subnet {netuid} price: {subnet.price}/alpha")