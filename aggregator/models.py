from django.db import models

class Product(models.Model):
    product_link = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    product_name = models.CharField(max_length=255)
    product_price = models.CharField(max_length=50)  
    rating = models.FloatField()
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