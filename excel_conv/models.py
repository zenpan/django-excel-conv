from django.db import models

# Create your models here.
class ConvJob(models.Model):
    excel_file = models.FileField(upload_to='excel_files/')
    conv_file = models.FileField(upload_to='conv_files/', null=True, blank=True,)
    upload_at = models.DateTimeField(auto_now_add=True, null=True, blank=True,)
    conv_at = models.DateTimeField(auto_now_add=False, null=True, blank=True,)
    error = models.CharField(max_length=300, null=True, blank=True,)
    success = models.BooleanField(default=False)
    # Detected (or manually set) input format key; routes the conversion.
    source_type = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return self.excel_file.name

    @property
    def source_label(self):
        """Human-readable label for the detected/selected source format."""
        from excel_conv.lib.sources import source_label
        return source_label(self.source_type)
    