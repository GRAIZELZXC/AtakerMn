#!/usr/bin/env python3

"""
Main entry point for Bittensor registration assistant
"""

import sys
import io
import colorama
from colorama import Fore, Style
import argparse

# Fix encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# For Windows console
if sys.platform.startswith('win'):
    import os
    os.system('chcp 65001 > nul')

# Initialize colorama
colorama.init(autoreset=True)

# Import from local modules
from logic.utils import setup_logging
from strategy.registration import RegistrationAssistant
from bittensor_registration.config import DEFAULT_NETUID, MIN_DELAY, MAX_DELAY

def main():
    """Main entry point"""
    # Set up logging
    logger = setup_logging()
    
    # Print banner
    print(f"""
{Fore.CYAN}=====================================================
   Bittensor Advanced Registration Assistant v1.0.2
=====================================================
{Style.RESET_ALL}
""")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Bittensor Registration Assistant")
    parser.add_argument("--network", type=str, default="finney", choices=["finney", "test", "local"], help="Bittensor network")
    parser.add_argument("--netuid", type=int, default=DEFAULT_NETUID, help="Subnet UID to register on")
    parser.add_argument("--rpc", type=str, default=None, help="Custom RPC endpoint URL")
    parser.add_argument("--threads", type=int, default=1, help="Number of registration threads")
    parser.add_argument("--min-delay", type=int, default=MIN_DELAY, help="Minimum delay between registration attempts")
    parser.add_argument("--max-delay", type=int, default=MAX_DELAY, help="Maximum delay between registration attempts")
    parser.add_argument("--no-priority-fee", action="store_true", help="Disable priority fees")
    args = parser.parse_args()
    
    # Initialize assistant
    assistant = RegistrationAssistant(network=args.network, rpc_url=args.rpc)
    
    # Discover wallets
    available_wallets = assistant.discover_wallets()
    
    if not available_wallets:
        print(f"{Fore.RED}No wallets found. Please run 'btcli wallet new' to create a wallet.{Style.RESET_ALL}")
        return 1
        
    # Select wallets for registration
    selected_wallets = assistant.select_wallets(available_wallets)
    
    if not selected_wallets:
        print(f"{Fore.RED}No wallets selected. Exiting.{Style.RESET_ALL}")
        return 1
        
    # Get registration cost
    reg_cost = assistant.get_registration_cost(args.netuid)
    if reg_cost is None:
        print(f"{Fore.RED}Failed to get registration cost. Check network connection.{Style.RESET_ALL}")
        return 1
        
    # Display configuration
    print(f"\n{Fore.CYAN}Registration Configuration:{Style.RESET_ALL}")
    print(f"• Network: {args.network}")
    print(f"• Subnet UID: {args.netuid}")
    print(f"• Registration cost: {reg_cost:.6f} TAO")
    print(f"• Priority fees: {'Disabled' if args.no_priority_fee else 'Enabled'}")
    print(f"• Threads: {args.threads}")
    print(f"• Delay between attempts: {args.min_delay} - {args.max_delay}s")
    
    # Start registration process
    try:
        assistant.multi_register(
            netuid=args.netuid,
            wallets=selected_wallets,
            thread_count=args.threads,
            use_priority_fee=not args.no_priority_fee,
            delay=(args.min_delay, args.max_delay)
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Registration process interrupted by user.{Style.RESET_ALL}")
        return 0
    except Exception as e:
        print(f"\n{Fore.RED}Error during registration: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())