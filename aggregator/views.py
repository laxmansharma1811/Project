import json
import subprocess
import sys
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Q
import matplotlib.pyplot as plt
import io
import base64
from django.views.generic import TemplateView
from .scraper.utils import DarazScraper
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import csv
from pathlib import Path
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .scraper.hukut import scrape_products



# Create your views here.


def clean_price(price_str):
    return float(price_str.replace('Rs.', '').replace('₹', '').replace(',', '').strip())

@login_required(login_url='login')
def home(request):
    # Get query parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Filter by search query
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(specifications__icontains=search_query)
        )
    
    # Filter by price range
    if price_min or price_max:
        filtered_products = []
        for product in products:
            try:
                price = clean_price(product.product_price)
                if price_min and price < float(price_min):
                    continue
                if price_max and price > float(price_max):
                    continue
                filtered_products.append(product)
            except ValueError:
                # Handle cases where price cannot be converted
                continue
        products = filtered_products
    
    # Sort products
    if sort_by == 'price_low':
        products = sorted(products, key=lambda x: clean_price(x.product_price))
    elif sort_by == 'price_high':
        products = sorted(products, key=lambda x: clean_price(x.product_price), reverse=True)
    elif sort_by == 'rating':
        products = sorted(products, key=lambda x: x.rating, reverse=True)
    
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Context for the template
    context = {
        'page_obj': page_obj,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'price_min': price_min,
        'price_max': price_max
    }
    
    return render(request, 'dashboard/home.html', context)



def select_product(request, product_id):
    selected_products = request.session.get('selected_products', [])
    
    if product_id not in selected_products:
        if len(selected_products) >= 3:  # Limit of 3 products
            messages.warning(request, "You can only compare up to 3 products at a time.")
            return redirect('home')
            
        selected_products.append(product_id)
        request.session['selected_products'] = selected_products
        
    if len(selected_products) >= 2:  # Redirect when 2 or more products selected
        return redirect('comparison')
    
    return redirect('home')



def comparison(request):
    selected_product_ids = request.session.get('selected_products', [])
    products = Product.objects.filter(id__in=selected_product_ids)
    
    price_differences = []
    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            diff = abs(clean_price(products[i].product_price) - clean_price(products[j].product_price))
            price_differences.append({
                'products': f'{products[i].product_name} vs {products[j].product_name}',
                'difference': diff
            })

    if request.method == 'POST' and 'clear_comparison' in request.POST:
        request.session['selected_products'] = []
        messages.success(request, "Comparison cleared.")
        return redirect('home')
    
    if request.method == 'POST' and 'remove_product' in request.POST:
        product_id = int(request.POST.get('remove_product'))
        selected_products = request.session.get('selected_products', [])
        if product_id in selected_products:
            selected_products.remove(product_id)
            request.session['selected_products'] = selected_products
            messages.success(request, "Product removed from comparison.")
            if len(selected_products) < 2:
                return redirect('home')
            return redirect('comparison')
    
    context = {
        'products': products,
        'price_differences': price_differences,
    }
    
    return render(request, 'comparison/comparison.html', context)



@login_required(login_url='login')
def analysis(request):
    selected_product_ids = request.session.get('selected_products', [])
    products = Product.objects.filter(id__in=selected_product_ids)

    # Calculate price differences
    price_differences = []
    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            diff = abs(clean_price(products[i].product_price) - clean_price(products[j].product_price))
            price_differences.append({
                'products': f"{products[i].product_name} vs {products[j].product_name}",
                'difference': diff
            })

    # Generate a price comparison bar chart
    product_names = [p.product_name for p in products]
    product_prices = [clean_price(p.product_price) for p in products]

    plt.figure(figsize=(8, 6))
    plt.bar(product_names, product_prices, color='skyblue')
    plt.xlabel("Products")
    plt.ylabel("Price (Rs.)")
    plt.title("Product Price Comparison")
    plt.tight_layout()

    # Save the chart as a base64-encoded image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    context = {
        'products': products,
        'price_differences': price_differences,
        'chart_url': f"data:image/png;base64,{chart_url}",
    }

    return render(request, 'comparison/analysis.html', context)




class ProductSearchView(TemplateView):
    template_name = 'live/search.html'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        if query and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Scrape products
            scraper = DarazScraper()
            products = scraper.search_products(query, limit=5)

            # Save each product to the database
            for product in products:
                ScrapedProduct.objects.get_or_create(
                    product_link=product['product_link'],
                    defaults={
                        'image_url': product['image_url'],
                        'product_name': product['product_name'],
                        'product_price': product['product_price'],
                        'rating': product.get('rating'),
                        'number_of_ratings': product.get('number_of_ratings'),
                        'specifications': product.get('specifications'),
                    }
                )
            return JsonResponse({'products': products})

        return render(request, self.template_name)
    

def search_products(request):
    if request.method == "POST":
        query = request.POST.get('query')
        results = scrape_products(query)
        return JsonResponse({'products': results})
    return render(request, "live/hukut_live.html")


@login_required(login_url='login')    
@csrf_exempt
def save_to_csv(request):
    if request.method == 'POST':
        try:
            product_data = json.loads(request.body)
            csv_path = 'product_aggregator/data/scraped_products.csv'
            
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
                fieldnames = ['Product Link', 'Image URL', 'Product Name', 'Product Price', 
                            'Rating', 'Number of Ratings', 'Specifications']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                csv_row = {
                    'Product Link': product_data['product_link'],
                    'Image URL': product_data['image_url'],
                    'Product Name': product_data['product_name'],
                    'Product Price': product_data['product_price'],
                    'Rating': float(product_data['rating']),
                    'Number of Ratings': product_data['number_of_ratings'],
                    'Specifications': product_data['specifications']
                }
                writer.writerow(csv_row)

            # Run the management command to load the CSV data
            subprocess.run([sys.executable, 'manage.py', 'load_default_csv'], check=True)

            return JsonResponse({'status': 'success', 'message': 'Product saved to CSV and data loaded into database'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)





def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user) 
        return redirect('home')

    return render(request, 'authentication/register.html')



def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password!")
            return redirect('login')

    return render(request, 'authentication/login.html')



@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out!")
    return redirect('login')

