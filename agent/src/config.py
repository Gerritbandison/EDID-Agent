"""
Agent Configuration Module
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration management for the agent."""

    DEFAULT_CONFIG = {
        'api_url': 'http://localhost:5000',
        'api_key': '',
        'check_in_interval': 1800,  # 30 minutes
        'max_retries': 3,
        'retry_delay': 5,
        'request_timeout': 30,
        'log_level': 'INFO',
        'log_file': 'agent.log'
    }

    def __init__(self, config_path: Optional[str] = None):
        """Load configuration from file or environment."""
        self._config = self.DEFAULT_CONFIG.copy()

        # Try to load from config file
        if config_path:
            self._load_from_file(config_path)
        else:
            # Try default paths
            default_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'config', 'agent.json'),
                '/etc/inventory-agent/config.json',
                os.path.expanduser('~/.inventory-agent/config.json'),
            ]

            for path in default_paths:
                if os.path.exists(path):
                    self._load_from_file(path)
                    break

        # Override with environment variables
        self._load_from_env()

        logger.debug(f"Configuration loaded: {self._sanitize_config()}")

    def _load_from_file(self, path: str):
        """Load configuration from JSON file."""
        try:
            with open(path, 'r') as f:
                file_config = json.load(f)
                self._config.update(file_config)
                logger.info(f"Configuration loaded from {path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mapping = {
            'INVENTORY_API_URL': 'api_url',
            'INVENTORY_API_KEY': 'api_key',
            'INVENTORY_CHECK_IN_INTERVAL': ('check_in_interval', int),
            'INVENTORY_MAX_RETRIES': ('max_retries', int),
            'INVENTORY_RETRY_DELAY': ('retry_delay', int),
            'INVENTORY_REQUEST_TIMEOUT': ('request_timeout', int),
            'INVENTORY_LOG_LEVEL': 'log_level'
        }

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                if isinstance(config_key, tuple):
                    key, converter = config_key
                    try:
                        self._config[key] = converter(value)
                    except ValueError:
                        logger.warning(f"Invalid value for {env_var}: {value}")
                else:
                    self._config[config_key] = value

    def _sanitize_config(self) -> dict:
        """Return config with sensitive values masked."""
        sanitized = self._config.copy()
        if sanitized.get('api_key'):
            sanitized['api_key'] = sanitized['api_key'][:8] + '...'
        return sanitized

    @property
    def api_url(self) -> str:
        return self._config['api_url'].rstrip('/')

    @property
    def api_key(self) -> str:
        return self._config['api_key']

    @property
    def check_in_interval(self) -> int:
        return self._config['check_in_interval']

    @property
    def max_retries(self) -> int:
        return self._config['max_retries']

    @property
    def retry_delay(self) -> int:
        return self._config['retry_delay']

    @property
    def request_timeout(self) -> int:
        return self._config['request_timeout']

    @property
    def log_level(self) -> str:
        return self._config['log_level']

    def save(self, path: str):
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def to_dict(self) -> dict:
        """Return configuration as dictionary."""
        return self._config.copy()
