from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, VoucherForm, MpesaForm
from .models import Plan, Voucher, Payment
from mpesa.models import LipaNaMpesaOnlinePayment
import requests

# Create your views here.

class IndexView(View):
    def get(self, request):
        plans = Plan.objects.all()
        voucher_form = VoucherForm()
        mpesa_form = MpesaForm()
        login_form = LoginForm()
        context = {
            'plans': plans,
            'voucher_form': voucher_form,
            'mpesa_form': mpesa_form,
            'login_form': login_form,
        }
        return render(request, 'index.html', context)
    
    def post(self, request):
        if 'voucher_code' in request.POST:
            form = VoucherForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data['code']
                try:
                    voucher = Voucher.objects.get(code=code, used=False)
                    if request.user.is_authenticated:
                        voucher.used = True
                        voucher.user = request.user
                        voucher.save()
                        messages.success(request, f"Voucher {code} applied successfully!")
                    else:
                        messages.error(request, "You must be logged in to use a voucher.")
                except Voucher.DoesNotExist:
                    messages.error(request, "Invalid or already used voucher code.")
            else:
                messages.error(request, "Please enter a valid voucher code.")
            return redirect('index')
        
        elif 'phone_number' in request.POST:
            form = MpesaForm(request.POST)
            if form.is_valid():
                phone_number = form.cleaned_data['phone_number']
                amount = form.cleaned_data['amount']
                plan_id = form.cleaned_data['plan_id']
                plan = Plan.objects.get(id=plan_id)
                
                try:
                    plan = Plan.objects.get(id=plan_id)
                    payment = Payment.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        plan=plan,
                        amount=amount,
                        status='Pending'
                    )
                    lipa_payment = LipaNaMpesaOnlinePayment.objects.create(
                        phone_number=phone_number,
                        amount=amount,
                        account_reference=f"Plan {plan.name}",
                        transaction_desc=f"Payment for {plan.name}",
                        callback_url='http://127.0.0.1:8000/mpesa/request-stk-push/',
                        payment=payment
                    )
                    lipa_payment.initiate_payment()
                    messages.success(request, f"Mpesa payment initiated. Please complete the payment on your phone.")
                except Plan.DoesNotExist:
                    messages.error(request, "Selected plan does not exist.")
            else:
                messages.error(request, "Please enter valid payment details.")
            return redirect('index')
        
        elif 'login_username' in request.POST:
            form = LoginForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
            return redirect('index')
        else:
            messages.error(request, "Invalid form submission.")
            return redirect('index')
        
class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to access the dashboard.")
            return redirect('index')
        
        vouchers = Voucher.objects.filter(user=request.user)
        payments = Payment.objects.filter(user=request.user)
        context = {
            'vouchers': vouchers,
            'payments': payments,
        }
        return render(request, 'dashboard.html', context)        
