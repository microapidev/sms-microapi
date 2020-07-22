from __future__ import absolute_import, unicode_literals
import requests
from requests.auth import HTTPBasicAuth
from celery import shared_task
import uuid


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
    if response['status']['code'] == 290:
        print('We are 2')
        mydata['service_type'] = 'TS'
        mydata['messageStatus'] = 'SC'
        mydata['transactionID'] = response['reference_id']
        print(mydata)
    else:
        print('We are 3')
        print(response['status']['code'])
        mydata['service_type'] = 'TS'
        mydata['messageStatus'] = 'SC'
        mydata['transactionID'] = uuid.uuid4()
        print(mydata)
    print('We are 4')
    return True