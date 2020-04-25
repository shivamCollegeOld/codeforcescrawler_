from django.shortcuts import render
from .forms import UserForm,UserProfileInfoForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from . import models
from .forms import SearchHandle
from .models import languages, verdicts, levels

from bs4 import BeautifulSoup
import requests
from lxml import html

import pandas as pd
import matplotlib.pyplot as plt, mpld3

from collections import OrderedDict
from . import fusioncharts

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
    # OneToOne Field hai user in UserProfileInfo model to usko access karne
    # ka tareeka!!!    
    profile = request.user.userprofileinfo
    handle = profile.cf_handle

    fcs = fetch_contest_stats(handle)
    chart = {"output_languages" :  display_stats_languages(handle).render(),
            "output_verdicts" :  display_stats_verdicts(handle).render(),
            "output_levels" :  display_stats_levels(handle).render(),
    }

    fcs.update(chart)

    return render(request, 'login/contest_stats.html', fcs)

def fetch_contest_stats(handle):
    start_url = "https://www.codeforces.com/"

    cf_handle = handle
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

def search_handle(request):
    if request.method == "POST":
        form = SearchHandle(request.POST)

        if form.is_valid():
            handle = form.cleaned_data["cf_handle"]
            # print(handle)

            fcs = fetch_contest_stats(handle)
            chart = {"output_languages" :  display_stats_languages(handle).render(),
                    "output_verdicts" :  display_stats_verdicts(handle).render(),
                    "output_levels" :  display_stats_levels(handle).render(),
            }

            fcs.update(chart)

            return render(request, 'login/contest_stats.html', fcs)

    else :
        form = SearchHandle()
    
    form = SearchHandle()

    return render(request, 'login/search.html', {"form":form})

def get_submission_stats(handle):
    languages.objects.all().delete()
    verdicts.objects.all().delete()

    page = requests.get("https://codeforces.com/submissions/" + handle)

    soup = BeautifulSoup(page.content, 'lxml')
    div = soup.find_all('div', class_='pagination')[1]

    ul = div.find('ul')
    li = ul.find_all('li')

    t = int(li[-2].text)
    val = pd.Series()
    verd = pd.Series()
    lev = pd.Series()

    for i in range(t):
        p = pd.read_html("https://codeforces.com/submissions/" + handle + "/page/" + str(i+1))
        table = p[5]

        val = val.combine(table['Lang'].value_counts(),(lambda x1, x2 : x1+x2), fill_value=0)
        verd = verd.combine(table['Verdict'].value_counts(),(lambda x1, x2 : x1+x2), fill_value=0)
        lev = lev.combine(table['Problem'].value_counts(),(lambda x1, x2 : x1+x2), fill_value=0)

    labels_lang = val._index
    labels_verd = verd._index
    labels_lev = lev._index


    for l in labels_lang:
        a = languages.objects.update_or_create(name = l, val = val[l])[0]
        a.save()
    
    for l in labels_verd:
        a = verdicts.objects.update_or_create(name = l, val = verd[l])[0]
        a.save()

    for l in labels_lev:
        a = levels.objects.update_or_create(name = l, val = lev[l])[0]
        a.save()


def display_stats_languages(handle):
    get_submission_stats(handle)

    chartConfig = OrderedDict()
    chartConfig["caption"] = "Languages of " + handle
    chartConfig["xAxisName"] = "Languages"
    chartConfig["xAxisName"] = "Submissions"
    chartConfig["theme"] = "fusion"
    chartConfig["animation"] = ""

    datasource = OrderedDict()
    datasource["Chart"] = chartConfig
    datasource["data"] = []
    # print(languages.objects.all())
    for l in languages.objects.all():
        datasource["data"].append({"label": l.name, "value": str(l.val)})
    
    graph2D = fusioncharts.FusionCharts("pie2d", "Languages Chart", "600", "400", "languages_chart", "json", datasource)

    return graph2D

def display_stats_verdicts(handle):

    chartConfig = OrderedDict()
    chartConfig["caption"] = "Verdicts of " + handle
    chartConfig["xAxisName"] = "Verdicts"
    chartConfig["xAxisName"] = "Submissions"
    chartConfig["theme"] = "fusion"
    chartConfig["animation"] = ""

    datasource = OrderedDict()
    datasource["Chart"] = chartConfig
    datasource["data"] = []

    WA = 0
    AC = 0
    RTE = 0
    MLE = 0
    CE = 0
    TLE = 0

    for l in verdicts.objects.all():
        item = l.name
        if item[:5] == "Wrong":
            WA += l.val
        
        elif item[:5] == "Time":
            TLE += l.val

        elif item == "Accepted":
            AC += l.val

        elif item[:6] == "Memory":
            MLE += l.val

        elif item[:11] == "Compilation":
            CE += l.val

        elif item[:7] == "Runtime":
            RTE += l.val
        
    datasource["data"].append({"label": "Accepted", "value": AC})
    datasource["data"].append({"label": "Wrong Answer", "value": WA})
    datasource["data"].append({"label": "Runtime Error", "value": RTE})
    datasource["data"].append({"label": "Memory Limit Exceeded", "value": MLE})
    datasource["data"].append({"label": "Compilation Error", "value": CE})
    datasource["data"].append({"label": "Time Limit Exceeded", "value": TLE})
    
    graph2D = fusioncharts.FusionCharts("pie2d", "Verdicts Chart", "700", "500", "verdicts_chart", "json", datasource)

    return graph2D

def display_stats_levels(handle):

    chartConfig = OrderedDict()
    chartConfig["caption"] = "Levels of " + handle
    chartConfig["xAxisName"] = "Levels"
    chartConfig["xAxisName"] = "Submissions"
    chartConfig["theme"] = "fusion"
    chartConfig["animation"] = ""

    datasource = OrderedDict()
    datasource["Chart"] = chartConfig
    datasource["data"] = []

    A = 0
    B = 0
    C = 0
    D = 0
    E = 0
    R = 0

    for l in levels.objects.all():
        item = l.name
        if item[0] == "A":
            A += l.val
        
        elif item[0] == "B":
            B += l.val

        elif item[0] == "C":
            C += l.val

        elif item[0] == "D":
            D += l.val
        
        elif item[0] == "E":
            E += l.val
        
        else:
            R += l.val
        
    # print('{} {} {} {} {} {}'.format(A, B, C, D, E, R))
    datasource["data"].append({"label": "A", "value": A})
    datasource["data"].append({"label": "B", "value": B})
    datasource["data"].append({"label": "C", "value": C})
    datasource["data"].append({"label": "D", "value": D})
    datasource["data"].append({"label": "E", "value": E})
    datasource["data"].append({"label": "R", "value": R})
    
    
    graph2D = fusioncharts.FusionCharts("column2d", "Levels Chart", "700", "500", "levels_chart", "json", datasource)

    return graph2D  










