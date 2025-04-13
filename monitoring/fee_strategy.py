#!/usr/bin/env python3

"""
Fee strategy module for Bittensor registration
"""

import logging
from bittensor_registration.config import BASE_PRIORITY_FEE, MAX_PRIORITY_FEE

logger = logging.getLogger("registration")

class AdaptiveFeeStrategy:
    """Advanced adaptive fee strategy for registration"""
    def __init__(self, base_multiplier=0.5, max_multiplier=2.0, adapt_threshold=5):
        self.base_multiplier = base_multiplier
        self.max_multiplier = max_multiplier
        self.adapt_threshold = adapt_threshold
        self.attempts = 0
        self.successes = 0
        self.success_rate = 0.5
        self.block_congestion = 0.0
        self.recent_fees = []
        self.last_fee = None
        
    def update_statistics(self, success=None, block_time=None):
        """Update fee statistics based on results"""
        if success is not None:
            self.attempts += 1
            if success:
                self.successes += 1
            self.success_rate = self.successes / self.attempts
            
        if block_time is not None:
            if block_time > 12.0:
                self.block_congestion = min(1.0, self.block_congestion + 0.1)
            elif block_time > 9.0:
                self.block_congestion = min(0.8, self.block_congestion + 0.05)
            elif block_time > 6.0:
                self.block_congestion = min(0.5, self.block_congestion + 0.02)
            else:
                self.block_congestion = max(0.0, self.block_congestion - 0.05)
                
    def compute_priority_fee(self, base_cost):
        """Compute adaptive priority fee based on success rate and network conditions"""
        if self.attempts > self.adapt_threshold:
            if self.success_rate < 0.2:
                congestion_boost = self.block_congestion * 0.5
                modifier = min(self.max_multiplier, self.max_multiplier - 0.5 + congestion_boost)
                logger.info(f"Low success rate ({self.success_rate:.2f}), using high fee multiplier: {modifier:.2f}x")
            elif self.success_rate < 0.5:
                congestion_boost = self.block_congestion * 0.3
                modifier = min(self.max_multiplier - 0.2, self.base_multiplier + 0.5 + congestion_boost)
                logger.info(f"Medium success rate ({self.success_rate:.2f}), using enhanced fee multiplier: {modifier:.2f}x")
            else:
                congestion_boost = self.block_congestion * 0.2
                modifier = self.base_multiplier + congestion_boost
                logger.info(f"Good success rate ({self.success_rate:.2f}), using base fee multiplier: {modifier:.2f}x")
                
            fee = base_cost * modifier
        else:
            fee = base_cost * self.base_multiplier
            
        self.last_fee = fee
        self.recent_fees.append(fee)
        
        if len(self.recent_fees) > 10:
            self.recent_fees.pop(0)
            
        return fee
    
    def get_fee_statistics(self):
        """Get statistics about fee strategy"""
        if not self.recent_fees:
            return {
                'current_multiplier': self.base_multiplier,
                'success_rate': self.success_rate,
                'congestion': self.block_congestion,
                'avg_fee': 0.0,
                'min_fee': 0.0,
                'max_fee': 0.0
            }
            
        return {
            'current_multiplier': self.last_fee / (self.last_fee / self.base_multiplier) if self.last_fee else self.base_multiplier,
            'success_rate': self.success_rate,
            'congestion': self.block_congestion,
            'avg_fee': sum(self.recent_fees) / len(self.recent_fees),
            'min_fee': min(self.recent_fees),
            'max_fee': max(self.recent_fees)
        }