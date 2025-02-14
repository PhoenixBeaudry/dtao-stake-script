
#!/usr/bin/env python3
import bittensor as bt

def configure_wallet():
    """
    Configures and returns a wallet if not in dry run mode.
    """
    wallet = bt.wallet(name="snipe")
    wallet.unlock_coldkey()
    return wallet



def unstake_on_subnet(sub, netuid, wallet):
    """
    Processes staking for a given subnet.
    Dynamically finds an optimal stake increment that yields a slippage within the desired range.

    Returns:
        A tuple (updated_increment, spent) where updated_increment is the optimal increment,
        and spent is the TAO amount used in the staking transaction.
    """
    print(f"\n==== Processing Subnet {netuid} ====")
    subnet = sub.subnet(netuid)

    try:
        current_stake = sub.get_stake(
            coldkey_ss58=wallet.coldkeypub.ss58_address,
            hotkey_ss58=subnet.owner_hotkey,
            netuid=netuid
        )

        value_of_stake = subnet.price*current_stake/10**9
        
        if(value_of_stake.tao > 3):
            sub.unstake(
                wallet=wallet,
                netuid=netuid,
                hotkey_ss58=subnet.owner_hotkey,
                amount=bt.Balance.from_tao(current_stake.tao/2)
            )
        
            print(f"Unstaking succeeded on subnet {netuid}. New stake: {current_stake}")
        else:
            print(f"Value isn't high enough, waiting....")

    except Exception as e:
        print(f"Error during unstaking on subnet {netuid}: {e}")

    return

if __name__ == '__main__':
    sub = bt.Subtensor("finney")

    wallet = configure_wallet()

    # List of subnets (netuids) to stake into
    subnets_to_unstake = [19, 4, 51, 9, 1, 8, 34, 64, 51, 29]


    while True:
        try:
            for netuid in subnets_to_unstake:
                unstake_on_subnet(sub, netuid, wallet)
            print("Waiting for next block...")
            sub.wait_for_block()
        except:
            print("Network not upgraded, trying again.")
            sub.wait_for_block()

