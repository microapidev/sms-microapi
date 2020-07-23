from __future__ import absolute_import, unicode_literals
import requests
from requests.auth import HTTPBasicAuth
from celery import shared_task
import uuid, json
from .models import Message
from django_celery_beat.models import PeriodicTask, IntervalSchedule


@shared_task
def singleMessageSchedule(mydata, messageID):
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
    # print('We are 1')
    print(f'This is messageID1 {messageID}')
    message = Message.objects.filter(messageID=messageID).first()
    print(f'This is messageID2 {messageID}')
    print(f'message is {message}')
    if response['status']['code'] == 290:
        message.transactionID=response['reference_id'],
        message.messageStatus="S"
        message.save()
        print("saving sent message")
    else:
        message.messageStatus="F"
        print("saving failed message")
        message.save()
    # print('We are 4')
    return 


def getNumbersFromList(stringOfNumbers):
    stringOfNumbers = stringOfNumbers.split(',')
    number = []
    for num in stringOfNumbers:
        num = num.strip()
        number.append(num)
    number = list(dict.fromkeys(number))
    return number


@shared_task
def listMessageSchedule(mydata, messageID):
    '''
    This async task is similar to the group sms just that it'll take in a sting of numb seperated by comma
    instead of saving a group to the db. I hope it works

    PS it's a work in
    '''
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
    # print('We are 1')
    print(f'This is messageID1 {messageID}')
    message = Message.objects.filter(messageID=messageID).first()
    print(f'This is messageID2 {messageID}')
    print(f'message is {message}')
    if response['status']['code'] == 290:
        message.transactionID=response['reference_id'],
        message.messageStatus="S"
        message.save()
        print("saving sent message")
    else:
        message.messageStatus="F"
        print("saving failed message")
        message.save()
    # print('We are 4')
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
        name='nameless',          # simply describes this periodic task.
        task='smsApp.tasks.periodicTask',  # name of task.
        args=json.dumps([x, y]),
    )
    print(PeriodicTask.objects.all())
    print('Periodic Task Scheduled')
    return True

@shared_task
def periodicTask(x,y):
    sums = x + y
    print(f'The sum of the number is {sums}')
    return sums
