# api/urls.py
# All REST API endpoints that the Flet mobile app will call.
# Every URL here starts with /api/ (set in the main urls.py)

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginAPI.as_view(), name='api_login'),
    path('register/', views.RegisterAPI.as_view(), name='api_register'),
    path('logout/', views.LogoutAPI.as_view(), name='api_logout'),
    path('profile/', views.ProfileAPI.as_view(), name='api_profile'),
    path('profile/update/', views.UpdateProfileAPI.as_view(), name='api_profile_update'),

    path('vehicles/', views.VehicleListAPI.as_view(), name='api_vehicles'),
    path('vehicles/nearby/', views.NearbyVehiclesAPI.as_view(), name='api_nearby'),
    path('vehicles/<int:pk>/', views.VehicleDetailAPI.as_view(), name='api_vehicle_detail'),
    path('my-vehicles/', views.MyVehiclesAPI.as_view(), name='api_my_vehicles'),
    path('vehicles/upload/', views.UploadVehicleAPI.as_view(), name='api_upload_vehicle'),
    path('vehicles/<int:pk>/update/', views.UpdateVehicleAPI.as_view(), name='api_update_vehicle'),
    path('vehicles/<int:pk>/delete/', views.DeleteVehicleAPI.as_view(), name='api_delete_vehicle'),

    path('reviews/', views.ReviewListAPI.as_view(), name='api_reviews'),
    path('reviews/submit/', views.ReviewSubmitAPI.as_view(), name='api_review_submit'),
    path('reviews/report/', views.ReviewReportAPI.as_view(), name='api_report_review'),
    path('reviews/report-vehicle/', views.VehicleReportAPI.as_view(), name='api_report_vehicle'),

    
    path('saved/sorted/', views.SavedVehiclesSortedAPI.as_view(), name='api_saved_sorted'),
    path('saved/', views.SavedVehiclesAPI.as_view(), name='api_saved'),
    path('saved/toggle/<int:vehicle_id>/', views.ToggleSaveAPI.as_view(), name='api_toggle_save'),

    path('homepage/featured/', views.FeaturedVehiclesAPI.as_view(), name='api_featured_vehicles'),
    path('homepage/stats/', views.VehicleStatsAPI.as_view(), name='api_homepage_stats'),

    # ── CONTACT MESSAGE CRUD (added by Rishab — Main app) ────────────────
    # POST   /api/contact/       → public  (anyone can submit)
    # GET    /api/contact/       → admin only (list all messages)
    # GET    /api/contact/<id>/  → admin only (retrieve one)
    # PATCH  /api/contact/<id>/  → admin only (mark resolved)
    # DELETE /api/contact/<id>/  → admin only (delete)
    path('contact/', views.ContactMessageListAPI.as_view(), name='api_contact_list'),
    path('contact/<int:pk>/', views.ContactMessageDetailAPI.as_view(), name='api_contact_detail'),
]