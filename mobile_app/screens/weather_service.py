import time
import httpx

class WeatherService:
    def __init__(self):
        self.cache = {}
        self.ttl = 600
        self.client = httpx.AsyncClient(timeout=8)

    def _is_valid(self, vehicle_id):
        entry = self.cache.get(vehicle_id)
        if not entry:
            return False
        return (time.time() - entry["time"]) < self.ttl

    async def get_weather(self, vehicle_id, lat, lng, helpers):
        """
        helpers = (get_city, weather_desc, maybe_visit)
        """
        if self._is_valid(vehicle_id):
            return self.cache[vehicle_id]["data"]

        get_city, weather_desc, maybe_visit = helpers

        city = get_city(lat, lng)

        try:
            r = await self.client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "current": "temperature_2m,weather_code",
                    "forecast_days": 1,
                },
            )
            r.raise_for_status()
            data = r.json()

            temp = data["current"]["temperature_2m"]
            unit = data["current_units"]["temperature_2m"]
            code = data["current"]["weather_code"]

            result = {
                "text": f"{city}: {temp}{unit}, {weather_desc(code)} — {maybe_visit(code)}",
                "bg": "#fff3e0" if code >= 61 else "#f0f4ff"
            }

            self.cache[vehicle_id] = {
                "data": result,
                "time": time.time()
            }

            return result

        except:
            return {
                "text": f"Weather unavailable for {city}",
                "bg": "#f5f5f5"
            }

weather_service = WeatherService()