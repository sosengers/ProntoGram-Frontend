const messageTemplate = "<div class=\"col\">" +
    "<div class=\"card rounded shadow-sm m-1\">" +
    "<div class=\"card-body\">" +
    "<h2 class=\"card-title\">Messaggio da {{sender}}</h2>" +
    "<h3 class=\"card-subtitle mb-2 text-muted\">{{send_time}}</h3>" +
    "<p class=\"card-text\">{{body}}</p>" +
    "</div></div></div>";

$(document).ready(function () {
    const params = new URLSearchParams(window.location.search);

    // If the username was not set in the login page then empty_username is set as query parameter with value 1.
    const empty_username = params.get('empty_username');

    $("#pg_username").change(function() {
        $("#empty_username").remove();
    })

    if(empty_username !== "1") {
        $("#empty_username").remove();
    }
});
