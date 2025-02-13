#!/usr/bin/env python3
import bittensor as bt

sub = bt.Subtensor(network="test")

subnets_to_stake = [19, 4, 51]

for netuid in subnets_to_stake:
    subnet = sub.subnet(netuid)
    print(f"Subnet {netuid} price: {subnet.price}/alpha")