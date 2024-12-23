from django.urls import path
from .views import DepositMoneyView, WithdrawMoneyView, LoanRequestView, TransactionReportView, PayLoanView, LoanListView, TransferBalanceView

urlpatterns = [
    path('deposit/', DepositMoneyView.as_view(), name='deposit_money'),
    path('withdraw/', WithdrawMoneyView.as_view(), name='withdraw_money'),
    path('loan_request/', LoanRequestView.as_view(), name='loan_request'),
    path('transaction_report/', TransactionReportView.as_view(), name='transaction_report'),
    path('loan_list/', LoanListView.as_view(), name='loan_list'),   
    path('pay_loan/<int:loan_id>/', PayLoanView.as_view(), name='pay_loan'),
    path('transfer_balance/', TransferBalanceView.as_view(), name='transfer_balance'),
]