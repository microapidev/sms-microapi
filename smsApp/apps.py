import threading

from django.apps import AppConfig

from smsApp.amqp import AMQPConsuming


class SmsappConfig(AppConfig):
    name = 'smsApp'

    def ready(self):
        consumer = AMQPConsuming()
        consumer.daemon = True
        consumer.start()
