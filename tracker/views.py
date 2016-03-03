from django.shortcuts import render
from django.conf import settings
from tracker.models import Character, System, Connection
import pycrest
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone
import time
import json
import math
# Create your views here.

def index(request):
    kspace_debug=False;
    context={}
    if not request.user.is_authenticated():
        return HttpResponse("You're not logged in. How'd you get here?")

    authed_crest = pycrest.eve.AuthedConnection(
        res=request.user._get_crest_tokens(),
        endpoint=pycrest.EVE()._authed_endpoint,
        oauth_endpoint=pycrest.EVE()._oauth_endpoint,
        client_id=settings.SOCIAL_AUTH_EVEONLINE_KEY,
        api_key=settings.SOCIAL_AUTH_EVEONLINE_SECRET
    )
    authed_crest()

    #get character name, create/store it
    name = request.user.get_full_name()
    char_obj = Character.objects.filter(name=name)
    print char_obj
    #get starting system, create/store it
    print "Ajax? " + str(request.is_ajax())
    sec = ""
    try:
        if request.is_ajax():
            points = 0
            connection = "INVALID"
            prev_system = str(char_obj[0].location)
            prev_sys_obj = char_obj[0].location
            system_root = authed_crest.decode().character().location()
            system = system_root.solarSystem.name
            sid = system_root.solarSystem.id
            constellation = authed_crest.get(authed_crest.get("https://public-crest.eveonline.com/solarsystems/%s/" % (sid,))["constellation"]['href'])['name']
            print constellation
            if(constellation[1] == '-'): #if wh system
                c = constellation[0];
                classdict= {"A":"c1","B":"c2","C":"c3","D":"c4","E":"c5","F":"c6","G":"Thera","H":"c13",};
                sec = classdict[c];
            else:
                sec = str(math.ceil(authed_crest.get(system_root.solarSystem.href)["securityStatus"] * 10)/10.0)
                sec = ("k" + sec.translate(None,'.'))[:3]
            sys_obj = System.objects.filter(name=system)
            if not sys_obj:
                print "Making system object"
                sys_obj = System(name=system, sysid=sid, color_code=sec)
                sys_obj.save()
            else:
                print sys_obj
                sys_obj = sys_obj[0]
            print sys_obj
        else:
            system = None
            sys_obj= None
    except AttributeError as e:
        system = None
        sys_obj = None
        print e
    if not char_obj:
        print "Making character object"
        char_obj = Character(name=name,location=sys_obj)
        char_obj.save()
    else:
        char_obj.update(location=sys_obj)
        char_obj = char_obj[0]
    #get starting ship, create/store it
    #can't do this yet
    if request.is_ajax():
        print "kspace_debug:"
        print kspace_debug
        if ((prev_system != "None" and system != "None") and
            prev_system != system
            and ((prev_system[0] == 'J' and prev_system[1:].isdigit()) or
            (system[0] == 'J' and system[1:].isdigit()) or kspace_debug == True or
            prev_system == "Thera" or system == "Thera")
            ):
                print "Wormhole connection found"
                print type(prev_system)
                print system
                #make connection
                system_A = prev_system
                system_A_obj = prev_sys_obj
                system_B = system
                system_B_obj = sys_obj
                #get systems in alphabetical order
                if system_A > system_B:
                    system_B = prev_system
                    system_B_obj = prev_sys_obj
                    system_A = system
                    system_A_obj = sys_obj
                print "system A is " + system_A
                print "system B is " + system_B
                #see if the connection exists
                con_obj = Connection.objects.filter(system_A=system_A_obj, system_B=system_B_obj)
                #doesn't exist, create and assign 1 point
                if not con_obj:
                    con_obj = Connection(system_A=system_A_obj, system_B=system_B_obj,last_updated=timezone.now(),verification_count=1, can_timeout=True)
                    con_obj.save()
                    points = 1
                #does exist, update and assign scaled points
                else:
                    last_updated = con_obj[0].last_updated
                    now = timezone.now()
                    elapsed = now - last_updated
                    if elapsed.total_seconds() <= 14400: #four hours to recharge point value
                        points = (elapsed.total_seconds())/(14400)
                    else:
                        points = 1
                    con_obj.update(last_updated=now,verification_count=con_obj[0].verification_count+1)
                    con_obj = con_obj[0]
                connection = str(con_obj)
                print connection

        char_obj.points += points;
        char_obj.save()

        if system == None or system == "None":
            system = "Unknown system or character offline..."
        jsonObj = json.dumps({"update": {
            "system" :{
                "name": system,
                "sec": sec,
                },
            "points" : str(char_obj.points),
            "connection" :{
                "system_A": system,
                "system_B": prev_system,
                "name": connection}
            }
        }, separators=(',',': '))
        return HttpResponse( jsonObj, content_type="application/json" )


    else:
        return render(request, 'tracker/index.html', context=context)


