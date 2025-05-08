
from . import views
from django.urls import path

urlpatterns = [
    # ... customer ...
    path('', views.main, name='main'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('services/', views.services, name='services'),
    path('book/<int:service_id>/', views.book_service, name='book_service'),
    path('invoice/', views.invoice, name='invoice'),
    path('pay/gcash/', views.pay_gcash, name='pay_gcash'),
    path('pay/paypal/', views.pay_paypal, name='pay_paypal'),
    path('bookings/', views.booking_line, name='booking_line'),
    path('rate/<int:booking_id>/', views.rate_booking, name='rate_booking'),
    path('public_feedback/', views.public_feedback, name='public_feedback'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('logout/', views.user_logout, name='user_logout'),

    # --- Custom Admin ---
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
    path('dashboard/bookings/change-status/<int:bookingline_id>/', views.admin_change_booking_status, name='admin_change_booking_status'),
    path('dashboard/services/', views.admin_services, name='admin_services'),
    path('dashboard/services/add/', views.admin_add_service, name='admin_add_service'),
    path('dashboard/services/<int:service_id>/edit/', views.admin_edit_service, name='admin_edit_service'),
    path('dashboard/services/<int:service_id>/delete/', views.admin_delete_service, name='admin_delete_service'),
    path('dashboard/servicecategories/add/', views.admin_add_servicecategory, name='admin_add_servicecategory'),
    path('dashboard/servicecategories/', views.admin_servicecategory_list, name='admin_servicecategory_list'),
    path('dashboard/servicecategories/<int:category_id>/edit/', views.admin_edit_servicecategory, name='admin_edit_servicecategory'),
    path('dashboard/servicecategories/<int:category_id>/delete/', views.admin_delete_servicecategory, name='admin_delete_servicecategory'),
    path('dashboard/schedules/', views.admin_schedule, name='admin_schedule'),
    path('dashboard/schedules/add/', views.admin_add_schedule, name='admin_add_schedule'),
    path('dashboard/schedules/<int:pk>/edit/', views.admin_edit_schedule, name='admin_edit_schedule'),
    path('dashboard/schedules/<int:pk>/delete/', views.admin_delete_schedule, name='admin_delete_schedule'),
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/bookings/<int:bookingline_id>/receipt/', views.admin_receipt_detail, name='admin_receipt_detail'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
]
