from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from .models import Donation, Request, Matching, Notification

# Function to match available donations to pending requests based on food items and quantities
def match_donations_to_requests():
    unmatched_donations = Donation.objects.filter(status='available')
    unmatched_requests = Request.objects.filter(status='pending')

    for donation in unmatched_donations:
        for request in unmatched_requests:
            if donation.food_item == request.food_item and donation.quantity >= request.quantity:
                # Match found
                request.donation = donation
                request.status = 'matched'
                request.save()

                donation.quantity -= request.quantity
                if donation.quantity == 0:
                    donation.status = 'completed'
                donation.save()

                # Send notifications to the recipient and donor
                create_notification(request.recipient.user, f"Your request for {request.food_item.name} has been matched!")
                create_notification(donation.donor.user, f"Your donation of {donation.food_item.name} has been matched!")
                
                break  # Move to next donation

# Function to create notifications
def create_notification(user, message):
    Notification.objects.create(user=user, message=message)

# Optimized matching algorithm considering proximity and expiration dates
def optimized_matching_algorithm():
    unmatched_donations = Donation.objects.filter(status='available').order_by('food_item__expiry_date')
    unmatched_requests = Request.objects.filter(status='pending')

    for donation in unmatched_donations:
        # Find nearby requests within a 50 km radius, ordered by distance and creation time
        nearby_requests = unmatched_requests.filter(
            recipient__location__distance_lte=(donation.donor.location, D(km=50))
        ).annotate(
            distance=Distance('recipient__location', donation.donor.location)
        ).order_by('distance', 'created_at')

        for request in nearby_requests:
            if donation.food_item == request.food_item and donation.quantity >= request.quantity:
                # Create a match
                Matching.objects.create(
                    donation=donation,
                    request=request,
                    matched_quantity=request.quantity
                )

                request.status = 'matched'
                request.save()

                donation.quantity -= request.quantity
                if donation.quantity == 0:
                    donation.status = 'completed'
                donation.save()

                # Send notifications to the recipient and donor
                create_notification(request.recipient.user, f"Your request for {request.food_item.name} has been matched!")
                create_notification(donation.donor.user, f"Your donation of {donation.food_item.name} has been partially matched!")

                if donation.status == 'completed':
                    break  # Move to the next donation

    # Handle remaining partial matches
    optimize_partial_matches()

# Function to handle partial matches between donations and requests
def optimize_partial_matches():
    partial_donations = Donation.objects.filter(status='available', quantity__gt=0)
    partial_requests = Request.objects.filter(status='pending')

    for donation in partial_donations:
        for request in partial_requests:
            if donation.food_item == request.food_item:
                # Determine the quantity that can be matched
                matched_quantity = min(donation.quantity, request.quantity)
                Matching.objects.create(
                    donation=donation,
                    request=request,
                    matched_quantity=matched_quantity
                )

                # Update quantities and statuses
                donation.quantity -= matched_quantity
                request.quantity -= matched_quantity
                
                if donation.quantity == 0:
                    donation.status = 'completed'
                if request.quantity == 0:
                    request.status = 'matched'

                donation.save()
                request.save()

    # Clean up any remaining requests or donations that have been fulfilled
    Donation.objects.filter(quantity=0).update(status='completed')
    Request.objects.filter(quantity=0).update(status='matched')
