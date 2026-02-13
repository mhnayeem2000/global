from django.db import models


class PaymentProvider(models.Model):
    class ProviderType(models.TextChoices):
        CRYPTO = 'CRYPTO', 'Crypto'
        FIAT = 'FIAT', 'Fiat Gateway'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Manual Bank Transfer' 

    title = models.CharField(max_length=100)
    provider_name_code = models.CharField(max_length=50, unique=True, help_text="The code name RiskPay uses, e.g., 'simplex'")
    logo = models.ImageField(upload_to='provider_logos/', null=True, blank=True)
    account_number = models.CharField(max_length=255, blank=True, null=True, help_text="Your account number with this provider, if any.")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Enable or disable this provider on the frontend.")
    bank_details = models.TextField(blank=True, null=True, help_text="Markdown or text instructions for bank transfer.")
    
    processing_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="The fee percentage, e.g., 12.00 for 12%"
    )
    type = models.CharField(max_length=20, choices=ProviderType.choices, default=ProviderType.FIAT)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)

    def __str__(self):
        return self.title
