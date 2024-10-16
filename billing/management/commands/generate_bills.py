from django.core.management.base import BaseCommand
from billing.utils import generate_monthly_bills

class Command(BaseCommand):
    help = 'Generates monthly bills for all active customers'

    def handle(self, *args, **kwargs):
        generate_monthly_bills()
        self.stdout.write(self.style.SUCCESS('Successfully generated bills'))
