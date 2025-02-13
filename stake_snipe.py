####################
# This is a script to automatically stake TAO into new dTAO Subnets
# In order to run this script, first create a new venv in this directory: 'python3 -m venv venv'
# Activate the venv: 'source venv/bin/activate'
# Install release candidate bittensor sdk: 'pip install bittensor==9.0.0rc6'
# Install latest release candidate btcli: 'pip install bittensor-cli==9.0.0rc4'
# Ensure you have a Bittensor wallet + hotkey created using 'btcli w create' called 'snipe'
# Fill in preferred parameters in __main__ and TARGET_TOTAL_SPEND
# For actual run make sure variables DRY_RUN and TEST_NET_RUN are set to False.
# Run script after network upgrade.
####################


#!/usr/bin/env python3
import bittensor as bt

DRY_RUN = False
TEST_NET_RUN = True
TARGET_TOTAL_SPEND = 0.3 if TEST_NET_RUN else 20.0

def configure_wallet(dry_run):
    """
    Configures and returns a wallet if not in dry run mode.
    """
    if dry_run:
        return None
    wallet = bt.wallet(name="snipe")
    wallet.unlock_coldkey()
    return wallet


def find_optimal_increment(subnet, min_increment, max_increment, target_min, target_max, tolerance=1e-3, max_iterations=20):
    """
    Uses binary search to find a stake increment that yields a slippage percentage within the target range [target_min, target_max].

    Assumes that slippage is a monotonic function with respect to the increment.

    Args:
        subnet: The subnet object for slippage queries.
        min_increment: The minimum allowable stake increment.
        max_increment: The maximum allowable stake increment.
        target_min: The minimum desired slippage percentage.
        target_max: The maximum desired slippage percentage.
        tolerance: The acceptable difference between high and low bounds.
        max_iterations: Maximum iterations for the binary search.

    Returns:
        A tuple (optimal_increment, optimal_slippage)
    """
    low = min_increment
    high = max_increment
    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        try:
            sl = subnet.slippage(mid, percentage=True)
        except Exception as e:
            print(f"Error calculating slippage: {e}")
            return mid, None
        if target_min <= sl <= target_max:
            return mid, sl
        if sl < target_min:
            low = mid
        else:
            high = mid
        if high - low < tolerance:
            mid_final = (low + high) / 2.0
            try:
                sl_final = subnet.slippage(mid_final, percentage=True)
            except Exception as e:
                sl_final = None
            return mid_final, sl_final
    mid_final = (low + high) / 2.0
    try:
        sl_final = subnet.slippage(mid_final, percentage=True)
    except Exception as e:
        sl_final = None
    return mid_final, sl_final

def stake_on_subnet(sub, netuid, current_increment, dry_run, wallet, lower_threshold, upper_threshold, min_increment, max_increment):
    """
    Processes staking for a given subnet.
    Dynamically finds an optimal stake increment that yields a slippage within the desired range.

    Returns:
        A tuple (updated_increment, spent) where updated_increment is the optimal increment,
        and spent is the TAO amount used in the staking transaction.
    """
    print(f"\n==== Processing Subnet {netuid} ====")
    subnet = sub.subnet(netuid)

    optimal_increment, optimal_slippage = find_optimal_increment(
        subnet, min_increment, max_increment, lower_threshold, upper_threshold
    )

    if optimal_slippage is None:
        print("Could not determine optimal slippage. Skipping transaction.")
        return current_increment, 0.0

    print(f"Optimal increment found: {optimal_increment:.3f} TAO with slippage: {optimal_slippage:.4f}%")
    spent = 0.0
    if optimal_slippage < 10.0:
        print("Slippage acceptable, proceeding with staking transaction.")
        if not dry_run:
            try:
                sub.add_stake(
                    wallet=wallet,
                    netuid=netuid,
                    hotkey_ss58=subnet.owner_hotkey,
                    amount=bt.Balance.from_tao(optimal_increment)
                )
                current_stake = sub.get_stake(
                    coldkey_ss58=wallet.coldkeypub.ss58_address,
                    hotkey_ss58=subnet.owner_hotkey,
                    netuid=netuid
                )
                print(f"Staking succeeded on subnet {netuid}. Current stake: {current_stake}")
                spent = optimal_increment
            except Exception as e:
                print(f"Error during staking on subnet {netuid}: {e}")
        else:
            print("Dry run enabled: Skipping actual staking transaction.")
            spent = optimal_increment
    else:
        print(f"Optimal slippage for subnet {netuid} ({optimal_slippage:.4f}%) too high; skipping this transaction.")
    return optimal_increment, spent

if __name__ == '__main__':
    # Connect to the network: use test network if TEST_NET_RUN is True, otherwise use main network.
    sub = bt.Subtensor(network="test" if TEST_NET_RUN else "main")

    wallet = configure_wallet(DRY_RUN)

    # List of subnets (netuids) to stake into
    subnets_to_stake = [19, 4, 51]
    stake_tracker = {net: 0.0 for net in subnets_to_stake}
    total_spend = 0.0

    # Initialize stake increment and dynamic adjustment parameters
    current_increment = 0.025 if TEST_NET_RUN else 1.0
    lower_threshold = 0    # Minimum desired slippage (in %)
    upper_threshold = 5.0   # Maximum desired slippage (in %)
    min_increment = 0.01
    max_increment = 0.025 if TEST_NET_RUN else 1.0

    while total_spend < TARGET_TOTAL_SPEND:
        for netuid in subnets_to_stake:
            current_increment, spent = stake_on_subnet(
                sub, netuid, current_increment, DRY_RUN, wallet,
                lower_threshold, upper_threshold, min_increment, max_increment
            )
            if spent > 0:
                stake_tracker[netuid] += spent
                total_spend += spent
                print(f"Total TAO spent so far: {total_spend:.3f}")
            if total_spend >= TARGET_TOTAL_SPEND:
                break
        print("Waiting for next block...")
        sub.wait_for_block()

    print("Target TAO spending reached. Staking complete.")
