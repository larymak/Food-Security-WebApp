from django.contrib import admin
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import views as auth_views
from api import views 

schema_view = get_schema_view(
    openapi.Info(
        title="Food Security API",
        default_version='v1',
        description="API for Food Security Application",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home and Authentication URLs
    path('', views.home, name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='api/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Dashboard and CRUD Operations
    path('request-list/', views.request_list, name='request_list'),
    path('create-donation/', views.create_donation, name='create_donation'),
    path('create-request/', views.create_request, name='create_request'),

    # Donor and Recipient Dashboards
    path('donor-dashboard/', views.DonorDashboardView.as_view(), name='donor_dashboard'),
    path('recipient-dashboard/', views.RecipientDashboardView.as_view(), name='recipient_dashboard'),
    path('donor-homepage/', views.donor_homepage, name='donor_homepage'),
    path('map/', views.MapView.as_view(), name='map_view'),
    path('donations/', views.DonationListView.as_view(), name='donation_list'),
    path('requests/', views.RequestListView.as_view(), name='request_list'),

    # API URLs
    path('api/v1/', include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger and ReDoc Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
