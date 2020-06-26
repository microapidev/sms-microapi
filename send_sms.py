import twilio.rest import client

Account_sid = "AC1569f4d689eb86034414994fd3fbce4b"
auth_token = "731b78598477af5423a8485c79b31d6"

client = Client(Account_sid, auth_token)

message = client.message.create(
    to="+2347044896129, +2348063616529, +2348186454684"
    from="+2348086108361"
    body="Greetings! How are you today?"
)

print(message.sid)
