from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from datetime import datetime
import base64

from .forms import RegistrationForm, LoginForm, VoucherForm, MpesaForm
from .models import Plan, Voucher, Payment
from django_daraja.mpesa.core import MpesaClient

# Set up logging
logger = logging.getLogger(__name__)

# Generate M-Pesa password dynamically
def generate_mpesa_password(shortcode, passkey, timestamp):
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')

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
                
                try:
                    plan = Plan.objects.get(id=plan_id)
                    # Create a pending payment
                    payment = Payment.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        plan=plan,
                        amount=amount,
                        status='Pending'
                    )

                    # Initialize MpesaClient
                    mpesa_client = MpesaClient()
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # e.g., 20250825233000
                    password = generate_mpesa_password(174379, 'bfb279f9a9b9dbcfe158e97dd71a467cd2e0c893059b10f78e6b72ad1ed2c91', timestamp)
                    response = mpesa_client.stk_push(
                        phone_number=f'254{phone_number[-9:]}',  # Ensure Kenyan format
                        amount=amount,
                        business_shortcode=174379,
                        password=password,
                        timestamp=timestamp,
                        callback_url='http://127.0.0.1:8000/mpesa/stk-push/callback/',  # Update with ngrok URL
                        account_reference=f'mtec_{plan_id}',
                        transaction_desc=f'Payment for {plan.name}'
                    )
                    
                    if response.get('ResponseCode') == '0':
                        payment.mpesa_code = response.get('MerchantRequestID', '')
                        payment.save()
                        messages.success(request, f"M-Pesa payment initiated. Complete the payment on your phone using Merchant Request ID: {payment.mpesa_code}")
                    else:
                        payment.status = 'Failed'
                        payment.save()
                        messages.error(request, f"Payment initiation failed: {response.get('errorMessage', 'Unknown error')}")
                except Plan.DoesNotExist:
                    messages.error(request, "Selected plan does not exist.")
                except Exception as e:
                    logger.error(f"STK Push error: {str(e)}")
                    messages.error(request, "An error occurred during payment initiation. Please try again.")
            else:
                messages.error(request, "Please enter a valid phone number and amount.")
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

    def post(self, request):
        if 'logout' in request.POST:
            logout(request)
            messages.success(request, "You have been logged out.")
            return redirect('index')
        return redirect('dashboard')

# Callback View to handle M-Pesa STK Push response
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = request.POST
        logger.info(f"M-Pesa Callback Data: {data}")
        merchant_request_id = data.get('MerchantRequestID')
        result_code = data.get('ResultCode')
        result_desc = data.get('ResultDesc')
        transaction_id = data.get('TransactionID')

        try:
            payment = Payment.objects.get(mpesa_code=merchant_request_id)
            if result_code == '0':
                payment.status = 'Success'
                payment.transaction_id = transaction_id
                payment.save()
                messages.success(request, f"Payment {merchant_request_id} completed successfully.")
            else:
                payment.status = 'Failed'
                payment.save()
                messages.error(request, f"Payment failed: {result_desc}")
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for MerchantRequestID: {merchant_request_id}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment not found'}, status=400)

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'}, status=400)