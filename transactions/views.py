from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.views import View
from . models import Transaction
from accounts.models import UserBankAccount
from .forms import DepositForm, WithdrawForm, LoanForm, TransferForm
from .constants import DEPOSIT,WITHDRAWAL, LOAN, LOAN_PAID, TRANSFER_BALANCE,RECEIVE_BALANCE
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from core.models import BankCorrupt
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.


def send_transaction_mail(account,account_no,amount,subject,template):
    
    user = account.user
    
    mail_message = render_to_string(template, {
        'user': user,
        'amount': amount,
        'account_no': account_no,
        'time': timezone.now(),
    })
        
    send_mail = EmailMultiAlternatives(subject, '' , to=[user.email])
    send_mail.attach_alternative(mail_message, 'text/html')
    send_mail.send()


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('transaction_report')
    title = ''
    
    
    def dispatch(self, request, *args, **kwargs):
        if BankCorrupt.is_corrupt == True:
            return HttpResponse("Bank is currently corrupt, transactions are temporarily disabled.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account,
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        
        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'
    
    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        account = self.request.user.account
        # print(amount)
        # print(account.balance)
        account.balance += amount
        account.save(
            update_fields=['balance']
        )
        
        messages.success(self.request, f'{amount}$ was deposited in your account Successfully!')
        
        send_transaction_mail(self.request.user.account,self.request.user.account.account_no,amount,"Deposit Message","transactions/deposit_mail.html")
        
        return super().form_valid(form)



class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'
    
    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(
            update_fields=['balance']
        )
        
        messages.success(self.request, f'Successfully Withdrawn {amount}$ from your account!')
        
        send_transaction_mail(self.request.user.account,self.request.user.account.account_no,amount,"Withdrawal Message","transactions/withdrawal_mail.html")
        
        return super().form_valid(form)
    
    
class LoanRequestView(TransactionCreateMixin):
    form_class = LoanForm
    title = 'Request For Loan'
    
    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = 3, loan_approve = True).count()
        
        if current_loan_count >= 3:
            return HttpResponse('You have crossed your limits')
        
        messages.success(self.request, f'{amount}$ load request Successfully!')
        send_transaction_mail(self.request.user.account,self.request.user.account.account_no,amount,"Loan Request Message","transactions/loan_mail.html")

        return super().form_valid(form)
    
    
    
class TransactionReportView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/transaction_report.html'
    balance = 0
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account = self.request.user.account
        )
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date)
            # Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date)
            self.balance = queryset.aggregate(Sum('amount'))['amount__sum']
        
        else:
            self.balance = self.request.user.account.balance
            
        return queryset.distinct()            
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
        })
        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id = loan_id)
        
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                messages.success(request, f'Loan ID {loan_id} paid successfully!')
            else:
                messages.error(request, 'Insufficient funds')
            return redirect('loan_list')


class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'Transactions/loan_request.html'
    context_object_name = 'loans'
    
    def dispatch(self, request, *args, **kwargs):
        if BankCorrupt.is_corrupt == True:
            return HttpResponse("Bank is currently corrupted.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type = 3)
        return queryset



class TransferBalanceView(TransactionCreateMixin):
    form_class = TransferForm
    title = 'Transfer Balance'
    
    def get_initial(self):
        initial = {'transaction_type': TRANSFER_BALANCE}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        to_account_no = form.cleaned_data.get('account_no')
        
        from_account = self.request.user.account
        from_account.balance -= amount
        from_account.save(
            update_fields=['balance']
        )
        
        to_account = get_object_or_404(UserBankAccount, account_no = to_account_no)
        
        to_account.balance += amount
        to_account.save(
            update_fields=['balance']
        )
        
        transaction_log_sender = form.save(commit=False)
        transaction_log_sender.account = from_account
        transaction_log_sender.balance_after_transaction = from_account.balance
        transaction_log_sender.transaction_type = TRANSFER_BALANCE
        transaction_log_sender.save()
        
        transaction_log_recipient = Transaction(
            account=to_account,
            amount=amount,
            balance_after_transaction=to_account.balance,
            transaction_type=RECEIVE_BALANCE
        )
        transaction_log_recipient.save()
        
        messages.success(self.request, f'{amount}$ transferred successfully!')
        
        send_transaction_mail(self.request.user.account,self.request.user.account.account_no,amount,f"Transferred to Account {to_account.account_no}","transactions/transfer_money_mail.html")
        send_transaction_mail(to_account,to_account_no, amount, f"Received {from_account.account_no}", "transactions/receive_money_mail.html")
        
        return super().form_valid(form)
