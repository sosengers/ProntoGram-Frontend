from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
)
from flask_socketio import SocketIO, join_room
from os import environ
from threading import Thread, Timer
import sys
from json import loads, dumps
import pika
from prontogram.models.message import Message
import logging

# Initialziation of Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = environ.get("FLASK_SECRET_KEY")
rabbitmq_host = environ.get("RABBITMQ_HOST")
socketio = SocketIO(app, cors_allowed_origins="*")


# RabbitMQ


def connection_handler(host: str) -> pika.adapters.blocking_connection.BlockingChannel:
    print("Connecting to ProntoGram [host = {}]...".format(host))
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        print("...CONNECTED!")

        return channel
    except pika.exceptions.AMQPConnectionError:
        print("...ERROR!")
        print("ProntoGram: unable to connect to the ProntoGram message queue.")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


def queue_selection(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    context,
    pg_username: str,
):
    with context:

        def message_handler(ch, method, properties, body: bytes):
            with context:
                json = loads(body)
                msg = Message.from_dict(json)
                print("---")
                print("Sender: {} -- {}".format(msg.sender, msg.send_time))
                print(msg.body)
                print("---\n")
                socketio.send(dumps(json), json=True, room=pg_username)

        channel.queue_declare(queue=pg_username, durable=True)

        channel.basic_consume(
            queue=pg_username, on_message_callback=message_handler, auto_ack=True
        )

        channel.start_consuming()


# Flask

@socketio.on('join')
def on_join(room):
    join_room(room)
    #TODO: send(username + ' has entered the room.', room=room)

@app.route("/messages", methods=["GET"])
def messages():
    pg_username = request.args.get("pg_username")
    channel = connection_handler(rabbitmq_host)
    # Creating a thread with some delay otherwise the pending messages on the queue would be handled without showing them
    timer = Timer(
        3, function=queue_selection, args=(channel, app.app_context(), pg_username)
    )
    timer.start()
    return render_template("messages.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        un = request.form.get("pg_username") or "not-set"
        if un == "not-set":
            return redirect(url_for("login", empty_username=1))
        else:
            return redirect(
                url_for("messages", pg_username=request.form.get("pg_username"))
            )
    return render_template("login.html")


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("login"))


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="8080")
