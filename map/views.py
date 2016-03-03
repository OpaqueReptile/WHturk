from django.shortcuts import render
from django.conf import settings
from tracker.models import Character, System, Connection
import pycrest
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone
import time
import json
import random
import math
from django.db.models import Q
from map.dijkstra import *
# Create your views here.

def _get_sec_color(code):
    graph_colors = {}
    graph_colors = {
         "k00": "#F00000",
         "k01": "#D73000",
         "k02": "#F04800",
         "k03": "#F06000",
         "k04": "#D77700",
         "k05": "#EFEF00",
         "k06": "#8FEF2F",
         "k07": "#00F000",
         "k08": "#00EF47",
         "k09": "#48F0C0",
         "k10": "#2FEFEF",
         "c1": "#deacff",
         "c2": "#d392ff",
         "c3": "#c979ff",
         "c4": "#bf5fff",
         "c5": "#b546ff",
         "c6": "#ab2cff",
         "c13": "#a013ff",
         "Thera": "#6f5fff",};
    return graph_colors[code]

def node_add(system, x=0,y=0):
    sec = _get_sec_color(system.color_code)
    node = {
        "id" : system.sysid,
        "label" : system.name,
        "x" : x,
        "y" : y,
        "size" : 1,
        "color" : sec,
    }
    return node

def edge_add(con):

    edge_colors= {1 : "#d8d8d8", 2: "#b2b2b2", 3: "#8c8c8c", 4:"#666666", 5:"#404040", 6:"#1a1a1a"}
    color = edge_colors.get(con.verification_count,"#000000")
    edge = {
        "id" : con.__str__(),
        "source" : con.system_A.sysid,
        "target" : con.system_B.sysid,
        "size" : con.verification_count/1000.0,
        "color" : "#d8d8d8",
    }
    return edge

def index(request):
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
    try:
        authed_crest()
        context["tq"] = ""
    except:
        context["tq"] = "Cannot connect to TQ"

    #get starting system, create/store it
    return render(request, 'map/index.html', context=context)


def graphTraverse(node, depth, graph,  visited, dead_cons = set(), prev=None, connections=Connection.objects.all()):
    #add node to graph, and return if we're done
    visited[node] = depth
    graph["nodes"].append(node_add(node, 0, 0))
    if depth == 0:
        return graph
    new_depth = depth-1
    #get connections
    cons = connections.filter(( Q(system_A = node) | Q(system_B = node)))
    for con in cons:
        dead_cons.add(con)
        print con
        #get the next node
        if con.system_A == node:
            new_node = con.system_B
        elif con.system_B == node:
            new_node = con.system_A

        #make sure the next node isnt a system we've already seen
        if visited.get(new_node) != None  and visited[new_node] > new_depth :
     #       print "already been to "+ str(new_node) + " at depth " + str(visited[new_node])
            continue

        #make sure it's not a dead connection
        #if dead_cons is not None and con in dead_cons:
        #    print "dead connection?"
        #    continue
        #add connection to graph, dead connections
        #dead_cons.append(con)
        #new_dead = list(dead_cons)
        graph = graphTraverse(new_node, new_depth, graph,  visited, dead_cons, node, connections)
    if prev == None:
        print "adding edges"
        for con in dead_cons:
            graph["edges"].append(edge_add(con))
    return graph





#change wh systems to anokis for a given graph
def maskwh(graph, exclude=[]):
    sysids = []
    for node in graph["nodes"]:
        first = True
        name = node["label"]
        if first and  name[0] == 'J' and name[1:].isdigit() and name not in exclude:
            sysids.append(node["id"])
            node["id"] = 0
            node["label"] = "Anokis (Wormhole Space)"
            node["size"] = 1,
            first = False
        elif name[0] and name[0] == 'J' and name[1:].isdigit() and name not in exclude:
            sysids.append(node["id"])
            graph["nodes"].remove(node)
    for edge in graph["edges"]:
        source = edge["source"]
        target = edge["target"]
        if source in sysids:
            edge["source"] = 0
            edge["id"] = source
        if target in sysids:
            edge["target"] = 0
            edge["id"] = target
        if edge["source"] == 0 and edge["target"] == 0:
            edge["id"] = 0
    return graph




def rootAndDepth(request):
    root = request.GET["sys"].strip()
    try:
        depth = int(request.GET["d"].strip())
    except:
        return HttpResponse("Depth is not a integer.")

    root_obj =  System.objects.filter(name__iexact=root)
    if not root_obj:
        return HttpResponse("System not found.")
    if depth < 0 or depth > 5:
        return HttpResponse("Depth not within range.")
    graph = {"nodes" : [], "edges" : []};
    dead_cons = []
    root_obj = root_obj[0];
    graph = graphTraverse(root_obj, depth, graph,{})
    graph["nodes"] = [dict(t) for t in set([tuple(d.items()) for d in graph["nodes"]])]
    graph["edges"] = [dict(t) for t in set([tuple(d.items()) for d in graph["edges"]])]

    graph = maskwh(graph,request.GET["sys"].strip())
    jsonObj = json.dumps(graph, separators=(',',': '))
    return HttpResponse( jsonObj, content_type="application/json" )


def getPath(request):
    A = request.GET["A"].strip()
    B = request.GET["B"].strip()
    buy = False
    if request.GET["buy"] == 'true':
        buy = True
    A_obj =  System.objects.filter(name__iexact=A)
    B_obj =  System.objects.filter(name__iexact=B)
    if not A_obj:
        return HttpResponse("Start system not found.")
    if not B_obj:
        return HttpResponse("End system not found.")
    A_obj = A_obj[0]
    B_obj = B_obj[0]
    graph = Graph();

    #add all connections into the search. this isnt ideal
    #for sys in System.objects.all():
    #    graph.add_node(sys.name)
    #for con in Connection.objects.all():
    #    graph.add_edge(con.system_A.name,con.system_B.name,1)
    """
    #add chunks of systems around the source and dest
    chunk_s = {"nodes" : [], "edges" : []}
    chunk_d = {"nodes" : [], "edges" : []}
    chunk_f = {"nodes" : [], "edges" : []}
    for depth in range(10,26,5):
        print "trying range at " + str(depth)
        chunk_s = {"nodes" : [], "edges" : []}
        chunk_d = {"nodes" : [], "edges" : []}
        A_depth = depth
        B_depth = depth
        chunk_s = graphTraverse(A_obj, A_depth, chunk_s, {}, set())
        print "---"
        chunk_d = graphTraverse(B_obj, B_depth, chunk_d, {}, set())
        end = False

        print_test = []
        for i in range(0, len(chunk_s["nodes"])):
            print_test.append( str(chunk_s["nodes"][i]["label"]))
            if chunk_s["nodes"][i] in chunk_d["nodes"]:
                end = True

        print "End? " + str(end)
        if end:
            #print sorted(print_test)
            break
    if not end:
        return HttpResponse("Couldn't find path.")


    chunk_s["nodes"].extend(chunk_d["nodes"])
    chunk_s["edges"].extend(chunk_d["edges"])
    for node in chunk_s["nodes"]:
        if node not in chunk_f["nodes"]:
            chunk_f["nodes"].append(node)
    for edge in chunk_s["edges"]:
        if edge not in chunk_f["edges"]:
            chunk_f["edges"].append(edge)
    for node in chunk_f["nodes"]:
        graph.add_node(node["label"])
    for edge in chunk_f["edges"]:
        graph.add_edge(System.objects.get(sysid=edge["source"]).name,System.objects.get(sysid=edge["target"]).name,1)
    """

    print "loading nodes"
    for node in System.objects.values_list('name',flat=True):
        graph.add_node(node)
    print "loading edges"
    con = Connection.objects.all().prefetch_related('system_A', 'system_B')
    for edge in con:
        graph.add_edge(edge.system_A.name,edge.system_B.name,1)

    try:
        dist, path = shortest_path(graph,A_obj.name,B_obj.name)
    except:
        pass
    print "distance: " + str(dist)

    final_graph = {"nodes" : [], "edges" : []};
    for i in range(0,len(path)):
        final_graph["nodes"].append(node_add(System.objects.get(name=path[i]), 0, 0))
        if i < len(path)-1:
            A = path[i]
            B = path[i+1]
            if A > B:
                temp = A
                A = B
                B = temp
            A_obj =  System.objects.get(name=A)
            B_obj =  System.objects.get(name=B)
            final_graph["edges"].append(edge_add(Connection.objects.get(system_A=A_obj,system_B=B_obj)))

    if not buy:
        final_graph = maskwh(final_graph)
    jsonObj = json.dumps(final_graph, separators=(',',': '))
    return HttpResponse( jsonObj, content_type="application/json" )




def kspace_gen(request):
    import csv
    import os
    eve = pycrest.EVE()
    eve()
    crest_dict = eve.get("https://public-crest.eveonline.com/solarsystems/");
    system_dict = {}

    """
    #get our systems loaded
    count = 5000
    for sys in crest_dict["items"][5000:]:
        system_dict[sys["id_str"]] = sys

        constellation = eve.get(eve.get("https://public-crest.eveonline.com/solarsystems/%s/" %      (sys["id_str"]))["constellation"]['href'])['name']
        if(constellation[1] == '-' and len(constellation) == 8): #if wh system
            c = constellation[0];
            classdict= {"A":"c1","B":"c2","C":"c3","D":"c4","E":"c5","F":"c6","G":"Thera","H":"c13",};
            sec = classdict.get(c,"c13");
        else:
            sec = math.ceil(eve.get(sys['href'])["securityStatus"] * 10)/10.0
            if sec < 0.0:
                sec = 0.0
            sec = str(abs(sec))

            sec = ("k" + sec.translate(None,'.'))[:3]
            if (sec == "k-0"):
                print "ERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\nERROR\n"

        #check if system exists
        sys_obj = System.objects.filter(sysid = sys["id_str"])
        if not sys_obj:
            count = count+1
            print "Making system object " + str(count)
            sys_obj = System(name=sys["name"], sysid=sys["id_str"], color_code=sec)
            sys_obj.save()
            print sys_obj
        else:
            count = count+1
            print "Skipping system object " + str(count)
            print sys_obj
    """
    count = 0
    with open(os.path.abspath('/usr/share/nginx/backend/whturk/map/mapSolarSystemJumps.csv'), 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        firstline = True
        for row in reader:
            if firstline:
                firstline = False
                continue
            A = System.objects.filter(sysid = row[2])[0];
            B = System.objects.filter(sysid = row[3])[0];
            if A.name > B.name:
                temp = A
                A = B
                B = temp
            con_obj = Connection.objects.filter(system_A = A, system_B = B)
            if not con_obj:
                count = count+1
                print "Making connection object " + str(count)
                con_obj = Connection(system_A = A, system_B = B, last_updated = timezone.now(), verification_count = 1)
                con_obj.save()


    return HttpResponse("populating systems and connections")



