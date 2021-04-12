const messageTemplate = "<div class=\"col\">" +
    "<div class=\"card rounded shadow-sm m-1\">" +
    "<div class=\"card-body\">" +
    "<h2 class=\"card-title\">Messaggio da {{sender}}</h2>" +
    "<h3 class=\"card-subtitle mb-2 text-muted\">{{send_time}}</h3>" +
    "<p class=\"card-text\">{{body}}</p>" +
    "</div></div></div>";

$(document).ready(function () {
    let socket = io.connect(prontogramSocket);

    const params = new URLSearchParams(window.location.search);
    const pg_username = params.get('pg_username');
        
    socket.emit('join', pg_username);

    socket.on('json', function (json_msg) {

        const message = JSON.parse(json_msg);
        if (message.receiver === pg_username){
            if($('#no_messages').length > 0) {
                $('#no_messages').remove();
            }

            const date = new Date(message.send_time);

            const html = messageTemplate
                .replace('{{sender}}', message.sender)
                .replace('{{send_time}}', date.toLocaleString())
                .replace('{{body}}', message.body);

            $('#messages').prepend(html);
        }
    });
});
