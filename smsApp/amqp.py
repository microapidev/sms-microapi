import threading
import logging

import pika

RABBITMQ_HOST='localhost'
logging.basicConfig(filename='rabbitmq.log', level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


class AMQPConsuming(threading.Thread):

    def get_connection(self):
        parameters = pika.ConnectionParameters(RABBITMQ_HOST)
        return pika.BlockingConnection(parameters)

    def declaringQueues(self):
        # making queues as durable ->inorder not to lose msgs
        self.channel.queue_declare(queue='ScheduledMsgs', durable=True)
        self.channel.queue_declare(queue='UndeliveredMsgs', durable=True)

    def establish_connection(self):
        print('Establishing connection with rabbitmq')
        logging.debug("Establishing connection with rabbitmq")
        self.connection = self.get_connection()
        self.channel = self.connection.channel()
        print('declaring queues')
        logging.debug("declaring queues")
        self.declaringQueues()
        print('listening  to queues inorder to consume ')
        logging.debug("listening  to queues inorder to consume ")
        self.consume_messages()
        # example of how to publish messages
        # print('ScheduledMsgs Publishing')
        # self.publish_message('ScheduledMsgs', "test")

    def run(self):
        try:
            self.establish_connection()
            # Don't recover if connection was closed by broker
        except pika.exceptions.ConnectionClosedByBroker as error:
            print(error)
            logging.debug("ERROR->",error)
            # Don't recover on channel errors
        except pika.exceptions.AMQPChannelError as error:
            print(error)
            logging.debug("ERROR->", error)
            # Recover on all other connection errors
        except pika.exceptions.AMQPConnectionError as error:
            print(error)
            logging.debug("ERROR->", error)
            logging.debug("RETRYING TO CONNECT")
            self.establish_connection()

    def publish_message(self, queueName, message):
        print("message publishing")
        self.channel.basic_publish(exchange='',
                                   routing_key=queueName,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message persistent
                                   ))

    def scheduledMsgsCallback(self, ch, method, properties, body):
        print('Received Scheduled Message %r' % body)
        logger.debug('Received Scheduled Message %r' % body)
        # Ack message if the message is delivered
        self.channel.basic_ack(method.delivery_tag);
        # if not ack the message remains in the queue
        return body

    def consume_messages(self):
        try:
            # example of how to consume msgs
            # HERE you can declare all the queues that you want to consume from
            print('Started listener')
            self.channel.basic_consume(queue="ScheduledMsgs", auto_ack=False,
                                       on_message_callback=self.scheduledMsgsCallback)
            # Started Listener
            print('Started listener')
            self.channel.start_consuming()
            print('End of consuming listener')
        except Exception as error:
            print(error)
            logger.debug(error)
