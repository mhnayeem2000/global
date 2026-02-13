from django.core.management.base import BaseCommand
from django.conf import settings
from ecommerce.models import Transaction
from billing.models import Milestone
import requests

class Command(BaseCommand):
    help = 'Checks the status of PENDING transactions with RiskPay'

    def handle(self, *args, **options):
        self.stdout.write("Starting payment status check...")

        pending_transactions = Transaction.objects.filter(
            status=Transaction.Status.PENDING,
            gateway_ipn_token__isnull=False
        ).exclude(gateway_ipn_token='')

        count = pending_transactions.count()
        self.stdout.write(f"Found {count} pending transactions to check.")

        for transaction in pending_transactions:
            self.check_transaction(transaction)

        self.stdout.write("Status check complete.")

    def check_transaction(self, transaction):
        token = transaction.gateway_ipn_token
        
        url = settings.RISKPAY_API_STATUS_URL 
        params = {'ipn_token': token}

        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(f"API Error for Tx #{transaction.id}: {response.status_code}"))
                return

            data = response.json()
            remote_status = data.get('status') 

            if remote_status and remote_status.upper() == 'ACCEPT':
                self.stdout.write(self.style.SUCCESS(f"Transaction #{transaction.id} confirmed as SUCCESS! Updating..."))
                
                transaction.status = Transaction.Status.SUCCESS
                
                transaction.gateway_txid_out = data.get('txid_out', transaction.gateway_txid_out)
                transaction.gateway_coin_type = data.get('coin', transaction.gateway_coin_type)
                transaction.gateway_value_in_coin = data.get('value_coin', transaction.gateway_value_in_coin)
                transaction.save()

                if transaction.milestone:
                    transaction.milestone.status = Milestone.Status.PAID
                    transaction.milestone.save()
            elif remote_status and remote_status.upper() in ['REJECT', 'FAILED']:
                 self.stdout.write(self.style.ERROR(f"Transaction #{transaction.id} FAILED."))
                 transaction.status = Transaction.Status.FAILED
                 transaction.save()
            else:
                self.stdout.write(f"Transaction #{transaction.id} is still {remote_status}...")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking Tx #{transaction.id}: {str(e)}"))


