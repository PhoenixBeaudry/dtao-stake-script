import bittensor as bt

# Configuration flags
dry_run = True
test_net_run = True

# Connect to the network (using "test" network for testing)
sub = bt.Subtensor(network="test")

if not dry_run:
    wallet = bt.wallet(name="test")
    wallet.unlock_coldkey()

# List of subnets (netuids) to stake into
subnets_to_stake = [19, 4, 51]

# Initialize tracking variables:
total_spend = 0.0  # Total TAO spent across subnets
stake = {netuid: 0.0 for netuid in subnets_to_stake}  # Current stake per subnet

# Set the base stake increment according to the environment
if test_net_run:
    increment = 0.025  # Use a small increment on testnet
else:
    increment = 1.0    # Larger increment on mainnet

# Dynamic adjustment parameters:
lower_threshold = 3.0    # If slippage is below 5%, liquidity is plentiful -> increase stake size
upper_threshold = 11.0   # If slippage is above 15%, reduce stake size
min_increment = 0.01     # Minimum allowable stake increment (TAO)

if(test_net_run):
    max_increment = 0.1      # Maximum allowable stake increment (TAO)
else:
    max_increment = 1.0      # Maximum allowable stake increment (TAO)

adjustment_factor = 1.5  # Factor to increase stake size when liquidity is good

target_total_spend = 10.0  # Global TAO spending target

while total_spend < target_total_spend:
    for netuid in subnets_to_stake:
        print(f"\n==== Processing Subnet {netuid} ====")
        subnet = sub.subnet(netuid)

        # Get an estimate of alpha received and slippage (as a percentage)
        slippage = subnet.slippage(increment, percentage=True)
        estimated_alpha = subnet.tao_to_alpha_with_slippage(increment)[0].tao
        print(f"Estimated alpha for staking t{increment:.3f}: {estimated_alpha}")
        print(f"Current slippage for subnet {netuid}: {slippage:.4f}%")

        # Dynamically adjust the stake increment based on slippage conditions
        if slippage < lower_threshold:
            new_increment = min(increment * adjustment_factor, max_increment)
            if new_increment != increment:
                print(f"Low slippage ({slippage:.4f}%). Increasing stake increment from {increment} to {new_increment}.")
                increment = new_increment
        elif slippage > upper_threshold:
            new_increment = max(increment * 0.9, min_increment)
            if new_increment != increment:
                print(f"High slippage ({slippage:.4f}%). Decreasing stake increment from {increment} to {new_increment}.")
                increment = new_increment

        # Proceed with staking if slippage is within acceptable bounds
        if slippage < 20.0:
            print("Slippage acceptable, proceeding with staking transaction.")
            if not dry_run:
                try:
                    sub.add_stake(
                        wallet=wallet,
                        netuid=netuid,
                        hotkey_ss58=subnet.owner_hotkey,
                        amount=bt.Balance.from_tao(increment)
                    )
                    # Retrieve and log the updated stake for this subnet
                    current_stake = sub.get_stake(
                        coldkey_ss58=wallet.coldkeypub.ss58_address,
                        hotkey_ss58=subnet.owner_hotkey,
                        netuid=netuid
                    )
                    if current_stake != stake[netuid]:
                        print(f"Staking succeeded on subnet {netuid}. Current stake: {current_stake}")
                        stake[netuid] = current_stake
                        total_spend += increment
                        print(f"Total TAO spent so far: {total_spend}")
                except Exception as e:
                    print(f"Error during staking on subnet {netuid}: {e}")
            else:
                print("Dry run enabled: Skipping actual staking transaction.")
        else:
            print(f"Slippage for subnet {netuid} ({slippage:.4f}%) too high; skipping this transaction.")

    print("Waiting for next block...")
    sub.wait_for_block()

print("Target TAO spending reached. Staking complete.")
