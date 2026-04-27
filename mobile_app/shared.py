# ─────────────────────────────────────────────────────────────
# SHARED MODULE — Do NOT modify without telling the whole team
# Contains: API class, theme colors, helper components,
#           navigation bar, vehicle card, global state
# ─────────────────────────────────────────────────────────────

import flet as ft
import requests
import threading

# ── CONFIG ───────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000/api"

# ── GLOBAL STATE (replaces page.session for Flet 0.84) ───────
APP_STATE = {}

# ── THEME COLORS ─────────────────────────────────────────────
PRIMARY    = "#1a237e"
ACCENT     = "#ff6f00"
BG         = "#f5f5f5"
CARD_BG    = "#ffffff"
TEXT_DARK  = "#212121"
TEXT_LIGHT = "#757575"
SUCCESS    = "#388e3c"
ERROR      = "#c62828"
CENTER     = ft.alignment.Alignment(0, 0)


# ── API CLASS ────────────────────────────────────────────────
class API:
    def __init__(self):
        self.token     = None
        self.user_name = ""
        self.user_type = ""

    def h(self):
        return {"Authorization": f"Token {self.token}"} if self.token else {}

    def login(self, email, pwd):
        r = requests.post(f"{BASE_URL}/login/", json={"email": email, "password": pwd}, timeout=10)
        return r.status_code, r.json()

    def register(self, data):
        r = requests.post(f"{BASE_URL}/register/", json=data, timeout=10)
        return r.status_code, r.json()

    def logout(self):
        try: requests.post(f"{BASE_URL}/logout/", headers=self.h(), timeout=5)
        except: pass
        self.token = None; self.user_name = ""; self.user_type = ""

    def profile(self):
        return requests.get(f"{BASE_URL}/profile/", headers=self.h(), timeout=10).json()

    def update_profile(self, data):
        r = requests.patch(f"{BASE_URL}/profile/update/", json=data, headers=self.h(), timeout=10)
        return r.status_code, r.json()

    def vehicles(self, search="", vtype=""):
        p = {}
        if search: p["search"] = search
        if vtype:  p["type"]   = vtype
        return requests.get(f"{BASE_URL}/vehicles/", params=p, timeout=10).json()

    def nearby(self, lat, lng, radius=20):
        return requests.get(f"{BASE_URL}/vehicles/nearby/",
            params={"lat": lat, "lng": lng, "radius": radius}, timeout=10).json()

    def saved(self):
        return requests.get(f"{BASE_URL}/saved/", headers=self.h(), timeout=10).json()
    
    def saved_sorted(self, lat, lng):
        return requests.get(
            f"{BASE_URL}/saved/sorted/",
            params={"lat": lat, "lng": lng},
            headers=self.h(),
            timeout=15,
        ).json()

    def toggle_save(self, vid):
        return requests.post(f"{BASE_URL}/saved/toggle/{vid}/", headers=self.h(), timeout=10).json()

    def reviews(self):
        return requests.get(f"{BASE_URL}/reviews/", timeout=10).json()

    def submit_review(self, data):
        r = requests.post(f"{BASE_URL}/reviews/submit/", json=data, timeout=10)
        return r.status_code, r.json()

    def submit_report(self, data):
        try:
            r = requests.post(f"{BASE_URL}/report/", json=data, timeout=10)
            return r.status_code, r.json()
        except:
            return 201, {}

# Global API instance — import this in every screen
api = API()

# ── REUSABLE UI COMPONENTS ────

def big_btn(label, on_click, bg=None, fg="white", width=300):
    """Standard primary button used across all screens"""
    bg = bg or PRIMARY
    return ft.Container(
        content=ft.Text(label, color=fg, size=15,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500),
        bgcolor=bg, border_radius=8, width=width,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
        alignment=CENTER, on_click=on_click, ink=True,
    )

def link_btn(label, on_click, color=None):
    """Text-style link button"""
    color = color or PRIMARY
    return ft.TextButton(
        content=ft.Text(label, color=color, size=13),
        on_click=on_click,
    )

def field(label, password=False, keyboard=None, icon=None):
    """Standard styled text field"""
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard,
        prefix_icon=icon,
        border_color=PRIMARY,
        focused_border_color=ACCENT,
    )

def section(text):
    """Section header label"""
    return ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=PRIMARY)


# ── NAVIGATION BAR ──────
ROUTES = ["home", "nearby", "saved", "reviews", "profile"]

def nav(selected, go_to):
    """Bottom navigation bar — used in every main screen"""
    return ft.NavigationBar(
        selected_index=ROUTES.index(selected),
        bgcolor=CARD_BG,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME,        label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.LOCATION_ON, label="Nearby"),
            ft.NavigationBarDestination(icon=ft.Icons.BOOKMARK,    label="Saved"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR,        label="Reviews"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON,      label="Profile"),
        ],
        on_change=lambda e: go_to(ROUTES[e.control.selected_index]),
    )


# ── VEHICLE CARD ───
def v_card(v, on_tap, on_save=None, saved=False):
    """Vehicle listing card — used in home, nearby and saved screens"""
    images  = v.get("images", [])
    img_url = images[0]["image"] if images else None

    img_box = ft.Container(
        content=ft.Image(src=img_url, fit=ft.BoxFit.COVER) if img_url
                else ft.Icon(ft.Icons.DIRECTIONS_CAR, size=50, color=TEXT_LIGHT),
        height=160, bgcolor="#e0e0e0",
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        alignment=CENTER,
    )

    save_btn = ft.Container(
        content=ft.Icon(
            ft.Icons.BOOKMARK if saved else ft.Icons.BOOKMARK_BORDER,
            color=ACCENT if saved else TEXT_LIGHT, size=22,
        ),
        on_click=on_save, padding=4,
    ) if on_save else ft.Container()

    badge = ft.Container(
        content=ft.Text("For Rent" if v['is_rental'] else "For Sale",
                        size=11, color="white"),
        bgcolor=PRIMARY if v['is_rental'] else SUCCESS,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=10,
    )

    info = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"{v['make']} {v['model']}", size=15,
                        weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                save_btn,
            ]),
            ft.Text(f"{v['year']}  •  {v['type_of_vehicle']}  •  {v['fuel_type']}",
                    size=12, color=TEXT_LIGHT),
            ft.Text(
                f"Rs {int(v['price']):,}{'  /month' if v['is_rental'] else ''}",
                size=17, weight=ft.FontWeight.BOLD, color=ACCENT,
            ),
            badge,
        ], spacing=5),
        padding=ft.padding.all(12),
    )

    return ft.GestureDetector(
        content=ft.Card(
            content=ft.Column([img_box, info], spacing=0),
            elevation=3,
        ),
        on_tap=on_tap,
    )
LOCAL_IMAGES = {}


