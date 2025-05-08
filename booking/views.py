from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import date, datetime, timedelta
from django.db.models import Q, Case, When, Value, IntegerField
from .models import User, ServiceCategory, Service, Schedule, Booking, Payment, Feedback, BookingLine
from .forms import (
    RegisterForm, LoginForm, CategoryFilterForm, BookingForm, FeedbackForm, 
    PaymentMethodForm, PaymentForm, BookingFilterForm, AdminUserSearchForm,
    ScheduleForm, EditProfileForm, ServiceEditForm, ServiceCategoryForm,AdminBookingLineFilterForm, BookingLineStatusForm
)

def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'is_admin', False):
            return redirect('admin_dashboard')
        else:
            return redirect('main')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_admin:
                return redirect('admin_dashboard')
            else:
                return redirect('main')
        else:
            messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    response = render(request, 'login.html', {'form': form})
    response['Cache-Control'] = 'no-store'
    return response

def main(request):
    return render(request, 'main.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='register')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('main')

def services(request):
    form = CategoryFilterForm(request.GET or None)
    categories = ServiceCategory.objects.filter(is_active=True)
    services_qs = Service.objects.filter(is_active=True, category__is_active=True)
    selected_category = None

    if form.is_valid():
        selected_category = form.cleaned_data.get('category')
        if selected_category:
            services_qs = services_qs.filter(category=selected_category)

    paginator = Paginator(services_qs, 9)
    page_number = request.GET.get('page')
    services_page = paginator.get_page(page_number)

    context = {
        'categories': categories,  
        'services': services_page,
        'selected_category': selected_category,
        'form': form,
        'paginator': paginator,
        'page_obj': services_page,  
    }
    return render(request, 'customer/services.html', context)

@login_required
def book_service(request, service_id):
    service = Service.objects.filter(id=service_id, is_active=True, category__is_active=True).first()
    if not service:
        messages.error(request, "Service not found or not available.")
        return redirect('services')

    today = date.today()
    schedules = Schedule.objects.filter(is_available=True)
    booking_date = request.POST.get('booking_date', today.isoformat())
    selected_schedule = None

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking_date = form.cleaned_data['booking_date']
            selected_schedule = form.cleaned_data['schedule_id']
            existing_count = Booking.objects.filter(
                date=booking_date,
                schedule=selected_schedule
            ).count()
            if existing_count >= selected_schedule.capacity:
                messages.error(request, "This time slot is already fully booked. Please choose another time.", extra_tags='booking')
            else:
                
                request.session['pending_booking'] = {
                    'service_id': service.id,
                    'date': str(booking_date),
                    'schedule_id': selected_schedule.id,
                }
                return redirect('invoice')
    else:
        form = BookingForm()

    selected_schedule_id = request.POST.get("schedule_id") if request.method == "POST" else None
    if selected_schedule_id:
        try:
            selected_schedule = Schedule.objects.get(id=selected_schedule_id, is_available=True)
        except Schedule.DoesNotExist:
            selected_schedule = None

    return render(request, 'customer/book_service.html', {
        'form': form,
        'service': service,
        'schedules': schedules,
        'today': today,
        'selected_date': booking_date,
        'selected_schedule': selected_schedule
    })

@login_required
def invoice(request):
    print("invoice session pending_booking:", request.session.get('pending_booking'))
    pending_booking = request.session.get('pending_booking')
    if not pending_booking:
        messages.error(request, "Please select a service and time slot first.")
        return redirect('services')

    service = get_object_or_404(Service, id=pending_booking['service_id'], is_active=True)
    schedule = get_object_or_404(Schedule, id=pending_booking['schedule_id'], is_available=True)
    booking_date = pending_booking['date']
    booking_duration = service.total_duration_minutes
    start_dt = datetime.combine(datetime.strptime(booking_date, "%Y-%m-%d").date(), schedule.available_time)
    end_dt = start_dt + timedelta(minutes=booking_duration)
    calculated_end_time = end_dt.time()
    booking_price = service.price

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['method']
            valid_methods = dict(PaymentMethodForm.METHOD_CHOICES)
            if method not in valid_methods:
                messages.error(request, "Invalid payment method selected.")
            else:
                request.session['pending_booking_method'] = method
                return redirect(reverse(f'pay_{method}'))
        else:
            messages.error(request, "Please select a payment method.")
    else:
        form = PaymentMethodForm()
    return render(request, 'customer/invoice.html', {
        'pending_service': service,
        'pending_schedule': schedule,
        'pending_date': booking_date,
        'calculated_end_time': calculated_end_time,
        'booking_price': booking_price,
        'form': form,
    })

@login_required
def pay_gcash(request):
    print("In pay_gcash view, request method:", request.method)
    pending = request.session.get('pending_booking')
    method = request.session.get('pending_booking_method')
    if not pending or method != 'gcash':
        messages.error(request, "No pending GCash payment found.")
        return redirect('services')

    service = get_object_or_404(Service, id=pending['service_id'], is_active=True)
    schedule = get_object_or_404(Schedule, id=pending['schedule_id'], is_available=True)
    booking_date = datetime.strptime(pending['date'], "%Y-%m-%d").date()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            booking = Booking.objects.create(
                user=request.user,
                service=service,
                date=booking_date,
                schedule=schedule,
                booking_time=timezone.now()
            )
            BookingLine.objects.create(
                booking=booking,
                service=service,
                status='pending'
            )
            payment = Payment.objects.create(
                booking=booking,
                user=request.user,
                method='gcash',
                amount=service.price,
                transaction_id="GCASH123456"
            )
            # Create Receipt
            from .models import Receipt
            Receipt.objects.create(
                payment=payment,
                issued_at=timezone.now(),
                number=f"RCPT-{payment.id:06d}"
            )
            # Clean up session
            request.session.pop('pending_booking', None)
            request.session.pop('pending_booking_method', None)
            messages.success(request, "GCash payment successful!")
            return redirect('services')
    else:
        form = PaymentForm()
    class DummyPayment: pass
    dummy = DummyPayment()
    dummy.amount = service.price
    return render(request, 'customer/pay_gcash.html', {'payment': dummy, 'form': form})

@login_required
def pay_paypal(request):
    pending = request.session.get('pending_booking')
    method = request.session.get('pending_booking_method')
    if not pending or method != 'paypal':
        messages.error(request, "No pending PayPal payment found.")
        return redirect('services')

    service = get_object_or_404(Service, id=pending['service_id'], is_active=True)
    schedule = get_object_or_404(Schedule, id=pending['schedule_id'], is_available=True)
    booking_date = datetime.strptime(pending['date'], "%Y-%m-%d").date()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            booking = Booking.objects.create(
                user=request.user,
                service=service,
                date=booking_date,
                schedule=schedule,
                booking_time=timezone.now()
            )
            BookingLine.objects.create(
                booking=booking,
                service=service,
                status='pending'
            )
            payment = Payment.objects.create(
                booking=booking,
                user=request.user,
                method='paypal',
                amount=service.price,
                transaction_id="PAYPAL123456"
            )
            # Create Receipt
            from .models import Receipt
            Receipt.objects.create(
                payment=payment,
                issued_at=timezone.now(),
                number=f"RCPT-{payment.id:06d}"
            )
            request.session.pop('pending_booking', None)
            request.session.pop('pending_booking_method', None)
            messages.success(request, "PayPal payment successful!")
            return redirect('services')
    else:
        form = PaymentForm()
    class DummyPayment: pass
    dummy = DummyPayment()
    dummy.amount = service.price
    return render(request, 'customer/pay_paypal.html', {'payment': dummy, 'form': form})

@login_required
def booking_line(request):
    form = BookingFilterForm(request.GET or None)
    
    qs = BookingLine.objects.filter(
        booking__user=request.user
    ).select_related(
        'booking', 'service', 'booking__schedule'
    ).annotate(
        completed_sort=Case(
            When(status='completed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    )
    
    qs = qs.order_by('completed_sort', 'booking__date', 'booking__booking_time')

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        service = form.cleaned_data.get('service_id')
        if start_date:
            qs = qs.filter(booking__date__gte=start_date)
        if end_date:
            qs = qs.filter(booking__date__lte=end_date)
        if service:
            qs = qs.filter(service=service)

    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
    booking_lines = paginator.get_page(page_number)
    return render(request, 'customer/booking_line.html', {
        'booking_lines': booking_lines,
        'form': form,
    })
@login_required
def rate_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    feedback = Feedback.objects.filter(user=request.user, booking=booking).first()

    if feedback:
        return render(request, 'customer/rate_booking.html', {
            'booking': booking,
            'feedback': feedback,
            'feedback_exists': True,
        })

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            Feedback.objects.create(
                user=request.user,
                service=booking.service,
                booking=booking,
                rating=form.cleaned_data["rating"],
                comment=form.cleaned_data["comment"]
            )
            messages.success(request, "Thank you for your feedback!")
            return redirect('booking_line')
        else:
            messages.error(request, "Please provide a valid rating and comment.")
    else:
        form = FeedbackForm()
    return render(request, 'customer/rate_booking.html', {
        'booking': booking,
        'feedback_exists': False,
        'form': form
    })

def public_feedback(request):
    feedback_list = Feedback.objects.select_related('service', 'user').order_by('-created_at')
    paginator = Paginator(feedback_list, 9)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'customer/public_feedback.html', {
        'feedbacks': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })

@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=user)
    return render(request, "customer/edit_profile.html", {"form": form})

@login_required
def profile(request):
    bookings = Booking.objects.filter(user=request.user).select_related('service', 'schedule').order_by('-date', '-booking_time')[:3]
    feedbacks = Feedback.objects.filter(user=request.user).select_related('service').order_by('-created_at')[:3]
    return render(request, "customer/profile.html", {
        "user": request.user,
        "bookings": bookings,
        "feedbacks": feedbacks,
    })

@login_required
def admin_dashboard(request):
    stats = {
        'total_bookings': Booking.objects.count(),
        'total_users': User.objects.count(),
        'total_services': Service.objects.count(),
        'bookings_today': Booking.objects.filter(date=date.today()).count()
    }
    recent_bookings = Booking.objects.select_related('user', 'service', 'schedule').order_by('-booking_time')[:10]
    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@login_required
def admin_users(request):
    form = AdminUserSearchForm(request.GET or None)
    users_qs = User.objects.all().order_by('-created_at')
    search_query = ""
    if form.is_valid():
        search_query = form.cleaned_data.get("q", "").strip()
        if search_query:
            users_qs = users_qs.filter(
                username__icontains=search_query
            ) | users_qs.filter(
                email__icontains=search_query
            ) | users_qs.filter(
                fullname__icontains=search_query
            )

    paginator = Paginator(users_qs, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    context = {
        'users': users_page,
        'paginator': paginator,
        'page_obj': users_page,
        'form': form,
        'search_query': search_query,
    }
    return render(request, 'admin/admin_users.html', context)

from django.core.paginator import Paginator

@login_required
def admin_services(request):
    service_qs = Service.objects.select_related('category').order_by('category__name', 'name')
    selected_category_id = request.GET.get('category')
    if selected_category_id:
        service_qs = service_qs.filter(category_id=selected_category_id)
    paginator = Paginator(service_qs, 10)
    page_number = request.GET.get('page')
    services = paginator.get_page(page_number)

    
    categories = ServiceCategory.objects.all().order_by('name')

    return render(request, 'admin/admin_services.html', {
        'services': services,
        'categories': categories,
        'selected_category_id': selected_category_id,
    })

@login_required
def admin_edit_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        form = ServiceEditForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully.")
            return redirect('admin_services')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceEditForm(instance=service)
    return render(request, 'admin/admin_service_edit.html', {
        'form': form,
        'service': service,
    })

@login_required
def admin_delete_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service deleted.")
        return redirect('admin_services')
    return render(request, 'admin/admin_service_confirm_delete.html', {'service': service})

def admin_logout(request):
    print(f"admin_logout called with method: {request.method}")
    logout(request)
    return redirect('main')

@login_required
def admin_add_servicecategory(request):
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service category added successfully.")
            return redirect('admin_servicecategory_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceCategoryForm(initial={'is_active': True})
    return render(request, 'admin/admin_addServicecategory.html', {'form': form})

@login_required
def admin_servicecategory_list(request):
    category_qs = ServiceCategory.objects.order_by("name")
    paginator = Paginator(category_qs, 10)  
    page_number = request.GET.get("page")
    categories = paginator.get_page(page_number)
    return render(request, "admin/admin_servicecategory_list.html", {"categories": categories})

@login_required
def admin_add_service(request):
    if request.method == 'POST':
        form = ServiceEditForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Service added successfully.")
            return redirect('admin_services')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceEditForm()
    return render(request, 'admin/admin_add_service.html', {'form': form})

@login_required
def admin_edit_servicecategory(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Service category updated successfully.")
            return redirect('admin_servicecategory_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceCategoryForm(instance=category)
    return render(request, "admin/admin_editServicecategory.html", {"form": form, "category": category})

@login_required
def admin_delete_servicecategory(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Service category deleted.")
        return redirect('admin_servicecategory_list')
    return render(request, "admin/admin_confirm_delete_servicecategory.html", {"category": category})

@login_required
def admin_schedule(request):
    schedule_qs = Schedule.objects.all().order_by('available_time')
    paginator = Paginator(schedule_qs, 10)
    page_number = request.GET.get('page')
    schedules = paginator.get_page(page_number)  
    context = {
        'schedules': schedules,  
        'is_paginated': schedules.has_other_pages(),
        'page_obj': schedules,
    }
    return render(request, 'admin/admin_schedule.html', context)

@login_required
def admin_add_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_schedule')
    else:
        form = ScheduleForm()
    return render(request, 'admin/admin_schedule_form.html', {'form': form})

@login_required
def admin_edit_schedule(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return redirect('admin_schedule')
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'admin/admin_schedule_form.html', {'form': form})

@login_required
def admin_delete_schedule(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
    return redirect('admin_schedule')

@login_required
def admin_bookings(request):
    filter_form = AdminBookingLineFilterForm(request.GET or None)

    # Annotate: completed_sort=1 if completed, else 0
    booking_lines = BookingLine.objects.select_related(
        'booking__user', 'service', 'booking__schedule'
    ).annotate(
        completed_sort=Case(
            When(status='completed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by(
        'completed_sort',         
        'booking__date',
        'booking__schedule__available_time',
        '-booking__booking_time'  
    )

    # Check for "Bookings Today" quick filter
    if request.GET.get('bookings_today'):
        booking_lines = booking_lines.filter(booking__date=date.today())
    else:
        if filter_form.is_valid():
            cd = filter_form.cleaned_data
            if cd['service']:
                booking_lines = booking_lines.filter(service=cd['service'])
            if cd['status']:
                booking_lines = booking_lines.filter(status=cd['status'])
            if cd['q']:
                booking_lines = booking_lines.filter(
                    Q(booking__user__username__icontains=cd['q']) |
                    Q(booking__user__fullname__icontains=cd['q']) |
                    Q(service__name__icontains=cd['q'])
                )

    paginator = Paginator(booking_lines, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for line in page_obj.object_list:
        line.status_form = BookingLineStatusForm(initial={'status': line.status})

    context = {
        'booking_lines': page_obj.object_list,
        'filter_form': filter_form,
        'page_obj': page_obj,
        'paginator': paginator
    }
    return render(request, 'admin/admin_bookings.html', context)

@login_required
def admin_change_booking_status(request, bookingline_id):
    booking_line = get_object_or_404(BookingLine, pk=bookingline_id)
    form = BookingLineStatusForm(request.POST)
    if form.is_valid():
        booking_line.status = form.cleaned_data['status']
        booking_line.save()
        messages.success(request, f"Status updated for {booking_line.booking.user.username}'s booking.")
    else:
        messages.error(request, "Invalid status.")
    referer = request.META.get("HTTP_REFERER") or reverse('admin_bookings')
    return redirect(referer)

@login_required
def admin_receipt_detail(request, bookingline_id):
    
    line = get_object_or_404(BookingLine.objects.select_related("booking", "service", "booking__user", "booking__schedule"), pk=bookingline_id)
    payment = Payment.objects.filter(booking=line.booking).first()  
    context = {
        "line": line,
        "booking": line.booking,
        "service": line.service,
        "payment": payment,
    }
    return render(request, "admin/admin_receipt_detail.html", context)