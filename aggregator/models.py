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
