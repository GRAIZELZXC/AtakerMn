# Bittensor Registration Assistant

Advanced registration assistant for Bittensor network that helps manage and automate the registration process for multiple wallets.

## Features

- Multi-wallet management
- Automatic registration window detection
- Adaptive fee strategy based on network congestion
- Multi-threaded registration
- Telegram notifications
- Block monitoring with multiple fallback APIs

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/bittensor-registration.git
cd bittensor-registration
```

2. Install requirements:
```bash
pip install bittensor requests colorama
```

## Usage

Run the registration assistant from the root directory:

```bash
python run_registration.py --network finney --netuid 1 --threads 2
```

### Command-line Arguments

- `--network`: Bittensor network to use (`finney`, `test`, or `local`)
- `--netuid`: Subnet UID to register on
- `--rpc`: Custom RPC endpoint URL (optional)
- `--threads`: Number of registration threads
- `--min-delay`: Minimum delay between registration attempts
- `--max-delay`: Maximum delay between registration attempts
- `--no-priority-fee`: Disable priority fees

## Configuration

You can modify the configuration parameters in `bittensor_registration/config.py`:

- Network settings
- Fee strategy parameters
- Telegram notifications
- API keys
- Registration window settings

## Project Structure

```
bittensor_registration/ - Core module
  ├── __init__.py
  ├── main.py - Main entry point 
  └── config.py - Configuration parameters
settings/ - Settings modules
  ├── __init__.py
  └── block_monitor.py - Block monitoring functionality
monitoring/ - Monitoring modules
  ├── __init__.py
  └── fee_strategy.py - Adaptive fee calculation
strategy/ - Strategy modules
  ├── __init__.py
  └── registration.py - Registration logic
logic/ - Utility modules
  ├── __init__.py
  └── utils.py - Helper functions
run_registration.py - Root-level entry point
```