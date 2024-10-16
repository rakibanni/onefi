import json
from django.db.models import Sum
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Customer, Payment, Expense

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def get_dashboard_data(self):
        total_income = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        total_due = Customer.objects.filter(is_paid=False).aggregate(Sum('monthly_bill'))['monthly_bill__sum'] or 0
        total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        new_customers = Customer.objects.filter(join_date=timezone.now().date()).count()
        return {
            'total_income': total_income,
            'total_due': total_due,
            'total_expense': total_expense,
            'new_customers': new_customers,
        }

    async def receive(self, text_data):
        data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps(data))
