from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib.auth import login,logout
from .forms import UserRegisterForm, UserUpdateForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.views import View
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

# Create your views here.

def send_transaction_mail(user,subject,template):
    
    
    mail_message = render_to_string(template, {
        'user': user,
        'time': timezone.now(),
    })
        
    send_mail = EmailMultiAlternatives(subject, '' , to=[user.email])
    send_mail.attach_alternative(mail_message, 'text/html')
    send_mail.send()

class UserRegisterView(FormView):
    form_class = UserRegisterForm
    template_name = 'accounts/user_registration.html'
    success_url = reverse_lazy('profile')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request,user)
        return super().form_valid(form)
    
    
class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    
    def get_success_url(self):
        return reverse_lazy('home')
    

class UserPasswordChange(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        # Call the parent class's form_valid method
        response = super().form_valid(form)

        # Add a success message
        messages.success(self.request, 'Password changed successfully!')

        # Send a transactional email (assuming you have a function to send emails)
        send_transaction_mail(
            self.request.user, 
            "Password Change Successful", 
            "accounts/password_change_email.html"
        )

        return response

    
class UserLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return redirect('home')
    
class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        # print(request.user)
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    
    