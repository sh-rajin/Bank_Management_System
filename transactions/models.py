from django.db import models
from accounts.models import UserBankAccount
from . constants import TRANSACTION_TYPE
# Create your models here.

class Transaction(models.Model):
    account = models.ForeignKey(UserBankAccount, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    loan_approve = models.BooleanField(default=False)
    account_no = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        
        
    def __str__(self):
        return f'{self.account.account_no} {self.get_transaction_type_display()}'
    
