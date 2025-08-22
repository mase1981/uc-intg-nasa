# NASA Mission Control Integration for Unfolded Circle

Access live NASA data feeds on your Unfolded Circle Remote 2/3 including Astronomy Picture of the Day, ISS location tracking, Earth imagery, and space weather updates.

![NASA Mission Control](https://img.shields.io/badge/NASA-Mission%20Control-blue)
![Version](https://img.shields.io/badge/version-0.1.0-green)
![License](https://img.shields.io/badge/license-MPL--2.0-orange)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)

## Features

This integration creates a **Media Player** entity on your remote that provides access to **6 different NASA data sources** with beautiful space imagery and live data updates.

### 🌌 Data Sources

1. **Daily Universe** - Astronomy Picture of the Day (APOD)
   - High-resolution space imagery and astronomical objects
   - Professional explanations written by NASA astronomers
   - Updated daily with stunning cosmic photography

2. **Earth Live** - Real-time Earth imagery from DSCOVR satellite
   - Full-disc Earth images from 1 million miles away  
   - Updated every 2 hours by the EPIC camera
   - Shows Earth's rotation and weather patterns

3. **ISS Tracker** - International Space Station live location
   - Real-time ISS coordinates and regional position
   - Current crew count and orbital velocity (27,600 km/h)
   - Updates every 2 minutes as ISS orbits Earth

4. **NEO Watch** - Near Earth Objects monitoring
   - Daily asteroid count with speed and distance data
   - Potentially hazardous object identification
   - Size estimates for approaching asteroids

5. **Mars Archive** - Mars mission data from rovers
   - Historical data from Curiosity, Opportunity, and Spirit
   - Sol information, camera details, and image counts
   - Mission status and operational details

6. **Space Weather** - Solar events and space weather monitoring
   - Recent solar flare and geomagnetic storm alerts
   - 7-day space weather event summaries
   - Critical updates for satellite operations

### 🎨 Visual Experience

- **26 Optimized Space Images**: Beautiful static images categorized by theme (Earth, Space, Planets, Nebulae, Galaxies)
- **Smart Display**: Line 1 scrollable for detailed data, Line 2 static for key metrics
- **Instant Source Switching**: Change between NASA feeds with no delays
- **Contextual Icons**: Images automatically match the data source theme

## Prerequisites

- Unfolded Circle Remote 2 or Remote 3
- Internet connection for NASA API access
- **Optional**: Free NASA API key for higher rate limits

## Installation

### Option 1: `tar.gz` File (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-nasa/releases) page.
2. Download the latest `uc-intg-nasa-<version>-aarch64.tar.gz` file.
3. Open your Unfolded Circle remote's web configurator.
4. Go to **Settings** → **Integrations**.
5. Click **"UPLOAD"** and select the downloaded `.tar.gz` file.

### Option 2: Docker (Advanced Users)
For users running Docker environments:

**Docker Compose:**
```yaml
version: '3.8'
services:
  nasa-integration:
    image: mase1981/uc-intg-nasa:latest
    container_name: nasa-mission-control
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config:/app/config
```

**Docker Run:**
```bash
docker run -d --restart=unless-stopped --net=host \
  -v /path/to/config:/app/config \
  --name nasa-mission-control \
  mase1981/uc-intg-nasa:latest
```

## Configuration

### Setup Process

1. After installation, go to **Settings** → **Integrations** and click **+ ADD INTEGRATION**.
2. Select **NASA Mission Control** from the discovered integrations.
3. Follow the setup wizard:
   - **NASA API Key**: Enter your free API key or leave empty for DEMO_KEY
   - **Refresh Interval**: Set data update frequency (5-60 minutes, default: 10)
4. The integration will test your NASA API connection
5. Once complete, the **NASA Mission Control** media player will be available

### Getting a NASA API Key (Recommended)

While the integration works with NASA's `DEMO_KEY`, a personal API key provides much higher rate limits:

1. Visit [api.nasa.gov](https://api.nasa.gov)
2. Click **"Generate API Key"**
3. Fill out the simple form (takes 2 minutes)
4. Use your key during setup for best performance

**Rate Limits:**
- `DEMO_KEY`: 30 requests/hour, 50/day
- **Personal key**: 1,000 requests/hour

## Usage

### Media Player Controls

- **Power On/Off**: Start/stop NASA data updates
- **Source Selection**: Choose from 6 NASA data feeds using the source dropdown
- **Next/Previous**: Navigate between sources with remote buttons
- **Display**: Shows space imagery + 2 lines of live NASA data

### Example Display

```
🌌 Daily Universe (APOD)
━━━━━━━━━━━━━━━━━━━━━━━━
Line 1: "The Horsehead Nebula in Orion constellation..."
Line 2: "Dark nebula • 1,500 light years"
Image: [Stunning space photograph from NASA]
```

### Data Update Behavior

- **Smart Caching**: Different refresh intervals per source (2 minutes to 8 hours)
- **Instant Switching**: Source changes are immediate with cached data
- **Background Updates**: Fresh data loads in background while UI stays responsive
- **Graceful Fallbacks**: Shows meaningful messages when APIs are temporarily down

## Technical Details

### Architecture
```
Remote 2/3 ↔ Integration API ↔ NASA Client ↔ NASA APIs
                    ↓
             Media Player Entity
                    ↓
              6 Live Data Sources
```

### NASA APIs Used

| Source | API Endpoint | Cache Interval | Data Type |
|--------|-------------|----------------|-----------|
| APOD | `api.nasa.gov/planetary/apod` | 6 hours | Images + Descriptions |
| EPIC | `epic.gsfc.nasa.gov/api/natural` | 2 hours | Earth Image Metadata |
| ISS | `api.open-notify.org/iss-now.json` | 2 minutes | Real-time Position |
| NEO | `api.nasa.gov/neo/rest/v1/feed` | 4 hours | Asteroid Statistics |
| Mars | `api.nasa.gov/mars-photos/api/v1/rovers` | 8 hours | Mission Archives |
| DONKI | `api.nasa.gov/DONKI/notifications` | 3 hours | Space Weather Events |

### Performance Features

- **Static Icon Library**: 26 optimized space images (400x300, <100KB each)
- **Smart Caching**: Prevents unnecessary API calls with intelligent intervals
- **Async Processing**: Non-blocking data fetches with instant UI responsiveness
- **Error Resilience**: Robust error handling with meaningful user feedback

## Troubleshooting

### Common Issues

1. **"API Connection Failed"**
   - Verify internet connectivity
   - Check if your API key is valid at [api.nasa.gov](https://api.nasa.gov)
   - Try leaving API key empty to use DEMO_KEY

2. **"Data Not Updating"**
   - Check if refresh interval is appropriate (not too short)
   - Verify NASA APIs are operational
   - Try switching to a different source

3. **"Integration Not Found"**
   - Ensure Remote and integration are on same network
   - Check firewall settings (port 9090)
   - Wait 30 seconds for mDNS discovery

### Debug Information

Enable detailed logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

Check NASA API status:
- [NASA API Status](https://api.nasa.gov)
- [EPIC Service Status](https://epic.gsfc.nasa.gov)
- [ISS API Status](http://open-notify.org)

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-nasa.git
   cd uc-intg-nasa
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run integration:**
   ```bash
   python main.py
   ```

3. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Integration available at `localhost:9090`

### Project Structure

```
uc-intg-nasa/
├── uc_intg_nasa/           # Main package
│   ├── icons/              # 26 optimized space images
│   ├── __init__.py         # Package info
│   ├── client.py           # NASA API client
│   ├── config.py           # Configuration management  
│   ├── driver.py           # Integration driver
│   ├── media_player.py     # Media player entity
│   └── setup.py            # Setup flow handler
├── .github/workflows/      # Build automation
├── main.py                 # Entry point
├── driver.json             # Integration metadata
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## Credits

- **Developer**: Meir Miyara
- **NASA APIs**: National Aeronautics and Space Administration
- **Unfolded Circle**: Remote 2/3 integration platform
- **Static Images**: NASA's public domain space photography

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-nasa/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
---
**Made with ❤️ for the Unfolded Circle Community**

**Bring the universe to your remote control! 🚀🌌**

**Author**: Meir Miyara  
