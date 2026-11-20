import json
import math
import re
import urllib.parse
import urllib.request

_GEO_CACHE = {}

_KNOWN_PLACES = {
    "mabula": ("Mabula Game Lodge, R516, Bela-Bela, Limpopo, South Africa", -24.7436, 27.9433),
    "mabula game lodge": ("Mabula Game Lodge, R516, Bela-Bela, Limpopo, South Africa", -24.7436, 27.9433),
    "mabula bela bela": ("Mabula Game Lodge, R516, Bela-Bela, Limpopo, South Africa", -24.7436, 27.9433),
    "mabula bela-bela": ("Mabula Game Lodge, R516, Bela-Bela, Limpopo, South Africa", -24.7436, 27.9433),
    "bela bela": ("Bela-Bela (Warmbaths), Limpopo, South Africa", -24.8833, 28.2936),
    "bela-bela": ("Bela-Bela (Warmbaths), Limpopo, South Africa", -24.8833, 28.2936),
}

def _http_json(url, timeout=2.5):
    if url in _GEO_CACHE:
        return _GEO_CACHE[url]
    req = urllib.request.Request(url, headers={"User-Agent": "ACEsi-Local/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
        _GEO_CACHE[url] = data
        return data

def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
def get_origin(data):
    try:
        if data.get("lat") is not None and data.get("lon") is not None:
            lat, lon = float(data["lat"]), float(data["lon"])
            label = data.get("location_label") or "Browser Geolocation"
            try:
                rev = _http_json(f"https://nominatim.openstreetmap.org/reverse?lat={lat:.5f}&lon={lon:.5f}&format=json&zoom=14", 2.0)
                addr = rev.get("address") or {}
                sub = addr.get("suburb") or addr.get("neighbourhood") or addr.get("town") or addr.get("city")
                city = addr.get("city") or addr.get("municipality") or addr.get("state")
                parts = [p for p in dict.fromkeys([sub, city, addr.get("country")]) if p]
                if parts:
                    label = ", ".join(parts)
            except Exception:
                pass
            return {"lat": lat, "lon": lon, "label": label, "source": "Browser GPS/Wi-Fi"}
    except Exception:
        pass
    try:
        info = _http_json("https://ipinfo.io/json", 2.0)
        if "," in info.get("loc", ""):
            lat_s, lon_s = info["loc"].split(",", 1)
            label = ", ".join([x for x in (info.get("city"), info.get("region"), info.get("country")) if x]) or "IP Location"
            return {"lat": float(lat_s), "lon": float(lon_s), "label": label, "source": "IP Geolocation"}
    except Exception:
        pass
    return {"lat": -26.2785, "lon": 28.0536, "label": "Glenvista, Johannesburg South, South Africa", "source": "Default Fallback"}

def handle_location_query(user_message, data):
    low = user_message.lower()
    if not any(k in low for k in ("my location", "where am i", "how far", "distance", "drive time", "travel time", "mabula", "bela-bela", "bela bela")):
        return None
    origin = get_origin(data)
    dest = next((k for k in sorted(_KNOWN_PLACES, key=len, reverse=True) if k in low), None)
    if not dest:
        m = re.search(r"(?:how far(?:\s+is|\s+are)?|distance\s+(?:to|from\s+me\s+to)|drive\s+(?:to|from\s+me\s+to)|travel\s+time\s+(?:to|from\s+me\s+to))\s+(.+?)(?:\s+(?:from\s+me|from\s+here|by\s+car|driving)\b|[?.!]|$)", user_message, re.I)
        if m:
            dest = re.sub(r"\bfrom\s+me\b", "", m.group(1), flags=re.I).strip(" ,.!?")
    if not dest:
        return f"Your current location is **{origin['label']}** ({origin['lat']:.4f}, {origin['lon']:.4f}) via {origin['source']}."
    if dest.lower() in _KNOWN_PLACES:
        d_name, d_lat, d_lon = _KNOWN_PLACES[dest.lower()]
    else:
        geo = _http_json(f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(dest)}&countrycodes=za&format=json&limit=1", 2.5)
        if not geo:
            return f"Your current location is **{origin['label']}** ({origin['lat']:.4f}, {origin['lon']:.4f}), but I could not find '{dest}'."
        d_name, d_lat, d_lon = geo[0].get("display_name") or dest, float(geo[0]["lat"]), float(geo[0]["lon"])
    straight_km = round(_haversine_km(origin["lat"], origin["lon"], d_lat, d_lon), 1)
    road_km, mins = None, None
    try:
        rt = _http_json(f"https://router.project-osrm.org/route/v1/driving/{origin['lon']},{origin['lat']};{d_lon},{d_lat}?overview=false", 2.5)
        if rt.get("routes"):
            road_km = round(float(rt["routes"][0]["distance"]) / 1000.0, 1)
            mins = int(round(float(rt["routes"][0]["duration"]) / 60.0))
    except Exception:
        pass
    if road_km is None:
        road_km = round(straight_km * 1.24, 1)
        mins = int(round((road_km / 95.0) * 60.0))
    h, m = divmod(mins, 60)
    eta = f"{h}h {m}m" if h else f"{m}m"
    return f"Your current location is **{origin['label']}** ({origin['lat']:.4f}, {origin['lon']:.4f}) via {origin['source']}.\n\n**Destination:** {d_name}\n• **Driving distance:** {road_km} km ({straight_km} km straight-line)\n• **Estimated drive time:** {eta}"
