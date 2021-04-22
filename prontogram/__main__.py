from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
)
from flask_socketio import SocketIO, join_room
from os import environ
from threading import Timer
import sys
from json import loads, dumps
import pika
from prontogram.models.message import Message
from datetime import datetime, timezone

# Initialization of Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = environ.get("FLASK_SECRET_KEY")
rabbitmq_host = environ.get("RABBITMQ_HOST")
socket_io = SocketIO(app, cors_allowed_origins="*")


# RabbitMQ

def connection_handler(rmq_host: str) -> pika.adapters.blocking_connection.BlockingChannel:
    """
    Creates the connection channel through which connecting to ProntoGram's RabbitMQ instance.
    @param rmq_host: host of the RabbitMQ instance.
    @return: connection channel for RabbitMQ.
    """
    print(f"Connecting to ProntoGram [host = {rmq_host}]...")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rmq_host))
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
    """
    Callback for setting up the handler for messages published on the queue.
    @param channel: RabbitMQ channel in which to consume messages.
    @param context: context required for RabbitMQ to work properly inside a different thread than MainThread.
    @param pg_username: name of the queue and the socket in which messages are respectively read and written.
    """
    with context:

        def message_handler(ch, method, properties, body: bytes):
            """
            Callback for handling message consuming and publishing on the WebSocket.
            @param ch:
            @param method:
            @param properties:
            @param body: message body
            """
            with context:
                json = loads(body)
                msg = Message.from_dict(json)
                print(f"---\nSender: {msg.sender} -- {msg.send_time}\n{msg.body}\n---\n")
                socket_io.send(dumps(json), json=True, room=pg_username)

        channel.queue_declare(queue=pg_username, durable=True)

        channel.basic_consume(
            queue=pg_username, on_message_callback=message_handler, auto_ack=True
        )

        channel.start_consuming()


# Flask

@socket_io.on('join')
def on_join(room):
    """
    Handles the join event published on the WebSocket created by Socket.IO in __main__.
    A message is published when the user joins the room.
    @param room: channel in which publishing messages for the WebSocket.
    """
    join_room(room)
    msg = Message("ProntoGram", room, "Hai effettuato l'accesso a ProntoGram.", datetime.now(tz=timezone.utc).isoformat())
    socket_io.send(dumps(msg.to_dict()), json=True, room=room)


@app.route("/messages", methods=["GET"])
def messages():
    """
    Returns the messages page.
    """
    pg_username = request.args.get("pg_username")
    channel = connection_handler(rabbitmq_host)

    # Creating a thread with some delay (3 seconds)
    # otherwise the pending messages on the queue
    # would be handled without showing them.
    timer = Timer(
        3, function=queue_selection, args=(channel, app.app_context(), pg_username)
    )
    timer.start()
    return render_template("messages.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Returns the login page. If the query parameter pg_username is set in a POST request then it redirects to the messages page.
    """
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
    """
    Redirects to the login page.
    """
    return redirect(url_for("login"))


if __name__ == "__main__":
    host = environ.get("PRONTOGRAM_HOST", "0.0.0.0")
    port = environ.get("PRONTOGRAM_PORT", "8080")
    socket_io.run(app, host=host, port=port)
