#!/usr/bin/env python3

"""
Configuration manager for Bittensor registration assistant
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("registration")

class ConfigManager:
    """Configuration manager for the registration assistant"""
    
    def __init__(self, config_path=None):
        """Initialize the configuration manager"""
        if config_path is None:
            home_dir = Path.home()
            self.config_dir = home_dir / ".bittensor_registration"
            self.config_file = self.config_dir / "config.json"
        else:
            self.config_file = Path(config_path)
            self.config_dir = self.config_file.parent
            
        # Ensure the directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create default configuration
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from file or return defaults"""
        if not self.config_file.exists():
            return {
                "network": "finney",
                "netuid": 1,
                "rpc_url": None,
                "strategy": "default",
                "base_fee": 0.5,
                "max_fee": 2.0,
                "min_delay": 10,
                "max_delay": 30,
                "threads": 2,
                "telegram_enabled": True
            }
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
            
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
            
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
        return True
        
    def get_all(self):
        """Get the entire configuration"""
        return self.config