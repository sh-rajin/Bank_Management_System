from django import forms
from . models import Transaction
from accounts.models import UserBankAccount
from core.models import BankCorrupt


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount', 
            'transaction_type',
        ]
        
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()
        
    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()
    
    

    
class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 200
        amount = self.cleaned_data.get('amount')
        # print(amount)
        if amount < min_deposit_amount:
            raise forms.ValidationError (
                f'Minimum deposit amount is {min_deposit_amount}.'
                )
        return amount
    
class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        min_withdrawal_amount = 200
        max_withdrawal_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        if amount < min_withdrawal_amount:
            raise forms.ValidationError (
                f'Minimum withdrawal amount is {min_withdrawal_amount}.'
                )
        if amount > max_withdrawal_amount:
            raise forms.ValidationError (
                f'Maximum withdrawal amount is {max_withdrawal_amount}.'
                )
        if amount > balance:
            raise forms.ValidationError (
                'Insufficient balance.'
                )
        return amount
    
    
class LoanForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        account = self.account
        balance = account.balance
        max_loan_amount = balance*2
        if amount > max_loan_amount:
            raise forms.ValidationError (
                f'Maximum loan amount is {max_loan_amount}.'
                )
        return amount
    
class TransferForm(TransactionForm):
    account_no  = forms.IntegerField(label="Recipient Account Number")
    class Meta(TransactionForm.Meta):
        fields = TransactionForm.Meta.fields + ['account_no']
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        account = self.account
        balance = account.balance
        
        if amount is None:
            raise forms.ValidationError('Amount is required.')
        
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        
        if amount > balance:
            raise forms.ValidationError('Insufficient balance.')
        
        return amount
    
    def clean_account_no(self):
        account_no = self.cleaned_data.get('account_no')
        
        if len(str(account_no)) != 6:
            raise forms.ValidationError('Account number must be exactly 6 digits long.')
        
        if not UserBankAccount.objects.filter(account_no=account_no).exists():
            raise forms.ValidationError('Invalid account number.')
        
        if self.account and self.account.account_no == account_no:
            raise forms.ValidationError('You cannot transfer funds to your own account.')
        
        return account_no