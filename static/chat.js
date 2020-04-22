
$(document).ready(function() {
    url = window.location.href;
    name = url.slice(url.lastIndexOf('/')+1);
    const chat = new WebSocket("ws://127.0.0.1:8080/chat/"+name);

    chat.onmessage = function(event) {
        data = JSON.parse(event.data);
        message = $('<div>', {class:'chat_message', text:`${data.message}`}).appendTo('.chat');
    };

    $('#chat_form').submit(function(event){
        event.preventDefault()
        if ($('.chat_form').find('textarea').val() == '') {
            return;
        }
        chat.send($('#chat_form').find('textarea').val());
        $('#chat_form').find('textarea').val('');
    });

})