from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('select_product/<int:product_id>/', select_product, name='select_product'),
    path('comparison/', comparison, name='comparison'),
    path('analysis/', analysis, name='analysis'),
    path('scrape/', scrape_view, name='scrape'),
]
