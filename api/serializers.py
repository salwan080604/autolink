from rest_framework import serializers
from django.contrib.auth.models import User
from Vehicles.models import Vehicle, VehicleImage
from Reviews.models import Review
from Profile.models import SavedVehicle
from Users.models import UserProfile



# Vehicle Image Serializer
# Converts each image of a vehicle into a URL string
class VehicleImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = VehicleImage
        fields = ['id', 'image']

    def get_image(self, obj):
        # Returns the full URL of the image so the Flet app can display it
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# Vehicle Serializer
# Converts a Vehicle object to JSON with all its details
class VehicleSerializer(serializers.ModelSerializer):
    images = VehicleImageSerializer(many=True, read_only=True)
    uploader_name = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'model', 'year', 'mileage',
            'transmission', 'fuel_type', 'type_of_vehicle',
            'price', 'gps_coor', 'is_rental', 'desc',
            'contact', 'is_sold', 'is_rented',
            'images', 'uploader_name'
        ]

    def get_uploader_name(self, obj):
        return obj.uploader.get_full_name() or obj.uploader.username


# Review Serializer
# Converts a Review object to JSON
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id', 'title', 'review_text', 'rating',
            'author_name', 'created_date', 'is_approved'
        ]


# Review Submit Serializer
# Used when the Flet app POSTS a new review
class ReviewSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['title', 'review_text', 'rating', 'author_name', 'email']


# User Registration Serializer
# Used when a new user registers from the Flet app
class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['buyer', 'seller', 'renter'])
    address = serializers.CharField()
    contact_number = serializers.CharField()
    driver_license = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        UserProfile.objects.create(
            user=user,
            user_type=validated_data['user_type'],
            address=validated_data['address'],
            contact_number=validated_data['contact_number'],
            driver_license=validated_data.get('driver_license', ''),
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'user_type', 'address', 'contact_number', 'driver_license'
        ]

class SavedVehicleSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SavedVehicle
        fields = ['id', 'vehicle', 'vehicle_id', 'saved_at']