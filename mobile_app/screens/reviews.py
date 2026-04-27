import flet as ft
import requests
import threading
import time
import datetime

ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"
BASE_URL = "http://127.0.0.1:8000/api"

PRIMARY    = "#1a237e"
ACCENT     = "#ff6f00"
BG         = "#f5f5f5"
CARD_BG    = "#ffffff"
TEXT_DARK  = "#212121"
TEXT_LIGHT = "#757575"
SUCCESS    = "#388e3c"
ERROR      = "#c62828"
STAR_ON    = "#FFB300"
STAR_OFF   = "#e0e0e0"
LOGO_PATH  = "assets/logo copy.png"

_app_store = {}

def _load_logo_base64():
    import base64, os
    paths = [
        "assets/logo copy.png",
        "assets/logo.png",
        os.path.join(os.path.dirname(__file__), "..", "assets", "logo copy.png"),
        os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"),
    ]
    for p in paths:
        try:
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except:
            continue
    return None

LOGO_BASE64 = _load_logo_base64()
SENTIMENT_COLORS = {"positive": "#2e7d32", "neutral": "#f57c00", "negative": "#c62828"}


def _emoji(label):
    return {"positive": "😊", "neutral": "😐", "negative": "😟"}.get(label, "")

def _avatar_color(name):
    colors = ["#1565C0", "#6A1B9A", "#00695C", "#E65100", "#37474F", "#AD1457"]
    return colors[sum(ord(c) for c in (name or "?")) % len(colors)]

def _fmt_date(iso):
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return iso[:10] if iso else ""

def _sentiment(text):
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 10,
                  "system": "Reply with exactly one word: positive, neutral, or negative.",
                  "messages": [{"role": "user", "content": text}]},
            timeout=15,
        )
        label = r.json()["content"][0]["text"].strip().lower()
        return label if label in ("positive", "neutral", "negative") else "neutral"
    except Exception:
        return "neutral"

def _rating_bar(reviews):
    if not reviews:
        return ft.Container()
    total  = len(reviews)
    counts = {i: 0 for i in range(1, 6)}
    for r in reviews:
        counts[r.get("rating", 5)] += 1
    avg = sum(r.get("rating", 5) for r in reviews) / total
    bars = []
    for s in range(5, 0, -1):
        pct = counts[s] / total
        bars.append(ft.Row([
            ft.Text(f"{s}★", size=11, color=TEXT_LIGHT, width=24),
            ft.Container(
                content=ft.Container(width=max(2, int(140 * pct)), height=8, bgcolor=STAR_ON, border_radius=4),
                width=140, height=8, bgcolor=STAR_OFF, border_radius=4,
            ),
            ft.Text(str(counts[s]), size=11, color=TEXT_LIGHT, width=20),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return ft.Card(
        content=ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"{avg:.1f}", size=38, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Row([ft.Icon(ft.Icons.STAR, color=STAR_ON, size=13) for _ in range(round(avg))], spacing=1),
                    ft.Text(f"{total} reviews", size=11, color=TEXT_LIGHT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                ft.VerticalDivider(width=1, color="#e0e0e0"),
                ft.Column(bars, spacing=4),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(14),
        ), elevation=2,
    )

def _review_card(r, on_report):
    stars = ft.Row([
        ft.Icon(ft.Icons.STAR, color=STAR_ON if i < r.get("rating", 5) else STAR_OFF, size=13)
        for i in range(5)
    ], spacing=2)
    sentiment = r.get("sentiment", "")
    badge = ft.Container()
    if sentiment:
        badge = ft.Container(
            content=ft.Text(f"{_emoji(sentiment)} {sentiment.capitalize()}", size=10, color="white"),
            bgcolor=SENTIMENT_COLORS.get(sentiment, TEXT_LIGHT),
            padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=12,
        )
    loc = ft.Container()
    if r.get("location_label"):
        loc = ft.Row([
            ft.Icon(ft.Icons.LOCATION_ON, size=12, color=ACCENT),
            ft.Text(r["location_label"], size=11, color=TEXT_LIGHT),
        ], spacing=3)
    name     = r.get("author_name") or "Anonymous"
    initials = "".join(p[0].upper() for p in name.split()[:2])
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(
                        content=ft.Text(initials, size=12, color="white"),
                        bgcolor=_avatar_color(name), radius=18,
                    ),
                    ft.Column([
                        ft.Text(name, weight=ft.FontWeight.BOLD, size=14, color=TEXT_DARK),
                        ft.Text(_fmt_date(r.get("created_at", "")), size=11, color=TEXT_LIGHT),
                    ], spacing=1, expand=True),
                    badge,
                    ft.IconButton(
                        icon=ft.Icons.FLAG, icon_color=TEXT_LIGHT, icon_size=18,
                        tooltip="Report", on_click=lambda e, rv=r: on_report(rv),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                ft.Row([
                    stars,
                    ft.Text(r.get("title", ""), weight=ft.FontWeight.W_600, size=14, expand=True),
                ], spacing=8),
                ft.Text(r.get("review_text", ""), size=13, color=TEXT_LIGHT),
                loc,
            ], spacing=7),
            padding=ft.padding.all(14),
        ), elevation=2,
    )


# ── REVIEWS SCREEN ────────────────────────────────────────────

def reviews_screen(page, go_to):
    all_reviews  = []
    reviews_col  = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    summary_box  = ft.Container()
    status_text  = ft.Text("", color=TEXT_LIGHT, text_align=ft.TextAlign.CENTER)
    spinner      = ft.ProgressRing(color=PRIMARY)
    star_state   = {"value": 0}
    gps_coords   = {"lat": None, "lng": None, "label": ""}
    photo_files  = []

    # ── Geolocator — read from page.data["geo"] set by main.py ──────
    # main.py creates one Geolocator and stores it in page.data["geo"].
    # We just read it here — no duplicate creation, no overlay conflict.
    _geo = (page.data or {}).get("geo", None)

    gps_label  = ft.Text("", size=12, color=TEXT_LIGHT, italic=True)
    submit_msg = ft.Text("", text_align=ft.TextAlign.CENTER)

    title_field  = ft.TextField(label="Review Title", border_color=PRIMARY, border_radius=10, width=float("inf"))
    review_field = ft.TextField(label="Share your experience…", multiline=True, min_lines=4,
                                border_color=PRIMARY, border_radius=10, width=float("inf"))
    author_field = ft.TextField(label="Your Name", prefix_icon=ft.Icons.PERSON,
                                border_color=PRIMARY, border_radius=10, width=float("inf"))
    email_field  = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL,
                                prefix_icon=ft.Icons.EMAIL, border_color=PRIMARY, border_radius=10, width=float("inf"))

    # =========================================================
    # GESTURE FEATURES — all use ft.GestureDetector only
    # Confirmed working in Flet 0.84 on the QR viewer + web
    #
    # FEATURE 1: Horizontal drag  → swipe left/right to rate
    # FEATURE 2: Double-tap       → lock / unlock rating
    # FEATURE 3: Long press       → lock / unlock rating
    # FEATURE 4: Pinch (scale)    → pinch-out +1 star, pinch-in -1 star
    # FEATURE 5: Vertical drag    → scroll the reviews list
    # FEATURE 6: Swipe-to-report  → fast left swipe on a review card
    # =========================================================

    gesture_state = {"locked": False}
    star_row = ft.Row(spacing=2, alignment=ft.MainAxisAlignment.CENTER)

    RATING_LABELS = {
        0: ("👉 Swipe ← →  |  Pinch to rate", TEXT_LIGHT),
        1: ("😞  Poor",       "#e53935"),
        2: ("😐  Fair",       "#fb8c00"),
        3: ("🙂  Good",       "#fdd835"),
        4: ("😊  Great",      "#7cb342"),
        5: ("🤩  Excellent!", "#2e7d32"),
    }

    tilt_hint = ft.Text(
        "👉 Swipe ← →  |  Pinch to rate",
        size=12, color=TEXT_LIGHT, italic=True,
        text_align=ft.TextAlign.CENTER,
    )

    lock_indicator = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.LOCK_OPEN, color=TEXT_LIGHT, size=16),
            ft.Text("Hold or double-tap stars to lock", size=11, color=TEXT_LIGHT),
        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=20,
        bgcolor="#f0f0f0",
    )

    def build_stars():
        star_row.controls.clear()
        v = int(star_state["value"])
        for i in range(1, 6):
            filled = (i <= v) and (v > 0)
            star_row.controls.append(
                ft.Icon(
                    ft.Icons.STAR if filled else ft.Icons.STAR_BORDER,
                    color=STAR_ON if filled else STAR_OFF,
                    size=40,
                )
            )

    def update_hint():
        v = int(star_state["value"])
        if gesture_state["locked"]:
            tilt_hint.value  = f"🔒 Locked at {v} star{'s' if v != 1 else ''} — hold/double-tap to unlock"
            tilt_hint.color  = SUCCESS
            lock_indicator.content = ft.Row([
                ft.Icon(ft.Icons.LOCK, color=SUCCESS, size=16),
                ft.Text("Hold or double-tap to unlock", size=11, color=SUCCESS),
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
            lock_indicator.bgcolor = "#e8f5e9"
        else:
            label, color = RATING_LABELS.get(v, RATING_LABELS[0])
            tilt_hint.value  = label
            tilt_hint.color  = color
            lock_indicator.content = ft.Row([
                ft.Icon(ft.Icons.LOCK_OPEN, color=TEXT_LIGHT, size=16),
                ft.Text("Hold or double-tap stars to lock", size=11, color=TEXT_LIGHT),
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
            lock_indicator.bgcolor = "#f0f0f0"

    def set_star(v):
        if gesture_state["locked"]:
            return
        star_state["value"] = max(0, min(5, v))
        build_stars()
        update_hint()
        page.update()

    def toggle_lock():
        gesture_state["locked"] = not gesture_state["locked"]
        update_hint()
        page.update()

    def reset_rating(e=None):
        star_state["value"] = 0
        gesture_state["locked"] = False
        build_stars()
        update_hint()
        page.update()

    # ── FEATURE 1: Horizontal drag → swipe to rate ────────────
    drag_accum = {"x": 0.0}

    def on_drag_start(e):
        drag_accum["x"] = 0.0

    def on_drag_update(e):
        if gesture_state["locked"]:
            return
        drag_accum["x"] += e.primary_delta or 0.0
        if drag_accum["x"] > 30 and star_state["value"] < 5:
            set_star(star_state["value"] + 1)
            drag_accum["x"] = 0.0
        elif drag_accum["x"] < -30 and star_state["value"] > 0:
            set_star(star_state["value"] - 1)
            drag_accum["x"] = 0.0

    # ── FEATURE 2: Double-tap → toggle lock ───────────────────
    def on_double_tap(e):
        toggle_lock()

    # ── FEATURE 3: Long press → toggle lock ───────────────────
    def on_long_press(e):
        toggle_lock()

    # ── FEATURE 4: Pinch / Scale → adjust star rating ─────────
    # ScaleUpdateEvent.scale: >1.0 = spreading fingers, <1.0 = pinching
    # Spread fingers (pinch out) → +1 star
    # Pinch in               → -1 star
    # Threshold 0.15 prevents accidental triggers on tiny movements
    scale_state = {"last_scale": 1.0, "triggered": False}

    def on_scale_start(e):
        scale_state["last_scale"] = 1.0
        scale_state["triggered"] = False

    def on_scale_update(e):
        if gesture_state["locked"]:
            return
        current = e.scale
        diff = current - scale_state["last_scale"]
        if not scale_state["triggered"]:
            if diff > 0.15:              # spreading = more stars
                set_star(star_state["value"] + 1)
                scale_state["triggered"] = True
                scale_state["last_scale"] = current
            elif diff < -0.15:           # pinching = fewer stars
                set_star(star_state["value"] - 1)
                scale_state["triggered"] = True
                scale_state["last_scale"] = current
        # Re-arm when fingers return near neutral
        if abs(current - 1.0) < 0.05:
            scale_state["triggered"] = False
            scale_state["last_scale"] = 1.0

    # ── FEATURE 5: Vertical drag on star area → scroll reviews ─
    # Drag finger UP on star area   → scroll reviews list DOWN
    # Drag finger DOWN on star area → scroll reviews list UP
    # primary_delta is negative when dragging up
    vdrag_accum = {"y": 0.0}

    def on_vdrag_start(e):
        vdrag_accum["y"] = 0.0

    def on_vdrag_update(e):
        vdrag_accum["y"] += e.primary_delta or 0.0
        if vdrag_accum["y"] > 40:
            try:
                reviews_col.scroll_to(delta=120, duration=150)
                page.update()
            except Exception:
                pass
            vdrag_accum["y"] = 0.0
        elif vdrag_accum["y"] < -40:
            try:
                reviews_col.scroll_to(delta=-120, duration=150)
                page.update()
            except Exception:
                pass
            vdrag_accum["y"] = 0.0

    build_stars()
    update_hint()

    # NESTED GestureDetectors fix Flutter recognizer conflicts:
    #   scale + drag in one GestureDetector = scale suppresses drag
    #   long_press + drag in one GestureDetector = drag cancels long press
    # Fix: INNER = single-finger (drag, double-tap, long-press, vertical drag)
    #      OUTER = two-finger scale (pinch) only, wraps inner

    inner_gesture = ft.GestureDetector(
        content=ft.Column([
            star_row,
            ft.OutlinedButton(
                content=ft.Text("🔄 Reset Rating", color=ACCENT),
                on_click=reset_rating,
                style=ft.ButtonStyle(
                    side=ft.BorderSide(1, ACCENT),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        on_horizontal_drag_start=on_drag_start,
        on_horizontal_drag_update=on_drag_update,
        on_double_tap=on_double_tap,
        on_long_press_start=on_long_press,
        on_vertical_drag_start=on_vdrag_start,
        on_vertical_drag_update=on_vdrag_update,
    )

    star_gesture = ft.GestureDetector(
        content=inner_gesture,
        on_scale_start=on_scale_start,
        on_scale_update=on_scale_update,
    )

    # ── FEATURE 6: Swipe-to-report on review cards ────────────
    # Fast left swipe (velocity_x < -800) on any review → report screen
    # DragEndEvent.velocity_x is confirmed in Flet 0.84
    def _review_card_swipeable(r, on_report):
        card = _review_card(r, on_report)
        hint = ft.Text("", size=11, color=ERROR, italic=True,
                       text_align=ft.TextAlign.CENTER)

        def on_swipe_update(e):
            delta = e.primary_delta or 0.0
            if delta < -8:
                hint.value = "← Swipe left to report this review"
                page.update()
            elif delta > 8:
                hint.value = ""
                page.update()

        def on_swipe_end(e):
            hint.value = ""
            # -300 threshold is reliable on phone (was -800, too hard to trigger)
            if (e.velocity_x or 0) < -300:
                _app_store["report_target_review"] = r
                go_to("report_review")
            else:
                page.update()

        return ft.Column([
            ft.GestureDetector(
                content=ft.Container(content=card, width=float("inf")),
                on_horizontal_drag_update=on_swipe_update,
                on_horizontal_drag_end=on_swipe_end,
            ),
            hint,
        ], spacing=2)

    # ── Confetti success dialog ───────────────────────────────
    def show_success_dialog():
        confetti_items = ["🎉", "⭐", "🎊", "✨", "🌟", "💫", "🎈", "🏆"]
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=CARD_BG,
            content=ft.Container(
                content=ft.Column([
                    ft.Row(
                        [ft.Text(c, size=28) for c in confetti_items],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                    ),
                    ft.Container(height=8),
                    ft.Text("Review Submitted!", size=22,
                            weight=ft.FontWeight.BOLD, color=PRIMARY,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("Thank you for sharing\nyour experience! 🙏",
                            size=14, color=TEXT_LIGHT,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Row(
                        [ft.Text(c, size=28) for c in ["🎉", "🌟", "🎊", "✨", "🎈"]],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=ft.padding.all(20),
                width=280,
            ),
            actions=[
                ft.TextButton(
                    "Great! 🎉",
                    on_click=lambda e: _close_dlg(dlg),
                    style=ft.ButtonStyle(color=PRIMARY),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

        def auto_close():
            time.sleep(3)
            _close_dlg(dlg)
        threading.Thread(target=auto_close, daemon=True).start()

    def _close_dlg(dlg):
        try:
            dlg.open = False
            if dlg in page.overlay:
                page.overlay.remove(dlg)
            page.update()
        except Exception:
            pass

    # ── Render reviews ────────────────────────────────────────
    def render_reviews(reviews):
        reviews_col.controls.clear()
        if not reviews:
            reviews_col.controls.append(
                ft.Text("No reviews yet. Be the first!", color=TEXT_LIGHT,
                        text_align=ft.TextAlign.CENTER)
            )
        for r in reviews:
            def on_report(rv):
                _app_store["report_target_review"] = rv
                go_to("report_review")
            reviews_col.controls.append(
                _review_card_swipeable(r, on_report=on_report)
            )
        page.update()

    def load_reviews(show_spinner=True):
        if show_spinner:
            spinner.visible = True
            page.update()
        def fetch():
            try:
                nonlocal all_reviews
                data = requests.get(f"{BASE_URL}/reviews/", timeout=10).json()
                all_reviews = data if isinstance(data, list) else []
                spinner.visible = False
                summary_box.content = _rating_bar(all_reviews)
                status_text.value = "" if all_reviews else "No reviews yet. Be the first!"
                render_reviews(all_reviews)
            except Exception as ex:
                spinner.visible = False
                status_text.value = ""
                page.update()
        threading.Thread(target=fetch).start()

    # ── Mauritius districts ───────────────────────────────────
    MAURITIUS_LOCATIONS = {
        "Port Louis":    (-20.1654, 57.4896),
        "Curepipe":      (-20.3167, 57.5167),
        "Vacoas":        (-20.2985, 57.4784),
        "Quatre Bornes": (-20.2667, 57.4667),
        "Rose Hill":     (-20.2333, 57.4667),
        "Beau Bassin":   (-20.2333, 57.4500),
        "Mahebourg":     (-20.4000, 57.7000),
        "Grand Baie":    (-19.9667, 57.5833),
        "Flic en Flac":  (-20.3000, 57.3667),
        "Tamarin":       (-20.3167, 57.3667),
        "Moka":          (-20.2333, 57.4833),
        "Ebène":         (-20.2417, 57.4833),
    }

    def get_location(e):
        gps_label.value = "📍 Requesting permission..."
        page.update()

        async def _gps():
            import flet_geolocator as ftg
            p = await _geo.request_permission()
            if p not in (
                ftg.GeolocatorPermissionStatus.ALWAYS,
                ftg.GeolocatorPermissionStatus.WHILE_IN_USE,
            ):
                gps_label.value = "⚠️ Permission denied — check phone settings"
                page.update()
                return

            gps_label.value = "📍 Getting position..."
            page.update()

            pos = await _geo.get_current_position()
            lat = pos.latitude
            lng = pos.longitude

            # Snap to nearest Mauritius district
            best_label = "Unknown"
            best_dist  = float("inf")
            for name, (dlat, dlng) in MAURITIUS_LOCATIONS.items():
                dist = ((lat - dlat) ** 2 + (lng - dlng) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist  = dist
                    best_label = name

            gps_coords.update({"lat": lat, "lng": lng, "label": best_label})
            gps_label.value = f"📍 {best_label} ({lat:.4f}, {lng:.4f})"
            page.update()

        if _geo is None:
            # Web or geolocator unavailable — fall back to IP
            gps_label.value = "📍 Detecting via IP..."
            page.update()
            def _ip():
                try:
                    r       = requests.get("https://ipapi.co/json/", timeout=8).json()
                    lat     = r.get("latitude",  -20.1654)
                    lng     = r.get("longitude",  57.4896)
                    country = r.get("country_code", "")
                    city    = r.get("city", "")
                    best_label = city or "Port Louis"
                    if country == "MU" or (-21.5 < float(lat) < -19.5 and 56.5 < float(lng) < 63.5):
                        best_dist = float("inf")
                        for name, (dlat, dlng) in MAURITIUS_LOCATIONS.items():
                            dist = ((float(lat)-dlat)**2 + (float(lng)-dlng)**2)**0.5
                            if dist < best_dist:
                                best_dist  = dist
                                best_label = name
                        label = best_label
                    else:
                        label = city or r.get("country_name", "Unknown")
                    gps_coords.update({"lat": lat, "lng": lng, "label": label})
                    gps_label.value = f"📍 {label}"
                except Exception:
                    gps_label.value = "📍 Could not detect location"
                page.update()
            threading.Thread(target=_ip, daemon=True).start()
        else:
            page.run_task(_gps)
    # ── File picker ───────────────────────────────────────────
    file_picker = ft.FilePicker()

    # ── Photos display ────────────────────────────────────────
    photos_row = ft.Column(spacing=4)

    def refresh_photos():
        photos_row.controls.clear()
        if not photo_files:
            photos_row.controls.append(
                ft.Text("No photos selected", size=11, color=TEXT_LIGHT, italic=True)
            )
        else:
            for i, pf in enumerate(photo_files):
                def make_delete(i):
                    def delete(e):
                        photo_files.pop(i)
                        refresh_photos()
                        page.update()
                    return delete
                photos_row.controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.IMAGE, color=SUCCESS, size=16),
                        ft.Text(pf["name"], size=11, color=SUCCESS, expand=True,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ERROR, icon_size=18,
                            tooltip="Remove",
                            on_click=make_delete(i),
                        ),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )
        page.update()

    refresh_photos()

    def _handle_files(files):
        if files:
            for f in files:
                photo_files.append({
                    "name":  f.name,
                    "bytes": f.bytes,
                    "path":  f.path,
                })
            refresh_photos()
        page.update()

    def open_gallery(e):
        async def _pick():
            try:
                files = await file_picker.pick_files(
                    allow_multiple=True,
                    file_type=ft.FilePickerFileType.IMAGE,
                    with_data=True,
                )
                _handle_files(files)
            except Exception:
                page.update()
        page.run_task(_pick)

    # ── Camera (only on Android/iOS/Web — not on Windows desktop) ──
    # fc.Camera crashes on desktop with "only supported on Android, iOS and Web"
    # Guard: only create it when platform is mobile or web.
    import flet_camera as fc

    _cam_supported = page.web or page.platform in (
        ft.PagePlatform.ANDROID,
        ft.PagePlatform.IOS,
    )

    cam             = fc.Camera(expand=True, preview_enabled=True) if _cam_supported else None
    cam_state       = {"open": False}
    cam_preview_img = ft.Image(src="", width=80, height=80,
                               border_radius=8, visible=False,
                               fit=ft.BoxFit.COVER)
    cam_container   = ft.Container(
        content=cam,
        height=250,
        visible=False,
        border_radius=10,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    ) if _cam_supported else ft.Container()
    cam_status = ft.Text("", size=11, color=TEXT_LIGHT, italic=True)

    async def toggle_camera(e):
        if not _cam_supported:
            cam_status.value = "📷 Camera only works on phone — use Choose Photos below"
            cam_status.color = TEXT_LIGHT
            page.update()
            return

        if cam_container.visible:
            # Camera is open — take the picture
            try:
                path = await cam.take_picture()
                if path:
                    import os
                    name = os.path.basename(path)
                    photo_files.append({"name": name, "bytes": None, "path": path})
                    cam_preview_img.src     = path
                    cam_preview_img.visible = True
                    cam_container.visible   = False
                    cam_state["open"]       = False
                    cam_btn.content = ft.Row([
                        ft.Icon(ft.Icons.REPLAY, color="white", size=18),
                        ft.Text("Retake Photo", color="white", size=13),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
                    cam_status.value = "✅ Photo captured"
                    cam_status.color = SUCCESS
                    refresh_photos()
            except Exception as err:
                cam_status.value = f"Camera error: {err}"
                cam_status.color = ERROR
                page.update()
        else:
            # Open the viewfinder
            cam_container.visible = True
            cam_state["open"]     = True
            page.update()  # must update BEFORE initialize so camera is on screen
            try:
                cameras = await cam.get_available_cameras()
                if not cameras:
                    cam_status.value = "No camera found on this device"
                    cam_status.color = ERROR
                    cam_container.visible = False
                    page.update()
                    return
                await cam.initialize(
                    description=cameras[0],
                    resolution_preset=fc.ResolutionPreset.HIGH,
                    enable_audio=False,   # no mic permission needed for photo capture
                )
                cam_btn.content = ft.Row([
                    ft.Icon(ft.Icons.CAMERA, color="white", size=18),
                    ft.Text("Snap Photo!", color="white", size=13),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
                cam_status.value = "📷 Point and tap Snap Photo!"
                cam_status.color = TEXT_LIGHT
                page.update()
            except Exception as err:
                cam_status.value = f"Could not start camera: {err}"
                cam_status.color = ERROR
                cam_container.visible = False
                page.update()

    cam_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.CAMERA_ALT, color="white", size=18),
            ft.Text("Take Photo", color="white", size=13),
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ACCENT,
        on_click=lambda e: page.run_task(toggle_camera, e),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        width=float("inf"),
    )

    camera_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.PHOTO_LIBRARY, color="white", size=18),
            ft.Text("Choose Photos", color="white", size=13),
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=PRIMARY,
        on_click=open_gallery,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        width=float("inf"),
    )

    submit_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.RATE_REVIEW, color="white", size=18),
            ft.Text("Submit Review", color="white", size=14),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=PRIMARY, width=float("inf"), height=46,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    def do_submit(e):
        if not all([title_field.value, review_field.value, author_field.value, email_field.value]):
            submit_msg.value = "⚠️ Fill in all fields."
            submit_msg.color = ERROR
            page.update()
            return
        submit_btn.disabled = True
        submit_btn.content = ft.Row([
            ft.ProgressRing(width=18, height=18, stroke_width=2, color="white"),
            ft.Text("Submitting…", color="white", size=14),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        submit_msg.value = ""
        page.update()
        def post():
            try:
                label   = _sentiment(review_field.value)
                payload = {
                    "title":          title_field.value,
                    "review_text":    review_field.value,
                    "rating":         star_state["value"],
                    "author_name":    author_field.value,
                    "email":          email_field.value,
                    "sentiment":      label,
                    "location_label": gps_coords.get("label", ""),
                    "latitude":       gps_coords.get("lat"),
                    "longitude":      gps_coords.get("lng"),
                }
                if photo_files:
                    files_payload = [
                        ("photos", (pf["name"], pf["bytes"], "image/jpeg"))
                        for pf in photo_files if pf.get("bytes")
                    ]
                    resp = requests.post(
                        f"{BASE_URL}/reviews/submit/", data=payload,
                        files=files_payload if files_payload else None,
                        timeout=15,
                    )
                else:
                    resp = requests.post(f"{BASE_URL}/reviews/submit/", json=payload, timeout=15)

                if resp.status_code == 201:
                    new_review = {
                        "title":          payload["title"],
                        "review_text":    payload["review_text"],
                        "rating":         payload["rating"],
                        "author_name":    payload["author_name"],
                        "sentiment":      payload["sentiment"],
                        "location_label": payload.get("location_label", ""),
                        "created_at":     datetime.datetime.now().isoformat(),
                    }
                    all_reviews.insert(0, new_review)
                    summary_box.content = _rating_bar(all_reviews)
                    render_reviews(all_reviews)
                    title_field.value = review_field.value = author_field.value = email_field.value = ""
                    star_state["value"] = 0
                    gesture_state["locked"] = False
                    build_stars()
                    update_hint()
                    gps_coords.update({"lat": None, "lng": None, "label": ""})
                    gps_label.value = ""
                    photo_files.clear()
                    refresh_photos()
                    submit_msg.value = "👇 Scroll down to see your review"
                    submit_msg.color = SUCCESS
                    page.update()
                    show_success_dialog()
                    load_reviews(show_spinner=False)
                    def do_scroll():
                        time.sleep(1.5)
                        status_text.value = "👇 Scroll down to see your review"
                        status_text.color = SUCCESS
                        page.update()
                        time.sleep(3)
                        status_text.value = ""
                        page.update()
                    threading.Thread(target=do_scroll, daemon=True).start()
                else:
                    submit_msg.color = ERROR
                    submit_msg.value = str(resp.json())
            except Exception as ex:
                submit_msg.color = ERROR
                submit_msg.value = f"Error: {ex}"
            finally:
                submit_btn.disabled = False
                submit_btn.content = ft.Row([
                    ft.Icon(ft.Icons.RATE_REVIEW, color="white", size=18),
                    ft.Text("Submit Review", color="white", size=14),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
                page.update()
        threading.Thread(target=post).start()

    submit_btn.on_click = do_submit

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME,        label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.LOCATION_ON, label="Nearby"),
            ft.NavigationBarDestination(icon=ft.Icons.BOOKMARK,    label="Saved"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR,        label="Reviews"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON,      label="Profile"),
        ],
        selected_index=3, bgcolor=CARD_BG,
        on_change=lambda e: go_to(
            ["home", "nearby", "saved", "reviews", "profile"][e.control.selected_index]
        ),
    )

    load_reviews()

    return ft.View(
        route="/reviews", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Row([
                ft.Icon(ft.Icons.STAR, color=STAR_ON),
                ft.Text("Reviews", color="white", weight=ft.FontWeight.BOLD),
            ]),
            bgcolor=PRIMARY,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.FLAG, icon_color="white", tooltip="Report vehicle",
                    on_click=lambda e: go_to("report_vehicle"),
                )
            ],
        ),
        navigation_bar=nav,
        controls=[
            ft.Container(
                content=ft.Column([
                    summary_box,

                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.EDIT, color=PRIMARY),
                                ft.Text("Write a Review", size=18,
                                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                            ft.Divider(height=1, color="#e0e0e0"),
                            ft.Text("Your Rating", size=13, color=TEXT_LIGHT,
                                    text_align=ft.TextAlign.CENTER),
                            star_gesture,
                            tilt_hint,
                            lock_indicator,
                            title_field,
                            review_field,
                            author_field,
                            email_field,
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_ON, color="white", size=18),
                                    ft.Text("Detect Location", color="white", size=13),
                                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                bgcolor=ACCENT,
                                on_click=get_location,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                width=float("inf"),
                            ),
                            gps_label,
                            cam_btn,
                            cam_container,
                            cam_preview_img,
                            cam_status,
                            camera_btn,
                            photos_row,
                            submit_msg,
                            submit_btn,
                        ], spacing=10),
                        padding=ft.padding.all(16),
                        bgcolor=CARD_BG,
                        border_radius=16,
                        shadow=ft.BoxShadow(blur_radius=8, color="#00000014"),
                    ),
                    ft.Container(height=8),
                    spinner,
                    status_text,
                    reviews_col,

                ], spacing=14),
                padding=ft.padding.all(16),
            )
        ],
    )


# ── REPORT REVIEW SCREEN ──────────────────────────────────────

def report_screen_for_review(page, go_to):
    review  = _app_store.get("report_target_review", {})
    reasons = [
        ("spam",       "🚫 Spam / Fake"),
        ("offensive",  "😡 Offensive"),
        ("irrelevant", "🤔 Not relevant"),
        ("misleading", "⚠️ Misleading"),
        ("other",      "📝 Other"),
    ]
    selected    = {"value": None}
    reason_btns = []
    details     = ft.TextField(label="Details (optional)", multiline=True, min_lines=3,
                               border_color=PRIMARY, border_radius=10, width=float("inf"))
    msg         = ft.Text("", text_align=ft.TextAlign.CENTER)
    submit_btn  = ft.ElevatedButton(
        content=ft.Text("Submit Report", color="white"),
        bgcolor=ERROR, width=float("inf"), height=46, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    reason_col = ft.Column(spacing=8)
    for key, lbl in reasons:
        b = ft.ElevatedButton(
            content=ft.Text(lbl, color=TEXT_DARK), bgcolor=CARD_BG, data=key,
            width=float("inf"),
            style=ft.ButtonStyle(side=ft.BorderSide(1, "#e0e0e0"),
                                 shape=ft.RoundedRectangleBorder(radius=10)),
        )
        b.data_label = lbl
        def make_click(k, l):
            def click(e):
                selected["value"] = k
                for btn in reason_btns:
                    active      = btn.data == k
                    btn.bgcolor = PRIMARY if active else CARD_BG
                    btn.content = ft.Text(btn.data_label, color="white" if active else TEXT_DARK)
                submit_btn.disabled = False
                page.update()
            return click
        b.on_click = make_click(key, lbl)
        reason_btns.append(b)
        reason_col.controls.append(b)

    def do_report(e):
        if not selected["value"]:
            msg.value = "⚠️ Please select a reason first."
            msg.color = ERROR
            page.update()
            return
        submit_btn.disabled = True
        submit_btn.content = ft.Row([
            ft.ProgressRing(width=18, height=18, stroke_width=2, color="white"),
            ft.Text("Submitting…", color="white", size=14),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        msg.value = ""
        page.update()
        def post():
            try:
                resp = requests.post(f"{BASE_URL}/reviews/report/", json={
                    "review_id": review.get("id"),
                    "reason":    selected["value"],
                    "details":   details.value,
                }, timeout=10)
                if resp.status_code in (200, 201):
                    msg.color = SUCCESS
                    msg.value = "✅ Report submitted! Thank you for helping keep AutoLink safe."
                    submit_btn.content = ft.Text("Submit Report", color="white")
                    submit_btn.disabled = False
                    page.update()
                    time.sleep(2)
                    go_to("reviews")
                else:
                    msg.color = ERROR
                    msg.value = f"Could not submit. Status: {resp.status_code}"
                    submit_btn.content = ft.Text("Submit Report", color="white")
                    submit_btn.disabled = False
                    page.update()
            except Exception as ex:
                msg.color = ERROR
                msg.value = f"Error: {ex}"
                submit_btn.content = ft.Text("Submit Report", color="white")
                submit_btn.disabled = False
                page.update()
        threading.Thread(target=post).start()
    submit_btn.on_click = do_report

    body    = review.get("review_text", "")
    preview = ft.Container(
        content=ft.Column([
            ft.Text("Reporting:", size=12, color=TEXT_LIGHT),
            ft.Container(
                content=ft.Column([
                    ft.Text(review.get("title", ""), weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(body[:100] + "…" if len(body) > 100 else body, size=12, color=TEXT_LIGHT),
                    ft.Text(f"— {review.get('author_name', '')}", size=11, color=ACCENT, italic=True),
                ], spacing=4),
                padding=ft.padding.all(10), bgcolor="#fff8e1", border_radius=8,
            ),
        ], spacing=4),
    ) if review else ft.Container()

    return ft.View(
        route="/report_review", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Text("Report Review", color="white"), bgcolor=ERROR,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="white",
                                  on_click=lambda e: go_to("reviews")),
        ),
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FLAG, color=ERROR, size=26),
                        ft.Column([
                            ft.Text("Report Content", size=18,
                                    weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text("Help keep AutoLink safe", size=12, color=TEXT_LIGHT),
                        ], spacing=2),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    preview,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Why are you reporting?", size=14,
                                    weight=ft.FontWeight.W_600, color=TEXT_DARK,
                                    text_align=ft.TextAlign.CENTER),
                            reason_col,
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                        padding=ft.padding.all(14), bgcolor=CARD_BG, border_radius=12,
                        shadow=ft.BoxShadow(blur_radius=6, color="#00000012"),
                    ),
                    details,
                    msg,
                    submit_btn,
                    ft.Container(height=16),
                ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                padding=ft.padding.all(16),
            )
        ],
    )


# ── REPORT VEHICLE SCREEN ─────────────────────────────────────

def report_vehicle_screen(page, go_to):
    vehicle_field = ft.TextField(
        label="Vehicle ID or Title", prefix_icon=ft.Icons.DIRECTIONS_CAR,
        border_color=PRIMARY, border_radius=10, width=float("inf"),
    )
    reasons = [
        ("fraud",       "💸 Fraudulent listing"),
        ("wrong_info",  "📋 Incorrect info"),
        ("stolen",      "🚨 Stolen vehicle"),
        ("unavailable", "❌ Already sold"),
        ("other",       "📝 Other"),
    ]
    selected    = {"value": None}
    reason_btns = []
    details     = ft.TextField(label="Describe the issue", multiline=True, min_lines=3,
                               border_color=PRIMARY, border_radius=10, width=float("inf"))
    msg         = ft.Text("", text_align=ft.TextAlign.CENTER)
    submit_btn  = ft.ElevatedButton(
        content=ft.Text("Submit Report", color="white"),
        bgcolor=ERROR, width=float("inf"), height=46, disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    reason_col = ft.Column(spacing=8)
    for key, lbl in reasons:
        b = ft.ElevatedButton(
            content=ft.Text(lbl, color=TEXT_DARK), bgcolor=CARD_BG, data=key,
            width=float("inf"),
            style=ft.ButtonStyle(side=ft.BorderSide(1, "#e0e0e0"),
                                 shape=ft.RoundedRectangleBorder(radius=10)),
        )
        b.data_label = lbl
        def make_click(k):
            def click(e):
                selected["value"] = k
                for btn in reason_btns:
                    active      = btn.data == k
                    btn.bgcolor = PRIMARY if active else CARD_BG
                    btn.content = ft.Text(btn.data_label, color="white" if active else TEXT_DARK)
                submit_btn.disabled = False
                page.update()
            return click
        b.on_click = make_click(key)
        reason_btns.append(b)
        reason_col.controls.append(b)

    def do_report(e):
        if not selected["value"]:
            msg.value = "⚠️ Please select a reason first."
            msg.color = ERROR
            page.update()
            return
        submit_btn.disabled = True
        submit_btn.content = ft.Row([
            ft.ProgressRing(width=18, height=18, stroke_width=2, color="white"),
            ft.Text("Submitting…", color="white", size=14),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        msg.value = ""
        page.update()
        def post():
            try:
                resp = requests.post(f"{BASE_URL}/reviews/report-vehicle/", json={
                    "vehicle_ref": vehicle_field.value,
                    "reason":      selected["value"],
                    "details":     details.value,
                }, timeout=10)
                if resp.status_code in (200, 201):
                    msg.color = SUCCESS
                    msg.value = "✅ Report submitted! Thank you for helping keep AutoLink safe."
                    submit_btn.content = ft.Text("Submit Report", color="white")
                    submit_btn.disabled = False
                    page.update()
                    time.sleep(2)
                    go_to("home")
                else:
                    msg.color = ERROR
                    msg.value = f"Could not submit. Status: {resp.status_code}"
                    submit_btn.content = ft.Text("Submit Report", color="white")
                    submit_btn.disabled = False
                    page.update()
            except Exception as ex:
                msg.color = ERROR
                msg.value = f"Error: {ex}"
                submit_btn.content = ft.Text("Submit Report", color="white")
                submit_btn.disabled = False
                page.update()
        threading.Thread(target=post).start()
    submit_btn.on_click = do_report

    return ft.View(
        route="/report_vehicle", bgcolor=BG, scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Text("Report Vehicle", color="white"), bgcolor=ERROR,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="white",
                                  on_click=lambda e: go_to("home")),
        ),
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.REPORT_PROBLEM, color=ERROR, size=26),
                        ft.Column([
                            ft.Text("Report a Vehicle", size=18,
                                    weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text("Help remove bad listings", size=12, color=TEXT_LIGHT),
                        ], spacing=2),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    vehicle_field,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("What's the issue?", size=14,
                                    weight=ft.FontWeight.W_600, color=TEXT_DARK,
                                    text_align=ft.TextAlign.CENTER),
                            reason_col,
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                        padding=ft.padding.all(14), bgcolor=CARD_BG, border_radius=12,
                        shadow=ft.BoxShadow(blur_radius=6, color="#00000012"),
                    ),
                    details,
                    msg,
                    submit_btn,
                    ft.Container(height=16),
                ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                padding=ft.padding.all(16),
            )
        ],
    )