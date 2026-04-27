import flet as ft
import flet_map as fm
import requests
import math

from shared import api, nav, PRIMARY, BG, APP_STATE


# CONFIG
DEFAULT_ZOOM = 13
TILE_URL = "https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}"

FALLBACK_LAT = -20.3185
FALLBACK_LNG = 57.5260



# FORMAT PRICE (FIXED)
def format_price(price):
    try:
        val = float(price)

        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"

        if val >= 1_000:
            return f"{math.floor(val/1000)}k"

        return str(int(val))

    except:
        return "?"



# ROUTE API (OSRM)
def get_route(user_lat, user_lng, v_lat, v_lng):
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{user_lng},{user_lat};{v_lng},{v_lat}"
        f"?overview=full&geometries=geojson"
    )

    res = requests.get(url).json()
    coords = res["routes"][0]["geometry"]["coordinates"]

    return [
        fm.MapLatitudeLongitude(lat, lng)
        for lng, lat in coords
    ]


# MAIN SCREEN
def nearby_screen(page: ft.Page, go_to, geo=None):

    user_location = {"lat": FALLBACK_LAT, "lng": FALLBACK_LNG}

    state = {
        "vehicles": [],
        "selected": None,
        "route": []
    }

    map_container = ft.Container(expand=True)

    
    # ACTION BAR
    action_bar = ft.Container(
    visible=False,
    bgcolor="white",
    padding=12,
    border_radius=15,
    shadow=ft.BoxShadow(
        blur_radius=25,
        spread_radius=2,
        color=ft.Colors.BLACK26
    ),
    content=ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[

            # LEFT SIDE → VEHICLE DETAILS
            ft.Row(
                spacing=12,
                controls=[

                    # ICON
                    ft.Container(
                        content=ft.Icon(ft.Icons.DIRECTIONS_CAR, color="white"),
                        bgcolor=PRIMARY,
                        padding=8,
                        border_radius=10
                    ),

                    # TEXT DETAILS
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("", weight="bold", size=14),   # make + model
                            ft.Text("", size=12, color=ft.Colors.GREY),  # year + fuel + transmission
                            ft.Text("", size=13, color=ft.Colors.RED, weight="bold"),  # price
                        ],
                    ),
                ],
            ),

            # RIGHT SIDE → BUTTONS
            ft.Row(
                spacing=8,
                controls=[
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.NEAR_ME, size=16),
                            ft.Text("Directions", size=12)
                        ], spacing=5),
                        bgcolor=PRIMARY,
                        color="white",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding(10, 6, 10, 6),
                        ),
                        on_click=lambda e: get_directions()
                    ),

                    ft.OutlinedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16),
                            ft.Text("Details", size=12)
                        ], spacing=5),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding(10, 6, 10, 6),
                        ),
                        on_click=lambda e: view_details()
                    ),
                ]
            )
        ],
    ),
)


    
    # MARKER CLICK
    def on_marker_click(vehicle):
        state["selected"] = vehicle

        make_model = f"{vehicle.get('make')} {vehicle.get('model')}"
        year = vehicle.get("year", "")
        fuel = vehicle.get("fuel_type", "")
        trans = vehicle.get("transmission", "")
        price = f"Rs {format_price(vehicle.get('price', 0))}"

        action_bar.content.controls[0].controls[1].controls[0].value = make_model
        action_bar.content.controls[0].controls[1].controls[1].value = f"{year} • {fuel} • {trans}"
        action_bar.content.controls[0].controls[1].controls[2].value = price
        action_bar.visible = True
        page.update()


    # VIEW DETAILS
    def view_details():
        APP_STATE["sv"] = state["selected"]
        go_to("detail")

    # GET DIRECTIONS
    def get_directions():
        v = state["selected"]
        if not v:
            return

        try:
            gps = v.get("gps_coor")
            v_lat, v_lng = map(float, gps.split(","))

            state["route"] = get_route(
                user_location["lat"],
                user_location["lng"],
                v_lat,
                v_lng
            )

            render_map()

        except Exception as e:
            print("Route error:", e)


    # BUILD MARKERS
    def build_markers():
        markers = []

        for v in state["vehicles"]:
            gps = v.get("gps_coor")
            if not gps:
                continue

            try:
                lat, lng = map(float, gps.split(","))
                color = ft.Colors.RED if not v.get("is_rental") else ft.Colors.BLUE

                markers.append(
                    fm.Marker(
                        coordinates=fm.MapLatitudeLongitude(lat, lng),
                        content=ft.Container(
                            content=ft.Text(
                                format_price(v.get("price", 0)),
                                size=8.5,
                                weight="bold",
                                color="white",
                                max_lines=1,
                                
                            ),
                            bgcolor=color,
                            padding=4,
                            border_radius=8,
                            ink=True,
                            on_click=lambda e, veh=v: on_marker_click(veh),
                        ),
                    )
                )
            except:
                continue

        # USER LOCATION
        markers.append(
            fm.Marker(
                coordinates=fm.MapLatitudeLongitude(
                    user_location["lat"],
                    user_location["lng"]
                ),
                content=ft.Icon(ft.Icons.MY_LOCATION),
            )
        )

        return markers

    # MAP RENDER
    def render_map():

        layers = [
            fm.TileLayer(url_template=TILE_URL),
            fm.MarkerLayer(markers=build_markers()),
        ]

        if state["route"]:
            route_markers = [
                fm.Marker(
                    coordinates=pt,
                    content=ft.Container(
                        width=5,
                        height=5,
                        bgcolor=ft.Colors.BLUE,
                        border_radius=3,
                    ),
                )
                for pt in state["route"]
            ]

            layers.append(fm.MarkerLayer(markers=route_markers))

        map_container.content = fm.Map(
            expand=True,
            initial_center=fm.MapLatitudeLongitude(
                user_location["lat"],
                user_location["lng"]
            ),
            initial_zoom=DEFAULT_ZOOM,
            layers=layers,
        )

        page.update()

    # LOAD DATA
    def fetch_data():
        try:
            state["vehicles"] = api.vehicles()
            render_map()
        except Exception as e:
            map_container.content = ft.Text("Failed to load vehicles", color="red")
            page.update()

    # LIVE LOCATION
    def on_position_change(e):
        user_location["lat"] = e.position.latitude
        user_location["lng"] = e.position.longitude
        render_map()

    def init_location():
        if not geo:
            return

        geo.on_position_change = on_position_change

        async def start():
            try:
                await geo.request_permission()
                pos = await geo.get_current_position()

                user_location["lat"] = pos.latitude
                user_location["lng"] = pos.longitude

                render_map()

            except Exception as e:
                print("GPS error:", e)

        page.run_task(start)

    # UI
    ui = ft.Column(
        expand=True,
        controls=[
            ft.Text("Nearby Vehicles", size=22, weight="bold"),
            ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        content=ft.Text("🔑 Renting", size=12),
                        bgcolor=ft.Colors.BLUE,
                        padding=ft.Padding(8, 4, 8, 4),
                        border_radius=8,
                    ),
                    ft.Container(
                        content=ft.Text("🚗 Selling", size=12),
                        bgcolor=ft.Colors.RED,
                        padding=ft.Padding(8, 4, 8, 4),
                        border_radius=8,
                    ),
                ],
            ),
            map_container,
            action_bar,
        ],
    )

    fetch_data()
    init_location()

    return ft.View(
        route="/nearby",
        bgcolor=BG,
        navigation_bar=nav("nearby", go_to),
        appbar=ft.AppBar(
            title=ft.Text("Vehicle Map"),
            bgcolor=PRIMARY,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: go_to("home"),
            ),
        ),
        controls=[ft.Container(ui, padding=10, expand=True)],
    )