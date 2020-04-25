from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfileInfo(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    cf_handle = models.CharField(max_length=35)
    profile_pic = models.ImageField(upload_to='profile_pics',blank=True)
    
    def __str__(self):
        return self.user.username

class languages(models.Model):
    name = models.CharField(max_length = 200)
    val = models.IntegerField()

    def __str__(self):
        return self.name

class verdicts(models.Model):
    name = models.CharField(max_length = 200)
    val = models.IntegerField()

    def __str__(self):
        return self.name

class levels(models.Model):
    name = models.CharField(max_length = 200)
    val = models.IntegerField()

    def __str__(self):
        return self.name
