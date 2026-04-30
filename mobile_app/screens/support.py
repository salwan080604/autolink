# mobile_app/screens/support.py
# ─────────────────────────────────────────────────────────────
# Contact / Support screen
# Demonstrates: consuming the /api/contact/ REST API from Flet
#   - User fills in the form
#   - Flet calls api.contact_support(data) which does a POST
#     to the Django REST endpoint with a JSON body
#   - The raw JSON response is shown on screen (JSON consumption)
# ─────────────────────────────────────────────────────────────

import flet as ft
import threading
from shared import api, big_btn, field, section, nav
from shared import PRIMARY, ACCENT, BG, CARD_BG, TEXT_DARK, TEXT_LIGHT, SUCCESS, ERROR, CENTER


def support_screen(page: ft.Page, go_to):

    # ── Form fields ──────────────────────────────────────────
    name_field    = field("Full Name",    icon=ft.Icons.PERSON)
    email_field   = field("Email",        icon=ft.Icons.EMAIL,
                          keyboard=ft.KeyboardType.EMAIL)
    subject_field = field("Subject",      icon=ft.Icons.TITLE)
    message_field = ft.TextField(
        label="Message",
        multiline=True,
        min_lines=4,
        max_lines=6,
        border_color=PRIMARY,
        focused_border_color=ACCENT,
    )

    # Inquiry type dropdown
    inquiry_dd = ft.Dropdown(
        label="Inquiry Type",
        border_color=PRIMARY,
        focused_border_color=ACCENT,
        options=[
            ft.dropdown.Option("general",   "General Question"),
            ft.dropdown.Option("technical", "Technical Support"),
            ft.dropdown.Option("listing",   "Listing Assistance"),
            ft.dropdown.Option("account",   "Account Help"),
            ft.dropdown.Option("feature",   "Feature Request"),
            ft.dropdown.Option("other",     "Other"),
        ],
        value="general",
    )

    # Status message shown after submit
    status_msg = ft.Container(visible=False)

    # Raw JSON response box — shows JSON consumption in action
    json_box = ft.Container(
        visible=False,
        bgcolor="#1e1e1e",
        border_radius=10,
        padding=ft.padding.all(14),
        content=ft.Column(spacing=6, controls=[
            ft.Row(controls=[
                ft.Text("JSON Response", color=ACCENT,
                        size=13, weight=ft.FontWeight.BOLD),
                ft.Text("from /api/contact/", color=TEXT_LIGHT, size=11),
            ]),
            ft.Divider(color="#374151", height=1),
        ])
    )
    json_text = ft.Text(
        "",
        color="#a5f3fc",
        size=12,
        font_family="monospace",
        selectable=True,
        no_wrap=False,
    )

    submit_btn = ft.ElevatedButton(
        "Send Message",
        icon=ft.Icons.SEND,
        bgcolor=PRIMARY,
        color="white",
        width=float("inf"),
        expand=True,
    )

    # ── Submit handler ───────────────────────────────────────
    def on_submit(e):
        # Basic validation
        if not name_field.value or not name_field.value.strip():
            _show_error("Please enter your full name.")
            return
        if not email_field.value or "@" not in email_field.value:
            _show_error("Please enter a valid email address.")
            return
        if not subject_field.value or not subject_field.value.strip():
            _show_error("Please enter a subject.")
            return
        if not message_field.value or len(message_field.value.strip()) < 10:
            _show_error("Message must be at least 10 characters.")
            return

        submit_btn.disabled = True
        submit_btn.text = "Sending…"
        status_msg.visible = False
        json_box.visible = False
        page.update()

        # Build the JSON payload — this is consumed by the Django REST API
        payload = {
            "full_name":    name_field.value.strip(),
            "email":        email_field.value.strip(),
            "phone":        "",
            "inquiry_type": inquiry_dd.value or "general",
            "subject":      subject_field.value.strip(),
            "message":      message_field.value.strip(),
        }

        def do_post():
            # ── API CONSUMPTION ───────────────────────────────
            # api.contact_support() POSTs JSON to POST /api/contact/
            # Returns (status_code, response_dict)
            status_code, response = api.contact_support(payload)

            # ── JSON CONSUMPTION ──────────────────────────────
            # Format the raw JSON response for display
            import json
            raw_json = json.dumps(response, indent=2)

            if status_code == 201:
                _show_success("✅ Message sent! We'll reply within 24 hours.")
                # Clear form
                name_field.value    = ""
                email_field.value   = ""
                subject_field.value = ""
                message_field.value = ""
                inquiry_dd.value    = "general"
            else:
                err = response.get("error") or response.get("detail") or "Something went wrong."
                _show_error(f"❌ {err}")

            # Show raw JSON response on screen — demonstrates JSON consumption
            json_text.value = raw_json
            json_box.content.controls = [
                ft.Row(controls=[
                    ft.Text("JSON Response", color=ACCENT,
                            size=13, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            f"{status_code} {'Created' if status_code == 201 else 'Error'}",
                            color="white", size=11,
                        ),
                        bgcolor=SUCCESS if status_code == 201 else ERROR,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=10,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="#374151", height=1),
                json_text,
            ]
            json_box.visible = True

            submit_btn.disabled = False
            submit_btn.text = "Send Message"
            page.update()

        threading.Thread(target=do_post).start()

    def _show_success(msg):
        status_msg.bgcolor = "#dcfce7"
        status_msg.border_radius = 8
        status_msg.padding = ft.padding.all(12)
        status_msg.content = ft.Text(msg, color="#166534", size=14)
        status_msg.visible = True
        page.update()

    def _show_error(msg):
        status_msg.bgcolor = "#fef2f2"
        status_msg.border_radius = 8
        status_msg.padding = ft.padding.all(12)
        status_msg.content = ft.Text(msg, color=ERROR, size=14)
        status_msg.visible = True
        page.update()

    submit_btn.on_click = on_submit

    # ── Layout ───────────────────────────────────────────────
    return ft.View(
        route="/support",
        bgcolor=BG,
        scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Text("Contact Support", color="white"),
            bgcolor=PRIMARY,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color="white",
                on_click=lambda e: go_to("home"),
            ),
        ),
        navigation_bar=nav("home", go_to),
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.all(16),
                content=ft.Column(
                    expand=True,
                    spacing=16,
                    controls=[
                        # ── Form ─────────────────────────────────────
                        ft.Container(
                            bgcolor=CARD_BG,
                            border_radius=12,
                            padding=ft.padding.all(20),
                            content=ft.Column(spacing=14, controls=[
                                ft.Text(
                                    "We usually reply within 24 hours.",
                                    size=13, color=TEXT_LIGHT,
                                ),
                                name_field,
                                email_field,
                                inquiry_dd,
                                subject_field,
                                message_field,
                                status_msg,
                                submit_btn,
                            ])
                        ),

                        # ── JSON response box — slides in after submit ──
                        json_box,

                        ft.Container(height=30),
                    ]
                )
            )
        ]
    )
