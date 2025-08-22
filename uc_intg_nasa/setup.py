"""
Setup flow for NASA Mission Control integration with robust API validation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Callable, Dict

import ucapi

from uc_intg_nasa.client import NASAClient
from uc_intg_nasa.config import Config

_LOG = logging.getLogger(__name__)


class NASASetup:
    """NASA integration setup handler with robust validation and retry logic."""
    
    def __init__(self, config: Config, nasa_client: NASAClient, setup_complete_callback: Callable):
        """Initialize setup handler."""
        self._config = config
        self._nasa_client = nasa_client
        self._setup_complete_callback = setup_complete_callback

    async def setup_handler(self, driver_setup_request: ucapi.SetupDriver) -> ucapi.SetupAction:
        """
        Handle driver setup requests.
        
        :param driver_setup_request: setup request from Remote Two
        :return: setup action response
        """
        _LOG.debug("Setup handler called: %s", type(driver_setup_request).__name__)

        if isinstance(driver_setup_request, ucapi.DriverSetupRequest):
            return await self._handle_driver_setup_request(driver_setup_request)
        elif isinstance(driver_setup_request, ucapi.UserDataResponse):
            return await self._handle_user_data_response(driver_setup_request)
        elif isinstance(driver_setup_request, ucapi.UserConfirmationResponse):
            return await self._handle_user_confirmation_response(driver_setup_request)
        elif isinstance(driver_setup_request, ucapi.AbortDriverSetup):
            return await self._handle_abort_setup(driver_setup_request)
        else:
            _LOG.error("Unknown setup request type: %s", type(driver_setup_request))
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

    async def _handle_driver_setup_request(self, request: ucapi.DriverSetupRequest) -> ucapi.SetupAction:
        """Handle initial driver setup request with robust validation."""
        _LOG.debug("Handling driver setup request - reconfigure: %s", request.reconfigure)
        
        setup_data = request.setup_data
        if setup_data and "api_key" in setup_data:
            _LOG.debug("Processing setup data from initial form: %s", setup_data.keys())
            
            api_key = setup_data.get("api_key", "").strip()
            refresh_interval = int(setup_data.get("refresh_interval", 10))
            force_setup = setup_data.get("force_setup", False)
            
            if not api_key:
                api_key = "DEMO_KEY"
            
            # Save configuration FIRST
            self._config.update({
                "api_key": api_key,
                "refresh_interval": refresh_interval
            })
            
            if force_setup:
                _LOG.info("🔧 Setup forced by user - bypassing API validation")
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            
            # Test API connection with robust retry logic
            test_result = await self._test_nasa_api_connection()
            
            if test_result["success"]:
                _LOG.info("✅ Setup validation passed")
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            else:
                _LOG.warning("⚠️ API validation failed, offering options")
                return ucapi.RequestUserInput(
                    title="NASA API Connection Issue",
                    settings=[
                        {
                            "id": "api_key",
                            "label": {"en": f"⚠️ {test_result['error']}\n\nTry different API key or leave empty:"},
                            "field": {"text": {"value": api_key if api_key != "DEMO_KEY" else "", "placeholder": "New NASA API key or leave empty"}},
                        },
                        {
                            "id": "refresh_interval",
                            "label": {"en": "Data refresh interval (minutes)"},
                            "field": {"number": {"value": refresh_interval, "min": 5, "max": 60, "steps": 5}},
                        },
                        {
                            "id": "force_setup",
                            "label": {"en": "Force setup completion (ignore API errors)"},
                            "field": {"checkbox": {"value": False}},
                        }
                    ]
                )
        else:
            # Initial setup form
            return ucapi.RequestUserInput(
                title="NASA Mission Control Configuration",
                settings=[
                    {
                        "id": "api_key",
                        "label": {"en": "NASA API Key (leave empty to use DEMO_KEY with 30 req/hour limit)"},
                        "field": {"text": {"value": self._config.api_key if self._config.api_key != "DEMO_KEY" else "", "placeholder": "Get free key at api.nasa.gov"}},
                    },
                    {
                        "id": "refresh_interval",
                        "label": {"en": "Data refresh interval (minutes)"},
                        "field": {"number": {"value": self._config.refresh_interval, "min": 5, "max": 60, "steps": 5}},
                    }
                ]
            )

    async def _handle_user_data_response(self, response: ucapi.UserDataResponse) -> ucapi.SetupAction:
        """Handle user input data with smart retry logic and force option."""
        _LOG.debug("Received user data: %s", response.input_values.keys())
        
        try:
            api_key = response.input_values.get("api_key", "").strip()
            refresh_interval = int(response.input_values.get("refresh_interval", 10))
            force_setup = response.input_values.get("force_setup", False)
            
            if not api_key:
                api_key = "DEMO_KEY"
            
            if refresh_interval < 5 or refresh_interval > 60:
                return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
            
            # Save configuration FIRST
            self._config.update({
                "api_key": api_key,
                "refresh_interval": refresh_interval
            })
            
            if force_setup:
                # User chose to bypass API validation
                _LOG.info("🔧 Setup forced by user - bypassing API validation")
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            
            # Test API connection with retries
            test_result = await self._test_nasa_api_connection()
            
            if test_result["success"]:
                # At least one API works - proceed with setup
                _LOG.info("✅ Setup validation passed")
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            else:
                # All APIs failed - offer retry with force option
                _LOG.warning("⚠️ API validation failed, offering bypass option")
                return ucapi.RequestUserInput(
                    title="NASA API Connection Issue",
                    settings=[
                        {
                            "id": "api_key",
                            "label": {"en": f"⚠️ {test_result['error']}\n\nTry different API key or force setup:"},
                            "field": {"text": {"value": api_key if api_key != "DEMO_KEY" else "", "placeholder": "New NASA API key or leave empty"}},
                        },
                        {
                            "id": "refresh_interval",
                            "label": {"en": "Data refresh interval (minutes)"},
                            "field": {"number": {"value": refresh_interval, "min": 5, "max": 60, "steps": 5}},
                        },
                        {
                            "id": "force_setup",
                            "label": {"en": "✅ Force setup completion (integration will work with cached/fallback data)"},
                            "field": {"checkbox": {"value": False}},
                        }
                    ]
                )
                
        except Exception as ex:
            _LOG.error("Error handling user data: %s", ex)
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

    async def _handle_user_confirmation_response(self, response: ucapi.UserConfirmationResponse) -> ucapi.SetupAction:
        """Handle user confirmation response."""
        _LOG.debug("User confirmation: %s", response.confirm)
        
        if response.confirm:
            return ucapi.SetupComplete()
        else:
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

    async def _handle_abort_setup(self, request: ucapi.AbortDriverSetup) -> ucapi.SetupAction:
        """Handle setup abortion."""
        _LOG.debug("Setup aborted: %s", request.error)
        return ucapi.SetupError(request.error)

    async def _test_nasa_api_connection(self) -> Dict[str, Any]:
        """
        Test NASA API connection with robust retry logic and fallbacks.
        Tests multiple APIs and only fails if NO APIs work after retries.
        """
        _LOG.info("Testing NASA API connection with retry logic...")
        
        tested_apis = []
        errors = []
        
        # Test multiple APIs with retries
        apis_to_test = [
            ("APOD", self._nasa_client.fetch_apod_data, lambda r: r[1] and len(r[1]) > 5),
            ("ISS", self._nasa_client.fetch_iss_data, lambda r: "ISS" in r[1] and ("°" in r[1] or "over" in r[1])),
            ("NEO", self._nasa_client.fetch_neo_data, lambda r: "asteroid" in r[1].lower() or "today" in r[1].lower()),
        ]
        
        for api_name, api_method, validation_func in apis_to_test:
            for attempt in range(2):  # 2 attempts per API
                try:
                    _LOG.debug(f"Testing {api_name} API (attempt {attempt + 1}/2)")
                    
                    # Short timeout per attempt
                    result = await asyncio.wait_for(api_method(), timeout=3)
                    
                    if validation_func(result):
                        tested_apis.append(api_name)
                        _LOG.info(f"✅ {api_name} API test passed: {result[1][:40]}")
                        break  # Success - move to next API
                    else:
                        _LOG.debug(f"❌ {api_name} API returned invalid data: {result[1][:40]}")
                        if attempt == 1:  # Last attempt
                            errors.append(f"{api_name}: Invalid data format")
                        
                except asyncio.TimeoutError:
                    _LOG.debug(f"⏰ {api_name} API timeout (attempt {attempt + 1})")
                    if attempt == 1:  # Last attempt
                        errors.append(f"{api_name}: Timeout")
                        
                except Exception as ex:
                    _LOG.debug(f"❌ {api_name} API error: {str(ex)[:50]}")
                    if attempt == 1:  # Last attempt
                        errors.append(f"{api_name}: {str(ex)[:50]}")
                
                # Small delay between retries
                if attempt == 0:
                    await asyncio.sleep(0.5)
        
        # Success criteria: At least ONE API must work
        success = len(tested_apis) >= 1
        
        if success:
            _LOG.info(f"✅ API validation successful: {', '.join(tested_apis)}")
            return {
                "success": True,
                "tested_apis": ", ".join(tested_apis),
                "error": None
            }
        else:
            _LOG.warning(f"❌ All APIs failed: {'; '.join(errors)}")
            
            # Check if it's likely a network/SSL issue vs API key issue
            if all("timeout" in error.lower() or "connection" in error.lower() for error in errors):
                error_msg = "Network connectivity issue - check internet connection"
            elif any("APOD" in error for error in errors) and len([e for e in errors if "APOD" in e]) > 0:
                error_msg = "NASA API key may be invalid or rate limited"
            else:
                error_msg = f"Multiple API failures detected"
            
            return {
                "success": False,
                "tested_apis": "",
                "error": error_msg
            }