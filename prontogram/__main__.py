# ProntoGram client CLI

import pika
import sys
import os
from json import loads
from concurrent.futures.thread import ThreadPoolExecutor

from pika import connection
from prontogram.models import Message

def message_handler(ch, method, properties, body: bytes):
    msg = Message.from_dict(loads(body))
    print("---")
    print("Sender: {} -- {}".format(msg.sender, msg.send_time))
    print(msg.body)
    print("---\n")

def connection_handler(rabbitmq_host: str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        print("...CONNECTED!")

        pg_username = input("ProntoGram username: ")
        print("---\n")

        channel.queue_declare(queue=pg_username, durable=True)

        channel.basic_consume(queue=pg_username, on_message_callback=message_handler, auto_ack=True)

        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("...ERROR!")
        print('ProntoGram: unable to connect to the ProntoGram message queue.')
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        connection.close()

def main():
    rabbitmq_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    print("Connecting to ProntoGram [host = {}]...".format(rabbitmq_host))
    # executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ProntoGram-Frontend")
    # executor.submit(connection_handler, rabbitmq_host)
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        print("...CONNECTED!")

        pg_username = input("ProntoGram username: ")

        channel.queue_declare(queue=pg_username, durable=True)

        channel.basic_consume(queue=pg_username, on_message_callback=message_handler, auto_ack=True)

        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("...ERROR!")
        print('ProntoGram: unable to connect to the ProntoGram message queue.')
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('ProntoGram: shutting down.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)