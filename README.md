# NASA Mission Control Integration for Unfolded Circle Remote 2/3

Access live NASA data feeds including Astronomy Picture of the Day, ISS location, Earth imagery, and space weather directly from your Unfolded Circle Remote 2 or Remote 3.

![NASA Mission Control](https://img.shields.io/badge/NASA-Mission%20Control-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-nasa?style=flat-square)](https://github.com/mase1981/uc-intg-nasa/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-nasa?style=flat-square)](https://github.com/mase1981/uc-intg-nasa/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://community.unfoldedcircle.com/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-nasa/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

---

## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️

---

## Features

This integration creates a media player entity on your remote that provides access to **6 different NASA data sources** with beautiful space imagery and live data updates through NASA's official APIs.

### 🌌 **Daily Universe** - Astronomy Picture of the Day (APOD)
- High-resolution space imagery and astronomical objects
- Professional explanations written by NASA astronomers
- Updated daily with stunning cosmic photography
- Featured objects: nebulae, galaxies, planets, stars

### 🌍 **Earth Live** - Real-time Earth Imagery
- Full-disc Earth images from DSCOVR satellite (1 million miles away)
- Updated every 2 hours by the EPIC camera
- Shows Earth's rotation and weather patterns
- Natural color Earth photography

### 🛰️ **ISS Tracker** - International Space Station
- Real-time ISS coordinates and regional position
- Current crew count and orbital velocity (27,600 km/h)
- Updates every 2 minutes as ISS orbits Earth
- Live latitude/longitude tracking

### ☄️ **NEO Watch** - Near Earth Objects Monitoring
- Daily asteroid count with speed and distance data
- Potentially hazardous object identification
- Size estimates for approaching asteroids
- Close approach tracking

### 🔴 **Mars Archive** - Mars Mission Data
- Historical data from Curiosity, Opportunity, and Spirit rovers
- Sol information, camera details, and image counts
- Mission status and operational details
- Mars surface photography

### ⚡ **Space Weather** - Solar Events Monitoring
- Recent solar flare and geomagnetic storm alerts
- 7-day space weather event summaries
- Critical updates for satellite operations
- Space weather impact forecasts

### 🎨 **Visual Experience**
- **26 Optimized Space Images**: Beautiful static images categorized by theme (Earth, Space, Planets, Nebulae, Galaxies)
- **Smart Display**: Scrollable detailed data with static key metrics
- **Instant Source Switching**: Change between NASA feeds with no delays
- **Contextual Icons**: Images automatically match the data source theme

### 📊 **Smart Features**
- **Smart Caching**: Different refresh intervals per source (2 minutes to 8 hours)
- **Background Updates**: Fresh data loads in background while UI stays responsive
- **Graceful Fallbacks**: Meaningful messages when APIs are temporarily unavailable
- **Rate Limit Management**: Intelligent API call scheduling

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-nasa/releases) page
2. Download the latest `uc-intg-uc_intg_nasa-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration can be run as a standalone Docker container:

**Docker Compose:**
```yaml
services:
  uc-intg-nasa:
    image: ghcr.io/mase1981/uc-intg-nasa:latest
    container_name: uc-intg-nasa
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-nasa --restart unless-stopped --network host -v nasa-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-nasa:latest
```

## Configuration

### Step 1: Get NASA API Key (Optional but Recommended)

While the integration works with NASA's `DEMO_KEY`, a personal API key provides much higher rate limits:

1. Visit [api.nasa.gov](https://api.nasa.gov)
2. Click **"Generate API Key"**
3. Fill out the simple form
4. Use your key during setup for best performance

**Rate Limits:**
- `DEMO_KEY`: 30 requests/hour, 50/day
- **Personal key**: 1,000 requests/hour

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The NASA Mission Control integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **NASA API Key**: Enter your free API key or leave empty for DEMO_KEY
- **Refresh Interval**: Set data update frequency (5-60 minutes, default: 10)
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies NASA API connectivity
- API authentication confirmed
- Setup fails if internet connection unavailable

4. Integration will create entity:
   - **Media Player**: `media_player.nasa_mission_control` for accessing NASA data sources

## Using the Integration

### Media Player Entity

The media player entity provides comprehensive NASA data access:

- **Power Control**: Start/stop NASA data updates
- **Source Selection**: Choose from 6 NASA data feeds using source dropdown
- **Next/Previous**: Navigate between sources with remote buttons
- **Display**: Shows space imagery + 2 lines of live NASA data

### Data Sources

| Source | Description | Update Frequency |
|--------|-------------|------------------|
| Daily Universe | APOD with high-resolution space imagery | 6 hours |
| Earth Live | Real-time Earth images from DSCOVR | 2 hours |
| ISS Tracker | Live International Space Station position | 2 minutes |
| NEO Watch | Near Earth Objects monitoring | 4 hours |
| Mars Archive | Mars rover mission data | 8 hours |
| Space Weather | Solar events and space weather | 3 hours |

### NASA APIs Used

- **APOD**: `api.nasa.gov/planetary/apod` - Images and descriptions
- **EPIC**: `epic.gsfc.nasa.gov/api/natural` - Earth image metadata
- **ISS**: `api.open-notify.org/iss-now.json` - Real-time position
- **NEO**: `api.nasa.gov/neo/rest/v1/feed` - Asteroid statistics
- **Mars**: `api.nasa.gov/mars-photos/api/v1/rovers` - Mission archives
- **DONKI**: `api.nasa.gov/DONKI/notifications` - Space weather events

## Credits

- **Developer**: Meir Miyara
- **NASA APIs**: National Aeronautics and Space Administration
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Images**: NASA's public domain space photography
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-nasa/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **NASA API**: [NASA API Portal](https://api.nasa.gov)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara

**Bring the universe to your remote control! 🚀🌌**
