from django.contrib import admin
from django.urls import path
from django.conf.urls import url,include
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index'),
    path('special/',views.special,name='special'),
    path('login/',include('login.urls')),
    path('logout/', views.user_logout, name='logout'),
] 