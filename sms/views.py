from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json

# Create your views here.
BASE_URL = "http://localhost:3000/"
@csrf_exempt
def index(request):
    if request.method == 'POST':
        payload = {}
        payload["content"] = request.POST.get("message")
        payload["service_type"] = request.POST.get("provider")
        payload["senderID"] = request.POST.get("senderID")
        payload["receiver"] = request.POST.get("receiver")
        print(payload)
        req = requests.post(url=BASE_URL + "v2/sms/send_single_msg", data=payload)
        print(req.content)
        return JsonResponse({"details":str(req.content)})
    return render(request, "index.html")


@csrf_exempt
def bulk(request):
    if request.method == 'POST':
        payload = {}
        payload["content"] = request.POST.get("message")
        payload["service_type"] = request.POST.get("provider")
        payload["senderID"] = request.POST.get("senderID")
        payload["groupID"] = request.POST.get("receiver")
        req = requests.post(url=BASE_URL + "v2/sms/send_single_msg", data=payload)
        return JsonResponse({"details":str(req.content)})
    return render(request, "bulk.html")

def create_group(request):
    if request.method == 'POST':
        payload1 = {}
        payload1["groupName"] = request.POST.get("groupname")
        payload1["senderID"] = request.POST.get("senderID")
        req = requests.post(url=BASE_URL + "v1/sms/create_group", data=payload1)
        req = req.content.decode("utf8")
        req = json.loads(req)
        if isinstance(req, list):
            return JsonResponse({"details":str(req)})

        elif req["Success"] == "True":
            payload2 = {}
            payload2["groupID"] = req["groupID"]    
            payload2["phoneNumbers"] = request.POST.get("numbers")
            print(payload2)
            requ = requests.post(url=BASE_URL + "v1/sms/group_recipient/create", data=payload2)
            print(requ.content)
            requ = requ.content.decode("utf8")
            req = json.loads(requ)
            if requ["details"]["success"] == "True":
                data = "Group created, number saved"
        return JsonResponse({"details":data})
    return render(request, "groupcreate.html")

def check_status(request):
    return 0

def translate_message(request):
    return 0