# Main/urls.py
# ─────────────────────────────────────────────────────────────
# Changes made:
#   1. Added ajax_vehicle_search URL
#   2. Added ajax_contact URL
#   3. All original URLs unchanged
# ─────────────────────────────────────────────────────────────

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('',          views.index,         name='home'),
    path('faq/',      views.faq,           name='faq'),
    path('aboutus/',  views.aboutus_view,  name='aboutus'),

    # ── NEW AJAX endpoints ────────────────────────────────────
    # Called by jQuery $.ajax() — return JSON not HTML
    path('ajax/search/',  views.ajax_vehicle_search, name='ajax_search'),
    path('ajax/contact/', views.ajax_contact,         name='ajax_contact'),
]
