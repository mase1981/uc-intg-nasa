"""
NASA Mission Control Media Player with static icon management.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import base64
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional
import time

import ucapi
from ucapi import EntityTypes, StatusCodes

from uc_intg_nasa.client import NASAClient
from uc_intg_nasa.config import Config

_LOG = logging.getLogger(__name__)

CommandHandler = Callable[[ucapi.Entity, str, dict[str, Any] | None], Awaitable[StatusCodes]]

SUPPRESS_MEDIA_COMMANDS = [
    ucapi.media_player.Commands.PLAY_PAUSE,
    ucapi.media_player.Commands.SHUFFLE,
    ucapi.media_player.Commands.REPEAT,
    ucapi.media_player.Commands.STOP,
    ucapi.media_player.Commands.FAST_FORWARD,
    ucapi.media_player.Commands.REWIND,
    ucapi.media_player.Commands.SEEK,
    ucapi.media_player.Commands.RECORD,
    ucapi.media_player.Commands.MY_RECORDINGS,
    ucapi.media_player.Commands.MUTE_TOGGLE,
    ucapi.media_player.Commands.MUTE,
    ucapi.media_player.Commands.UNMUTE,
    ucapi.media_player.Commands.VOLUME,
    ucapi.media_player.Commands.VOLUME_UP,
    ucapi.media_player.Commands.VOLUME_DOWN
]


class StaticIconManager:
    """Manages static space icons for instant loading."""
    
    def __init__(self, base_dir: str):
        """Initialize the static icon manager."""
        self.base_dir = Path(base_dir)
        self.icons_dir = self.base_dir / "uc_intg_nasa" / "icons"
        self._icon_cache: Dict[str, str] = {}
        self._category_images: Dict[str, list] = {}
        self._daily_universe_image: Optional[str] = None
        self._daily_universe_date: Optional[str] = None
        
        self._load_icon_categories()
        
        _LOG.info(f"Static Icon Manager initialized with {len(self._icon_cache)} icons")
    
    def _load_icon_categories(self):
        """Load categorized icon lists from the icons directory."""
        try:
            if not self.icons_dir.exists():
                _LOG.warning(f"Icons directory not found: {self.icons_dir}")
                self._create_fallback_categories()
                return
            
            index_file = self.icons_dir / "image_index.py"
            if index_file.exists():
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("image_index", index_file)
                    index_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(index_module)
                    
                    if hasattr(index_module, 'CATEGORIES'):
                        self._category_images = index_module.CATEGORIES
                        _LOG.info(f"Loaded {len(self._category_images)} image categories")
                except Exception as ex:
                    _LOG.error(f"Error loading image index: {ex}")
                    self._scan_icons_directory()
            else:
                self._scan_icons_directory()
                
        except Exception as ex:
            _LOG.error(f"Error loading icon categories: {ex}")
            self._create_fallback_categories()
    
    def _scan_icons_directory(self):
        """Scan icons directory and categorize images."""
        _LOG.info("Scanning icons directory...")
        
        categories = {
            'earth': [],
            'space': [],
            'planets': [],
            'nebula': [],
            'galaxy': [],
            'general': []
        }
        
        for file_path in self.icons_dir.glob("*.jpg"):
            filename = file_path.name
            
            if 'earth' in filename.lower():
                categories['earth'].append(filename)
            elif any(word in filename.lower() for word in ['mars', 'jupiter', 'saturn', 'planet']):
                categories['planets'].append(filename)
            elif 'nebula' in filename.lower():
                categories['nebula'].append(filename)
            elif 'galaxy' in filename.lower():
                categories['galaxy'].append(filename)
            elif 'space' in filename.lower():
                categories['space'].append(filename)
            else:
                categories['general'].append(filename)
        
        self._category_images = {k: v for k, v in categories.items() if v}
        _LOG.info(f"Categorized {sum(len(v) for v in categories.values())} images")
    
    def _create_fallback_categories(self):
        """Create fallback icon categories when no icons are available."""
        _LOG.warning("No icons found, creating fallback categories")
        self._category_images = {
            'earth': [],
            'space': [],
            'planets': [],
            'nebula': [],
            'galaxy': [],
            'general': []
        }
    
    def get_icon_for_source(self, source_id: str, force_new: bool = False) -> str:
        """Get appropriate icon for source."""
        if source_id == "apod":
            return self._get_daily_universe_icon()
        
        category = self._get_category_for_source(source_id)
        return self._get_random_icon_from_category(category, force_new)
    
    def _get_daily_universe_icon(self) -> str:
        """Get Daily Universe icon - updates daily at 5am local time."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        refresh_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now < refresh_time:
            refresh_time -= timedelta(days=1)
            today_str = refresh_time.strftime("%Y-%m-%d")
        
        if self._daily_universe_date != today_str:
            _LOG.info(f"Refreshing Daily Universe image for {today_str}")
            self._daily_universe_image = self._get_random_icon_from_category('space', force_new=True)
            self._daily_universe_date = today_str
        
        return self._daily_universe_image or self._get_fallback_icon('apod')
    
    def _get_category_for_source(self, source_id: str) -> str:
        """Map source ID to icon category."""
        category_map = {
            'apod': 'space',
            'epic': 'earth', 
            'iss': 'space',
            'neo': 'general',
            'insight': 'planets',
            'donki': 'space'
        }
        return category_map.get(source_id, 'general')
    
    def _get_random_icon_from_category(self, category: str, force_new: bool = False) -> str:
        """Get random icon from category as base64."""
        available_images = self._category_images.get(category, [])
        
        if not available_images:
            all_images = []
            for imgs in self._category_images.values():
                all_images.extend(imgs)
            available_images = all_images
        
        if not available_images:
            return self._get_fallback_icon(category)
        
        if force_new or category not in self._icon_cache:
            selected_image = random.choice(available_images)
            icon_path = self.icons_dir / selected_image
            
            if icon_path.exists():
                try:
                    with open(icon_path, 'rb') as f:
                        image_data = f.read()
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        data_url = f"data:image/jpeg;base64,{b64_data}"
                        self._icon_cache[category] = data_url
                        _LOG.debug(f"Loaded icon: {selected_image} for {category}")
                        return data_url
                except Exception as ex:
                    _LOG.error(f"Error loading icon {selected_image}: {ex}")
        
        return self._icon_cache.get(category, self._get_fallback_icon(category))
    
    def _get_fallback_icon(self, source_id: str) -> str:
        """Get fallback SVG icon when no images available."""
        fallback_icons = {
            'apod': self._create_svg_icon("🌌", "#1a1a2e", "Daily Universe"),
            'epic': self._create_svg_icon("🌍", "#0077be", "Earth Live"),
            'iss': self._create_svg_icon("🛰️", "#c0c0c0", "ISS Tracker"),
            'neo': self._create_svg_icon("☄️", "#8b4513", "NEO Watch"),
            'insight': self._create_svg_icon("🔴", "#cd5c5c", "Mars Archive"),
            'donki': self._create_svg_icon("☀️", "#ffd700", "Space Weather"),
            'earth': self._create_svg_icon("🌍", "#0077be", "Earth"),
            'space': self._create_svg_icon("🌌", "#1a1a2e", "Space"),
            'planets': self._create_svg_icon("🪐", "#cd5c5c", "Planets"),
            'nebula': self._create_svg_icon("🌟", "#9932cc", "Nebula"),
            'galaxy': self._create_svg_icon("🌌", "#4b0082", "Galaxy"),
            'general': self._create_svg_icon("⭐", "#1a1a2e", "Space")
        }
        return fallback_icons.get(source_id, fallback_icons['general'])
    
    def _create_svg_icon(self, emoji: str, color: str, text: str) -> str:
        """Create SVG icon as base64 data URL."""
        svg_content = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="{color}"/>
            <text x="50%" y="35%" font-family="Arial" font-size="60" fill="#fff" text-anchor="middle" dy=".3em">{emoji}</text>
            <text x="50%" y="70%" font-family="Arial" font-size="24" fill="#fff" text-anchor="middle" dy=".3em">{text}</text>
        </svg>'''
        
        b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{b64_svg}"


class NASAMediaPlayer(ucapi.MediaPlayer):
    """NASA Mission Control Media Player with static icon management."""

    def __init__(
        self,
        config: Config,
        nasa_client: NASAClient,
        cmd_handler: CommandHandler | None = None,
    ):
        """Initialize the NASA Media Player entity."""
        self._config = config
        self._nasa_client = nasa_client
        self._current_source = "apod"
        self._update_task: Optional[asyncio.Task] = None
        self._source_updates: Dict[str, asyncio.Task] = {}
        self._api: Optional[ucapi.IntegrationAPI] = None
        self._last_push_time = 0
        
        base_dir = os.path.dirname(os.path.dirname(self._config._config_file_path))
        self._icon_manager = StaticIconManager(base_dir)
        
        features = [
            ucapi.media_player.Features.SELECT_SOURCE,
            ucapi.media_player.Features.MEDIA_IMAGE_URL,
            ucapi.media_player.Features.MEDIA_TITLE,
            ucapi.media_player.Features.MEDIA_ARTIST,
            ucapi.media_player.Features.ON_OFF,
            ucapi.media_player.Features.NEXT,
            ucapi.media_player.Features.PREVIOUS
        ]

        initial_icon = self._icon_manager.get_icon_for_source(self._current_source)
        attributes = {
            ucapi.media_player.Attributes.STATE: ucapi.media_player.States.BUFFERING,
            ucapi.media_player.Attributes.SOURCE_LIST: config.get_source_list(),
            ucapi.media_player.Attributes.SOURCE: config.get_source_data(self._current_source)["name"],
            ucapi.media_player.Attributes.MEDIA_IMAGE_URL: initial_icon,
            ucapi.media_player.Attributes.MEDIA_TITLE: "NASA Mission Control",
            ucapi.media_player.Attributes.MEDIA_ARTIST: "Initializing space data feeds..."
        }

        super().__init__(
            identifier=config.device_id,
            name=config.device_name,
            features=features,
            attributes=attributes,
            device_class=ucapi.media_player.DeviceClasses.STREAMING_BOX,
            cmd_handler=cmd_handler or self._handle_command,
        )

        _LOG.info("NASA Media Player initialized with static icon system")

    async def _handle_command(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle media player commands."""
        _LOG.debug("COMMAND: %s", cmd_id)

        try:
            if cmd_id == ucapi.media_player.Commands.ON:
                return await self._cmd_on()
            elif cmd_id == ucapi.media_player.Commands.OFF:
                return await self._cmd_off()
            elif cmd_id == ucapi.media_player.Commands.SELECT_SOURCE:
                return await self._cmd_select_source_instant(params)
            elif cmd_id == ucapi.media_player.Commands.NEXT:
                return await self._cmd_next_source_instant()
            elif cmd_id == ucapi.media_player.Commands.PREVIOUS:
                return await self._cmd_previous_source_instant()
            elif cmd_id in SUPPRESS_MEDIA_COMMANDS:
                _LOG.debug("Ignoring command '%s'", cmd_id)
                return StatusCodes.OK
            else:
                _LOG.warning("Unexpected command: %s", cmd_id)
                return StatusCodes.NOT_IMPLEMENTED

        except Exception as ex:
            _LOG.error("Error handling command %s: %s", cmd_id, ex)
            return StatusCodes.SERVER_ERROR

    async def _cmd_on(self) -> StatusCodes:
        """Turn on."""
        self.attributes[ucapi.media_player.Attributes.STATE] = ucapi.media_player.States.PLAYING
        asyncio.create_task(self._push_update_throttled())
        return StatusCodes.OK

    async def _cmd_off(self) -> StatusCodes:
        """Turn off."""
        self.attributes[ucapi.media_player.Attributes.STATE] = ucapi.media_player.States.OFF
        await self._stop_all_updates()
        asyncio.create_task(self._push_update_throttled())
        return StatusCodes.OK

    async def _cmd_select_source_instant(self, params: dict[str, Any] | None = None) -> StatusCodes:
        """Instant source selection with different static icons."""
        if not params or "source" not in params:
            return StatusCodes.BAD_REQUEST

        source_name = params["source"]
        source_id = self._config.get_source_by_name(source_name)
        
        if not source_id:
            return StatusCodes.NOT_FOUND

        self._current_source = source_id
        
        static_icon = self._icon_manager.get_icon_for_source(source_id, force_new=True)
        
        _LOG.info(f"SWITCHING TO: {source_name} ({source_id})")
        
        self.attributes[ucapi.media_player.Attributes.SOURCE] = source_name
        self.attributes[ucapi.media_player.Attributes.STATE] = ucapi.media_player.States.BUFFERING
        self.attributes[ucapi.media_player.Attributes.MEDIA_IMAGE_URL] = static_icon
        self.attributes[ucapi.media_player.Attributes.MEDIA_TITLE] = f"Loading {source_name}..."
        self.attributes[ucapi.media_player.Attributes.MEDIA_ARTIST] = "Fetching live NASA data..."
        
        asyncio.create_task(self._push_update_throttled())
        asyncio.create_task(self._update_source_background(source_id))
        
        return StatusCodes.OK

    async def _cmd_next_source_instant(self) -> StatusCodes:
        """Instant next source."""
        source_ids = list(self._config.sources.keys())
        current_index = source_ids.index(self._current_source)
        next_index = (current_index + 1) % len(source_ids)
        next_source_id = source_ids[next_index]
        
        source_name = self._config.sources[next_source_id]["name"]
        
        self._current_source = next_source_id
        static_icon = self._icon_manager.get_icon_for_source(next_source_id, force_new=True)
        
        self.attributes[ucapi.media_player.Attributes.SOURCE] = source_name
        self.attributes[ucapi.media_player.Attributes.STATE] = ucapi.media_player.States.BUFFERING
        self.attributes[ucapi.media_player.Attributes.MEDIA_IMAGE_URL] = static_icon
        self.attributes[ucapi.media_player.Attributes.MEDIA_TITLE] = f"Loading {source_name}..."
        self.attributes[ucapi.media_player.Attributes.MEDIA_ARTIST] = "Fetching live NASA data..."
        
        asyncio.create_task(self._push_update_throttled())
        asyncio.create_task(self._update_source_background(next_source_id))
        
        return StatusCodes.OK

    async def _cmd_previous_source_instant(self) -> StatusCodes:
        """Instant previous source."""
        source_ids = list(self._config.sources.keys())
        current_index = source_ids.index(self._current_source)
        prev_index = (current_index - 1) % len(source_ids)
        prev_source_id = source_ids[prev_index]
        
        source_name = self._config.sources[prev_source_id]["name"]
        
        self._current_source = prev_source_id
        static_icon = self._icon_manager.get_icon_for_source(prev_source_id, force_new=True)
        
        self.attributes[ucapi.media_player.Attributes.SOURCE] = source_name
        self.attributes[ucapi.media_player.Attributes.STATE] = ucapi.media_player.States.BUFFERING
        self.attributes[ucapi.media_player.Attributes.MEDIA_IMAGE_URL] = static_icon
        self.attributes[ucapi.media_player.Attributes.MEDIA_TITLE] = f"Loading {source_name}..."
        self.attributes[ucapi.media_player.Attributes.MEDIA_ARTIST] = "Fetching live NASA data..."
        
        asyncio.create_task(self._push_update_throttled())
        asyncio.create_task(self._update_source_background(prev_source_id))
        
        return StatusCodes.OK

    async def _update_source_background(self, source_id: str) -> None:
        """Update source data in background."""
        if source_id in self._source_updates:
            self._source_updates[source_id].cancel()
        
        update_task = asyncio.create_task(self._fetch_and_update_source(source_id))
        self._source_updates[source_id] = update_task
        
        try:
            await update_task
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            _LOG.error("Background update error for %s: %s", source_id, ex)
        finally:
            self._source_updates.pop(source_id, None)

    async def _fetch_and_update_source(self, source_id: str) -> None:
        """Fetch NASA text data and update display."""
        try:
            _LOG.info("FETCHING DATA: %s", source_id)
            
            api_image_url, title, description = await self._nasa_client.fetch_source_data(source_id)
            
            if self._current_source == source_id:
                final_image_url = await self._determine_final_image(api_image_url, source_id)
                
                _LOG.info("TITLE: %s", title)
                _LOG.info("DESC: %s", description[:50])
                
                self.attributes.update({
                    ucapi.media_player.Attributes.STATE: ucapi.media_player.States.PLAYING,
                    ucapi.media_player.Attributes.MEDIA_IMAGE_URL: final_image_url,
                    ucapi.media_player.Attributes.MEDIA_TITLE: title or "Unknown",
                    ucapi.media_player.Attributes.MEDIA_ARTIST: description or "No description available"
                })
                
                await self._push_update_force()
                
        except Exception as ex:
            _LOG.error("Error fetching %s: %s", source_id, ex)
            
            if self._current_source == source_id:
                static_icon = self._icon_manager.get_icon_for_source(source_id)
                self.attributes.update({
                    ucapi.media_player.Attributes.STATE: ucapi.media_player.States.PLAYING,
                    ucapi.media_player.Attributes.MEDIA_IMAGE_URL: static_icon,
                    ucapi.media_player.Attributes.MEDIA_TITLE: f"{source_id.upper()} Monitor",
                    ucapi.media_player.Attributes.MEDIA_ARTIST: "Data temporarily unavailable"
                })
                await self._push_update_force()

    async def _determine_final_image(self, api_image_url: str, source_id: str) -> str:
        """Determine final image based on source logic."""
        
        if source_id == "apod" and api_image_url and api_image_url.startswith("http"):
            if not (api_image_url.endswith('.png') and 'epic.gsfc.nasa.gov' in api_image_url):
                _LOG.info("Using NASA APOD image from API")
                return api_image_url
        
        static_icon = self._icon_manager.get_icon_for_source(source_id)
        _LOG.info(f"Using static icon for {source_id}")
        return static_icon

    async def _push_update_throttled(self) -> None:
        """Push update with throttling."""
        now = time.time()
        
        if now - self._last_push_time < 0.2:
            return
        
        self._last_push_time = now
        await self._push_update()

    async def _push_update(self) -> None:
        """Push state update to the remote."""
        try:
            if self._api and self._api.configured_entities.contains(self.id):
                self._api.configured_entities.update_attributes(self.id, self.attributes)
        except Exception as ex:
            _LOG.error("Error pushing update: %s", ex)

    async def _push_update_force(self) -> None:
        """Force push state update."""
        try:
            if self._api and self._api.configured_entities.contains(self.id):
                _LOG.info("UPDATE: %s -> %s", 
                         self.attributes[ucapi.media_player.Attributes.SOURCE],
                         self.attributes[ucapi.media_player.Attributes.MEDIA_TITLE])
                
                self._api.configured_entities.update_attributes(self.id, self.attributes)
        except Exception as ex:
            _LOG.error("Error in force push update: %s", ex)

    async def push_initial_state(self) -> None:
        """Push initial state."""
        _LOG.debug("Pushing initial state to remote")
        
        import ucapi
        if hasattr(ucapi, '_current_api'):
            self._api = ucapi._current_api
        
        await self._push_update()
        asyncio.create_task(self._update_source_background(self._current_source))

    async def _stop_all_updates(self) -> None:
        """Stop all running update tasks."""
        for task in self._source_updates.values():
            if not task.done():
                task.cancel()
        self._source_updates.clear()
        
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()

    async def shutdown(self) -> None:
        """Shutdown the media player and cleanup."""
        _LOG.debug("Shutting down NASA Mission Control media player")
        await self._stop_all_updates()

    @property
    def entity_id(self) -> str:
        """Get entity ID."""
        return self.id

    @property
    def current_source(self) -> str:
        """Get current source ID."""
        return self._current_source

    @property
    def current_source_name(self) -> str:
        """Get current source display name."""
        return self._config.sources[self._current_source]["name"]