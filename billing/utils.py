from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Customer, Bill
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def generate_monthly_bills():
    today = timezone.now().date()
    due_date = today + relativedelta(days=15)  # বিল জেনারেট করার 15 দিন পর
    
    for customer in Customer.objects.filter(is_active=True):
        Bill.objects.create(
            customer=customer,
            amount=customer.monthly_bill,
            due_date=due_date
        )

def generate_bill_pdf(bill):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content to the PDF
    p.drawString(100, 750, f"Bill for {bill.customer.name}")
    p.drawString(100, 730, f"Amount: {bill.amount}")
    p.drawString(100, 710, f"Due Date: {bill.due_date}")
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    return pdf