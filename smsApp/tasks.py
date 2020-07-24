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


#A Sample of myData that will be passed to the async func as args
# myData = {
#     "senderID":senderID,
#     "sender":sender,
#     "sid":sid,
#     "token":token,
#     "service_type":service_type,
#     "verified_no":verified_no,
#     "groupID":groupID,
#     "content":text,
#     "language":language,
#     "numbers":numbers,   #this will be a list of numbers for group
#     "number":number,     #this will be a single number for singlesms
#     "grouptoken":grouptoken
# }



#Actual Code to run the async tasks
#I decided to write the tasks as seperate functions according to the service_type



@shared_task
def taskInfobipAsync(myData, is_group):
    message = Message.objects.create(
                senderID=myData['senderID'],
                content=myData['content'],
                language=myData['language'],
                service_type="IS",
                # dateScheduled=dateScheduled
            )
    content=myData['content']
    language=myData['language']
    conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
    headers = {
        'Authorization': 'App %s' % (myData['token']),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
        }
    if is_group:
        message.grouptoken=myData['grouptoken']
        for number in myData['numbers']:
            message.receiver=number
            if (language != 'en' or language != None or language != " " ):
                original_txt.append(content)
                content = translateMsg(content, language)
                payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (myData['senderID'], number, content)
            else:
                payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (myData['senderID'], number, content)
            conn.request("POST", "/sms/2/text/advanced", payload, headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            data = json.loads(data)
            if res.status == 200:
                message.transactionID = data["messages"][0]["messageId"]
                if ( data["messages"][0]["status"]["groupId"] == 1):
                    message.messageStatus = "P"
                if ( data["messages"][0]["status"]["groupId"] == 2):
                    message.messageStatus = "U"
                if ( data["messages"][0]["status"]["groupId"] == 3):
                    message.messageStatus = "S"
                if ( data["messages"][0]["status"]["groupId"] == 4):
                    message.messageStatus = "E"
                if ( data["messages"][0]["status"]["groupId"] == 5):
                    message.messageStatus = "FR"
            else:
                message.messageStatus = "F"
            print(f'Processed Message to {number}')
            message.save()
        print("Sending Complete")
    else:
        number = myData['number']
        message.receiver=number #This Line will throw an error because we're passing
        if (language != 'en' or language != None or language != " " ):
                original_txt.append(content)
                content = translateMsg(content, language)
                payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (myData['senderID'], number, content)
        else:
            payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (myData['senderID'], number, content)
        conn.request("POST", "/sms/2/text/advanced", payload, headers)
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        data = json.loads(data)
        if res.status == 200:
            message.transactionID = data["messages"][0]["messageId"]
            if ( data["messages"][0]["status"]["groupId"] == 1):
                message.messageStatus = "P"
            if ( data["messages"][0]["status"]["groupId"] == 2):
                message.messageStatus = "U"
            if ( data["messages"][0]["status"]["groupId"] == 3):
                message.messageStatus = "S"
            if ( data["messages"][0]["status"]["groupId"] == 4):
                message.messageStatus = "E"
            if ( data["messages"][0]["status"]["groupId"] == 5):
                message.messageStatus = "FR"
        else:
            message.messageStatus = "F"
        print(f'Processed Message to {number}')
        message.save()
        print("Sending Complete")
    return True


@shared_task
def taskTwilioAsync(myData, is_group):
    message = Message.objects.create(
        senderID=myData['senderID'],
        content=myData['content'],
        language=myData['language'],
        service_type="TW",
        # dateScheduled=dateScheduled
    )
    language=myData['language']
    content=myData['content']
    client = Client(myData['sid'],myData['token'])
    if is_group:
        message.grouptoken=myData['grouptoken']
        for number in myData['numbers']:
            message.receiver = number
            if (language != 'en' or language != None or language != "" ):
                content = translateMsg(content, language)
                payload = {'content': content, "receiver": number,"senderID": senderID, "service_type": "TW"}
            else:
                payload = {'content': content, "receiver": number,
                        "senderID": senderID, "service_type": "TW"}

            try:
                twilioMessage = client.messages.create(
                    from_=myData['verified_no'],
                    to=myData['number'],
                    body=content
                )
                if (twilioMessage.status == 'sent'):
                    message.messageStatus = "S"
                elif (twilioMessage.status == 'queued'):
                    message.messageStatus = "P"
                elif (twilioMessage.status == 'failed'):
                    message.messageStatus = "F"
                elif (twilioMessage.status == 'delivered'):
                    message.messageStatus = "R"
                else:
                    message.messageStatus = "U"
                message.transactionID= twilioMessage.sid
                message.save()
                print(f"Processed Message to {number}")

            except TwilioRestException as e:
                message.messageStatus = "F"
                message.transactionID = "500-F"
                message.save()
                print(f"Processed Message to {number}")
    else:
        number = myData['number']
        if (language != 'en' or language != None or language != "" ):
            content = translateMsg(content, language)
            payload = {'content': content, "receiver": number,"senderID": senderID, "service_type": "TW"}
        else:
            payload = {'content': content, "receiver": number,
                    "senderID": senderID, "service_type": "TW"}

        try:
            twilioMessage = client.messages.create(
                from_=myData['verified_no'],
                to=myData['number'],
                body=content
            )
            if (twilioMessage.status == 'sent'):
                message.messageStatus = "S"
            elif (twilioMessage.status == 'queued'):
                message.messageStatus = "P"
            elif (twilioMessage.status == 'failed'):
                message.messageStatus = "F"
            elif (twilioMessage.status == 'delivered'):
                message.messageStatus = "R"
            else:
                message.messageStatus = "U"
            message.transactionID= twilioMessage.sid
            message.save()
            print(f"Processed Message to {number}")

        except TwilioRestException as e:
            message.messageStatus = "F"
            message.transactionID = "500-F"
            message.save()
            print(f"Processed Message to {number}")
    return True


@shared_task
def taskTelesignAsync(myData, is_group):
    message = Message.objects.create(
            senderID=myData['senderID'],
            content=myData['content'],
            language=myData['language'],
            service_type="TS",
            # dateScheduled=dateScheduled
        )
    content=myData['content']
    language=myData['language']
    api_key = myData['token']
    customer_id = myData['sid']
    url = 'https://rest-api.telesign.com/v1/messaging'
    headers = {'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'}
    if is_group:
        message.grouptoken=myData['grouptoken']
        for number in myData['numbers']:
            message.receiver = number
            if (language != 'en' or language != None or language != "" ):
                content = translateMsg(content, language)
                data = {'phone_number': number,
                    'message': content, 'message_type': 'ARN'}
            else:
                data = {'phone_number': number,
                    'message': content, 'message_type': 'ARN'}
            r = requests.post(url, auth=HTTPBasicAuth(customer_id, api_key), data=data, headers=headers)
            response = r.json()
            if response['status']['code'] == 290:
                message.transactionID = response['reference_id']
                message.messageStatus = 'P'
                message.save()
                print(f"Processed Message to {number}")
            else:
                message.transactionID = "500-F"
                message.messageStatus = 'F'
                message.save()
                print(f"Processed Message to {number}")
    else:
        number = myData['number']
        if (language != 'en' or language != None or language != "" ):
            content = translateMsg(content, language)
            data = {'phone_number': number,
                'message': content, 'message_type': 'ARN'}
        else:
            data = {'phone_number': number,
                'message': content, 'message_type': 'ARN'}
        r = requests.post(url, auth=HTTPBasicAuth(customer_id, api_key), data=data, headers=headers)
        response = r.json()
        if response['status']['code'] == 290:
            message.transactionID = response['reference_id']
            message.messageStatus = 'P'
            message.save()
            print(f"Processed Message to {number}")
        else:
            message.transactionID = "500-F"
            message.messageStatus = 'F'
            message.save()
            print(f"Processed Message to {number}")
    return True

