from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Vehicle
from Profile.models import SavedVehicle
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import VehicleSerializer


def standardsearch(request):
    vehicles = Vehicle.objects.filter(is_sold=False, is_rented=False).order_by('id')
    paginator = Paginator(vehicles, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    saved_vehicle_ids = []
    if request.user.is_authenticated:
        saved_vehicle_ids = list(SavedVehicle.objects.filter(
            user=request.user, vehicle__is_sold=False
        ).values_list('vehicle_id', flat=True))

    context = {
        'page_obj': page_obj,
        'all_vehicles': vehicles,
        'saved_vehicle_ids': saved_vehicle_ids
    }
    return render(request, 'standardsearch.html', context)


def filter(request):
    return render(request, 'filter.html')


def detail(request, pk):
    vehicle_detail = get_object_or_404(
        Vehicle.objects.prefetch_related('images'),
        pk=pk, is_sold=False, is_rented=False
    )

    saved_vehicle_ids = []
    if request.user.is_authenticated:
        saved_vehicle_ids = list(SavedVehicle.objects.filter(
            user=request.user
        ).values_list('vehicle_id', flat=True))

    return render(request, 'detail.html', {
        'vehicle': vehicle_detail,
        'saved_vehicle_ids': saved_vehicle_ids
    })


def vehicle_detail_api(request, pk):
    """
    JSON endpoint for a single vehicle — used by the detail page AJAX call.
    URL: /api/vehicles/<pk>/
    Returns all fields needed by the frontend including images and GPS.
    """
    vehicle = get_object_or_404(
        Vehicle.objects.prefetch_related('images'),
        pk=pk, is_sold=False, is_rented=False
    )

    images = [
        {"image": request.build_absolute_uri(img.image.url)}
        for img in vehicle.images.all()
    ]

    data = {
        "id": vehicle.id,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "fuel_type": vehicle.fuel_type,
        "transmission": vehicle.transmission,
        "mileage": vehicle.mileage,
        "price": str(vehicle.price),
        "is_rental": vehicle.is_rental,
        "desc": vehicle.desc,
        "contact": vehicle.contact,
        "gps_coor": vehicle.gps_coor,
        "uploader": vehicle.uploader.username if vehicle.uploader else "",
        "images": images,
    }

    return JsonResponse(data)


def category_list(request, category):
    normalized = category.strip().lower()
    aliases = {
        'car': 'Car',
        'motorbike': 'Motorbike',
        'bus': 'Bus',
        'truck': 'Truck',
    }
    label = aliases.get(normalized, category.title())

    vehicles = Vehicle.objects.filter(
        type_of_vehicle__iexact=label, is_sold=False, is_rented=False
    ).order_by('id')

    paginator = Paginator(vehicles, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    saved_vehicle_ids = []
    if request.user.is_authenticated:
        saved_vehicle_ids = list(
            SavedVehicle.objects.filter(
                user=request.user,
                vehicle__is_sold=False
            ).values_list('vehicle_id', flat=True)
        )

    context = {
        'category_label': label,
        'page_obj': page_obj,
        'all_vehicles': vehicles,
        'saved_vehicle_ids': saved_vehicle_ids,
        'count': vehicles.count(),
    }

    return render(request, 'standardsearch.html', context)


class VehicleListAPI(APIView):
    def get(self, request):
        vehicles = Vehicle.objects.filter(is_sold=False, is_rented=False)
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)