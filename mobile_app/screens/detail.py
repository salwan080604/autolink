# VEHICLE DETAIL SCREEN WITH IMAGE CAROUSEL + MINI MAP

import flet as ft
import threading
import flet_map as fm

from shared import api, APP_STATE, section
from shared import PRIMARY, ACCENT, BG, TEXT_LIGHT, SUCCESS, CENTER


def detail_screen(page, go_to):

    vehicle = APP_STATE.get("sv")
    if not vehicle:
        go_to("home")
        return ft.View(route="/detail")

    # SAVE BUTTON
    saved_ids = set()
    if api.token:
        try:
            saved_ids = {s["vehicle"]["id"] for s in api.saved()}
        except:
            pass

    is_saved = vehicle["id"] in saved_ids

    save_txt = ft.Text("Unsave" if is_saved else "Save", color="white", size=14)
    save_icon = ft.Icon(ft.Icons.BOOKMARK, color="white", size=16)

    save_box = ft.Container(
        content=ft.Row([save_icon, save_txt], spacing=6),
        bgcolor=ACCENT if is_saved else PRIMARY,
        border_radius=8,
        padding=ft.Padding(16, 10, 16, 10),
        alignment=CENTER,
        ink=True,
        expand=True,
    )

    def toggle(e):
        if not api.token:
            go_to("login")
            return

        def run():
            r = api.toggle_save(vehicle["id"])
            s = r.get("saved", False)
            save_txt.value = "Unsave" if s else "Save"
            save_box.bgcolor = ACCENT if s else PRIMARY
            page.update()

        threading.Thread(target=run).start()

    save_box.on_click = toggle

    # INFO ROW
    def irow(icon, lbl, val):
        return ft.Row([
            ft.Icon(icon, size=18, color=PRIMARY),
            ft.Text(f"{lbl}:", weight=ft.FontWeight.BOLD, size=13, width=110),
            ft.Text(str(val), size=13, color=TEXT_LIGHT, expand=True),
        ])

    # IMAGE CAROUSEL
    images = vehicle.get("images", [])
    img_count = max(len(images), 1)
    current_index = {"i": 0}

    index_text = ft.Text(f"1/{img_count}", size=12, color="white")

    def get_image_control(idx):
        if images:
            return ft.Image(
                src=images[idx]["image"],
                fit=ft.BoxFit.CONTAIN,
                expand=True,
            )
        return ft.Icon(ft.Icons.DIRECTIONS_CAR, size=80, color=TEXT_LIGHT)

    image_display = ft.Container(
        content=get_image_control(0),
        alignment=CENTER,
        bgcolor="#000000",
        expand=True,
    )

    def go_to_image(idx):
        current_index["i"] = idx
        image_display.content = get_image_control(idx)
        index_text.value = f"{idx + 1}/{img_count}"
        page.update()

    def prev_image(e):
        i = current_index["i"]
        if i > 0:
            go_to_image(i - 1)

    def next_image(e):
        i = current_index["i"]
        if i < img_count - 1:
            go_to_image(i + 1)

    carousel = ft.Stack(
        height=260,
        controls=[
            ft.Container(content=image_display, expand=True, bgcolor="#000000"),

            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color="white",
                bgcolor="#00000066",
                on_click=prev_image,
                left=10,
                top=110,
                visible=img_count > 1,
            ),

            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_color="white",
                bgcolor="#00000066",
                on_click=next_image,
                right=10,
                top=110,
                visible=img_count > 1,
            ),

            ft.Container(
                content=index_text,
                bgcolor="#00000088",
                padding=5,
                border_radius=6,
                bottom=10,
                right=10,
                visible=img_count > 1,
            ),
        ]
    )

    # MINI MAP (NEW FEATURE)
    gps = vehicle.get("gps_coor", "-20.1609,57.5012")

    try:
        lat, lng = map(float, gps.split(","))
    except:
        lat, lng = -20.1609, 57.5012

    mini_map = ft.Container(
        height=180,
        border_radius=12,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        margin=ft.margin.only(top=10),
        content=fm.Map(
            expand=True,
            initial_center=fm.MapLatitudeLongitude(lat, lng),
            initial_zoom=15,
            layers=[
                fm.TileLayer(
                    url_template="https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}"
                ),
                fm.MarkerLayer(
                    markers=[
                        fm.Marker(
                            coordinates=fm.MapLatitudeLongitude(lat, lng),
                            content=ft.Icon(
                                ft.Icons.LOCATION_ON,
                                color=ft.Colors.RED,
                                size=30,
                            ),
                        )
                    ]
                ),
            ],
        ),
    )


    # WHATSAPP BUTTON
    wa = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CHAT, color="white", size=16),
            ft.Text("WhatsApp", color="white", size=14),
        ], spacing=6),
        bgcolor="#25D366",
        border_radius=8,
        padding=ft.Padding(16, 10, 16, 10),
        alignment=CENTER,
        ink=True,
        expand=True,
        on_click=lambda e: page.launch_url(
            f"https://wa.me/{vehicle.get('contact', '')}"
        ),
    ) if vehicle.get("contact") else ft.Container()


    # VIEW
    return ft.View(
        route="/detail",
        bgcolor=BG,
        scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            bgcolor=PRIMARY,
            title=ft.Text(f"{vehicle['make']} {vehicle['model']}", color="white"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color="white",
                on_click=lambda e: go_to("home"),
            )
        ),
        controls=[
            ft.Column(
                spacing=0,
                controls=[

                    # IMAGE CAROUSEL
                    carousel,

                    ft.Container(
                        padding=ft.Padding(20, 20, 20, 20),
                        content=ft.Column(
                            spacing=12,
                            controls=[

                                # TITLE
                                ft.Row([
                                    ft.Column(expand=True, controls=[
                                        ft.Text(
                                            f"{vehicle['make']} {vehicle['model']} {vehicle['year']}",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"Rs {int(vehicle['price']):,}"
                                            f"{' /month' if vehicle['is_rental'] else ''}",
                                            size=18,
                                            color=ACCENT,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ]),
                                    ft.Container(
                                        content=ft.Text(
                                            "For Rent" if vehicle['is_rental'] else "For Sale",
                                            color="white",
                                            size=12,
                                        ),
                                        bgcolor=PRIMARY if vehicle['is_rental'] else SUCCESS,
                                        padding=ft.Padding(10, 5, 10, 5),
                                        border_radius=20,
                                    ),
                                ]),

                                ft.Divider(),

                                section("Specifications"),

                                irow(ft.Icons.SPEED, "Mileage", f"{vehicle['mileage']:,} km"),
                                irow(ft.Icons.SETTINGS, "Transmission", vehicle['transmission']),
                                irow(ft.Icons.LOCAL_GAS_STATION, "Fuel Type", vehicle['fuel_type']),
                                irow(ft.Icons.CATEGORY, "Type", vehicle['type_of_vehicle']),
                                irow(ft.Icons.PERSON, "Listed by", vehicle.get('uploader_name', 'N/A')),

                                ft.Divider(),
                                section("Description"),

                                ft.Text(
                                    vehicle.get('desc') or "No description provided.",
                                    size=14,
                                    color=TEXT_LIGHT,
                                ),

                                ft.Divider(),

                                ft.Row([save_box, wa], spacing=10),


                                section("Location"),

                                ft.Text(
                                    f"📍 GPS: {vehicle.get('gps_coor', 'N/A')}",
                                    size=12,
                                    color=TEXT_LIGHT,
                                ),

                                # MINI MAP HERE
                                mini_map,

                                ft.Divider(),

                                ft.Container(height=20),
                            ]
                        )
                    ),
                ]
            )
        ]
    )