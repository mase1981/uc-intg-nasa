"""
NASA API client for accessing live NASA data feeds - FIXED NETWORKING.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import ssl
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import aiohttp
import certifi

from uc_intg_nasa.config import Config

_LOG = logging.getLogger(__name__)


class NASAClient:
    """NASA API client for live data with intelligent caching and robust networking."""

    CACHE_INTERVALS = {
        "apod": 6 * 3600,       # 6 hours
        "epic": 2 * 3600,       # 2 hours
        "iss": 2 * 60,          # 2 minutes
        "neo": 4 * 3600,        # 4 hours
        "insight": 8 * 3600,    # 8 hours
        "donki": 3 * 3600       # 3 hours
    }

    def __init__(self, config: Config):
        """Initialize NASA client."""
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._data_cache: Dict[str, Dict[str, Any]] = {}
        self._request_locks: Dict[str, asyncio.Lock] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists with robust networking config."""
        if self._session is None or self._session.closed:
            # Create SSL context with proper certificate handling
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Create connector with SSL and connection pooling
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            # Timeout configuration - more generous for NASA APIs
            timeout = aiohttp.ClientTimeout(
                total=15,
                connect=5,
                sock_read=10
            )
            
            # Headers to identify as legitimate client
            headers = {
                'User-Agent': 'Mozilla/5.0 (Unfolded Circle NASA Integration) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=headers
            )
            
            _LOG.info("🌐 NASA HTTP session created with SSL verification")

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_api_key(self) -> str:
        """Get API key from configuration."""
        api_key = self._config.api_key
        return api_key if api_key and api_key != "" else "DEMO_KEY"

    def _is_cache_valid(self, source_id: str) -> bool:
        """Check if cached data is still valid."""
        if source_id not in self._data_cache:
            return False
        
        cached_time = self._data_cache[source_id].get("cached_at", 0)
        cache_interval = self.CACHE_INTERVALS.get(source_id, 3600)
        
        age = time.time() - cached_time
        return age < cache_interval

    def _cache_data(self, source_id: str, data: Dict[str, Any]) -> None:
        """Cache data with timestamp."""
        self._data_cache[source_id] = {
            **data,
            "cached_at": time.time()
        }

    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request with robust error handling and retries."""
        await self._ensure_session()
        
        # Merge additional headers with session headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        for attempt in range(2):  # 2 attempts
            try:
                _LOG.debug(f"Making request to {url} (attempt {attempt + 1})")
                
                async with self._session.get(url, params=params, headers=request_headers) as response:
                    _LOG.debug(f"Response: HTTP {response.status} from {url}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            # Some NASA APIs return JSON without proper content-type
                            text = await response.text()
                            if text.strip().startswith('{') or text.strip().startswith('['):
                                try:
                                    import json
                                    return json.loads(text)
                                except json.JSONDecodeError:
                                    _LOG.debug(f"Invalid JSON from {url}: {text[:100]}")
                                    return None
                            else:
                                _LOG.debug(f"Non-JSON response from {url}: {text[:100]}")
                                return None
                    elif response.status == 429:
                        _LOG.warning(f"Rate limited by {url}")
                        if attempt == 0:
                            await asyncio.sleep(2)
                            continue
                        return None
                    elif response.status in [403, 401]:
                        _LOG.warning(f"Authentication error {response.status} for {url}")
                        return None
                    else:
                        _LOG.debug(f"HTTP {response.status} for {url}")
                        if attempt == 0:
                            await asyncio.sleep(1)
                            continue
                        return None
                        
            except asyncio.TimeoutError:
                _LOG.debug(f"Timeout for {url} (attempt {attempt + 1})")
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                return None
            except aiohttp.ClientConnectorError as ex:
                _LOG.debug(f"Connection error for {url}: {ex}")
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                return None
            except aiohttp.ClientError as ex:
                _LOG.debug(f"Client error for {url}: {ex}")
                return None
            except Exception as ex:
                _LOG.error(f"Unexpected error for {url}: {ex}")
                return None
        
        return None

    async def fetch_apod_data(self) -> Tuple[str, str, str]:
        """Fetch APOD data - astronomy picture and description."""
        source_id = "apod"
        
        if self._is_cache_valid(source_id):
            cached = self._data_cache[source_id]
            return cached.get("image_url"), cached.get("title", ""), cached.get("description", "")

        _LOG.debug("Fetching APOD from NASA API...")
        params = {"api_key": self._get_api_key()}
        data = await self._make_request("https://api.nasa.gov/planetary/apod", params)
        
        if data and isinstance(data, dict):
            try:
                image_url = data.get("hdurl") or data.get("url")
                raw_title = data.get("title", "")
                explanation = data.get("explanation", "")
                date_str = data.get("date", "")
                
                if raw_title and explanation:
                    title = raw_title
                    
                    # Create short description for display
                    clean_explanation = explanation.replace("Explanation:", "").strip()
                    sentences = clean_explanation.split('. ')
                    if sentences:
                        first_sentence = sentences[0]
                        if len(first_sentence) <= 30:
                            description = first_sentence
                        else:
                            words = first_sentence.split()
                            short_desc = ""
                            for word in words:
                                if len(short_desc + " " + word) <= 28:
                                    short_desc += (" " + word if short_desc else word)
                                else:
                                    break
                            description = short_desc + "..." if short_desc else f"Image from {date_str}"
                    else:
                        description = f"NASA • {date_str}"
                    
                    _LOG.info("APOD data fetched: %s", raw_title[:30])
                    self._cache_data(source_id, {
                        "image_url": image_url or "",
                        "title": title,
                        "description": description
                    })
                    return image_url or "", title, description
                
            except Exception as ex:
                _LOG.debug("Error parsing APOD: %s", ex)
        
        _LOG.warning("APOD API failed")
        return "", "APOD service unavailable", "Check connection"

    async def fetch_epic_data(self) -> Tuple[str, str, str]:
        """Fetch EPIC data - Earth imagery metadata."""
        source_id = "epic"
        
        if self._is_cache_valid(source_id):
            cached = self._data_cache[source_id]
            return cached.get("image_url"), cached.get("title", ""), cached.get("description", "")

        _LOG.debug("Fetching EPIC from NASA API...")
        data = await self._make_request("https://epic.gsfc.nasa.gov/api/natural")
        
        if data and isinstance(data, list) and len(data) > 0:
            try:
                latest = data[0]
                date_str = latest.get("date", "")
                caption = latest.get("caption", "")
                coords = latest.get("centroid_coordinates", {})
                
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.split()[0])
                        readable_date = date_obj.strftime("%b %d")
                    except:
                        readable_date = date_str[:10]
                    
                    title = f"Earth {readable_date} • {caption}" if caption else f"Earth full-disc imagery from {readable_date}"
                    
                    if coords and "lat" in coords and "lon" in coords:
                        lat = coords["lat"]
                        lon = coords["lon"]
                        description = f"Center: {lat:.1f}°, {lon:.1f}°"
                    else:
                        description = f"DSCOVR • {readable_date}"
                    
                    _LOG.info("EPIC data fetched: %s", readable_date)
                    self._cache_data(source_id, {
                        "image_url": "",
                        "title": title,
                        "description": description
                    })
                    return "", title, description
                        
            except Exception as ex:
                _LOG.debug("Error parsing EPIC: %s", ex)
        
        _LOG.warning("EPIC API failed")
        return "", "Earth observation offline", "Service unavailable"

    async def fetch_iss_data(self) -> Tuple[str, str, str]:
        """Fetch ISS data - live position and crew information."""
        source_id = "iss"
        
        _LOG.debug("Fetching ISS data from API...")
        
        position_data = await self._make_request("http://api.open-notify.org/iss-now.json")
        people_data = await self._make_request("http://api.open-notify.org/astros.json")
        
        if position_data and position_data.get("message") == "success":
            try:
                iss_position = position_data.get("iss_position", {})
                latitude = float(iss_position.get("latitude", 0))
                longitude = float(iss_position.get("longitude", 0))
                timestamp = position_data.get("timestamp", 0)
                
                location_desc = self._get_location_description(latitude, longitude)
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M UTC")
                
                title = f"ISS {location_desc} • {latitude:.2f}°, {longitude:.2f}° • {time_str}"
                
                description = "27,600 km/h"
                
                if people_data and people_data.get("message") == "success":
                    people = people_data.get("people", [])
                    iss_crew = [p for p in people if p.get("craft") == "ISS"]
                    if iss_crew:
                        crew_count = len(iss_crew)
                        description = f"{crew_count} crew • 27,600 km/h"
                
                _LOG.info("ISS data fetched: %s", location_desc)
                
                self._cache_data(source_id, {
                    "title": title,
                    "description": description
                })
                
                return "", title, description
                
            except Exception as ex:
                _LOG.debug("Error parsing ISS: %s", ex)
        
        _LOG.warning("ISS API failed")
        return "", "ISS tracking offline", "Position unavailable"

    def _get_location_description(self, lat: float, lon: float) -> str:
        """Get descriptive location from coordinates."""
        if -30 < lat < 30:
            if -20 < lon < 60:
                return "over Africa"
            elif 60 < lon < 150:
                return "over Asia"
            elif 150 < lon or lon < -150:
                return "over Pacific"
            elif -150 < lon < -50:
                return "over Americas"
            else:
                return "over Atlantic"
        elif lat > 30:
            if -150 < lon < -50:
                return "over N.America"
            elif -50 < lon < 60:
                return "over Europe"
            else:
                return "over N.Asia"
        else:
            if -80 < lon < 20:
                return "over S.America"
            elif 20 < lon < 150:
                return "over S.Africa"
            else:
                return "over Oceania"

    async def fetch_neo_data(self) -> Tuple[str, str, str]:
        """Fetch NEO data - asteroid statistics."""
        source_id = "neo"
        
        if self._is_cache_valid(source_id):
            cached = self._data_cache[source_id]
            return "", cached.get("title", ""), cached.get("description", "")

        _LOG.debug("Fetching NEO data from NASA API...")
        params = {"api_key": self._get_api_key()}
        data = await self._make_request("https://api.nasa.gov/neo/rest/v1/feed/today", params)
        
        if data and isinstance(data, dict):
            try:
                neo_count = data.get("element_count", 0)
                date_keys = list(data.get("near_earth_objects", {}).keys())
                
                if date_keys and neo_count > 0:
                    today_objects = data["near_earth_objects"][date_keys[0]]
                    if today_objects:
                        speeds = []
                        distances = []
                        sizes = []
                        hazardous_count = 0
                        
                        for neo in today_objects:
                            try:
                                close_approach = neo.get("close_approach_data", [{}])[0]
                                velocity_kmh = float(close_approach.get("relative_velocity", {}).get("kilometers_per_hour", 0))
                                if velocity_kmh > 0:
                                    speeds.append(velocity_kmh)
                                
                                distance_km = float(close_approach.get("miss_distance", {}).get("kilometers", 0))
                                if distance_km > 0:
                                    distances.append(distance_km)
                                
                                diameter = neo.get("estimated_diameter", {}).get("kilometers", {})
                                max_diameter = diameter.get("estimated_diameter_max", 0)
                                if max_diameter > 0:
                                    sizes.append(max_diameter)
                                
                                if neo.get("is_potentially_hazardous_asteroid", False):
                                    hazardous_count += 1
                                    
                            except (ValueError, KeyError, IndexError):
                                continue
                        
                        stats_parts = [f"Today: {neo_count} asteroids"]
                        
                        if speeds:
                            fastest = max(speeds)
                            slowest = min(speeds)
                            stats_parts.append(f"Speed: {slowest:,.0f}-{fastest:,.0f} km/h")
                        
                        if distances:
                            closest = min(distances)
                            if closest > 1000000:
                                stats_parts.append(f"Closest: {closest/1000000:.2f}M km")
                            else:
                                stats_parts.append(f"Closest: {closest:,.0f} km")
                        
                        title = " • ".join(stats_parts)
                        
                        if hazardous_count > 0:
                            description = f"{hazardous_count} hazardous"
                        elif sizes:
                            largest = max(sizes)
                            if largest >= 1:
                                description = f"Largest: {largest:.1f} km"
                            else:
                                description = f"Largest: {largest*1000:.0f} m"
                        else:
                            description = f"{neo_count} tracked today"
                        
                        _LOG.info("NEO data fetched: %d objects", neo_count)
                        
                        self._cache_data(source_id, {
                            "title": title,
                            "description": description
                        })
                        
                        return "", title, description
                        
            except Exception as ex:
                _LOG.debug("Error parsing NEO: %s", ex)
        
        _LOG.warning("NEO API failed")
        return "", "Asteroid tracking offline", "Service unavailable"

    async def fetch_mars_rover_data(self) -> Tuple[str, str, str]:
        """Fetch Mars rover data - mission details."""
        source_id = "insight"
        
        if self._is_cache_valid(source_id):
            cached = self._data_cache[source_id]
            return "", cached.get("title", ""), cached.get("description", "")

        rovers_config = [
            {"name": "curiosity", "max_sol": 4000},
            {"name": "opportunity", "max_sol": 5111},
            {"name": "spirit", "max_sol": 2210}
        ]
        
        rover_config = random.choice(rovers_config)
        rover_name = rover_config["name"]
        random_sol = random.randint(100, min(1500, rover_config["max_sol"]))
        
        _LOG.debug("Fetching Mars %s Sol %d data...", rover_name, random_sol)
        params = {"api_key": self._get_api_key(), "sol": random_sol, "page": 1}
        data = await self._make_request(f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover_name}/photos", params)
        
        if data and "photos" in data:
            try:
                photos = data["photos"]
                if photos:
                    photo_count = len(photos)
                    
                    cameras = list(set([p.get("camera", {}).get("name", "UNK") for p in photos]))
                    camera_summary = f"{len(cameras)} cameras" if len(cameras) > 1 else cameras[0]
                    
                    earth_date = photos[0].get("earth_date", "")
                    if earth_date:
                        try:
                            date_obj = datetime.fromisoformat(earth_date)
                            readable_date = date_obj.strftime("%b %d, %Y")
                        except:
                            readable_date = earth_date
                    else:
                        readable_date = "Date unknown"
                    
                    title = f"{rover_name.title()} Sol {random_sol} • {camera_summary} • {photo_count} images • {readable_date}"
                    
                    if photo_count > 50:
                        description = f"Active Sol • {photo_count} pics"
                    else:
                        description = f"Sol {random_sol} • {photo_count} images"
                    
                    _LOG.info("Mars data fetched: %s Sol %d, %d images", rover_name.title(), random_sol, photo_count)
                    
                    self._cache_data(source_id, {
                        "title": title,
                        "description": description
                    })
                    
                    return "", title, description
                        
            except Exception as ex:
                _LOG.debug("Error parsing Mars: %s", ex)
        
        _LOG.warning("Mars API failed")
        return "", "Mars mission data offline", "Service unavailable"

    async def fetch_donki_data(self) -> Tuple[str, str, str]:
        """Fetch space weather data - solar events."""
        source_id = "donki"
        
        if self._is_cache_valid(source_id):
            cached = self._data_cache[source_id]
            return "", cached.get("title", ""), cached.get("description", "")

        _LOG.debug("Fetching space weather from DONKI...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        params = {
            "api_key": self._get_api_key(),
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        data = await self._make_request("https://api.nasa.gov/DONKI/notifications", params)
        
        if data and isinstance(data, list):
            try:
                if len(data) > 0:
                    event_types = {}
                    latest_event = None
                    latest_time = None
                    
                    for event in data:
                        try:
                            event_type = event.get("messageType", "")
                            event_time_str = event.get("messageIssueTime", "")
                            
                            if event_type:
                                event_types[event_type] = event_types.get(event_type, 0) + 1
                                
                                if event_time_str and (latest_time is None or event_time_str > latest_time):
                                    latest_time = event_time_str
                                    latest_event = event
                                    
                        except Exception:
                            continue
                    
                    if latest_event and event_types:
                        try:
                            event_datetime = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                            days_ago = (datetime.now(event_datetime.tzinfo) - event_datetime).days
                            time_desc = f"{days_ago}d ago" if days_ago > 0 else "Today"
                        except:
                            time_desc = "Recent"
                        
                        latest_type = latest_event.get("messageType", "Event")
                        
                        event_summary = []
                        for etype, count in sorted(event_types.items()):
                            if count > 1:
                                event_summary.append(f"{count} {etype}s")
                            else:
                                event_summary.append(f"{count} {etype}")
                        
                        title = f"Solar activity: {', '.join(event_summary[:3])} (7 days)"
                        description = f"Latest: {latest_type} {time_desc}"
                        
                        _LOG.info("DONKI data fetched: %d events", len(data))
                        
                        self._cache_data(source_id, {
                            "title": title,
                            "description": description
                        })
                        
                        return "", title, description
                else:
                    title = "Solar activity: Quiet period (7 days)"
                    description = "No major events"
                    
                    self._cache_data(source_id, {
                        "title": title,
                        "description": description
                    })
                    
                    return "", title, description
                        
            except Exception as ex:
                _LOG.debug("Error parsing DONKI: %s", ex)
        
        _LOG.warning("DONKI API failed")
        return "", "Space weather offline", "Service unavailable"

    async def fetch_source_data(self, source_id: str) -> Tuple[str, str, str]:
        """
        Fetch live data for source.
        Returns: (image_url, title, description)
        """
        if source_id not in self._request_locks:
            self._request_locks[source_id] = asyncio.Lock()
        
        if self._request_locks[source_id].locked():
            _LOG.debug("Source %s request in progress, using cache", source_id)
            if source_id in self._data_cache:
                cached = self._data_cache[source_id]
                image_url = cached.get("image_url", "") if source_id == "apod" else ""
                return image_url, cached.get("title", ""), cached.get("description", "")
            else:
                return "", "Fetching live data...", "Connecting to NASA..."
        
        async with self._request_locks[source_id]:
            try:
                _LOG.info("Fetching live data: %s", source_id.upper())
                
                fetch_methods = {
                    "apod": self.fetch_apod_data,
                    "epic": self.fetch_epic_data,
                    "iss": self.fetch_iss_data,
                    "neo": self.fetch_neo_data,
                    "insight": self.fetch_mars_rover_data,
                    "donki": self.fetch_donki_data
                }
                
                method = fetch_methods.get(source_id)
                if method:
                    result = await asyncio.wait_for(method(), timeout=10)
                    image_url, title, description = result
                    
                    _LOG.info("Live data complete: %s", source_id.upper())
                    return image_url, title, description
                
                _LOG.warning("Unknown source: %s", source_id)
                return "", "Unknown data source", "Invalid request"
                
            except asyncio.TimeoutError:
                _LOG.warning("Live data timeout: %s", source_id)
                return "", f"{source_id.upper()} service timeout", "Connection slow"
            
            except Exception as ex:
                _LOG.error("Live data error %s: %s", source_id, str(ex)[:50])
                return "", f"{source_id.upper()} service error", "Check connection"

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all data sources."""
        stats = {}
        for source_id in self.CACHE_INTERVALS.keys():
            if source_id in self._data_cache:
                age = time.time() - self._data_cache[source_id].get("cached_at", 0)
                valid = self._is_cache_valid(source_id)
                stats[source_id] = {
                    "cached": True,
                    "age_seconds": int(age),
                    "valid": valid,
                    "last_title": self._data_cache[source_id].get("title", "")[:30]
                }
            else:
                stats[source_id] = {"cached": False}
        
        return stats