from django.shortcuts import render
from .forms import UserForm,UserProfileInfoForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from bs4 import BeautifulSoup
import requests
from lxml import html


def index(request):
    return render(request,'login/index.html')

@login_required
def special(request):
    return HttpResponse("You are logged in !")

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))
def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileInfoForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            if 'profile_pic' in request.FILES:
                print('found it')
                profile.profile_pic = request.FILES['profile_pic']
            profile.save()
            registered = True
        else:
            print(user_form.errors,profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileInfoForm()
    return render(request,'login/registration.html',
                          {'user_form':user_form,
                           'profile_form':profile_form,
                           'registered':registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your account was inactive.")
        else:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(username,password))
            return HttpResponse("Invalid login details given")
    else:
        return render(request, 'login/login.html', {})

def time_table(request):
    fcd = fetch_time_table()

    return render(request, "login/time_table.html", {"cols" : fcd})

def fetch_time_table():

    url = "https://codeforces.com/contests"
    page = requests.get(url) 

    bs=BeautifulSoup(page.content, 'html.parser')
    table_body = bs.find_all('table', class_="")
    
    cnt = 0
    for item in table_body:
        rows = item.find_all('tr')
        for row in rows:
            cols=row.find_all('td')
            cols=[x.text.strip() for x in cols]
            
            if len(cols) == 0:
                cnt = cnt + 1
                
            if cnt < 2 and len(cols)>=3:
                yield cols

def contest_stats(request):
    handle = request.user.get_username()
    fcs = fetch_contest_stats(handle)
    return render(request, 'login/contest_stats.html', fcs)

def fetch_contest_stats(handle):
    start_url = "https://www.codeforces.com/"

    cf_handle = handle
    profile_url = start_url+'profile/'+cf_handle
    contests_url = start_url+'contests/with/'+cf_handle

    page = requests.get(contests_url)
    soup = BeautifulSoup(page.content, 'lxml')

    table = soup.find('table', class_='tablesorter user-contests-table')
    tbody = table.find('tbody')

    ROWS = tbody.find_all('tr')

    delta_rating = []
    rank_list = []

    for item in ROWS:
        elements = item.find_all('td')
        contest_no = int(elements[0].text)
        contest_name = elements[1].find('a').text
        rank = int(elements[2].find('a').text)
        rating_change = int(elements[4].text)

        delta_rating.append(rating_change)
        rank_list.append(rank)

    delta_rating.sort()
    rank_list.sort()

    mydict = {
        'Handle' : cf_handle,
        'No_of_Contests' : ROWS[0].find('td').text, 
        'Best_Rank' : rank_list[0],
        'Worst_Rank' : rank_list[len(rank_list)-1],
        'Max_Up' : delta_rating[len(delta_rating)-1],
        'Max_Down' : delta_rating[0],
    }

    return mydict


















