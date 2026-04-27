import flet as ft
from shared import BG

from screens.login   import login_screen, register_screen
from screens.home    import home_screen
from screens.detail  import detail_screen
from screens.nearby  import nearby_screen
from screens.saved   import saved_screen
from screens.reviews import report_vehicle_screen, reviews_screen, report_screen_for_review
from screens.profile import profile_screen
from screens.upload  import upload_vehicle_screen, my_vehicles_screen, edit_vehicle_screen

SCREENS = {
    "login":          login_screen,
    "register":       register_screen,
    "home":           home_screen,
    "detail":         detail_screen,
    "nearby":         nearby_screen,
    "saved":          saved_screen,
    "reviews":        reviews_screen,
    "profile":        profile_screen,
    "report_review":  report_screen_for_review,
    "report_vehicle": report_vehicle_screen,
    "upload_vehicle": upload_vehicle_screen,
    "my_vehicles":    my_vehicles_screen,
    "edit_vehicle":   edit_vehicle_screen,
}


async def main(page: ft.Page):
    page.title         = "AutoLink"
    page.theme_mode    = ft.ThemeMode.LIGHT
    page.bgcolor       = BG
    page.window_width  = 400
    page.window_height = 800
    page.padding       = 0

    # Add geo to overlay and update BEFORE any navigation
    geo = None
    if not page.web:
        import flet_geolocator as ftg
        geo = ftg.Geolocator(
            configuration=ftg.GeolocatorConfiguration(
                accuracy=ftg.GeolocatorPositionAccuracy.HIGH,
            ),
        )

    # Store geo in page.data so any screen can access it via page.data["geo"]
    # This does NOT affect nearby.py or any other screen — they don't read page.data
    page.data = {"geo": geo}

    def go_to(route):
        page.views.clear()
        if route in SCREENS:
            if route in ["nearby", "saved"]:
                page.views.append(SCREENS[route](page, go_to, geo))
            else:
                page.views.append(SCREENS[route](page, go_to))
        page.update()

    go_to("login")


ft.run(main, assets_dir="assets")