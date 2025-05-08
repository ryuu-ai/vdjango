from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import ServiceCategory, Service, Schedule,BookingLine

class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label="Full Name")
    email = forms.EmailField(required=False)

    # Override password1 to set custom help_text
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="""
            <ul style='padding-left: 20px; margin-bottom: 0;'>
                <li>At least 8 characters long</li>
                <li>Not too similar to your username or personal info</li>
                <li>Not a commonly used password</li>
                <li>Not entirely numeric</li>
            </ul>
        """
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        if full_name:
            names = full_name.strip().split(' ', 1)
            user.first_name = names[0]
            user.last_name = names[1] if len(names) > 1 else ''
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput
    )

class CategoryFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        required=False,
        label='Category',
        empty_label="All Categories",  
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'})
    )

class FeedbackForm(forms.Form):
    RATING_CHOICES = [(i, f'{i} Star') for i in range(5, 0, -1)]
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="Your Rating"
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50, 'placeholder': 'Leave a comment here...'}),
        required=True,
        label="Comment"
    )

class PaymentForm(forms.Form):
    pass

class PaymentMethodForm(forms.Form):
    METHOD_CHOICES = [
        ('gcash', 'GCash'),
        ('paypal', 'PayPal'),
    ]
    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        label='Choose Payment Method',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class BookingFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="From"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="To"
    )
    service_id = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        empty_label="All Services",
        label="Service"
    )

class BookingForm(forms.Form):
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date"
    )
    schedule_id = forms.ModelChoiceField(
        queryset=Schedule.objects.none(),
        label="Time Slot",
        empty_label="Select a time slot"
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["schedule_id"].queryset = Schedule.objects.filter(is_available=True)

class AdminUserSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search users",
        widget=forms.TextInput(attrs={
            'placeholder': 'Search users...',
            'class': 'form-control'
        })
    )

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['available_time', 'is_available', 'capacity']

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['fullname', 'email']
        widgets = {
            'fullname': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
        }

class ServiceEditForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'category', 'name', 'description', 'price',
            'duration_hours', 'duration_minutes', 'is_active', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Category Name'}),
            'is_active': forms.CheckboxInput(),
        }

class AdminBookingLineFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="From"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="To"
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        empty_label="All Services",
        label="Service"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + BookingLine.STATUS_CHOICES,
        required=False,
        label="Status"
    )
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "User or Service"})
    )

class BookingLineStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=BookingLine.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Status"
    )