#!/usr/bin/env python3

"""
Interactive CLI for registration configuration
"""

from colorama import Fore, Style
from logic.utils import safe_input
from logic.config_manager import ConfigManager
import sys

class InteractiveCLI:
    def __init__(self):
        self.cfg = ConfigManager()
        self.current_strategy = self.cfg.get('strategy', 'default')
        self.available_strategies = self._discover_strategies()

    def _discover_strategies(self):
        """Automatically discover available strategies"""
        strategies = {}
        try:
            from strategy import STRATEGIES
            for name, cls in STRATEGIES.items():
                strategies[name] = cls.description
        except ImportError:
            pass
        return strategies or {'default': 'Basic registration strategy'}

    def main_menu(self):
        """Main menu"""
        while True:
            print(f"\n{Fore.CYAN}=== Bittensor Registration Manager ===")
            print("1. Configure Network Settings")
            print("2. Select Registration Strategy")
            print("3. Manage Wallets")
            print("4. Fee Settings")
            print("5. Start Registration")
            print(f"6. Save and Exit{Style.RESET_ALL}")

            choice = safe_input("Select option: ").strip()

            if choice == '1':
                self.network_menu()
            elif choice == '2':
                self.strategy_menu()
            elif choice == '3':
                self.wallet_menu()
            elif choice == '4':
                self.fee_menu()
            elif choice == '5':
                self.start_registration()
            elif choice == '6':
                self.cfg.save()
                return
            else:
                print(f"{Fore.RED}Invalid option{Style.RESET_ALL}")

    def network_menu(self):
        """Network configuration menu"""
        print(f"\n{Fore.YELLOW}=== Network Configuration ===")
        current_network = self.cfg.get('network', 'finney')
        print(f"Current network: {current_network}")

        new_network = safe_input(
            "Enter network [finney/test/local] (Enter to skip): ",
            default=current_network
        )
        if new_network.lower() in ['finney', 'test', 'local']:
            self.cfg.set('network', new_network.lower())

        current_rpc = self.cfg.get('rpc_url', '')
        new_rpc = safe_input(
            "Enter custom RPC URL (Enter to skip): ",
            default=current_rpc
        )
        if new_rpc:
            self.cfg.set('rpc_url', new_rpc)

    def strategy_menu(self):
        """Strategy selection menu"""
        print(f"\n{Fore.GREEN}Available Strategies:")
        for i, (name, desc) in enumerate(self.available_strategies.items(), 1):
            print(f"{i}. {name} - {desc}")

        choice = safe_input("Select strategy (number or name): ").strip()
        try:
            if choice.isdigit():
                name = list(self.available_strategies.keys())[int(choice) - 1]
            else:
                name = choice

            if name in self.available_strategies:
                self.current_strategy = name
                self.cfg.set('strategy', name)
                print(f"{Fore.GREEN}Strategy {name} selected{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid strategy{Style.RESET_ALL}")
        except (IndexError, ValueError):
            print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")

    def wallet_menu(self):
        """Wallet management menu"""
        print(f"\n{Fore.BLUE}=== Wallet Management ===")
        # Functionality to manage wallets can be added here
        print("Wallet management feature coming soon")

    def fee_menu(self):
        """Fee configuration menu"""
        print(f"\n{Fore.MAGENTA}=== Fee Configuration ===")
        base_fee = self.cfg.get('base_fee', 0.5)
        new_base = safe_input(
            f"Enter base fee multiplier (current: {base_fee}): ",
            default=str(base_fee)
        )
        if new_base:
            self.cfg.set('base_fee', float(new_base))

    def start_registration(self):
        """Start the registration process"""
        from main import main as start_main
        print(f"{Fore.CYAN}Starting registration process...{Style.RESET_ALL}")
        sys.argv = [sys.argv[0]]  # Clear arguments
        for k, v in self.cfg.config.items():
            if v is not None:
                sys.argv.append(f"--{k}")
                sys.argv.append(str(v))
        start_main()

if __name__ == "__main__":
    cli = InteractiveCLI()
    cli.main_menu()
