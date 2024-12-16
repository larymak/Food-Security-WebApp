from rest_framework import viewsets, filters
from rest_framework.views import APIView
from django.db.models import Prefetch
from django_filters.views import FilterView
from .filters import DonationFilter, RequestFilter
from django.db.models import Sum
from django.core.mail import send_mail
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsDonorOrReadOnly
from .services import match_donations_to_requests, optimized_matching_algorithm
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    User, Donor, FoodItem, Donation, Recipient, Request, 
    Delivery, DeliveryTracking, Notification, TransactionHistory, Matching
)
from .serializers import (
    UserSerializer, DonorSerializer, FoodItemSerializer, DonationSerializer, 
    RecipientSerializer, RequestSerializer, DeliverySerializer, DeliveryTrackingSerializer, 
    NotificationSerializer, TransactionHistorySerializer
)
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, DonationForm, RequestForm
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView


# Custom Authentication Views
class CustomLoginView(LoginView):
    template_name = 'api/login.html'
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        else:
            return reverse_lazy('dashboard')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

# Registration View (Class-based)
class RegisterView(TemplateView):
    template_name = 'api/register.html'

    def get(self, request, *args, **kwargs):
        form = UserRegistrationForm()
        next_url = request.GET.get('next')
        return self.render_to_response({'form': form, 'next': next_url})

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save the user object yet
            user.user_type = form.cleaned_data['user_type']  # Set the user_type
            user.save()  # Now save the user object
            login(request, user)
            next_url = request.POST.get('next') or reverse_lazy('home')
            return redirect(next_url)
        return self.render_to_response({'form': form})

# Home View
def home(request):
    return render(request, 'api/home.html')

# Donation Creation (Login Required)
@login_required
def create_donation(request):
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user

            if form.cleaned_data['new_food_item']:
                food_item, created = FoodItem.objects.get_or_create(
                    food_name=form.cleaned_data['new_food_item'],
                    defaults={'expiry_date': form.cleaned_data['expiry_date']}
                )
            else:
                food_item = form.cleaned_data['food_item']

            donation.food_item = food_item
            donation.status = 'pending'
            donation.save()
            messages.success(request, 'Your donation has been submitted successfully!')
            return redirect('donor_homepage')
    else:
        form = DonationForm()
    
    popular_food_items = FoodItem.objects.annotate(total_quantity=Sum('donation__quantity')).order_by('-total_quantity')[:10]

    return render(request, 'api/create_donation.html', {
        'form': form,
        'popular_food_items': popular_food_items
    })

# Request Creation (Login Required)
@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            food_request = form.save(commit=False)
            food_request.recipient = request.user
            
            # Create or get the FoodItem without expiry_date
            food_item, created = FoodItem.objects.get_or_create(
                food_name=form.cleaned_data['food_item_name'],
                defaults={
                    'quantity': form.cleaned_data['quantity'],
                    'unit': form.cleaned_data['unit']
                }
            )
            
            if not created:
                food_item.quantity = form.cleaned_data['quantity']
                food_item.unit = form.cleaned_data['unit']
                food_item.save()
            
            food_request.food_item = food_item
            food_request.save()
            
            messages.success(request, 'Your food request has been submitted successfully!')
            return redirect('request_list')
    else:
        form = RequestForm()
    
    popular_food_items = FoodItem.objects.annotate(total_quantity=Sum('donation__quantity')).order_by('-total_quantity')[:10]

    return render(request, 'api/create_request.html', {
        'form': form,
        'popular_food_items': popular_food_items
    })

def request_list(request):
    requests = Request.objects.all().order_by('-request_date')
    return render(request, 'api/request_list.html', {'requests': requests})

@login_required
def donor_homepage(request):
    available_requests = Request.objects.filter(status='pending')
    donor_donations = Donation.objects.filter(donor=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        if request_id:
            food_request = get_object_or_404(Request, id=request_id)
            donation = Donation.objects.create(
                donor=request.user,
                food_item=food_request.food_item,
                quantity=food_request.quantity,
                status='approved',
                expiry_date=food_request.food_item.expiry_date
            )
            food_request.status = 'approved'
            food_request.donation = donation
            food_request.save()
            messages.success(request, 'Donation added and request approved!')
            messages.info(request, 'The recipient has been notified of the match.')
            return redirect('donor_homepage')

    return render(request, 'api/donor_homepage.html', {
        'available_requests': available_requests,
        'donor_donations': donor_donations,
    })

class DonorDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.user_type != 'donor':
            return redirect('home')
        donations = Donation.objects.filter(donor=request.user).prefetch_related('food_item').order_by('-donation_date')
        return render(request, 'api/donor_dashboard.html', {'donations': donations})

class RecipientDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.user_type != 'recipient':
            return redirect('home')
        requests = Request.objects.filter(recipient=request.user).prefetch_related('food_item').order_by('-request_date')
        return render(request, 'api/recipient_dashboard.html', {'requests': requests})

# ViewSets for API Endpoints
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class DonorViewSet(viewsets.ModelViewSet):
    queryset = Donor.objects.all()
    serializer_class = DonorSerializer

class RecipientViewSet(viewsets.ModelViewSet):
    queryset = Recipient.objects.all()
    serializer_class = RecipientSerializer

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer

class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

class DeliveryTrackingViewSet(viewsets.ModelViewSet):
    queryset = DeliveryTracking.objects.all()
    serializer_class = DeliveryTrackingSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class TransactionHistoryViewSet(viewsets.ModelViewSet):
    queryset = TransactionHistory.objects.all()
    serializer_class = TransactionHistorySerializer

# Donation ViewSet with Filters and Custom Action for Matching Donations
class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'donor__organization_name']
    search_fields = ['food_item__food_name', 'donor__organization_name']
    ordering_fields = ['donation_date', 'quantity']
    permission_classes = [IsDonorOrReadOnly]

    @action(detail=False, methods=['post'])
    def match_donations(self, request):
        # Call the service to match donations with requests
        match_donations_to_requests()
        return Response({"message": "Donation matching process completed"})

# Nearby Donations APIView
class NearbyDonationsView(APIView):
    def get(self, request):
        try:
            latitude = float(request.query_params.get('latitude'))
            longitude = float(request.query_params.get('longitude'))
            radius = float(request.query_params.get('radius', 10))  # default 10km
        except (TypeError, ValueError):
            return Response({"error": "Invalid latitude, longitude, or radius"}, status=400)

        user_location = Point(longitude, latitude)
        nearby_donations = Donation.objects.filter(
            donor__location__distance_lte=(user_location, D(km=radius))
        )

        serializer = DonationSerializer(nearby_donations, many=True)
        return Response(serializer.data)

class RunMatchingAlgorithmView(LoginRequiredMixin, View):
    def get(self, request):
        optimized_matching_algorithm()
        messages.success(request, "Matching algorithm has been run successfully.")
        return redirect('dashboard')

def notify_recipient(request):
    # This is a placeholder function. In a real application, you'd implement
    # a proper notification system (email, SMS, or in-app notifications)
    recipient_email = request.requester.email
    subject = "Your food request has been matched!"
    message = f"Good news! Your request for {request.food_item.food_name} has been matched with a donor."
    send_mail(subject, message, 'larykush@gmail.com', [recipient_email])  

class MapView(View):
    def get(self, request):
        donations = Donation.objects.filter(status='available')
        requests = Request.objects.filter(status='pending')
        
        items = []
        for d in donations:
            if d.donor.location:
                items.append({
                    'type': 'Donation',
                    'food_item': d.food_item.name,
                    'latitude': d.donor.location.y,
                    'longitude': d.donor.location.x
                })
        for r in requests:
            if r.recipient.location:
                items.append({
                    'type': 'Request',
                    'food_item': r.food_item.name,
                    'latitude': r.recipient.location.y,
                    'longitude': r.recipient.location.x
                })
        
        print(f"Number of items: {len(items)}")  # Debugging line
        return render(request, 'api/map_view.html', {'items': items})
    
class DonationListView(FilterView):
    model = Donation
    template_name = 'api/donation_list.html'
    filterset_class = DonationFilter

class RequestListView(FilterView):
    model = Request
    template_name = 'api/request_list.html'
    filterset_class = RequestFilter