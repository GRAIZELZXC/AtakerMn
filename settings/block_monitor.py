#!/usr/bin/env python3

"""
Block monitoring module for Bittensor registration
"""

import threading
import time
import logging
import requests
from datetime import datetime, timedelta
from bittensor_registration.config import TEMPO, BLOCK_WINDOW, TAOSTATS_API_KEY, SUBSCAN_API_KEY

logger = logging.getLogger("registration")

class EnhancedBlockMonitor:
    """Enhanced block monitoring for Bittensor network with multiple APIs"""
    def __init__(self, taostats_api_key=None, subscan_api_key=None):
        self.current_block = None
        self.last_updated = datetime.min
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.taostats_api_key = taostats_api_key
        self.subscan_api_key = subscan_api_key
        self.update_countdown = None
        self.tempo = TEMPO
        self.block_window = BLOCK_WINDOW
        
    def start_monitoring(self):
        """Start background block monitoring"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return  # Already running
            
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_blocks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Enhanced block monitor started")
        
    def stop_monitoring(self):
        """Stop block monitoring"""
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Block monitor stopped")
        
    def get_current_block(self):
        """Get the current block number and registration window info"""
        if self.current_block is not None and datetime.now() - self.last_updated < timedelta(seconds=10):
            return self.current_block, self._get_window_info(self.current_block)
        return None, None
        
    def _get_window_info(self, block):
        """Get registration window information for a block"""
        if block is None:
            return {
                'in_window': False,
                'block_in_tempo': None,
                'next_window': None,
                'status': 'Unknown'
            }
            
        block_in_tempo = block % self.tempo
        in_window = block_in_tempo in self.block_window
        
        if in_window:
            blocks_left = max(self.block_window) - block_in_tempo
            if blocks_left <= 0:
                blocks_left = max(self.block_window) - min(self.block_window) + self.tempo
                
            return {
                'in_window': True,
                'block_in_tempo': block_in_tempo,
                'blocks_left': blocks_left,
                'status': f"WINDOW ACTIVE - {blocks_left} blocks left"
            }
        else:
            next_window_blocks = []
            for w in self.block_window:
                if w > block_in_tempo:
                    next_window_blocks.append(w - block_in_tempo)
                else:
                    next_window_blocks.append(self.tempo - block_in_tempo + w)
                    
            next_window = min(next_window_blocks)
            
            return {
                'in_window': False,
                'block_in_tempo': block_in_tempo,
                'next_window': next_window,
                'status': f"Next window in ~{next_window} blocks"
            }
            
    def _monitor_blocks(self):
        """Background monitoring thread"""
        while not self.stop_event.is_set():
            try:
                methods = [
                    self._check_via_taostats,
                    self._check_via_subscan,
                    self._check_via_polkadot_subscan,
                    self._check_via_bittensor_dashboard,
                    self._check_via_finney_explorer
                ]
                
                for method in methods:
                    success = method()
                    if success:
                        break
                        
                if self.current_block is None:
                    logger.warning("Unable to fetch current block from any source")
                    
                time.sleep(5)
            except Exception as e:
                logger.error(f"Block monitor error: {str(e)}")
                time.sleep(30)
    
    def _check_via_taostats(self):
        """Check current block via TAO Stats API"""
        if not self.taostats_api_key:
            return False
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.taostats_api_key}"
            }
            response = requests.get(
                "https://api.taostats.io/api/network/blocks/latest",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "block_number" in data:
                    new_block = int(data["block_number"])
                    
                    if self.current_block != new_block:
                        window_info = self._get_window_info(new_block)
                        logger.debug(f"Block updated via TAO Stats: {new_block} - {window_info['status']}")
                    
                    self.current_block = new_block
                    self.last_updated = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"TAO Stats block check failed: {str(e)}")
        return False
                
    def _check_via_subscan(self):
        """Check current block via Subscan API"""
        if not self.subscan_api_key:
            return False
            
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.subscan_api_key
            }
            response = requests.post(
                "https://finney.api.subscan.io/api/scan/metadata",
                headers=headers,
                json={},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "blockNum" in data["data"]:
                    new_block = int(data["data"]["blockNum"])
                    
                    if self.current_block != new_block:
                        window_info = self._get_window_info(new_block)
                        logger.debug(f"Block updated via Subscan: {new_block} - {window_info['status']}")
                    
                    self.current_block = new_block
                    self.last_updated = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"Subscan block check failed: {str(e)}")
        return False
            
    def _check_via_polkadot_subscan(self):
        """Check current block via public Polkadot Subscan API"""
        try:
            url = "https://polkadot.webapi.subscan.io/api/scan/block"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json={}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "block_num" in data["data"]:
                    new_block = int(data["data"]["block_num"])
                    
                    if self.current_block != new_block:
                        window_info = self._get_window_info(new_block)
                        logger.debug(f"Block updated via Polkadot API: {new_block} - {window_info['status']}")
                    
                    self.current_block = new_block
                    self.last_updated = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"Polkadot Subscan check failed: {str(e)}")
        return False
        
    def _check_via_bittensor_dashboard(self):
        """Check current block via Bittensor Dashboard API"""
        try:
            url = "https://api.bittensor.com/data/api/v1/blocks"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and "finalized_block" in data:
                    new_block = int(data["finalized_block"])
                    
                    if self.current_block != new_block:
                        window_info = self._get_window_info(new_block)
                        logger.debug(f"Block updated via Bittensor API: {new_block} - {window_info['status']}")
                    
                    self.current_block = new_block
                    self.last_updated = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"Bittensor API check failed: {str(e)}")
        return False
        
    def _check_via_finney_explorer(self):
        """Check current block via Finney Explorer"""
        try:
            url = "https://explorer.finney.opentensor.ai/api/blocks?page=0&size=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and data["data"] and "number" in data["data"][0]:
                    new_block = int(data["data"][0]["number"])
                    
                    if self.current_block != new_block:
                        window_info = self._get_window_info(new_block)
                        logger.debug(f"Block updated via Finney Explorer: {new_block} - {window_info['status']}")
                    
                    self.current_block = new_block
                    self.last_updated = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"Finney Explorer check failed: {str(e)}")
        return False