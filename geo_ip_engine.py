"""
================================================================================
  🌍 CyberCalling IP Geolocation, Proxy Detection & MapTiler Mapping Engine
================================================================================
  Features:
  - 📍 Real-Time IP Geolocation (City, State, Country, Postal Code, Lat/Lon)
  - 🛡️ Advanced Threat & Proxy Detection (VPN, Tor, Proxy, Hosting/Datacenter)
  - 🗺️ MapTiler High-Resolution Satellite & Street Map Tile Generation
  - ⚡ Thread-safe Caching Layer to respect ip-api.com rate limits (45 req/min)
================================================================================
"""

import os
import time
import threading
import requests
from dotenv import load_dotenv
from proxy_manager import proxy_manager

load_dotenv(override=True)

MAPTILER_API_KEY = os.getenv("MAPTILER_API_KEY", "rI7D4azokc5aP5YLg0SG").strip()
IP_API_ENDPOINT = "http://ip-api.com/json/{query}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query"

_GEO_CACHE = {}
_GEO_CACHE_LOCK = threading.Lock()
CACHE_TTL_SECONDS = 3600  # 1 Hour Cache


def iso_to_flag_emoji(country_code: str) -> str:
    """Convert 2-letter country code (e.g. 'IN', 'US') to emoji flag 🇮🇳, 🇺🇸."""
    if not country_code or len(country_code) != 2:
        return "🌐"
    try:
        return "".join(chr(127397 + ord(c.upper())) for c in country_code)
    except Exception:
        return "🌐"


def is_private_ip(ip: str) -> bool:
    """Check if an IP is private/local."""
    if not ip:
        return True
    ip = ip.strip()
    if ip in ["127.0.0.1", "localhost", "::1", "0.0.0.0"]:
        return True
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16."):
        return True
    return False


def get_maptiler_static_map_url(lat: float, lon: float, zoom: int = 12, width: int = 600, height: int = 300) -> str:
    """Generate MapTiler High-Res Static Map image URL with location pin."""
    if not lat or not lon or not MAPTILER_API_KEY:
        return ""
    return (
        f"https://api.maptiler.com/maps/streets-v2/static/{lon},{lat},{zoom}/{width}x{height}@2x.png"
        f"?key={MAPTILER_API_KEY}&markers={lon},{lat},red"
    )


def lookup_ip_geo(ip: str) -> dict:
    """
    Lookup full geolocation, ISP, ASN, threat/proxy flags, and MapTiler tiles for an IP.
    """
    clean_ip = str(ip or "").strip()
    if not clean_ip:
        clean_ip = "127.0.0.1"

    # 1. Check local cache
    with _GEO_CACHE_LOCK:
        if clean_ip in _GEO_CACHE:
            cached_data, cached_time = _GEO_CACHE[clean_ip]
            if time.time() - cached_time < CACHE_TTL_SECONDS:
                return cached_data

    # 2. Handle private/loopback
    if is_private_ip(clean_ip):
        res = {
            "status": "success",
            "ip": clean_ip,
            "country": "Local Network",
            "country_code": "LOC",
            "flag": "🏠",
            "region": "Internal",
            "city": "Localhost / Server",
            "zip": "000000",
            "lat": 28.6139,
            "lon": 77.2090,
            "timezone": "Asia/Kolkata",
            "isp": "Local Development Loopback",
            "org": "Internal Gateway",
            "is_mobile": False,
            "is_proxy": False,
            "is_hosting": False,
            "map_url": get_maptiler_static_map_url(28.6139, 77.2090),
            "google_maps_url": "https://www.google.com/maps?q=28.6139,77.2090"
        }
        with _GEO_CACHE_LOCK:
            _GEO_CACHE[clean_ip] = (res, time.time())
        return res

    # 3. Query ip-api.com
    try:
        url = IP_API_ENDPOINT.format(query=clean_ip)
        s = proxy_manager.get_session()
        resp = s.get(url, timeout=6)
        data = resp.json()

        if data.get("status") == "success":
            lat = float(data.get("lat") or 0.0)
            lon = float(data.get("lon") or 0.0)
            cc = data.get("countryCode", "UN")
            flag = iso_to_flag_emoji(cc)

            res = {
                "status": "success",
                "ip": clean_ip,
                "country": data.get("country", "Unknown"),
                "country_code": cc,
                "flag": flag,
                "region": data.get("regionName", ""),
                "city": data.get("city", "Unknown City"),
                "zip": data.get("zip", ""),
                "lat": lat,
                "lon": lon,
                "timezone": data.get("timezone", "UTC"),
                "isp": data.get("isp", "Unknown ISP"),
                "org": data.get("org", ""),
                "as": data.get("as", ""),
                "is_mobile": bool(data.get("mobile")),
                "is_proxy": bool(data.get("proxy")),
                "is_hosting": bool(data.get("hosting")),
                "map_url": get_maptiler_static_map_url(lat, lon),
                "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}"
            }
        else:
            res = {
                "status": "fail",
                "ip": clean_ip,
                "country": "Unknown",
                "flag": "🌐",
                "city": "Unknown",
                "region": "",
                "isp": "Unknown",
                "is_proxy": False,
                "map_url": "",
                "google_maps_url": ""
            }
    except Exception as e:
        print(f"[GeoIP Lookup Error for {clean_ip}]:", e)
        res = {
            "status": "error",
            "ip": clean_ip,
            "country": "Unknown",
            "flag": "🌐",
            "city": "Lookup Timeout",
            "region": "",
            "isp": "Unknown",
            "is_proxy": False,
            "map_url": "",
            "google_maps_url": ""
        }

    with _GEO_CACHE_LOCK:
        _GEO_CACHE[clean_ip] = (res, time.time())

    return res


def format_geo_card_markdown(geo: dict) -> str:
    """Format rich Markdown card for Telegram alerts."""
    flag = geo.get("flag", "🌐")
    country = geo.get("country", "Unknown")
    city = geo.get("city", "Unknown")
    region = geo.get("region", "")
    loc_str = f"{city}, {region} ({country})" if region else f"{city}, {country}"

    proxy_badge = "🛡️ Yes (VPN/Proxy/Tor)" if geo.get("is_proxy") else "🟢 Clean (Residential/Mobile)"
    if geo.get("is_hosting"):
        proxy_badge += " | Datacenter"

    lines = [
        f"• *Real Client IP:* `{geo.get('ip')}`",
        f"• *Location:* {flag} `{loc_str}`",
        f"• *ISP / Organization:* `{geo.get('isp')}`",
        f"• *Timezone:* `{geo.get('timezone', 'UTC')}`",
        f"• *Network Security:* `{proxy_badge}`"
    ]
    if geo.get("google_maps_url"):
        lines.append(f"• *Map Coordinates:* [📍 View on Map]({geo.get('google_maps_url')})")

    return "\n".join(lines)
