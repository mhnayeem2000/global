from django.db import models

class SiteSettings(models.Model):

    site_email = models.EmailField(blank=True, null=True)
    site_phone = models.CharField(max_length=50, blank=True, null=True)
    site_location = models.TextField(blank=True, null=True)
    copyright_text = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return "Global Site Settings"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return SiteSettings.objects.first().save(*args, **kwargs)
        return super(SiteSettings, self).save(*args, **kwargs)
