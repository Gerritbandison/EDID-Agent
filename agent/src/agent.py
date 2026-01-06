"""
Device Inventory Agent - Main Application

Cross-platform agent that collects system and monitor information
and reports to the inventory management server.
"""
import os
import sys
import time
import logging
import signal
import threading
from typing import Optional
from datetime import datetime

import requests

from .collectors import get_collector
from .config import Config


def setup_logging():
    """Configure logging with file handler."""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'agent.log')

    handlers = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(log_file, mode='a'))
    except (OSError, IOError):
        pass  # Skip file handler if we can't write

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


setup_logging()
logger = logging.getLogger('inventory-agent')


class InventoryAgent:
    """Main agent class for device inventory collection."""

    VERSION = '1.0.0'

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the agent with configuration."""
        self.config = Config(config_path)
        self.collector = get_collector()
        self.running = False
        self.last_check_in = None
        self._shutdown_event = threading.Event()

    def start(self):
        """Start the agent in continuous mode."""
        logger.info(f"Starting Device Inventory Agent v{self.VERSION}")
        logger.info(f"API Endpoint: {self.config.api_url}")
        logger.info(f"Check-in interval: {self.config.check_in_interval} seconds")

        self.running = True
        self._setup_signal_handlers()

        # Initial check-in
        self._perform_check_in()

        # Main loop
        while self.running and not self._shutdown_event.is_set():
            # Wait for next check-in or shutdown
            self._shutdown_event.wait(timeout=self.config.check_in_interval)

            if self.running and not self._shutdown_event.is_set():
                self._perform_check_in()

        logger.info("Agent stopped")

    def stop(self):
        """Stop the agent."""
        logger.info("Stopping agent...")
        self.running = False
        self._shutdown_event.set()

    def run_once(self):
        """Perform a single check-in and exit."""
        logger.info(f"Running single check-in (Agent v{self.VERSION})")
        success = self._perform_check_in()
        return success

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _perform_check_in(self):
        """Perform a check-in with the server."""
        try:
            logger.info("Collecting system information...")

            # Collect all data
            data = self.collector.collect_all()
            device_data = data['device']
            monitors_data = data['monitors']

            logger.info(f"Collected data for device: {device_data.get('hostname')}")
            logger.info(f"Found {len(monitors_data)} connected monitors")

            # Send device data
            success = self._send_device_data(device_data)

            if success and monitors_data:
                # Send monitor data
                self._send_monitor_data(device_data['id'], monitors_data)

            self.last_check_in = datetime.now()
            return success

        except Exception as e:
            logger.error(f"Check-in failed: {e}", exc_info=True)
            return False

    def _send_device_data(self, device_data: dict) -> bool:
        """Send device data to the API with retry logic."""
        url = f"{self.config.api_url}/api/devices"
        headers = self._get_headers()

        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    url,
                    json=device_data,
                    headers=headers,
                    timeout=self.config.request_timeout
                )

                if response.status_code in (200, 201):
                    logger.info("Device data sent successfully")
                    return True
                else:
                    logger.warning(
                        f"Device data submission failed: {response.status_code} - {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        logger.error("Failed to send device data after all retries")
        return False

    def _send_monitor_data(self, device_id: str, monitors: list) -> bool:
        """Send monitor data to the API."""
        url = f"{self.config.api_url}/api/monitors"
        headers = self._get_headers()

        payload = {
            'device_id': device_id,
            'monitors': monitors
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.request_timeout
            )

            if response.status_code in (200, 201):
                logger.info(f"Monitor data sent successfully ({len(monitors)} monitors)")
                return True
            else:
                logger.warning(
                    f"Monitor data submission failed: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send monitor data: {e}")
            return False

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.config.api_key,
            'User-Agent': f'InventoryAgent/{self.VERSION}'
        }

    def check_for_updates(self) -> Optional[dict]:
        """Check for agent updates."""
        url = f"{self.config.api_url}/api/agent/version"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                version_info = response.json()
                latest_version = version_info.get('version', '0.0.0')

                if self._compare_versions(latest_version, self.VERSION) > 0:
                    logger.info(f"Update available: {latest_version} (current: {self.VERSION})")
                    return version_info

        except Exception as e:
            logger.debug(f"Update check failed: {e}")

        return None

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare two version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0

            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1

        return 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Device Inventory Agent')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--version', '-v', action='store_true', help='Show version')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.version:
        print(f"Device Inventory Agent v{InventoryAgent.VERSION}")
        sys.exit(0)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    agent = InventoryAgent(config_path=args.config)

    if args.once:
        success = agent.run_once()
        sys.exit(0 if success else 1)
    else:
        agent.start()


if __name__ == '__main__':
    main()
