# Main/serializers.py
# DRF serializer for the ContactMessage model.
# Used by the REST API endpoints below to convert
# ContactMessage objects to/from JSON automatically.

from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializes ALL fields of ContactMessage.
    - On READ  (GET)  → converts DB row → JSON
    - On WRITE (POST) → validates JSON → saves to DB

    The 'created_at' and 'is_resolved' fields are read-only
    so clients cannot forge timestamps or mark items resolved
    via a plain POST.
    """
    class Meta:
        model = ContactMessage
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'inquiry_type',
            'subject',
            'message',
            'attachment',
            'created_at',
            'is_resolved',
        ]
        read_only_fields = ['id', 'created_at']


class ContactMessageUpdateSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for PATCH requests.
    Only admins can change 'is_resolved' and 'subject'.
    Prevents clients from overwriting sensitive fields like email.
    """
    class Meta:
        model = ContactMessage
        fields = ['is_resolved', 'subject', 'message']
