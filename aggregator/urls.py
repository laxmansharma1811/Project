from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('select_product/<int:product_id>/', select_product, name='select_product'),
    path('comparison/', comparison, name='comparison'),
    path('analysis/', analysis, name='analysis'),
    path('search/', ProductSearchView.as_view(), name='product_search'),
    path('save-to-csv/', save_to_csv, name='save_to_csv'),
    path('hukut/', search_products, name='search_products'),
    path('save-hukut/', save_hukut_to_csv, name='save_hukut'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
]
