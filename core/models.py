from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Plan(models.Model):
    name = models.CharField(max_length=100)
    duration_hours = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    data_limit_mb = models.IntegerField(null=True, blank=True)  # Optional data limit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    
    def __str__(self):
        return f"{self.name} - KSH {self.price} for {self.duration_hours} hours"
    
    
class Voucher(models.Model):
    code = models.CharField(max_length=50, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Voucher {self.code} for {self.plan.name} - {'Used' if self.used else 'Unused'}"
    

class Payment(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL) 
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_code = models.CharField(max_length=100, blank=True) 
    status = models.CharField(max_length=50, default='Pending')
    timestamp = models.DateTimeField(auto_now_add=True)  
    
    def __str__(self):
       return f"Payment {self.mpesa_code} for {self.plan}"