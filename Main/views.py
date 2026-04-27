# Main/views.py
# ─────────────────────────────────────────────────────────────
# Changes made:
#   1. Added ajax_vehicle_search view — returns JsonResponse
#   2. Added ajax_contact view — handles AJAX contact form POST
#   3. Original index, faq, aboutus_view unchanged
# ─────────────────────────────────────────────────────────────

from django.shortcuts import render
from django.db.models import Count, Q
from django.http import JsonResponse
from Vehicles.models import Vehicle
from Reviews.models import Review
from .forms import ContactForm


def index(request):
    recent_vehicles = (
        Vehicle.objects
        .filter(is_sold=False, is_rented=False)
        .prefetch_related('images')
        .order_by('-id')[:4]
    )

    recent_reviews = (
        Review.objects
        .filter(is_approved=True)
        .order_by('-created_date')[:6]
    )

    category_counts = (
        Vehicle.objects
        .values('type_of_vehicle')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    total_vehicles = Vehicle.objects.count()

    context = {
        'recent_vehicles':  recent_vehicles,
        'recent_reviews':   recent_reviews,
        'contact_form':     ContactForm(),
        'category_counts':  category_counts,
        'total_vehicles':   total_vehicles,
    }
    return render(request, 'index.html', context)


def faq(request):
    return render(request, 'faq.html')


def aboutus_view(request):
    return render(request, 'aboutus.html')


# ── NEW: AJAX vehicle search ──────────────────────────────────
# Called by jQuery $.ajax() on the homepage search box.
# Returns JSON — NOT a full HTML page (JsonResponse not render).
def ajax_vehicle_search(request):
    """
    GET /main/ajax/search/?q=toyota
    Returns up to 6 matching vehicles as JSON.
    Used by jQuery AJAX on the homepage for live search results.
    """
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'vehicles': []})

    vehicles = Vehicle.objects.filter(
        Q(make__icontains=query) |
        Q(model__icontains=query) |
        Q(type_of_vehicle__icontains=query)
    ).filter(is_sold=False, is_rented=False).prefetch_related('images')[:6]

    data = []
    for v in vehicles:
        first_img = v.images.first()
        data.append({
            'id':       v.id,
            'make':     v.make,
            'model':    v.model,
            'year':     v.year,
            'price':    str(int(v.price)),
            'type':     v.type_of_vehicle,
            'fuel':     v.fuel_type,
            'is_rental': v.is_rental,
            'image':    first_img.image.url if first_img else None,
        })

    return JsonResponse({'vehicles': data})


# ── NEW: AJAX contact form submission ─────────────────────────
# Called by jQuery $.ajax() when the contact form is submitted.
# Returns JSON success/error — page does NOT reload.
def ajax_contact(request):
    """
    POST /main/ajax/contact/
    Handles contact form via AJAX — returns JSON.
    e.preventDefault() in jQuery stops the normal page reload.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Your message has been sent! We will get back to you within 24 hours.'
            })
        else:
            # Return form errors as JSON
            errors = {field: errors[0] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)
