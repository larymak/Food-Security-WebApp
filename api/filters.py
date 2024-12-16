import django_filters
from .models import Donation, Request

class DonationFilter(django_filters.FilterSet):
    food_item = django_filters.CharFilter(lookup_expr='icontains')
    min_quantity = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    max_quantity = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    donation_date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Donation
        fields = ['status', 'donor', 'food_item']

class RequestFilter(django_filters.FilterSet):
    food_item = django_filters.CharFilter(lookup_expr='icontains')
    min_quantity = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    max_quantity = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    request_date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Request
        fields = ['status', 'recipient', 'food_item']