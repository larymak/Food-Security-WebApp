from celery import shared_task
from .services import match_donations_to_requests

@shared_task
def run_donation_matching():
    match_donations_to_requests()

@shared_task
def send_notification_email(user_id, message):
    # Implement email sending logic here
    pass