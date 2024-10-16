from django import forms
from .models import Customer, Payment, Expense
from django.utils import timezone

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'monthly_bill', 'advance_payment', 'due_balance', 'zone', 'referrer']
        widgets = {
            'due_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }

class PaymentForm(forms.ModelForm):
    customer_id = forms.CharField(max_length=6, label='Customer ID')
    date = forms.DateTimeField(initial=timezone.now, widget=forms.HiddenInput())

    class Meta:
        model = Payment
        fields = ['customer_id', 'amount', 'collector', 'date']

    def clean_customer_id(self):
        customer_id = self.cleaned_data['customer_id']
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            raise forms.ValidationError("Invalid Customer ID")
        return customer_id

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date']
