"""
Setup flow for NASA Mission Control integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Callable, Dict

import ucapi

from uc_intg_nasa.client import NASAClient
from uc_intg_nasa.config import Config

_LOG = logging.getLogger(__name__)


class NASASetup:
    """NASA integration setup handler."""
    
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
        """Handle initial driver setup request."""
        _LOG.debug("Handling driver setup request - reconfigure: %s", request.reconfigure)
        
        setup_data = request.setup_data
        if setup_data and "api_key" in setup_data:
            _LOG.debug("Processing setup data from initial form: %s", setup_data.keys())
            
            api_key = setup_data.get("api_key", "").strip()
            refresh_interval = int(setup_data.get("refresh_interval", 10))
            
            if not api_key:
                api_key = "DEMO_KEY"
            
            self._config.update({
                "api_key": api_key,
                "refresh_interval": refresh_interval
            })
            
            test_result = await self._test_nasa_api_connection()
            
            if test_result["success"]:
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            else:
                return ucapi.RequestUserInput(
                    title="NASA API Connection Failed",
                    settings=[
                        {
                            "id": "api_key",
                            "label": {"en": f"Connection error: {test_result['error']}\n\nNASA API Key (leave empty for DEMO_KEY)"},
                            "field": {"text": {"value": api_key if api_key != "DEMO_KEY" else "", "placeholder": "Enter your NASA API key or leave empty"}},
                        },
                        {
                            "id": "refresh_interval",
                            "label": {"en": "Data refresh interval (minutes)"},
                            "field": {"number": {"value": refresh_interval, "min": 5, "max": 60, "steps": 5}},
                        }
                    ]
                )
        else:
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

    async def _handle_user_confirmation_response(self, response: ucapi.UserConfirmationResponse) -> ucapi.SetupAction:
        """Handle user confirmation response."""
        _LOG.debug("User confirmation: %s", response.confirm)
        
        if response.confirm:
            return ucapi.SetupComplete()
        else:
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

    async def _handle_user_data_response(self, response: ucapi.UserDataResponse) -> ucapi.SetupAction:
        """Handle user input data and validate NASA API connection."""
        _LOG.debug("Received user data: %s", response.input_values.keys())
        
        try:
            api_key = response.input_values.get("api_key", "").strip()
            refresh_interval = int(response.input_values.get("refresh_interval", 10))
            
            if not api_key:
                api_key = "DEMO_KEY"
            
            if refresh_interval < 5 or refresh_interval > 60:
                return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
            
            self._config.update({
                "api_key": api_key,
                "refresh_interval": refresh_interval
            })
            
            test_result = await self._test_nasa_api_connection()
            
            if test_result["success"]:
                if self._setup_complete_callback:
                    await self._setup_complete_callback()
                return ucapi.SetupComplete()
            else:
                return ucapi.RequestUserInput(
                    title="NASA API Connection Failed",
                    settings=[
                        {
                            "id": "api_key",
                            "label": {"en": f"Connection error: {test_result['error']}\n\nNASA API Key (leave empty for DEMO_KEY)"},
                            "field": {"text": {"value": api_key if api_key != "DEMO_KEY" else "", "placeholder": "Enter your NASA API key or leave empty"}},
                        },
                        {
                            "id": "refresh_interval",
                            "label": {"en": "Data refresh interval (minutes)"},
                            "field": {"number": {"value": refresh_interval, "min": 5, "max": 60, "steps": 5}},
                        }
                    ]
                )
                
        except Exception as ex:
            _LOG.error("Error handling user data: %s", ex)
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

    async def _handle_abort_setup(self, request: ucapi.AbortDriverSetup) -> ucapi.SetupAction:
        """Handle setup abortion."""
        _LOG.debug("Setup aborted: %s", request.error)
        return ucapi.SetupError(request.error)

    async def _test_nasa_api_connection(self) -> Dict[str, Any]:
        """
        Test NASA API connection with current configuration.
        
        :return: Dictionary with test results
        """
        _LOG.debug("Testing NASA API connection")
        
        tested_apis = []
        errors = []
        
        try:
            try:
                image_url, title, description = await self._nasa_client.fetch_apod_data()
                if image_url and title:
                    tested_apis.append("APOD")
                else:
                    errors.append("APOD returned no data")
            except Exception as ex:
                errors.append(f"APOD: {str(ex)[:50]}")
            
            if len(tested_apis) == 0:
                try:
                    image_url, title, description = await self._nasa_client.fetch_iss_data()
                    if "Lat:" in description:
                        tested_apis.append("ISS")
                    else:
                        errors.append("ISS returned invalid data")
                except Exception as ex:
                    errors.append(f"ISS: {str(ex)[:50]}")
        
        except Exception as ex:
            errors.append(f"Client error: {str(ex)[:50]}")
        
        success = len(tested_apis) >= 1 or (len(errors) == 0)
        
        result = {
            "success": success,
            "tested_apis": ", ".join(tested_apis) if tested_apis else "Basic connectivity OK",
            "error": "; ".join(errors) if errors and not success else None
        }
        
        _LOG.debug("API test result: %s", result)
        return result