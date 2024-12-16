from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Donation, Request, FoodItem
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

class RequestForm(forms.ModelForm):
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    food_item_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'list': 'food-items'}))
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    unit = forms.ChoiceField(choices=FoodItem.UNIT_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    urgency = forms.ChoiceField(choices=URGENCY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    pickup_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Request
        fields = ['food_item_name', 'quantity', 'unit', 'urgency', 'description', 'pickup_date']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def save(self, commit=True):
        instance = super().save(commit=False)
        food_item_name = self.cleaned_data['food_item_name']
        quantity = self.cleaned_data['quantity']
        unit = self.cleaned_data['unit']
        
        
        food_item, created = FoodItem.objects.get_or_create(
            food_name=food_item_name,
            defaults={'quantity': quantity, 'unit': unit}
        )
        
        if not created:
            food_item.quantity = quantity
            food_item.unit = unit
            food_item.save()
        
        instance.food_item = food_item
        if commit:
            instance.save()
        return instance

class DonationForm(forms.ModelForm):
    food_item = forms.ModelChoiceField(
        queryset=FoodItem.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a food item"
    )
    new_food_item = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Or enter a new food item'})
    )
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Donation
        fields = ['food_item', 'new_food_item', 'quantity', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        food_item = cleaned_data.get('food_item')
        new_food_item = cleaned_data.get('new_food_item')
        
        if not food_item and not new_food_item:
            raise forms.ValidationError("Please either select an existing food item or enter a new one.")
        
        return cleaned_data

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['food_name', 'quantity', 'expiry_date']
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity
