from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

# URL patterns
urlpatterns = [

    path('', include('pwa.urls')),
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/<str:customer_id>/', views.customer_profile, name='customer_profile'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('add-payment/', views.add_payment, name='add_payment'),
    path('collector-stats/', views.collector_stats, name='collector_stats'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('bill/<int:bill_id>/pdf/', views.view_bill_pdf, name='view_bill_pdf'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add-payment/<str:customer_id>/', views.add_payment_for_customer, name='add_payment_for_customer'),
    path('provide-internet/', views.provide_internet, name='provide_internet'),
    path('online-customers/', views.online_customers, name='online_customers'),
    path('toggle-block/<str:mac_address>/', views.toggle_block_status, name='toggle_block_status'),
]
