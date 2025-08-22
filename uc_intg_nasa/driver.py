#!/usr/bin/env python3
"""
NASA Mission Control integration driver.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
import os
import signal
from typing import Optional

import ucapi

from uc_intg_nasa.client import NASAClient
from uc_intg_nasa.config import Config
from uc_intg_nasa.media_player import NASAMediaPlayer
from uc_intg_nasa.setup import NASASetup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

_LOG = logging.getLogger(__name__)

loop = asyncio.get_event_loop()
api: Optional[ucapi.IntegrationAPI] = None
nasa_client: Optional[NASAClient] = None
nasa_config: Optional[Config] = None
media_player: Optional[NASAMediaPlayer] = None

async def on_setup_complete():
    """Callback executed when driver setup is complete."""
    global media_player, nasa_client, api
    _LOG.info("Setup complete. Creating entities...")

    if not api or not nasa_client:
        _LOG.error("Cannot create entities: API or client not initialized.")
        await api.set_device_state(ucapi.DeviceStates.ERROR)
        return

    try:
        if not nasa_config.api_key:
            _LOG.error("NASA client is not configured after setup")
            await api.set_device_state(ucapi.DeviceStates.ERROR)
            return

        _LOG.info("Creating NASA Mission Control media player entity")
        
        media_player = NASAMediaPlayer(nasa_config, nasa_client)
        api.available_entities.add(media_player)
        _LOG.info(f"Added media player entity: {media_player.id}")
        
        _LOG.info("Media player entity created successfully. Setting state to CONNECTED.")
        await api.set_device_state(ucapi.DeviceStates.CONNECTED)
        
    except Exception as e:
        _LOG.error(f"Error creating entities: {e}", exc_info=True)
        await api.set_device_state(ucapi.DeviceStates.ERROR)

async def on_r2_connect():
    """Handle Remote connection."""
    _LOG.info("Remote connected.")
    
    if api and nasa_config and nasa_config.api_key:
        _LOG.info("NASA integration is configured. Setting state to CONNECTED.")
        await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    else:
        _LOG.info("Integration not configured yet.")

async def on_disconnect():
    """Handle Remote disconnection."""
    _LOG.info("Remote disconnected.")
    
    if media_player:
        await media_player.shutdown()

async def on_subscribe_entities(entity_ids: list[str]):
    """Handle entity subscription."""
    _LOG.info(f"Entities subscribed: {entity_ids}. Initializing entities...")
    
    for entity_id in entity_ids:
        if media_player and entity_id == media_player.id:
            _LOG.info(f"Initializing NASA media player entity: {entity_id}")
            
            try:
                media_player._api = api
                await media_player.push_initial_state()
                _LOG.info("NASA Mission Control media player fully initialized and ready")
                
            except Exception as ex:
                _LOG.error(f"Error initializing media player: {ex}", exc_info=True)

async def on_unsubscribe_entities(entity_ids: list[str]):
    """Handle entity unsubscription from Remote."""
    _LOG.info(f"Remote unsubscribed from entities: {entity_ids}")
    
    for entity_id in entity_ids:
        if media_player and entity_id == media_player.id:
            _LOG.info("Media player entity unsubscribed - stopping monitoring")
            await media_player.shutdown()

async def init_integration():
    """Initialize the integration objects and API."""
    global api, nasa_client, nasa_config
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    driver_json_path = os.path.join(project_root, "driver.json")
    
    if not os.path.exists(driver_json_path):
        driver_json_path = "driver.json"
        if not os.path.exists(driver_json_path):
            _LOG.error(f"Cannot find driver.json at {driver_json_path}")
            raise FileNotFoundError("driver.json not found")
    
    _LOG.info(f"Using driver.json from: {driver_json_path}")

    api = ucapi.IntegrationAPI(loop)
    ucapi._current_api = api

    config_path = os.path.join(api.config_dir_path, "config.json")
    _LOG.info(f"Using config file: {config_path}")
    nasa_config = Config(config_path)
    
    nasa_client = NASAClient(nasa_config)

    setup_handler = NASASetup(nasa_config, nasa_client, on_setup_complete)
    
    await api.init(driver_json_path, setup_handler.setup_handler)
    
    api.add_listener(ucapi.Events.CONNECT, on_r2_connect)
    api.add_listener(ucapi.Events.DISCONNECT, on_disconnect)
    api.add_listener(ucapi.Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
    api.add_listener(ucapi.Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
    
    _LOG.info("Integration API initialized successfully")
    
async def main():
    """Main entry point."""
    _LOG.info("Starting NASA Mission Control Integration Driver")
    
    try:
        await init_integration()
        
        if nasa_config and nasa_config.api_key:
            _LOG.info("Integration is already configured")
            await on_setup_complete()
        else:
            _LOG.warning("Integration is not configured. Waiting for setup...")

        _LOG.info("Integration is running. Press Ctrl+C to stop.")
        
    except Exception as e:
        _LOG.error(f"Failed to start integration: {e}", exc_info=True)
        if api:
            await api.set_device_state(ucapi.DeviceStates.ERROR)
        raise
    
def shutdown_handler(signum, frame):
    """Handle termination signals for graceful shutdown."""
    _LOG.warning(f"Received signal {signum}. Shutting down...")
    
    async def cleanup():
        try:
            if nasa_client:
                _LOG.info("Closing NASA client...")
                await nasa_client.close()
            
            if media_player:
                _LOG.info("Shutting down media player...")
                await media_player.shutdown()
            
            _LOG.info("Cancelling remaining tasks...")
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            [task.cancel() for task in tasks]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            _LOG.error(f"Error during cleanup: {e}")
        finally:
            _LOG.info("Stopping event loop...")
            loop.stop()

    loop.create_task(cleanup())

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Driver stopped.")
    except Exception as e:
        _LOG.error(f"Driver failed: {e}", exc_info=True)
    finally:
        if loop and not loop.is_closed():
            _LOG.info("Closing event loop...")
            loop.close()