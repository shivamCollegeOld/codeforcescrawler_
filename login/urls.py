from django.conf.urls import url
from . import views
from django.urls import path

# SET THE NAMESPACE!
app_name = 'login'

# Be careful setting the name to just /login use userlogin instead!
urlpatterns=[
    url(r'^register/$',views.register,name='register'),
    url(r'^user_login/$',views.user_login,name='user_login'),
]