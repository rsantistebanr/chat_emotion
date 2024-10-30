// static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    var socket = io();
    
    var sendButton = document.getElementById('send_button');
    var userInput = document.getElementById('user_input');
    var messagesDiv = document.getElementById('messages');
    
    sendButton.addEventListener('click', function() {
        var message = userInput.value;
        
        if (message) {
            // Mostrar el mensaje del usuario en el chat
            messagesDiv.innerHTML += '<div class="message user">' + message + '</div>';
            userInput.value = '';
            
            // Enviar el mensaje al servidor (Flask) para obtener la respuesta del bot
            socket.emit('message', {'message': message});
        }
    });

    // Recibir la respuesta del bot y mostrarla en el chat
    socket.on('bot_response', function(data) {
        var botMessage = data.response;
        messagesDiv.innerHTML += '<div class="message bot">' + botMessage + '</div>';
    });
});
