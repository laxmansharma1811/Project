from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

from product_aggregator.aggregator.scraper.utils import scrape_daraz_products
from .models import *
from django.db.models import Q
import matplotlib.pyplot as plt
import io
import urllib, base64
from django.http import JsonResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
    
    # Context for the template
    context = {
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'price_min': price_min,
        'price_max': price_max
    }
    
    return render(request, 'home.html', context)



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
    
    return render(request, 'comparison.html', context)



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

    return render(request, 'analysis.html', context)


def scrape_view(request):
    query = request.GET.get('query', 'laptops')  # Default to 'laptops' if no query is provided
    required_spec_keys = [
        'Brand', 'SKU', 'Wireless Connectivity', 'Display Size', 'Operating System', 'CPU Cores',
        'Ram Memory', 'Model No.', 'Touch Pad', 'Storage Capacity', 'Processor', 'Storage Type', 'Touch',
        'Generation', 'What’s in the box'
    ]
    data = scrape_daraz_products(query, required_spec_keys)
    return JsonResponse({'data': data})



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

    return render(request, 'register.html')



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

    return render(request, 'login.html')



@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out!")
    return redirect('login')

