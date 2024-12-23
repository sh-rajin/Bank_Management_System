from django.contrib import admin
from . models import Transaction
from .views import send_transaction_mail
# Register your models here.

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display =['account', 'amount', 'balance_after_transaction', 'transaction_type', 'loan_approve']
    
    def save_model(self, request, obj, form, change):
        if obj.loan_approve == True:
            obj.account.balance += obj.amount
            obj.balance_after_transaction = obj.account.balance
            send_transaction_mail(obj.account, obj.account.account_no, obj.amount ,"Loan Approval", "transactions/loan_approval.html")
            obj.account.save()
        
        super().save_model(request, obj, form, change)


