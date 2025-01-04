import csv
from django.core.management.base import BaseCommand
from aggregator.models import Product

class Command(BaseCommand):
    help = 'Load default product data from CSV'

    def handle(self, *args, **kwargs):
        file_path = 'product_aggregator/data/scraped_products.csv'
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert empty strings to None for the rating field
                    rating_value = row['Rating']
                    if rating_value == '':
                        rating_value = None
                    else:
                        rating_value = float(rating_value)

                    Product.objects.get_or_create(
                        product_link=row['Product Link'],
                        image_url=row['Image URL'],
                        product_name=row['Product Name'],
                        product_price=row['Product Price'],
                        rating=rating_value,
                        number_of_ratings=row['Number of Ratings'],
                        specifications=row['Specifications'],
                    )
            self.stdout.write(self.style.SUCCESS('Default CSV data loaded successfully.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'Value error: {e}'))
