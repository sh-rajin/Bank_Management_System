from django.db import models

# Create your models here.

class BankCorrupt(models.Model):
    is_corrupt = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.is_corrupt
