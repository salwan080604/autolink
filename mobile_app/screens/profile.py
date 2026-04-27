import flet as ft
import flet_camera as fc
import threading, asyncio
from shared import api, big_btn, nav
from shared import PRIMARY, ACCENT, BG, TEXT_DARK, TEXT_LIGHT, ERROR, SUCCESS

def profile_screen(page: ft.Page, go_to):
    col  = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    spin = ft.ProgressRing(visible=True, color=PRIMARY, width=30, height=30)

    photo_path = [None]
    user_initial = ["U"]

    avatar_image = ft.Image(
        src="", fit=ft.BoxFit.COVER,
        width=90, height=90,
        visible=False,
    )
    avatar_initials = ft.CircleAvatar(
        content=ft.Text("U", size=36, color="white"),
        bgcolor=PRIMARY, radius=45,
        visible=True,
    )
    avatar_stack = ft.Stack(
        [
            ft.Container(
                content=avatar_initials,
                width=90, height=90,
                border_radius=45,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Container(
                content=avatar_image,
                width=90, height=90,
                border_radius=45,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ],
        width=90, height=90,
    )

    def _show_photo(path):
        photo_path[0] = path
        avatar_image.src = path
        avatar_image.visible = True
        avatar_initials.visible = False
        delete_btn.visible = True
        page.update()

    def _clear_photo():
        photo_path[0] = None
        avatar_image.src = ""
        avatar_image.visible = False
        avatar_initials.visible = True
        cam_container.visible = False
        cam_btn.text = "Change Photo"
        cam_btn.icon = ft.Icons.CAMERA_ALT
        delete_btn.visible = False
        page.update()

    cam = fc.Camera(expand=True, preview_enabled=True)
    cam_container = ft.Container(
        content=cam,
        height=280,
        visible=False,
        border_radius=12,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        margin=ft.margin.symmetric(horizontal=0),
    )

    async def _toggle_camera(e):
        if cam_container.visible:
            try:
                path = await cam.take_picture()
                _show_photo(path)
                cam_container.visible = False
                cam_btn.text = "Retake Photo"
                cam_btn.icon = ft.Icons.REPLAY
                page.update()
            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"Camera error: {err}"))
                page.snack_bar.open = True
                page.update()

        else:
            cam_container.visible = True
            page.update()

            try:
                cameras = await cam.get_available_cameras()

                if not cameras:
                    page.snack_bar = ft.SnackBar(ft.Text("No camera found."))
                    page.snack_bar.open = True
                    page.update()
                    return

                await cam.initialize(
                    description=next(
                        (c for c in cameras if c.lens_direction == fc.CameraLensDirection.FRONT),
                        cameras[0]
                    ),
                    resolution_preset=fc.ResolutionPreset.MEDIUM,
                )

                cam_btn.text = "Snap Selfie!"
                cam_btn.icon = ft.Icons.CAMERA
                page.update()

            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"Camera init error: {err}"))
                page.snack_bar.open = True
                cam_container.visible = False
                page.update()
                        
    cam_btn = ft.ElevatedButton(
        "Change Photo",
        icon=ft.Icons.CAMERA_ALT,
        on_click=_toggle_camera,
        color="white",
        bgcolor=PRIMARY,
    )
    delete_btn = ft.TextButton(
        "Delete Photo",
        icon=ft.Icons.DELETE_OUTLINE,
        style=ft.ButtonStyle(color=ERROR),
        on_click=lambda e: _clear_photo(),
        visible=False,
    )

    battery_text = ft.Text(
        "", size=13, italic=True, no_wrap=False,
    )
    battery_banner = ft.Container(
        visible=False,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        content=battery_text,
    )

    async def _watch_battery():
        try:
            bat = ft.Battery()

            while True:
                level = await bat.get_battery_level()
                state = await bat.get_battery_state()

                is_charging = (
                    state == ft.BatteryState.CHARGING
                    or state == ft.BatteryState.FULL
                )

                if is_charging or level >= 50:
                    battery_banner.bgcolor = "#e8f5e9"
                    status_msg = "(charging)" if is_charging else "— all good!"
                    battery_text.value = f"🟢 Battery: {level}% {status_msg}"
                    battery_text.color = "#2e7d32"

                elif level >= 20:
                    battery_banner.bgcolor = "#fff3e0"
                    battery_text.value = f"🟠 Battery low: {level}% — consider charging soon."
                    battery_text.color = "#e65100"

                else:
                    battery_banner.bgcolor = "#ffebee"
                    battery_text.value = f"🔴 Battery critical: {level}% — plug in now!"
                    battery_text.color = ERROR

                battery_banner.visible = True
                page.update()

                await asyncio.sleep(0.5)

        except Exception as e:
            print("Battery watch error:", e)

    def do_logout():
        threading.Thread(target=api.logout).start()
        go_to("login")

    def load():
        def fetch():
            try:
                if not api.token:
                    spin.visible = False
                    col.controls += [
                        ft.Icon(ft.Icons.PERSON_OUTLINE, size=60, color=TEXT_LIGHT),
                        ft.Text("You are not logged in.", size=16, color=TEXT_LIGHT),
                        big_btn("Login", lambda e: go_to("login"), width=200),
                    ]
                    page.update()
                    return

                p = api.profile()
                spin.visible = False

                initial = (p.get("first_name") or "U")[0].upper()
                user_initial[0] = initial
                avatar_initials.content = ft.Text(initial, size=36, color="white")

                def tile(icon, lbl, val):
                    return ft.ListTile(
                        leading=ft.Icon(icon, color=PRIMARY),
                        title=ft.Text(lbl, size=12, color=TEXT_LIGHT),
                        subtitle=ft.Text(str(val or "N/A"), size=15, color=TEXT_DARK),
                    )

                col.controls += [
                    ft.Container(height=10),

                    avatar_stack,

                    ft.Row(
                        [cam_btn, delete_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),

                    cam_container,

                    ft.Text(
                        f"{p.get('first_name','')} {p.get('last_name','')}",
                        size=22, weight=ft.FontWeight.BOLD, color=TEXT_DARK,
                    ),
                    ft.Container(
                        content=ft.Text(
                            p.get("user_type", "").capitalize(),
                            color="white", size=13,
                        ),
                        bgcolor=ACCENT,
                        padding=ft.padding.symmetric(horizontal=12, vertical=4),
                        border_radius=20,
                    ),
                    ft.Container(height=4),

                    battery_banner,

                    ft.Container(height=6),
                    ft.Card(elevation=3, content=ft.Column(spacing=0, controls=[
                        tile(ft.Icons.EMAIL,       "Email",          p.get("email")),
                        ft.Divider(height=1),
                        tile(ft.Icons.PHONE,       "Contact",        p.get("contact_number")),
                        ft.Divider(height=1),
                        tile(ft.Icons.HOME,        "Address",        p.get("address")),
                        ft.Divider(height=1),
                        tile(ft.Icons.CREDIT_CARD, "Driver License", p.get("driver_license")),
                    ])),
                    ft.Container(height=10),
                ]

                if p.get("user_type") in ["seller", "renter"]:
                    col.controls.append(
                        big_btn("🚗  My Listings", lambda e: go_to("my_vehicles"), width=280)
                    )
                    col.controls.append(ft.Container(height=8))

                col.controls += [
                    big_btn("Logout", lambda e: do_logout(), bg=ERROR, width=200),
                    ft.Container(height=20),
                ]

                page.update()
                page.run_task(_watch_battery)

            except Exception as ex:
                spin.visible = False
                col.controls.append(ft.Text(f"Error: {ex}", color=ERROR))
                page.update()

        threading.Thread(target=fetch).start()

    load()

    return ft.View(
        route="/profile", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(title=ft.Text("My Profile", color="white"), bgcolor=PRIMARY),
        navigation_bar=nav("profile", go_to),
        controls=[
            ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column(spacing=10, controls=[
                    ft.Row([spin], alignment=ft.MainAxisAlignment.CENTER),
                    col,
                ])
            )
        ]
    )