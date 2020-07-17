# Create your tasks here
from __future__ import absolute_import, unicode_literals
from requests.auth import HTTPBasicAuth
from .models import Message
from smsApi.celery import app
import requests, json
import datetime
from datetime import timedelta
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from celery import shared_task
import uuid, http.client
from googletrans import Translator
from rest_framework.response import Response

#So guys Here i will try to explain what we have so far and how we can go about it. So
# have 2 functionsof note which are async_single_infobip and async_single_telesign 
#async_single_infobip is called from line 441 in d views file while async_single_telesign from line 479.
#async_single_infobip saves by calling Message.objects.create. this works fine because when you print the 'message' object object after a  save
#you'll get the correct instance with all saved data without any errors. The downside is that somehow it dosent save to the Message model which 
#drives me crazy anytime i thing about it.

#async_single_telesign on d other hand saves the serializer from d views and is passes an instance of that save which is 'value', used to add other
#fields. the 'value' is returned and the save method is called on it. And this saves to the db but it keeps throwin a long traceback of errors.
# something like this:
# File "/usr/local/lib/python3.8/site-packages/simplejson/encoder.py", line 272, in default
#    raise TypeError('Object of type %s is not JSON serializable' %
#    kombu.exceptions.EncodeError: Object of type Message is not JSON serializable  

#Cant figure out any of them.

def translateMsg(content, lang='en'):
    #This will help translate message of customer.
    
    translator = Translator(service_urls=[
        'translate.google.com',
        'translate.google.co.kr',
    ])

    if lang is None:
        lang = 'en'
        translated = translator.translate(text=content, dest=lang)
        content = translated.text
        return content
    else:
        translated = translator.translate(text=content, dest=lang)
        content = translated.text
        return content



def async_group_sms(value, senderID,number, text, payload, conn):
    data = {
        "from": senderID,
        "to": numbers,
        "text": text
    }
    headers = {
        'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
        }
    value.service_type = 'IF'
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    data = json.loads(data)
    if res.status == 200:
        value.save()
    return Response({"Status": res.status, "Message": "", "Data": data})

@app.task
def async_single_infobip(senderID, service_type, receiver, content, payload, language, original_txt):

    conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
    print("2 here")
    headers = {
        'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
        }
    if (language != 'en' or language != None or language != ""):
        original_txt.append(content)
        content = translateMsg(content, language)
        data = {
            "from": senderID,
            "to": receiver,
            "text": content
        }
    else:
        data = {
            "from": senderID,
            "to": receiver,
            "text": content
        }
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read().decode('utf-8')
    data = json.loads(data)
    print("5 here")
    if res.status == 200:
        transactionID = data["messages"][0]["messageId"]
        message = Message.objects.create(senderID=senderID, service_type=service_type, receiver=receiver, content=original_txt, transactionID=transactionID, language=language)
        message.save()
        print("6 here")
    if len(original_txt) != 0:
        print("Original Message")
    print("sending complete something")
    return True



@app.task
def async_single_telesign(headers,data,receiver,content, value):
    api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
    customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
    url = 'https://rest-api.telesign.com/v1/messaging'
    r = requests.post(url, 
                    auth=HTTPBasicAuth(customer_id, api_key), 
                    data=data, 
                    headers=headers)
    # value = serializer_message.save()
    response = r.json()
    if response['status']['code'] == 290:
        value.service_type = 'TS'
        value.messageStatus = 'SC'
        value.transactionID = response['reference_id']
        # value.save()
        if len(original_txt) != 0:
            print({
                "Success": True,
                "Message": "Message Sending",
                "Original SMS": f"{original_txt[0]}",
                "Data": response,
                "Service_Type": "TELESIGN"
                })
        print({
            "Success": True,
            "Message": "Message Sending",
            "Data": response,
            "Service_Type": "TELESIGN"
            })
    else:
        print(response['status']['code'])
        # value = serializer_message.save()
        value.service_type = 'TS'
        value.messageStatus = 'F'
        value.receiver = receiver
        value.transactionID = "500-F"
        # value.save()
        print({
            "Success": False,
            "Message": "Message Couldnt be sent",
            "Data": response,
            "Service_Type": "TELESIGN"})
    return response, value

























@shared_task
def add():
    sum = 3+2
    return f"This what we have {sum}"

# @shared_task
# def schedule_add():
#     schedule, _ = CrontabSchedule.objects.get_or_create(
#     minute='1',
#     hour='*',
#     day_of_week='*',
#     day_of_month='*',
#     month_of_year='*',
#     )

#     periodic_task = PeriodicTask.objects.create(
#     crontab=schedule,
#     name='Sending Scheduled Messages2',
#     task='add',
#     # args=json.dumps([x,y]),
#     # kwargs=json.dumps({
#     #    'be_careful': True,
#     # }),
#     # expires=datetime.datetime.utcnow() + timedelta(minutes=3)
#     )
#     print(f"Periodic_task id is {periodic_task.id}, task : {periodic_task.task}")
def save_to_db(data):
    message = Message.objects.create(
        service_type="TS",
        messageStatus=data["messageStatus"],
        receiver=data["numb"],
        transactionID=data["transactionID"],
        grouptoken=data["grouptoken"],
        content=data["text"],
        senderID=data["sender"])
    message.save()
    return message


def save_to_db2(data):
    message = Message.objects.create(
        service_type="TS",
        messageStatus=data["messageStatus"],
        receiver=data["numb"],
        grouptoken=data["grouptoken"],
        content=data["text"],
        senderID=data["sender"])
    message.save()
    return message


@shared_task
def send_group_sms(grouptoken, ListOFNumbers):
    setData = {
                "text" : "Hello World",
                "grouptoken" : grouptoken,
                "ListOFNumbers" : ListOFNumbers,
                "sender" : "BiggieSmallie"
            }
    ListOFNumbers= setData["ListOFNumbers"]
    grouptoken= setData["grouptoken"]
    sender= setData["sender"]
    content= setData["text"]
    # api_key = settings.TELESIGN_API
    # customer_id = settings.TELESIGN_CUST
    api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
    customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
    url = 'https://rest-api.telesign.com/v1/messaging'
    headers = {'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'}
    for numb in ListOFNumbers:
        data = {'phone_number': numb,
            'message': content, 'message_type': 'ARN'}
        r = requests.post(url, auth=HTTPBasicAuth(
            customer_id, api_key), data=data, headers=headers)
        response = r.json()
        if response['status']['code'] == 290:
            print(f"Sending to {numb}")
            setData["transactionID"] = response['reference_id']
            setData["messageStatus"] = "S"
            setData["numb"] = numb
            message = save_to_db(setData)
            print(message)
        else:
            print(f"Could not send to {numb}")
            setData["messageStatus"] = "F"
            setData["numb"] = numb
            message = save_to_db2(setData)
            print(message)
    print("Sending complete")
    return True


# @shared_task
# def send_scheduled_group_sms(setData):
#     ListOFNumbers= setData["ListOFNumbers"]
#     grouptoken= setData["grouptoken"]
#     sender= setData["sender"]
#     text= setData["text"]
#     # api_key = settings.TELESIGN_API
#     # customer_id = settings.TELESIGN_CUST
#     api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
#     customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
#     url = 'https://rest-api.telesign.com/v1/messaging'
#     headers = {'Accept': 'application/json',
#                 'Content-Type': 'application/x-www-form-urlencoded'}
#     for numb in ListOFNumbers:
#         data = {'phone_number': numb,
#             'message': text, 'message_type': 'ARN'}
#         r = requests.post(url, auth=HTTPBasicAuth(
#             customer_id, api_key), data=data, headers=headers)
#         response = r.json()
#         number = Message.objects.filter(scheduled_task_id=app.current_worker_task.request.id).filter(receiver=receiver)
#         if response['status']['code'] == 290:
#             print(f"Sending to {numb}")
#             number.messageStatus = 'S'
#             number.last_scheduled_msg_sent = datetime.datetime.utcnow()
#             number.save()
#         else:
#             print(f"Could not send to {numb}")
#             number.messageStatus = 'F'
#             number.last_scheduled_msg_sent = datetime.datetime.utcnow()
#             number.save()
#     print("Sending complete")
#     return True

# @shared_task
# def schedule_group_sms(setData):
#     schedule, _ = CrontabSchedule.objects.get_or_create(
#     minute='1',
#     hour='*',
#     day_of_week='*',
#     day_of_month='*',
#     month_of_year='*',
#     )

#     periodic_task = PeriodicTask.objects.create(
#     crontab=schedule,
#     name='Sending Scheduled Messages',
#     task='send_scheduled_group_sms',
#     args=json.dumps(setData),
#     kwargs=json.dumps({
#        'be_careful': True,
#     }),
#     expires=datetime.datetime.utcnow() + timedelta(minutes=5)
#     )
#     grouptoken= setData["grouptoken"]
#     senderID= setData["sender"]
#     content= setData["text"]
#     for numb in setData["ListOFNumbers"]:
#         message = Message.objects.create(
#             service_type="TS",
#             scheduled_task_id=periodic_task.id,
#             messageStatus="SC",
#             receiver=numb,
#             grouptoken=grouptoken,
#             senderID=senderID,
#             content=content)
#     print(f"Periodic_task id is {periodic_task.id}")
