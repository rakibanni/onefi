from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Customer, Payment, Collector, Expense, Bill
from .forms import CustomerForm, PaymentForm, ExpenseForm
from django.contrib import messages
from django.http import HttpResponse
from .utils import generate_bill_pdf
from rest_framework import viewsets
from .serializers import CustomerSerializer, PaymentSerializer
from .models import Zone
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from routeros_api import RouterOsApiPool
from routeros_api.exceptions import RouterOsApiConnectionError

@login_required
def dashboard(request):
    total_income = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_due = Customer.objects.aggregate(Sum('due_balance'))['due_balance__sum'] or 0
    total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    new_customers = Customer.objects.filter(is_active=True).count()
    inactive_customers = Customer.objects.filter(is_active=False).count()

    context = {
        'total_income': total_income,
        'total_due': total_due,
        'total_expense': total_expense,
        'new_customers': new_customers,
        'inactive_customers': inactive_customers,
    }
    return render(request, 'billing/dashboard.html', context)

@login_required
def customer_list(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')
    zone_id = request.GET.get('zone')

    customers = Customer.objects.filter(is_active=True)

    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(customer_id__icontains=query))

    if filter_type == 'paid':
        customers = customers.filter(is_paid=True)
    elif filter_type == 'unpaid':
        customers = customers.filter(is_paid=False)

    if zone_id:
        customers = customers.filter(zone_id=zone_id)

    for customer in customers:
        customer.last_payment = Payment.objects.filter(customer=customer).order_by('-date').first()

    zones = Zone.objects.all()

    return render(request, 'billing/customer_list.html', {'customers': customers, 'zones': zones})


@login_required
def customer_profile(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    payments = Payment.objects.filter(customer=customer).order_by('-date')
    context = {
        'customer': customer,
        'payments': payments,
    }
    return render(request, 'billing/customer_profile.html', context)

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            # গ্রাহকের ফোন নম্বরের শেষ 6 ডিজিট নিয়ে কাস্টমার আইডি তৈরি করা
            phone_number = form.cleaned_data['phone']
            customer.customer_id = phone_number[-6:]
            customer.save()
            messages.success(request, f'কাস্টমার {customer.name} সফলভাবে যোগ করা হয়েছে।')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'billing/add_customer.html', {'form': form})

@login_required
def add_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            customer = Customer.objects.get(customer_id=customer_id)
            payment = form.save(commit=False)
            payment.customer = customer
            payment.save()
            if payment.amount >= customer.monthly_bill:
                customer.is_paid = True
                customer.save()
            return redirect('customer_profile', customer_id=customer.customer_id)
    else:
        form = PaymentForm()
    return render(request, 'billing/add_payment.html', {'form': form})

def collector_stats(request):
    collectors = Collector.objects.select_related('user').all()
    for collector in collectors:
        collector.total_collection = Payment.objects.filter(collector=collector).aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'billing/collector_stats.html', {'collectors': collectors})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'billing/add_expense.html', {'form': form})

def view_bill_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    pdf = generate_bill_pdf(bill)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=bill_{bill.id}.pdf'
    response.write(pdf)
    return response

@login_required
def add_payment_for_customer(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.customer = customer
            payment.save()
            if payment.amount >= customer.monthly_bill:
                customer.is_paid = True
                customer.save()
            return redirect('customer_profile', customer_id=customer.customer_id)
    else:
        form = PaymentForm(initial={'customer_id': customer.customer_id})
    return render(request, 'billing/add_payment.html', {'form': form, 'customer': customer})


MIKROTIK_IP = '11.11.11.1'
MIKROTIK_USERNAME = 'admin'
MIKROTIK_PASSWORD = 'Onefi+700'
MIKROTIK_PORT = 8729

def connect_to_mikrotik():
    connection = RouterOsApiPool(
        host=MIKROTIK_IP,
        username=MIKROTIK_USERNAME,
        password=MIKROTIK_PASSWORD,
        port=8728,  # স্ট্যান্ডার্ড API পোর্ট
        plaintext_login=True
    )
    api = connection.get_api()
    return api, connection

def provide_internet(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        mac_address = request.POST.get('mac_address')

        customer = Customer.objects.filter(customer_id=customer_id).first()
        if customer:
            api, connection = connect_to_mikrotik()
            
            # ফায়ারওয়াল রুল যোগ করা
            api.get_resource('/ip/firewall/filter').add(
                chain='forward',
                src_mac_address=mac_address,
                action='accept',
                comment=customer.name,
                place_before='0'
            )

            connection.disconnect()
            messages.success(request, f"{customer.name} এর জন্য ইন্টারনেট সংযোগ প্রদান করা হয়েছে।")
            return redirect('dashboard')
        else:
            messages.error(request, "কাস্টমার আইডি পাওয়া যায়নি। অনুগ্রহ করে সঠিক কাস্টমার আইডি প্রবেশ করুন।")
    
    return render(request, 'billing/provide_internet.html')

import logging
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

def online_customers(request):
    try:
        # MikroTik সংযোগ
        api, connection = connect_to_mikrotik()
        online_users = api.get_resource('/ip/arp').get()

        # সার্চ কুয়েরি
        search_query = request.GET.get('search', '')
        logger.debug(f"Search query: {search_query}")

        processed_users = []

        # প্রতিটি অনলাইন গ্রাহকের তথ্য প্রসেস এবং ব্লক স্ট্যাটাস চেক
        for user in online_users:
            if search_query.lower() in user.get('mac-address', '').lower() or search_query.lower() in user.get('address', '').lower():
                
                # MikroTik ফায়ারওয়াল থেকে ব্লক স্ট্যাটাস চেক
                is_blocked = api.get_resource('/ip/firewall/filter').get(mac_address=user.get('mac-address', ''))
                
                # ব্লক স্ট্যাটাস যুক্ত করে প্রসেসড ইউজার তালিকায় যোগ করা
                processed_users.append({
                    'mac_address': user.get('mac-address', ''),
                    'address': user.get('address', ''),
                    'interface': user.get('interface', ''),
                    'blocked': bool(is_blocked)  # ব্লক স্ট্যাটাস যুক্ত করা
                })

        logger.debug(f"Number of processed users: {len(processed_users)}")

        # সংযোগ বন্ধ করা
        connection.disconnect()

        # Pagination (প্রতি পৃষ্ঠায় ২৫ জন গ্রাহক দেখাবে)
        paginator = Paginator(processed_users, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    except RouterOsApiConnectionError as e:
        page_obj = []
        messages.error(request, f"MikroTik সংযোগ সমস্যা: {str(e)}")

    # কন্টেক্সট সেট করা
    context = {
        'page_obj': page_obj,
        'search_query': search_query
    }

    # রেন্ডার করা
    return render(request, 'billing/online_customers.html', context)

def toggle_block_status(request, mac_address):
    try:
        api, connection = connect_to_mikrotik()
        
        # Check if user is already blocked
        firewall_rule = api.get_resource('/ip/firewall/filter').get(mac_address=mac_address)
        
        if firewall_rule:
            # Unblock the user by removing the firewall rule
            api.get_resource('/ip/firewall/filter').remove(id=firewall_rule[0]['id'])
            messages.success(request, f"{mac_address} এর ইন্টারনেট পুনরায় চালু করা হয়েছে।")
        else:
            # Block the user by adding a firewall rule
            api.get_resource('/ip/firewall/filter').add(
                chain="forward",
                src_mac_address=mac_address,
                action="drop"
            )
            messages.success(request, f"{mac_address} এর ইন্টারনেট ব্লক করা হয়েছে।")

        connection.disconnect()

    except RouterOsApiConnectionError as e:
        messages.error(request, f"MikroTik সংযোগ সমস্যা: {str(e)}")

    return redirect('online_customers')




