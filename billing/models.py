from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum


class Zone(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Collector(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True)
    referral_code = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


    def total_collection(self):
        return Payment.objects.filter(collector=self).aggregate(models.Sum('amount'))['amount__sum'] or 0

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    monthly_bill = models.DecimalField(max_digits=10, decimal_places=2)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_id = models.CharField(max_length=6, unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)
    referrer = models.ForeignKey(Collector, on_delete=models.SET_NULL, null=True)
    join_date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    due_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # নতুন ফিল্ড

    def __str__(self):
        return f"{self.name} ({self.customer_id})"

    def total_due(self):
        return self.monthly_bill - Payment.objects.filter(customer=self, date__month=timezone.now().month).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def latest_bill(self):
        return self.bill_set.order_by('-generated_date').first()
    
class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    collector = models.ForeignKey(Collector, on_delete=models.SET_NULL, null=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:  # শুধুমাত্র নতুন পেমেন্ট যুক্ত হলে
            self.update_customer_balance()
            self.update_total_due()

    def update_customer_balance(self):
        self.customer.due_balance -= self.amount
        self.customer.save()

    def update_total_due(self):
        total_due = Customer.objects.aggregate(total=Sum('due_balance'))['total'] or 0
        # আপনার ড্যাশবোর্ড মডেল আপডেট করুন, উদাহরণস্বরূপ:
        dashboard = Dashboard.objects.first()  # অথবা যেভাবে আপনি ড্যাশবোর্ড ডেটা স্টোর করেন
        if dashboard:
            dashboard.total_due = total_due
            dashboard.save()

class Expense(models.Model):
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.description} - {self.amount}"

class Bill(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    generated_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Bill for {self.customer.name} - {self.generated_date}"

class Dashboard(models.Model):
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # অন্যান্য ড্যাশবোর্ড-সংক্রান্ত ফিল্ড...
