#!/usr/bin/env python3

"""
Registration functionality for Bittensor nodes
"""

import os
import threading
import time
import random
import logging
import bittensor as bt
from datetime import datetime, timedelta

from settings.block_monitor import EnhancedBlockMonitor
from monitoring.fee_strategy import AdaptiveFeeStrategy
from logic.utils import send_telegram
from bittensor_registration.config import (
    TAOSTATS_API_KEY, 
    SUBSCAN_API_KEY, 
    BASE_PRIORITY_FEE, 
    MAX_PRIORITY_FEE,
    DEFAULT_NETUID
)

logger = logging.getLogger("registration")

class RegistrationAssistant:
    """Bittensor registration assistant"""
    def __init__(self, network="finney", rpc_url=None):
        self.network = network
        self.rpc_url = rpc_url
        self.block_monitor = EnhancedBlockMonitor(
            taostats_api_key=TAOSTATS_API_KEY,
            subscan_api_key=SUBSCAN_API_KEY
        )
        self.fee_strategy = AdaptiveFeeStrategy(
            base_multiplier=BASE_PRIORITY_FEE,
            max_multiplier=MAX_PRIORITY_FEE
        )
        
    def discover_wallets(self):
        """Discover available wallets in the local directory"""
        wallets = []
        wallet_path = os.path.expanduser("~/.bittensor/wallets")
        if not os.path.exists(wallet_path):
            logger.info(f"No wallets found at {wallet_path}")
            return wallets
            
        for coldkey_name in os.listdir(wallet_path):
            coldkey_path = os.path.join(wallet_path, coldkey_name)
            if os.path.isdir(coldkey_path):
                hotkey_path = os.path.join(coldkey_path, "hotkeys")
                if os.path.exists(hotkey_path):
                    for hotkey_name in os.listdir(hotkey_path):
                        if hotkey_name.endswith(".git"):
                            continue
                        wallets.append({
                            "coldkey": coldkey_name,
                            "hotkey": hotkey_name
                        })
                        
        logger.info(f"Discovered {len(wallets)} wallets")
        return wallets
        
    def select_wallets(self, available_wallets):
        """Select wallets to use for registration"""
        if not available_wallets:
            logger.warning("No wallets available")
            return []
            
        print("\nAvailable Wallets:")
        for i, wallet in enumerate(available_wallets):
            print(f"  [{i+1}] {wallet['coldkey']}/{wallet['hotkey']}")
            
        print("\nSelect wallets (comma separated numbers, or 'all'):")
        
        def safe_input():
            try:
                return input("> ").strip()
            except:
                return "all"
        
        selection = safe_input()
            
        selected_wallets = []
        if selection.lower() == "all":
            selected_wallets = available_wallets
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selection.split(",")]
                for i in indices:
                    if 0 <= i < len(available_wallets):
                        selected_wallets.append(available_wallets[i])
                    else:
                        logger.warning(f"Invalid selection index: {i+1}")
            except ValueError:
                logger.warning("Invalid selection format")
                
        logger.info(f"Selected {len(selected_wallets)} wallets")
        return selected_wallets
        
    def get_registration_cost(self, netuid):
        """Get current registration cost for a subnet"""
        try:
            subtensor = bt.subtensor(network=self.network, chain_endpoint=self.rpc_url)
            cost = subtensor.get_burn_cost(netuid=netuid)
            return float(cost)
        except Exception as e:
            logger.error(f"Failed to get registration cost: {str(e)}")
            return None
            
    def register_neuron(self, wallet, netuid, use_priority_fee=False):
        """Register a neuron on a subnet"""
        coldkey_name = wallet["coldkey"]
        hotkey_name = wallet["hotkey"]
        
        try:
            wallet_obj = bt.wallet(name=coldkey_name, hotkey=hotkey_name)
            subtensor = bt.subtensor(network=self.network, chain_endpoint=self.rpc_url)
            
            if subtensor.is_hotkey_registered(netuid=netuid, hotkey_ss58=wallet_obj.hotkey.ss58_address):
                logger.info(f"{coldkey_name}/{hotkey_name} already registered on subnet {netuid}")
                return True
                
            cost = subtensor.get_burn_cost(netuid=netuid)
            if cost is None:
                logger.error(f"Failed to get registration cost for {coldkey_name}/{hotkey_name}")
                return False
                
            balance = subtensor.get_balance(wallet_obj.coldkeypub.ss58_address)
            if balance < cost:
                logger.error(f"Insufficient balance for {coldkey_name}/{hotkey_name}: {balance:.6f} < {cost:.6f}")
                return False
                
            current_block, window_info = self.block_monitor.get_current_block()
            if current_block and window_info:
                if not window_info['in_window']:
                    logger.info(f"Not in registration window. {window_info['status']}")
                    return False
                    
            if use_priority_fee:
                priority_fee = self.fee_strategy.compute_priority_fee(cost)
                logger.info(f"Using priority fee: {priority_fee:.6f} TAO")
                total_cost = cost + priority_fee
            else:
                total_cost = cost
                priority_fee = 0
                
            logger.info(f"Attempting to register {coldkey_name}/{hotkey_name} on subnet {netuid}")
            logger.info(f"  - Cost: {cost:.6f} TAO")
            logger.info(f"  - Priority fee: {priority_fee:.6f} TAO")
            logger.info(f"  - Total: {total_cost:.6f} TAO")
            logger.info(f"  - Balance: {balance:.6f} TAO")
            
            result = bt.register(
                wallet=wallet_obj,
                netuid=netuid,
                subtensor=subtensor,
                prompt=False,
                use_custom_pow=True,
                cuda=True,
                tpb=256,
                num_processes=8,
                update_interval=15,
                output_in_place=True,
                dev_id=0,
                wait_for_finalization=True,
                wait_for_inclusion=True,
                max_retries=3,
                repeat_registration=False,
                priority_fee=priority_fee if use_priority_fee else None
            )
            
            if result is True:
                success_msg = f"Registration successful for {coldkey_name}/{hotkey_name} on subnet {netuid}"
                logger.info(success_msg)
                send_telegram(success_msg)
                self.fee_strategy.update_statistics(success=True)
                return True
            else:
                fail_msg = f"Registration failed for {coldkey_name}/{hotkey_name} on subnet {netuid}"
                logger.error(fail_msg)
                send_telegram(fail_msg)
                self.fee_strategy.update_statistics(success=False)
                return False
                
        except Exception as e:
            error_msg = f"Error during registration of {coldkey_name}/{hotkey_name}: {str(e)}"
            logger.error(error_msg)
            send_telegram(error_msg)
            self.fee_strategy.update_statistics(success=False)
            return False
            
    def register_thread(self, wallets, netuid, use_priority_fee, delay_range, stop_event):
        """Registration thread for multiple wallets"""
        while not stop_event.is_set() and wallets:
            wallet = wallets.pop(0)
            
            try:
                success = self.register_neuron(wallet, netuid, use_priority_fee)
                
                if success is False and not stop_event.is_set():
                    wallets.append(wallet)
                    
                if not stop_event.is_set() and wallets:
                    delay = random.uniform(delay_range[0], delay_range[1])
                    logger.info(f"Waiting {delay:.1f}s before next attempt...")
                    
                    for _ in range(int(delay)):
                        if stop_event.is_set():
                            break
                        time.sleep(1)
                        
            except Exception as e:
                logger.error(f"Thread error: {str(e)}")
                if not stop_event.is_set():
                    wallets.append(wallet)
                    time.sleep(5)

    def multi_register(self, netuid, wallets, thread_count=1, use_priority_fee=True, delay=(10, 30)):
        """Register multiple wallets concurrently"""
        if not wallets:
            logger.warning("No wallets to register")
            return
            
        self.block_monitor.start_monitoring()
        
        threads = []
        stop_event = threading.Event()
        
        try:
            wallet_groups = []
            for i in range(thread_count):
                wallet_groups.append([])
                
            for i, wallet in enumerate(wallets):
                wallet_groups[i % thread_count].append(wallet)
                
            for i in range(thread_count):
                if wallet_groups[i]:
                    thread = threading.Thread(
                        target=self.register_thread,
                        args=(wallet_groups[i], netuid, use_priority_fee, delay, stop_event)
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    
            start_time = datetime.now()
            total_wallets = len(wallets)
            registered_wallets = []
            
            while any(thread.is_alive() for thread in threads):
                try:
                    subtensor = bt.subtensor(network=self.network, chain_endpoint=self.rpc_url)
                    
                    newly_registered = []
                    for wallet in wallets:
                        if wallet in registered_wallets:
                            continue
                            
                        try:
                            wallet_obj = bt.wallet(name=wallet["coldkey"], hotkey=wallet["hotkey"])
                            hotkey_ss58 = wallet_obj.hotkey.ss58_address
                            
                            if subtensor.is_hotkey_registered(netuid=netuid, hotkey_ss58=hotkey_ss58):
                                registered_wallets.append(wallet)
                                newly_registered.append(wallet)
                        except Exception as e:
                            logger.debug(f"Error checking registration status: {str(e)}")
                            
                    current_block, window_info = self.block_monitor.get_current_block()
                    elapsed = datetime.now() - start_time
                    remaining_wallets = total_wallets - len(registered_wallets)
                    
                    for wallet in newly_registered:
                        logger.info(f"? Confirmed registration: {wallet['coldkey']}/{wallet['hotkey']}")
                        
                    if current_block and window_info:
                        status_msg = f"\n=== Registration Status ===\n"
                        status_msg += f"• Block: {current_block} - {window_info['status']}\n"
                        status_msg += f"• Progress: {len(registered_wallets)}/{total_wallets} wallets registered ({remaining_wallets} remaining)\n"
                        status_msg += f"• Running for: {elapsed.total_seconds()//3600:.0f}h {(elapsed.total_seconds()%3600)//60:.0f}m {elapsed.total_seconds()%60:.0f}s\n"
                        
                        fee_stats = self.fee_strategy.get_fee_statistics()
                        status_msg += f"• Success rate: {fee_stats['success_rate']*100:.1f}%\n"
                        status_msg += f"• Current fee multiplier: {fee_stats['current_multiplier']:.2f}x\n"
                        
                        logger.info(status_msg)
                        
                        if elapsed.total_seconds() % 1800 < 10:
                            self.send_telegram(
                                f"*Registration Status Update*\n"
                                f"• Block: `{current_block}` - {window_info['status']}\n"
                                f"• Progress: `{len(registered_wallets)}/{total_wallets}` registered\n"
                                f"• Running for: `{elapsed.total_seconds()//3600:.0f}h {(elapsed.total_seconds()%3600)//60:.0f}m`\n"
                                f"• Success rate: `{fee_stats['success_rate']*100:.1f}%`\n"
                            )
                    
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt detected, stopping registration...")
                    break
                except Exception as e:
                    logger.error(f"Error in monitor loop: {str(e)}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            logger.info("Registration interrupted by user")
        finally:
            stop_event.set()
            
            for thread in threads:
                thread.join(timeout=5.0)
                
            elapsed = datetime.now() - start_time
            logger.info(f"\n=== Registration Summary ===")
            logger.info(f"• Total wallets: {total_wallets}")
            logger.info(f"• Successfully registered: {len(registered_wallets)}")
            logger.info(f"• Remaining: {total_wallets - len(registered_wallets)}")
            logger.info(f"• Total runtime: {elapsed.total_seconds()//3600:.0f}h {(elapsed.total_seconds()%3600)//60:.0f}m {elapsed.total_seconds()%60:.0f}s")
            
            self.block_monitor.stop_monitoring()