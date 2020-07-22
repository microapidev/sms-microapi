from __future__ import absolute_import, unicode_literals
import requests
from requests.auth import HTTPBasicAuth
from celery import shared_task
import uuid, json
from .models import Message
from django_celery_beat.models import PeriodicTask, IntervalSchedule


@shared_task
def task1(mydata):
    api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
    customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
    url = 'https://rest-api.telesign.com/v1/messaging'

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'}

    data = {
        'phone_number': mydata['receiver'],
        'message': mydata['text'],
        'message_type': 'ARN'}
    r = requests.post(url, auth=HTTPBasicAuth(
                customer_id, api_key), data=data, headers=headers)
    response = r.json()
    print('We are 1')
    message = Message.objects.create(
        receiver=mydata['receiver'],
        senderID=mydata['sender'],
        content=mydata['text'],
        service_type="TS",
    )
    if response['status']['code'] == 290:
        message.transactionID=response['reference_id'],
        message.messageStatus="SC"
        message.save()
        print("saving sent message")
    else:
        message.messageStatus="F"
        print("saving failed message")
        message.save()
    print('We are 4')
    return 
    

@shared_task
def periodicTaskScheduler(x, y):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )
    print('Schedule Created')
    PeriodicTask.objects.create(
        interval=schedule,                  # we created this above.
        name='',          # simply describes this periodic task.
        task='smsApp.tasks.periodicTask',  # name of task.
        args=json.dumps(['x', 'y']),
    )
    print(PeriodicTask.objects.all())
    print('Periodic Task Scheduled')
    return True


def periodicTask(x,y):
    sums = x + y
    print(f'The sum of the number is {sums}')
    return sums
