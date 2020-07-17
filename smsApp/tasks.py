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
import uuid


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
