"""
Configuration management for NASA Mission Control integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "api_key": "",
    "refresh_interval": 10,
    "device_id": "nasa_mission_control",
    "device_name": "NASA Mission Control"
}

NASA_SOURCES = {
    "apod": {
        "name": "Daily Universe",
        "description": "Astronomy Picture of the Day"
    },
    "epic": {
        "name": "Earth Live", 
        "description": "Earth from Deep Space"
    },
    "iss": {
        "name": "ISS Tracker",
        "description": "International Space Station Location"
    },
    "neo": {
        "name": "NEO Watch",
        "description": "Near Earth Objects"
    },
    "insight": {
        "name": "Mars Archive",
        "description": "Mars Mission Data"
    },
    "donki": {
        "name": "Space Weather",
        "description": "Solar Events & Space Weather"
    }
}


class Config:
    """Configuration management for NASA integration."""

    def __init__(self, config_file_path: str):
        """Initialize configuration."""
        self._config_file_path = config_file_path
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self._config_file_path):
                with open(self._config_file_path, "r", encoding="utf-8") as file:
                    self._config = json.load(file)
                    _LOG.info("Configuration loaded from %s", self._config_file_path)
            else:
                _LOG.info("Configuration file not found, using defaults")
                self._config = DEFAULT_CONFIG.copy()
        except Exception as ex:
            _LOG.error("Failed to load configuration: %s", ex)
            self._config = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self._config_file_path), exist_ok=True)
            with open(self._config_file_path, "w", encoding="utf-8") as file:
                json.dump(self._config, file, indent=2)
                _LOG.info("Configuration saved to %s", self._config_file_path)
        except Exception as ex:
            _LOG.error("Failed to save configuration: %s", ex)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Update configuration with new data."""
        self._config.update(data)
        self.save()

    @property
    def api_key(self) -> str:
        """Get NASA API key."""
        return self._config.get("api_key", "")

    @property
    def refresh_interval(self) -> int:
        """Get refresh interval in minutes."""
        return self._config.get("refresh_interval", 10)

    @property
    def device_id(self) -> str:
        """Get device ID."""
        return self._config.get("device_id", "nasa_mission_control")

    @property
    def device_name(self) -> str:
        """Get device name."""
        return self._config.get("device_name", "NASA Mission Control")

    @property
    def sources(self) -> Dict[str, Dict[str, Any]]:
        """Get NASA data sources configuration."""
        return NASA_SOURCES

    def get_source_list(self) -> list[str]:
        """Get list of available sources for media player."""
        return [source_data["name"] for source_data in NASA_SOURCES.values()]

    def get_source_by_name(self, name: str) -> Optional[str]:
        """Get source ID by display name."""
        for source_id, source_data in NASA_SOURCES.items():
            if source_data["name"] == name:
                return source_id
        return None

    def get_source_data(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source configuration data."""
        return NASA_SOURCES.get(source_id)