from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    product_link = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    product_name = models.CharField(max_length=255)
    product_price = models.CharField(max_length=50)  
    rating = models.FloatField(null=True, blank=True)
    number_of_ratings = models.CharField(max_length=50)  
    specifications = models.TextField()

    def __str__(self):
        return self.product_name


class ScrapedProduct(models.Model):
    product_link = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    product_name = models.CharField(max_length=255)
    product_price = models.CharField(max_length=50)
    rating = models.CharField(max_length=10, null=True, blank=True)
    number_of_ratings = models.CharField(max_length=50, null=True, blank=True)
    specifications = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    