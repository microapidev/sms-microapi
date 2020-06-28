# from django.conf import settings
# from infobip.api.model.sms.mt.send.textual.SMSTextualRequest import SMSTextualRequest
# from infobip.clients import send_single_textual_sms, get_sent_sms_delivery_reports
# from infobip.util.configuration import Configuration

# # Infobip configuration details
# # Add to .env file
# # Install infobip module python 3 wrapper  using python -m pip install git+https://github.com/jonathan-golorry/infobip-api-python-client.git@python3
# infobip_username = settings.INFOBIP_USERNAME
# infobip_password = settings.INFOBIP_PASSWORD
# infobip_apikey = settings.INFOBIP_APIKEY
# configuration = Configuration(infobip_username, infobip_password,infobip_apikey)


# def send_single_message_ibp(message, recipient):
#     send_sms_client = send_single_textual_sms(Configuration("username", "password"))
#     request = SMSTextualRequest()
#     request.text = message
#     request.to = [recipient]
#     response = send_sms_client.execute(request)
#     return response


# def delivery_reports_ibp():
#     get_delivery_reports_client = get_sent_sms_delivery_reports(Configuration("username", "password"))
#     response = get_delivery_reports_client.execute({"limit": 5})
#     return response
