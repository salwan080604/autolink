# screens/home.py
# ─────────────────────────────────────────────────────────────
# HOME SCREEN
# Owner: Keshni Nunkoo (2412390)
# ─────────────────────────────────────────────────────────────

import flet as ft
import httpx
import asyncio
from shared import (
    api, APP_STATE, nav,
    PRIMARY, ACCENT, BG, CARD_BG, TEXT_DARK, TEXT_LIGHT,
    CENTER, SUCCESS, BASE_URL
)

# ══════════════════════════════════════════════════════════════
# CUSTOM VEHICLE CARD — @ft.control 
# ══════════════════════════════════════════════════════════════
@ft.control
class VehicleCard(ft.GestureDetector):
    def __init__(self, vehicle: dict, on_tap, on_save=None, saved: bool = False):
        super().__init__()
        self._vehicle = vehicle
        self._saved   = saved
        self._on_save = on_save
        self.on_tap   = on_tap
        self.content  = self._build()

    def _build(self):
        v       = self._vehicle
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
                ft.Icons.BOOKMARK if self._saved else ft.Icons.BOOKMARK_BORDER,
                color=ACCENT if self._saved else TEXT_LIGHT, size=22,
            ),
            on_click=self._handle_save, padding=4,
        ) if self._on_save else ft.Container()

        badge = ft.Container(
            content=ft.Text(
                "For Rent" if v['is_rental'] else "For Sale",
                size=11, color="white",
            ),
            bgcolor=PRIMARY if v['is_rental'] else SUCCESS,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=10,
        )

        price = f"Rs {int(v['price']):,}"
        if v['is_rental']: price += "  /month"

        info = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{v['make']} {v['model']}", size=15,
                            weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                    save_btn,
                ]),
                ft.Text(
                    f"{v['year']}  •  {v['type_of_vehicle']}  •  {v['fuel_type']}",
                    size=12, color=TEXT_LIGHT,
                ),
                ft.Text(price, size=17, weight=ft.FontWeight.BOLD, color=ACCENT),
                badge,
            ], spacing=5),
            padding=ft.padding.all(12),
        )

        return ft.Card(
            content=ft.Column([img_box, info], spacing=0),
            elevation=3,
        )

    def _handle_save(self, e):
        if self._on_save:
            self._on_save(e, self)

    def toggle_saved(self):
        """self.update() refreshes only this card — not the whole page"""
        self._saved  = not self._saved
        self.content = self._build()
        self.update()

# ══════════════════════════════════════════════════════════════
# ASYNC API HELPERS — httpx 
# ══════════════════════════════════════════════════════════════
async def fetch_vehicles(search="", vtype=""):
    params = {}
    if search: params["search"] = search
    if vtype:  params["type"]   = vtype
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/vehicles/", params=params, timeout=10)
        return r.json()


async def fetch_saved():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/saved/", headers=api.h(), timeout=10)
        return r.json()


async def async_toggle_save(vehicle_id):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/saved/toggle/{vehicle_id}/",
            headers=api.h(), timeout=10,
        )
        return r.json()

# ══════════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════════
def home_screen(page, go_to):

    # ── STATE ────────────────────────────────────────────────
    saved_ids    = set()
    filter_ref   = {"type": ""}
    sort_ref     = {"val": "default"}
    price_ref    = {"max": None}
    mileage_ref  = {"max": None}
    rental_ref   = {"val": None}   # None=all, True=rent, False=sale
    search_timer = {"t": None}
    all_vehicles = {"data": []}
    type_counts  = {}

    # ── CONTROLS ─────────────────────────────────────────────
    search_f = ft.TextField(
        hint_text="Search make, model, type...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=14,
        border_color="transparent",
        focused_border_color=PRIMARY,
        bgcolor=CARD_BG,
        expand=True,
        text_style=ft.TextStyle(color=TEXT_DARK, size=14),
        hint_style=ft.TextStyle(color=TEXT_LIGHT, size=14),
    )

    col          = ft.Column(spacing=14)
    status       = ft.Text("", color=TEXT_LIGHT, text_align=ft.TextAlign.CENTER, size=14)
    spin         = ft.ProgressRing(visible=True, color=ACCENT, width=28, height=28)
    result_count = ft.Text("", size=12, color=TEXT_LIGHT)

    # ── SPOTLIGHT ────────────────────────────────────────────
    spotlight     = ft.Container(visible=False)
    featured_spin = ft.ProgressRing(visible=True, color=PRIMARY, width=20, height=20)

    # ── FOR SALE / FOR RENT TOGGLE ────────────────────────────
    toggle_row = ft.Row(spacing=0)

    def build_toggle():
        toggle_row.controls.clear()
        opts = [("All", None), ("For Sale", False), ("For Rent", True)]
        for i, (lbl, val) in enumerate(opts):
            active = rental_ref["val"] == val
            if i == 0:
                br = ft.border_radius.only(top_left=10, bottom_left=10)
            elif i == 2:
                br = ft.border_radius.only(top_right=10, bottom_right=10)
            else:
                br = ft.border_radius.all(0)

            def on_toggle(e, v=val):
                rental_ref["val"] = v
                build_toggle()
                render_vehicles()
                page.update()

            toggle_row.controls.append(ft.Container(
                content=ft.Text(lbl, size=13, weight=ft.FontWeight.W_600,
                                color="white" if active else TEXT_DARK,
                                text_align=ft.TextAlign.CENTER),
                bgcolor=PRIMARY if active else CARD_BG,
                border=ft.border.all(1.5, PRIMARY),
                border_radius=br,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                on_click=on_toggle, ink=True,
                expand=True,
                alignment=CENTER,
            ))

    build_toggle()

    # ── FILTER CHIPS ─────────────────────────────────────────
    chips_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)

    TYPE_OPTS = [
        ("All", ""), ("Cars", "Car"),
        ("Motorbikes", "Motorbike"), ("Trucks", "Truck"),
        ("Vans", "Van"),
    ]

    def build_chips():
        chips_row.controls.clear()
        for lbl, val in TYPE_OPTS:
            active = filter_ref["type"] == val
            count  = type_counts.get(val, None)
            if val == "":
                count = sum(type_counts.values()) if type_counts else None
            label  = f"{lbl} ({count})" if count is not None else lbl
            def on_tap(e, v=val):
                filter_ref["type"] = v
                build_chips()
                render_vehicles()
                page.update()
            chips_row.controls.append(ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                                color="white" if active else TEXT_DARK),
                bgcolor=PRIMARY if active else CARD_BG,
                border=ft.border.all(1.5, PRIMARY if active else "#d1d5db"),
                border_radius=99,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                on_click=on_tap, ink=True,
            ))

    build_chips()

    # ── SORT BOTTOM SHEET ─────────────────────────────────────
    sort_label = ft.Text("Default", size=12, color=PRIMARY, weight=ft.FontWeight.W_600)

    def make_sort_opt(label, val):
        def select(e):
            sort_ref["val"] = val
            sort_label.value = label
            bs_sort.open = False
            render_vehicles()
            page.update()
        active = sort_ref["val"] == val
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=14, color=TEXT_DARK, expand=True),
                ft.Icon(ft.Icons.CHECK, color=PRIMARY, size=18) if active
                else ft.Container(),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            on_click=select, ink=True,
            bgcolor="#f0f2ff" if active else CARD_BG,
        )

    bs_sort = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Sort by", size=16,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE, icon_color=TEXT_LIGHT,
                            on_click=lambda e: (setattr(bs_sort, 'open', False),
                                               page.update()),
                        ),
                    ]),
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                ),
                ft.Divider(height=1),
                make_sort_opt("Default",            "default"),
                make_sort_opt("Price: Low to High", "price_asc"),
                make_sort_opt("Price: High to Low", "price_desc"),
                make_sort_opt("Newest First",       "year_desc"),
                make_sort_opt("Oldest First",       "year_asc"),
                ft.Container(height=20),
            ], spacing=0),
            bgcolor=CARD_BG,
        ),
        open=False,
    )
    page.overlay.append(bs_sort)

    # ── PRICE + MILEAGE FILTER BOTTOM SHEET ──────────────────
    price_display   = ft.Text("No limit", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY)
    mileage_display = ft.Text("No limit", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY)
    price_slider    = ft.Slider(min=0, max=10000000, value=10000000,
                                divisions=20, active_color=PRIMARY, thumb_color=ACCENT)
    mileage_slider  = ft.Slider(min=0, max=500000, value=500000,
                                divisions=20, active_color=PRIMARY, thumb_color=ACCENT)

    def on_price_change(e):
        val = int(price_slider.value)
        if val >= 10000000:
            price_display.value = "No limit"; price_ref["max"] = None
        else:
            price_display.value = f"Rs {val:,}"; price_ref["max"] = val
        page.update()
    price_slider.on_change = on_price_change

    def on_mileage_change(e):
        val = int(mileage_slider.value)
        if val >= 500000:
            mileage_display.value = "No limit"; mileage_ref["max"] = None
        else:
            mileage_display.value = f"{val:,} km"; mileage_ref["max"] = val
        page.update()
    mileage_slider.on_change = on_mileage_change

    def apply_filters(e):
        bs_price.open = False; render_vehicles(); page.update()

    def clear_price(e):
        price_slider.value    = 10000000; price_display.value   = "No limit"; price_ref["max"]   = None
        mileage_slider.value  = 500000;   mileage_display.value = "No limit"; mileage_ref["max"] = None
        bs_price.open = False; render_vehicles(); page.update()

    bs_price = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Price & Mileage", size=16,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE, icon_color=TEXT_LIGHT,
                            on_click=lambda e: (setattr(bs_price, 'open', False),
                                               page.update()),
                        ),
                    ]),
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                ),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Maximum price", size=13, color=TEXT_LIGHT,
                                weight=ft.FontWeight.W_600),
                        price_display, price_slider,
                        ft.Row([
                            ft.Text("Rs 0", size=11, color=TEXT_LIGHT),
                            ft.Container(expand=True),
                            ft.Text("Rs 10M+", size=11, color=TEXT_LIGHT),
                        ]),
                        ft.Divider(height=1),
                        ft.Text("Maximum mileage", size=13, color=TEXT_LIGHT,
                                weight=ft.FontWeight.W_600),
                        mileage_display, mileage_slider,
                        ft.Row([
                            ft.Text("0 km", size=11, color=TEXT_LIGHT),
                            ft.Container(expand=True),
                            ft.Text("500k+ km", size=11, color=TEXT_LIGHT),
                        ]),
                        ft.Container(height=16),
                        ft.Row([
                            ft.Container(
                                content=ft.Text("Clear", size=14, color=TEXT_LIGHT,
                                                text_align=ft.TextAlign.CENTER),
                                border=ft.border.all(1, "#d1d5db"), border_radius=10,
                                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                expand=True, on_click=clear_price, ink=True,
                            ),
                            ft.Container(
                                content=ft.Text("Apply", size=14, color="white",
                                                weight=ft.FontWeight.W_600,
                                                text_align=ft.TextAlign.CENTER),
                                bgcolor=PRIMARY, border_radius=10,
                                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                expand=True, on_click=apply_filters, ink=True,
                            ),
                        ], spacing=12),
                    ], spacing=8),
                    padding=ft.padding.symmetric(horizontal=20, vertical=16),
                ),
                ft.Container(height=20),
            ], spacing=0),
            bgcolor=CARD_BG,
        ),
        open=False,
    )
    page.overlay.append(bs_price)

    # ── CLEAR ALL ────────────────────────────────────────────
    def clear_all_filters():
        filter_ref["type"]    = ""; sort_ref["val"]  = "default"
        rental_ref["val"]     = None
        price_ref["max"]      = None; mileage_ref["max"]  = None
        sort_label.value      = "Default"
        price_slider.value    = 10000000; price_display.value   = "No limit"
        mileage_slider.value  = 500000;   mileage_display.value = "No limit"
        search_f.value        = ""
        build_chips(); build_toggle()
        page.run_task(load)
        page.update()

    # ── RENDER VEHICLES ───────────────────────────────────────
    def render_vehicles():
        col.controls.clear()
        vehicles = list(all_vehicles["data"])

        # Filter by type
        if filter_ref["type"]:
            vehicles = [v for v in vehicles
                        if v.get("type_of_vehicle","").lower() == filter_ref["type"].lower()]

        # Filter by rental/sale toggle
        if rental_ref["val"] is True:
            vehicles = [v for v in vehicles if v.get("is_rental")]
        elif rental_ref["val"] is False:
            vehicles = [v for v in vehicles if not v.get("is_rental")]

        # Filter by price
        if price_ref["max"] is not None:
            vehicles = [v for v in vehicles
                        if float(v.get("price", 0)) <= price_ref["max"]]

        # Filter by mileage
        if mileage_ref["max"] is not None:
            vehicles = [v for v in vehicles
                        if int(v.get("mileage", 0)) <= mileage_ref["max"]]

        # Sort
        s = sort_ref["val"]
        if s == "price_asc":    vehicles.sort(key=lambda v: float(v.get("price", 0)))
        elif s == "price_desc": vehicles.sort(key=lambda v: float(v.get("price", 0)), reverse=True)
        elif s == "year_desc":  vehicles.sort(key=lambda v: int(v.get("year", 0)), reverse=True)
        elif s == "year_asc":   vehicles.sort(key=lambda v: int(v.get("year", 0)))

        # Update result count
        result_count.value = f"{len(vehicles)} vehicle(s)"

        # No results
        if not vehicles:
            col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=64, color="#c7d2fe"),
                        ft.Text("No vehicles found", size=18,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text("Try adjusting your search or filters",
                                size=13, color=TEXT_LIGHT,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Text("Clear filters", size=13, color=PRIMARY,
                                            weight=ft.FontWeight.W_600,
                                            text_align=ft.TextAlign.CENTER),
                            border=ft.border.all(1.5, PRIMARY), border_radius=10,
                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            on_click=lambda e: clear_all_filters(), ink=True,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=ft.padding.symmetric(vertical=40), alignment=CENTER,
                )
            )
        else:
            for v in vehicles:
                def make_tap(veh):
                    def tap(e): APP_STATE["sv"] = veh; go_to("detail")
                    return tap

                def make_save(veh):
                    def do(e, card: VehicleCard):
                        if not api.token: go_to("login"); return
                        async def run():
                            try:
                                r = await async_toggle_save(veh["id"])
                                if r.get("saved"): saved_ids.add(veh["id"])
                                else: saved_ids.discard(veh["id"])
                                card.toggle_saved()
                            except: pass
                        page.run_task(run)
                    return do

                col.controls.append(
                    VehicleCard(
                        vehicle=v,
                        on_tap=make_tap(v),
                        on_save=make_save(v),
                        saved=(v["id"] in saved_ids),
                    )
                )

    # ── ASYNC LOAD ────────────────────────────────────────────
    async def load(e=None):
        nonlocal saved_ids
        spin.visible = True; status.value = ""; page.update()
        try:
            if api.token:
                try: saved_ids = {s["vehicle"]["id"] for s in await fetch_saved()}
                except: saved_ids = set()
            vehicles = await fetch_vehicles(search=search_f.value)
            all_vehicles["data"] = vehicles
            spin.visible = False
            render_vehicles()
        except Exception:
            spin.visible = False
            status.value = "Connection error. Is Django running?"
        page.update()

    # ── ASYNC LOAD STATS + SPOTLIGHT ─────────────────────────
    async def load_stats():
        try:
            all_v = await fetch_vehicles()
            for _, val in TYPE_OPTS:
                if val:
                    type_counts[val] = len([
                        v for v in all_v if v.get("type_of_vehicle","") == val
                    ])
            build_chips()

            if all_v:
                v       = all_v[0]
                images  = v.get("images", [])
                img_url = images[0]["image"] if images else None

                def spot_tap(e, veh=v):
                    APP_STATE["sv"] = veh; go_to("detail")

                featured_spin.visible = False
                spotlight.visible     = True
                spotlight.content     = ft.GestureDetector(
                    on_tap=spot_tap,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Stack([
                                ft.Container(
                                    content=ft.Image(src=img_url, fit=ft.BoxFit.COVER)
                                            if img_url else
                                            ft.Icon(ft.Icons.DIRECTIONS_CAR,
                                                    color="#c7d2fe", size=48),
                                    height=200, bgcolor="#eef2ff",
                                    width=float("inf"),
                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    alignment=CENTER,
                                ),
                                ft.Container(
                                    content=ft.Text("NEW", size=11, color="white",
                                                    weight=ft.FontWeight.W_700),
                                    bgcolor=ACCENT,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=99,
                                    margin=ft.margin.only(left=12, top=12),
                                ),
                                ft.Container(
                                    gradient=ft.LinearGradient(
                                        begin=ft.alignment.Alignment(0, 0.2),
                                        end=ft.alignment.Alignment(0, 1),
                                        colors=["#00000000", "#cc000000"],
                                    ),
                                    height=200,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        f"Rs {int(v['price']):,}" +
                                        ("  /mo" if v['is_rental'] else ""),
                                        size=18, weight=ft.FontWeight.BOLD, color="white",
                                    ),
                                    alignment=ft.alignment.Alignment(-1, 1),
                                    padding=ft.padding.only(left=14, bottom=12),
                                    height=200,
                                ),
                            ]),
                            ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(f"{v['make']} {v['model']}", size=16,
                                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                        ft.Text(
                                            f"{v['year']}  ·  {v['type_of_vehicle']}  ·  {v['fuel_type']}",
                                            size=12, color=TEXT_LIGHT,
                                        ),
                                    ], expand=True, spacing=3),
                                    ft.Container(
                                        content=ft.Text(
                                            "Rent" if v['is_rental'] else "Sale",
                                            size=11, color="white",
                                            weight=ft.FontWeight.W_700,
                                        ),
                                        bgcolor=PRIMARY if v['is_rental'] else SUCCESS,
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        border_radius=99,
                                    ),
                                ]),
                                padding=ft.padding.all(14),
                            ),
                        ], spacing=0),
                        bgcolor=CARD_BG, border_radius=16,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        shadow=ft.BoxShadow(blur_radius=16, color="#14000000",
                                            offset=ft.Offset(0, 4)),
                    ),
                )
        except:
            featured_spin.visible = False
        page.update()

    # ── LIVE SEARCH ───────────────────────────────────────────
    def on_search_change(e):
        page.run_task(load)
    search_f.on_change = on_search_change

    # ── INITIAL LOAD ──────────────────────────────────────────
    async def init():
        await asyncio.gather(load(), load_stats())
    page.run_task(init)

    # ── GREETING ──────────────────────────────────────────────
    first_name = api.user_name.split()[0] if api.user_name else None
    greeting   = f"Hey, {first_name} 👋" if first_name else "AutoLink"
    subtext    = "What are you looking for today?" if first_name else "Find your perfect vehicle"

    def do_logout(e):
        api.logout(); go_to("login")

    # ── VIEW ──────────────────────────────────────────────────
    return ft.View(
        route="/home", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        navigation_bar=nav("home", go_to),
        controls=[

            # GRADIENT HEADER
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(greeting, size=22,
                                    weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text(subtext, size=13, color="#b3ffffff"),
                        ], expand=True, spacing=2),
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.LOGOUT if api.token else ft.Icons.LOGIN,
                                color="white", size=20,
                            ),
                            on_click=do_logout if api.token else lambda e: go_to("login"),
                            padding=8, border_radius=99, bgcolor="#26ffffff",
                        ),
                    ]),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Row([search_f]),
                        bgcolor=CARD_BG, border_radius=14,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        shadow=ft.BoxShadow(blur_radius=16, color="#26000000",
                                            offset=ft.Offset(0, 4)),
                    ),
                ], spacing=0),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.Alignment(-1, -1),
                    end=ft.alignment.Alignment(1, 1),
                    colors=["#0a0f2e", "#1a237e", "#3949ab"],
                ),
                padding=ft.padding.only(left=20, right=20, top=52, bottom=24),
                border_radius=ft.border_radius.only(bottom_left=28, bottom_right=28),
            ),

            # FOR SALE / FOR RENT TOGGLE
            ft.Container(
                content=toggle_row,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),

            # FILTER CHIPS
            ft.Container(
                content=ft.Column([
                    ft.Text("Browse by type", size=13,
                            weight=ft.FontWeight.W_600, color=TEXT_LIGHT),
                    ft.Container(height=6),
                    chips_row,
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=16, vertical=4),
            ),

            # SORT + FILTER BAR
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SORT, color=PRIMARY, size=16),
                            ft.Text("Sort: ", size=12, color=TEXT_LIGHT),
                            sort_label,
                        ], spacing=4),
                        on_click=lambda e: (setattr(bs_sort, 'open', True), page.update()),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border=ft.border.all(1, "#d1d5db"),
                        border_radius=10, ink=True, bgcolor=CARD_BG,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TUNE, color=PRIMARY, size=16),
                            ft.Text("Filters", size=12, color=PRIMARY,
                                    weight=ft.FontWeight.W_600),
                        ], spacing=4),
                        on_click=lambda e: (setattr(bs_price, 'open', True), page.update()),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border=ft.border.all(1.5, PRIMARY),
                        border_radius=10, ink=True, bgcolor="#eef2ff",
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=16, vertical=4),
            ),

            # RECENTLY ADDED SPOTLIGHT
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Recently Added", size=16,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                        ft.Row([featured_spin]),
                    ]),
                    ft.Container(height=8),
                    spotlight,
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=16, vertical=4),
            ),

            # ALL VEHICLES
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("All Vehicles", size=18,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        result_count,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    ft.Row([spin], alignment=ft.MainAxisAlignment.CENTER),
                    status, col,
                    ft.Container(height=24),

                    # ── CONTACT SUPPORT LINK ──────────────────
                    ft.Row([
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.HEADSET_MIC, size=16, color=PRIMARY),
                                ft.Text("Contact Support", size=13, color=PRIMARY),
                            ], spacing=6),
                            on_click=lambda e: go_to("support"),
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),

                    ft.Container(height=16),
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=16),
            ),
        ]
    )