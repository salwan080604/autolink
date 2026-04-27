import flet as ft
import threading
import requests
import math
from shared import api, APP_STATE, nav, section
from shared import PRIMARY, ACCENT, BG, TEXT_LIGHT, TEXT_DARK, SUCCESS, ERROR

def _haversine(lat1, lon1, lat2, lon2):
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

async def _get_my_location_geo(geo):
    """Returns (lat, lng, city) using device GPS. Falls back to None on error."""
    try:
        if not geo:
            return None, None, None
            
        pos = await geo.get_current_position()

        if pos:
            lat = float(pos.latitude)
            lng = float(pos.longitude)
        
        # We still use Nominatim to get the city name from the GPS coords
            city = _get_city(lat, lng)
        return lat, lng, city
    except Exception as e:
        print("GPS error:", e)
        return None, None, None

def _weather_desc(code):
    if code == 0:                return "clear skies ☀️"
    elif code in (1, 2):         return "partly cloudy 🌤️"
    elif code == 3:              return "overcast ☁️"
    elif code in range(45, 50):  return "foggy 🌫️"
    elif code in range(51, 58):  return "drizzling 🌦️"
    elif code in range(61, 68):  return "raining 🌧️"
    elif code in range(71, 78):  return "snowing ❄️"
    elif code in range(80, 83):  return "rain showers 🌦️"
    elif code in range(95, 100): return "thunderstorming ⛈️"
    return "mixed conditions 🌡️"

def _maybe_visit(code):
    if code == 0:                return "great day to visit!"
    elif code in (1, 2):         return "not a bad day to visit."
    elif code == 3:              return "maybe bring a jacket."
    elif code in range(45, 50):  return "drive carefully if you visit."
    elif code in range(51, 68):  return "maybe visit tomorrow."
    elif code in range(71, 78):  return "best to wait for better weather."
    elif code in range(80, 83):  return "maybe visit tomorrow."
    elif code in range(95, 100): return "best to wait for better weather."
    return "check before visiting."

def _get_city(lat, lng):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json"},
            headers={"User-Agent": "AutoLink-MobileApp/1.0"},
            timeout=6,
        )
        r.raise_for_status()
        addr = r.json().get("address", {})
        return (
            addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("suburb") or addr.get("county") or "this area"
        )
    except Exception:
        return "this area"

def saved_screen(page: ft.Page, go_to, geo=None):
    col    = ft.Column(spacing=12)
    status = ft.Text("", color=TEXT_LIGHT, text_align=ft.TextAlign.CENTER)
    spin   = ft.ProgressRing(visible=True, color=PRIMARY, width=30, height=30)

    saved_items = [None]
    sort_active = [False]

    sort_label = ft.Text("📍 Sort by My Location", size=13, color="white")
    sort_spin  = ft.ProgressRing(
        visible=False, color="white", width=14, height=14, stroke_width=2,
    )
    sort_btn = ft.Container(
        content=ft.Row(
            [sort_spin, sort_label],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=PRIMARY, border_radius=20,
        padding=ft.Padding(16, 8, 16, 8),
        ink=True,
        on_click=lambda e: page.run_task(_toggle_sort_async),
    )
    location_status = ft.Text("", size=11, color=TEXT_LIGHT, italic=True)

    async def _toggle_sort_async():
        if sort_active[0]:
            sort_active[0]        = False
            sort_label.value      = "📍 Sort by My Location"
            sort_btn.bgcolor      = PRIMARY
            location_status.value = ""
            page.update()
            _render_cards(saved_items[0], user_lat=None, user_lng=None)
            return

        sort_spin.visible     = True
        sort_label.value      = "Accessing GPS…"
        sort_btn.bgcolor      = "#455a64"
        location_status.value = ""
        page.update()

        lat, lng, city = await _get_my_location_geo(geo)

        if lat is None:
            sort_spin.visible     = False
            sort_label.value      = "📍 Sort by My Location"
            sort_btn.bgcolor      = PRIMARY
            location_status.value = "GPS access denied or unavailable."
            page.update()
            return

        sort_active[0]        = True
        sort_spin.visible     = False
        sort_label.value      = "✕ Clear Sort"
        sort_btn.bgcolor      = ACCENT
        location_status.value = f"📍 Sorting from: {city}"
        page.update()

        _render_cards(saved_items[0], user_lat=lat, user_lng=lng)

    def _build_card(v, on_tap, on_unsave, distance_km=None):
        images  = v.get("images", [])
        img_url = images[0]["image"] if images else None

        from screens.weather_service import weather_service
        weather_text = ft.Text("Loading weather...", size=12, color=TEXT_LIGHT)
        weather_container = ft.Container(
            content=weather_text,
            bgcolor="#f0f4ff",
            border_radius=6,
            padding=10,
        )

        async def load_weather():
            parts = v.get("gps_coor", "").split(",")

            if len(parts) != 2:
                weather_text.value = "No location data"
                page.update()
                return

            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
            except:
                weather_text.value = "Invalid coordinates"
                page.update()
                return

            result = await weather_service.get_weather(
                v["id"],
                lat,
                lng,
                (_get_city, _weather_desc, _maybe_visit)
            )

            weather_text.value = result["text"]
            weather_container.bgcolor = result["bg"]
            page.update()

        page.run_task(load_weather)

        dist_badge = ft.Container(
            visible=distance_km is not None,
            content=ft.Row([
                ft.Icon(ft.Icons.NEAR_ME, size=13, color="white"),
                ft.Text(
                    f"{distance_km:.1f} km away" if distance_km is not None else "",
                    size=12, color="white", weight=ft.FontWeight.W_500,
                ),
            ], spacing=4),
            bgcolor=ACCENT, border_radius=10,
            padding=ft.Padding(10, 3, 10, 3),
        )

        img_box = ft.Container(
            content=ft.Image(src=img_url, fit=ft.BoxFit.COVER) if img_url
                    else ft.Icon(ft.Icons.DIRECTIONS_CAR, size=50, color=TEXT_LIGHT),
            height=160, bgcolor="#e0e0e0",
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.alignment.Alignment(0, 0),
        )

        badge = ft.Container(
            content=ft.Text(
                "For Rent" if v["is_rental"] else "For Sale",
                size=11, color="white",
            ),
            bgcolor=PRIMARY if v["is_rental"] else SUCCESS,
            padding=ft.Padding(8, 3, 8, 3),
            border_radius=10,
        )

        info = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        f"{v['make']} {v['model']}",
                        size=15, weight=ft.FontWeight.BOLD,
                        color=TEXT_DARK, expand=True,
                    ),
                    ft.Container(
                        content=ft.Icon(ft.Icons.BOOKMARK, color=ACCENT, size=22),
                        on_click=on_unsave, padding=ft.Padding(4, 4, 4, 4),
                    ),
                ]),
                ft.Text(
                    f"{v['year']}  •  {v['type_of_vehicle']}  •  {v['fuel_type']}",
                    size=12, color=TEXT_LIGHT,
                ),
                ft.Text(
                    f"Rs {int(v['price']):,}{'  /month' if v['is_rental'] else ''}",
                    size=17, weight=ft.FontWeight.BOLD, color=ACCENT,
                ),
                ft.Row([badge, dist_badge], spacing=6),
                weather_container,
            ], spacing=5),
            padding=ft.Padding(12, 12, 12, 12),
        )

        card = ft.GestureDetector(
            on_tap=on_tap,
            content=ft.Card(
                elevation=3,
                content=ft.Column([img_box, info], spacing=0),
            ),
        )

        return card

    def _render_cards(items, user_lat=None, user_lng=None):
        col.controls.clear()
        if items is None: return

        annotated = []
        for item in items:
            v    = item["vehicle"]
            gps  = v.get("gps_coor", "")
            dist = None
            if user_lat is not None and gps:
                try:
                    parts = gps.split(",")
                    dist  = _haversine(
                        user_lat, user_lng,
                        float(parts[0].strip()),
                        float(parts[1].strip()),
                    )
                except (ValueError, IndexError):
                    pass
            annotated.append((dist, v))

        if user_lat is not None:
            with_d    = sorted(
                [(d, v) for d, v in annotated if d is not None],
                key=lambda x: x[0],
            )
            without_d = [(d, v) for d, v in annotated if d is None]
            annotated = with_d + without_d

        for dist, v in annotated:
            def tap_fn(veh):
                def _tap(e):
                    APP_STATE["sv"] = veh
                    go_to("detail")
                return _tap

            def unsave_fn(veh):
                def _do(e):
                    def _run():
                        api.toggle_save(veh["id"])
                        _load()
                    threading.Thread(target=_run).start()
                return _do

            col.controls.append(
                _build_card(v, tap_fn(v), unsave_fn(v), distance_km=dist)
            )

        page.update()

    def _load():
        spin.visible = True
        col.controls.clear()
        status.value = ""
        page.update()

        def fetch():
            try:
                if not api.token:
                    spin.visible = False
                    status.value = "Please login to view saved vehicles."
                    page.update()
                    return

                items = api.saved()
                spin.visible = False
                page.update()

                if not items:
                    status.value = "You haven't saved any vehicles yet."
                    page.update()
                    return

                saved_items[0] = items
                _render_cards(items)

            except Exception as ex:
                spin.visible = False
                status.value = f"Error: {ex}"
                page.update()

        threading.Thread(target=fetch).start()

    _load()

    return ft.View(
        route="/saved", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Text("Saved Vehicles", color="white"),
            bgcolor=PRIMARY,
        ),
        navigation_bar=nav("saved", go_to),
        controls=[
            ft.Container(
                padding=ft.Padding(16, 16, 16, 16),
                content=ft.Column(spacing=12, controls=[
                    ft.Row(
                        [section("Your Saved Vehicles"), sort_btn],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    location_status,
                    ft.Row([spin], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    col,
                ])
            )
        ]
    )