# api/views.py
# These are the API endpoints that the Flet mobile app will call.
# Each view handles a specific URL and returns JSON data.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.db.models import Q
import math

from Vehicles.models import Vehicle, VehicleImage
from Reviews.models import Review, Report
from Profile.models import SavedVehicle
from Users.models import UserProfile

from .serializers import (
    VehicleSerializer,
    ReviewSerializer,
    ReviewSubmitSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    SavedVehicleSerializer,
)


# ============================================================
# AUTH ENDPOINTS
# ============================================================

class LoginAPI(APIView):
    """
    POST /api/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "token": "...", "user_type": "...", "name": "..." }
    """
    def post(self, request):
        email    = request.data.get('email')
        password = request.data.get('password')


        from django.contrib.auth.models import User
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(request, username=user_obj.username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        try:
            profile   = UserProfile.objects.get(user=user)
            user_type = profile.user_type
        except UserProfile.DoesNotExist:
            user_type = 'buyer'

        return Response({
            'token':     token.key,
            'user_type': user_type,
            'name':      user.get_full_name() or user.username,
            'email':     user.email,
        })


class RegisterAPI(APIView):

    """
    POST /api/register/
    Body: { "first_name", "last_name", "email", "password",
            "user_type", "address", "contact_number", "driver_license" }
    Returns: { "token": "...", "message": "..." }
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user    = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token':   token.key,
                'message': 'Account created successfully!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPI(APIView):

    """
    POST /api/logout/
    Header: Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'})
    
class MyVehiclesAPI(APIView):
    """
    GET /api/my-vehicles/
    Returns all vehicles uploaded by the logged-in seller/renter.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vehicles = Vehicle.objects.filter(
            uploader=request.user
        ).prefetch_related('images').order_by('-id')
        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        return Response(serializer.data)


class UploadVehicleAPI(APIView):
    """
    POST /api/vehicles/upload/
    Header: Authorization: Token <token>
    Body (multipart/form-data):
        make, model, year, mileage, transmission, fuel_type,
        type_of_vehicle, price, gps_coor, is_rental, desc, contact
    Creates a new vehicle listing for the logged-in seller/renter.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found.'}, status=400)

        if profile.user_type not in ['seller', 'renter']:
            return Response({'error': 'Only sellers and renters can upload vehicles.'}, status=403)

        # Determine if rental based on user type
        is_rental = profile.user_type == 'renter'
        
        try:
            vehicle = Vehicle.objects.create(
                uploader=request.user,
                make=request.data.get('make', ''),
                model=request.data.get('model', ''),
                year=int(request.data.get('year', 2000)),
                mileage=int(request.data.get('mileage', 0)),
                transmission=request.data.get('transmission', 'Manual'),
                fuel_type=request.data.get('fuel_type', 'Petrol'),
                type_of_vehicle=request.data.get('type_of_vehicle', 'Car'),
                price=float(request.data.get('price', 0)),
                gps_coor=request.data.get('gps_coor', ''),
                is_rental=is_rental,
                desc=request.data.get('desc', ''),
                contact=request.data.get('contact', ''),
            )
            photo = request.FILES.get('image') 
            if photo:
                VehicleImage.objects.create(vehicle=vehicle, image=photo)
            serializer = VehicleSerializer(vehicle, context={'request': request})
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class UpdateVehicleAPI(APIView):
    """
    PATCH /api/vehicles/<id>/update/
    Header: Authorization: Token <token>
    Body: any vehicle fields to update
    Only the uploader can update their own vehicle.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk, uploader=request.user)
        except Vehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found or not yours.'}, status=404)

        fields = ['make', 'model', 'year', 'mileage', 'transmission',
                  'fuel_type', 'type_of_vehicle', 'price', 'gps_coor', 'desc', 'contact']

        for field in fields:
            if field in request.data:
                val = request.data[field]
                if field in ['year', 'mileage']:
                    val = int(val)
                elif field == 'price':
                    val = float(val)
                setattr(vehicle, field, val)

        vehicle.save()
        serializer = VehicleSerializer(vehicle, context={'request': request})
        return Response(serializer.data)

class UpdateProfileAPI(APIView):
    """
    PATCH /api/profile/update/
    Header: Authorization: Token <token>
    Body: { first_name, last_name, contact_number, address, driver_license }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        # Update Django User fields
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        user.save()

        # Update UserProfile fields
        if 'contact_number' in request.data:
            profile.contact_number = request.data['contact_number']
        if 'address' in request.data:
            profile.address = request.data['address']
        if 'driver_license' in request.data:
            profile.driver_license = request.data['driver_license']
        profile.save()

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

class DeleteVehicleAPI(APIView):
    """
    DELETE /api/vehicles/<id>/delete/
    Header: Authorization: Token <token>
    Only the uploader can delete their own vehicle.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk, uploader=request.user)
        except Vehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found or not yours.'}, status=404)

        vehicle.delete()
        return Response({'message': 'Vehicle deleted successfully.'})
    
# ============================================================
# VEHICLE ENDPOINTS
# ============================================================

class VehicleListAPI(APIView):
    """
    GET /api/vehicles/
    Optional query params:
      ?search=toyota       - search by make/model
      ?type=Car            - filter by vehicle type
      ?min_price=100000    - filter by min price
      ?max_price=500000    - filter by max price
      ?is_rental=true      - show only rentals
    """
    def get(self, request):
        vehicles = Vehicle.objects.filter(
            is_sold=False, is_rented=False
        ).prefetch_related('images')

        search = request.GET.get('search', '')
        if search:
            vehicles = vehicles.filter(
                Q(make__icontains=search) |
                Q(model__icontains=search) |
                Q(desc__icontains=search)
            )

        vehicle_type = request.GET.get('type', '')
        if vehicle_type:
            vehicles = vehicles.filter(type_of_vehicle__iexact=vehicle_type)

        min_price = request.GET.get('min_price', '')
        if min_price:
            vehicles = vehicles.filter(price__gte=min_price)

        max_price = request.GET.get('max_price', '')
        if max_price:
            vehicles = vehicles.filter(price__lte=max_price)

        is_rental = request.GET.get('is_rental', '')
        if is_rental.lower() == 'true':
            vehicles = vehicles.filter(is_rental=True)
        elif is_rental.lower() == 'false':
            vehicles = vehicles.filter(is_rental=False)

        serializer = VehicleSerializer(
            vehicles, many=True, context={'request': request}
        )
        return Response(serializer.data)


class VehicleDetailAPI(APIView):
    """
    GET /api/vehicles/<id>/
    """
    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.prefetch_related('images').get(
                pk=pk, is_sold=False, is_rented=False
            )
        except Vehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found.'}, status=404)

        serializer = VehicleSerializer(vehicle, context={'request': request})
        return Response(serializer.data)


class NearbyVehiclesAPI(APIView):
    """
    GET /api/vehicles/nearby/
    Query params: ?lat=<latitude>&lng=<longitude>&radius=20
    """
    def get(self, request):
        lat    = request.GET.get('lat')
        lng    = request.GET.get('lng')
        radius = float(request.GET.get('radius', 20))

        if not lat or not lng:
            return Response(
                {'error': 'lat and lng query parameters are required.'},
                status=400
            )

        try:
            user_lat = float(lat)
            user_lng = float(lng)
        except ValueError:
            return Response({'error': 'Invalid lat/lng values.'}, status=400)

        def haversine(lat1, lon1, lat2, lon2):
            R    = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a    = (math.sin(dlat / 2) ** 2 +
                    math.cos(math.radians(lat1)) *
                    math.cos(math.radians(lat2)) *
                    math.sin(dlon / 2) ** 2)
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        all_vehicles = Vehicle.objects.filter(
            is_sold=False, is_rented=False,
        ).exclude(gps_coor__isnull=True).exclude(gps_coor='').prefetch_related('images')

        nearby = []
        for vehicle in all_vehicles:
            try:
                parts    = vehicle.gps_coor.split(',')
                v_lat    = float(parts[0].strip())
                v_lng    = float(parts[1].strip())
                distance = haversine(user_lat, user_lng, v_lat, v_lng)
                if distance <= radius:
                    nearby.append((distance, vehicle))
            except (ValueError, IndexError, AttributeError):
                continue

        nearby.sort(key=lambda x: x[0])
        vehicles   = [v for _, v in nearby]
        serializer = VehicleSerializer(
            vehicles, many=True, context={'request': request}
        )
        return Response({
            'count':      len(vehicles),
            'radius_km':  radius,
            'vehicles':   serializer.data,
        })

# ============================================================
# REVIEW ENDPOINTS
# ============================================================

class ReviewListAPI(APIView):
    """
    GET /api/reviews/
    Returns ALL reviews (no approval filter) so submitted
    reviews appear immediately in the Flet app.
    """
    def get(self, request):
        reviews    = Review.objects.all().order_by('-created_date')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewSubmitAPI(APIView):
    """
    POST /api/reviews/submit/
    Body: { "title", "review_text", "rating", "author_name",
            "email", "sentiment", "location_label",
            "latitude", "longitude" }
    Saves review and returns 201 immediately.
    """
    def post(self, request):
        serializer = ReviewSubmitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Review submitted successfully!'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewReportAPI(APIView):
    """
    POST /api/reviews/report/
    Body: { "review_id": 1, "reason": "spam", "details": "..." }
    Reports a specific review.
    """
    def post(self, request):
        try:
            review_id = request.data.get('review_id')
            reason    = request.data.get('reason', '')
            details   = request.data.get('details', '')

            Report.objects.create(
                reporter_name='',
                email='',
                subject=f'Review report: {reason}',
                report_content=f'Review ID: {review_id}\n\n{details}',
            )
            return Response(
                {'message': 'Report submitted. Thank you!'},
                status=status.HTTP_201_CREATED
            )
        except Exception as ex:
            return Response({'error': str(ex)}, status=400)


class VehicleReportAPI(APIView):
    """
    POST /api/reviews/report-vehicle/
    Body: { "vehicle_ref": "...", "reason": "fraud", "details": "..." }
    Reports a vehicle listing.
    """
    def post(self, request):
        try:
            vehicle_ref = request.data.get('vehicle_ref', '')
            reason      = request.data.get('reason', '')
            details     = request.data.get('details', '')

            Report.objects.create(
                reporter_name='',
                email='',
                subject=f'Vehicle report [{vehicle_ref}]: {reason}',
                report_content=details,
            )
            return Response(
                {'message': 'Report submitted. Thank you!'},
                status=status.HTTP_201_CREATED
            )
        except Exception as ex:
            return Response({'error': str(ex)}, status=400)


class ProfileAPI(APIView):
    """
    GET /api/profile/
    Header: Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile    = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found.'}, status=404)
        
class SavedVehiclesAPI(APIView):
    """
    GET /api/saved/
    Header: Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved = SavedVehicle.objects.filter(
            user=request.user,
            vehicle__is_sold=False,
        ).select_related('vehicle').order_by('-saved_at')

        serializer = SavedVehicleSerializer(
            saved, many=True, context={'request': request}
        )
        return Response(serializer.data)

class ToggleSaveAPI(APIView):
    """
    POST /api/saved/toggle/<vehicle_id>/
    Header: Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, vehicle_id):
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({'error': 'Vehicle not found.'}, status=404)

        saved, created = SavedVehicle.objects.get_or_create(
            user=request.user, vehicle=vehicle
        )

        if not created:
            saved.delete()
            return Response({'saved': False, 'message': 'Vehicle removed from saved.'})

        return Response({'saved': True, 'message': 'Vehicle saved!'})

class SavedVehiclesSortedAPI(APIView):
    """
    GET /api/saved/sorted/
    Header: Authorization: Token <token>
    Query params: ?lat=<latitude>&lng=<longitude>
 
    Returns saved vehicles sorted by distance (nearest first).
    Each item has an extra "distance_km" field.
    Vehicles with no GPS coordinates are appended at the end
    with distance_km = null.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        lat_str = request.GET.get("lat")
        lng_str = request.GET.get("lng")
 
        if not lat_str or not lng_str:
            return Response(
                {"error": "lat and lng query parameters are required."},
                status=400,
            )
 
        try:
            user_lat = float(lat_str)
            user_lng = float(lng_str)
        except ValueError:
            return Response({"error": "Invalid lat/lng values."}, status=400)
 
        saved = (
            SavedVehicle.objects
            .filter(user=request.user, vehicle__is_sold=False)
            .select_related("vehicle")
            .prefetch_related("vehicle__images")
            .order_by("-saved_at")
        )
 
        with_distance    = []
        without_distance = []
 
        for sv in saved:
            vehicle   = sv.vehicle
            gps       = vehicle.gps_coor or ""
            distance  = None
 
            if gps:
                try:
                    parts    = gps.split(",")
                    v_lat    = float(parts[0].strip())
                    v_lng    = float(parts[1].strip())
                    distance = self._haversine(user_lat, user_lng, v_lat, v_lng)
                except (ValueError, IndexError):
                    pass
 
            serialized = SavedVehicleSerializer(
                sv, context={"request": request}
            ).data
 
            if distance is not None:
                serialized["distance_km"] = round(distance, 2)
                with_distance.append((distance, serialized))
            else:
                serialized["distance_km"] = None
                without_distance.append(serialized)
 
        # sort nearest first, then append vehicles with no GPS
        with_distance.sort(key=lambda x: x[0])
        ordered = [item for _, item in with_distance] + without_distance
 
        return Response(ordered)
 
    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R    = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a    = (math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    

# ============================================================
# HOMEPAGE SPECIFIC ENDPOINTS
# ============================================================

class FeaturedVehiclesAPI(APIView):
    """
    GET /api/homepage/featured/
    Returns the latest 6 available vehicles for homepage display.
    Public endpoint - no authentication required.
    """
    def get(self, request):
        # Get latest 6 available vehicles
        featured_vehicles = Vehicle.objects.filter(
            is_sold=False,
            is_rented=False
        ).prefetch_related('images').order_by('-id')[:6]
        
        serializer = VehicleSerializer(
            featured_vehicles,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': len(featured_vehicles),
            'vehicles': serializer.data
        })


class VehicleStatsAPI(APIView):
    """
    GET /api/homepage/stats/
    Returns statistics for homepage display.
    Public endpoint - shows total available vehicles by type.
    """
    def get(self, request):
        from django.db.models import Count
        
        total_vehicles = Vehicle.objects.filter(
            is_sold=False,
            is_rented=False
        ).count()
        
        vehicles_by_type = Vehicle.objects.filter(
            is_sold=False,
            is_rented=False
        ).values('type_of_vehicle').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_available': total_vehicles,
            'by_type': list(vehicles_by_type)
        })

# ============================================================
# CONTACT MESSAGE ENDPOINTS
# ============================================================
# Demonstrates full CRUD via Django REST Framework with
# authentication and permission restrictions.
#
# Permissions summary:
#   POST   /api/contact/          → anyone (AllowAny)
#   GET    /api/contact/          → admin only (IsAdminUser)
#   GET    /api/contact/<id>/     → admin only (IsAdminUser)
#   PATCH  /api/contact/<id>/     → admin only (IsAdminUser)
#   DELETE /api/contact/<id>/     → admin only (IsAdminUser)

from rest_framework.permissions import IsAdminUser, AllowAny
from Main.models import ContactMessage
from Main.serializers import ContactMessageSerializer, ContactMessageUpdateSerializer


class ContactMessageListAPI(APIView):
    """
    GET  /api/contact/  — List all contact messages (admin only)
    POST /api/contact/  — Submit a new contact message (public)

    Two different permission classes are applied per HTTP method:
    - GET  requires IsAdminUser (only staff/superuser can read messages)
    - POST is open to everyone  (visitors can submit a contact form)

    This is a common real-world pattern: write is public, read is restricted.
    """

    def get_permissions(self):
        # Dynamically assign permissions based on the HTTP method
        if self.request.method == 'POST':
            return [AllowAny()]          # Anyone can submit a contact form
        return [IsAuthenticated(), IsAdminUser()]  # Only admins can read all messages

    def get(self, request):
        """
        LIST — returns all ContactMessage rows as a JSON array.
        Demonstrates: JSON PRODUCTION — Django queryset → serializer → JSON response
        Optional filter: ?resolved=true / ?resolved=false
        """
        messages_qs = ContactMessage.objects.all().order_by('-created_at')

        # Optional query param to filter by resolved status
        resolved = request.GET.get('resolved', '')
        if resolved.lower() == 'true':
            messages_qs = messages_qs.filter(is_resolved=True)
        elif resolved.lower() == 'false':
            messages_qs = messages_qs.filter(is_resolved=False)

        serializer = ContactMessageSerializer(messages_qs, many=True)
        # serializer.data is a list of dicts — DRF automatically converts to JSON
        return Response({
            'count': messages_qs.count(),
            'messages': serializer.data,   # JSON PRODUCTION happens here
        })

    def post(self, request):
        """
        CREATE — accepts JSON body and saves a new ContactMessage.
        Demonstrates: JSON CONSUMPTION — incoming JSON → serializer → validated → DB save

        Body (JSON):
        {
            "full_name":    "Alice",
            "email":        "alice@example.com",
            "phone":        "+230 5000 0000",
            "inquiry_type": "general",
            "subject":      "Test",
            "message":      "Hello there!"
        }
        """
        # JSON CONSUMPTION: request.data contains the parsed JSON body
        serializer = ContactMessageSerializer(data=request.data)

        if serializer.is_valid():
            # Save validated data to database
            contact = serializer.save()
            return Response({
                'message': 'Your message has been received. We will reply within 24 hours.',
                'id': contact.id,
                'data': ContactMessageSerializer(contact).data,  # Echo back the created object
            }, status=status.HTTP_201_CREATED)

        # Validation failed — return field-level errors as JSON
        return Response({
            'error': 'Invalid data submitted.',
            'details': serializer.errors,  # e.g. {"email": ["Enter a valid email address."]}
        }, status=status.HTTP_400_BAD_REQUEST)


class ContactMessageDetailAPI(APIView):
    """
    GET    /api/contact/<id>/  — Retrieve one message  (admin only)
    PATCH  /api/contact/<id>/  — Update is_resolved    (admin only)
    DELETE /api/contact/<id>/  — Delete a message      (admin only)

    All three methods require IsAdminUser — only staff can manage messages.
    This demonstrates endpoint-level authentication restrictions.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_object(self, pk):
        """Helper — fetch message or return 404"""
        try:
            return ContactMessage.objects.get(pk=pk)
        except ContactMessage.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        RETRIEVE — return a single ContactMessage as JSON.
        Demonstrates: JSON PRODUCTION for a single object.
        """
        obj = self._get_object(pk)
        if obj is None:
            return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ContactMessageSerializer(obj)
        return Response(serializer.data)   # Single object JSON production

    def patch(self, request, pk):
        """
        PARTIAL UPDATE — admin can mark a message as resolved.
        Demonstrates: JSON CONSUMPTION (PATCH body) + partial update pattern.

        Body (JSON):
        { "is_resolved": true }
        """
        obj = self._get_object(pk)
        if obj is None:
            return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

        # partial=True means only the supplied fields are updated
        serializer = ContactMessageUpdateSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Contact message updated successfully.',
                'data': ContactMessageSerializer(obj).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        DELETE — permanently remove a ContactMessage.
        Returns 204 No Content on success (standard REST practice).
        """
        obj = self._get_object(pk)
        if obj is None:
            return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response(
            {'message': f'Contact message {pk} deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
