// static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    var socket = io();
    
    var sendButton = document.getElementById('send_button');
    var userInput = document.getElementById('user_input');
    var micButton = document.getElementById('mic_button');
    var messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    var isRecording = false;
    var mediaRecorder;
    var audioChunks = [];

    // Mostrar el indicador de "escribiendo..."
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        typingIndicator.id = 'typingIndicator';
        typingIndicator.innerHTML = `
            <div class="container_mensaje_user">
                <img class="iconoChat bot" src="/static/images/logoGrande.png" alt="ChatBot" />
                <div class="message bot"> 
                    <div class="">Preparando respuesta </div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>`;
        messagesDiv.appendChild(typingIndicator);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Ocultar el indicador de "escribiendo..."
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Enviar mensaje de texto
    sendButton.addEventListener('click', function() {
        var message = userInput.value;
        if (message) {
            // Muestra el mensaje del usuario en el chat
            messagesDiv.innerHTML += `<div class="container_mensaje_user"><div class="message user">${message}</div><img class="iconoChat user" src="/static/images/icono_usuario.png" alt="ChatUser" /></div>`;
            userInput.value = '';  // Limpia el input
            socket.emit('message', {'message': message});  // Envía mensaje de texto
            showTypingIndicator();
        }
    });

    // Recibir la respuesta del bot y mostrarla en el chat junto con el audio
    socket.on('bot_response', function(data) {
        var botMessage = data.response;
        var audioUrl = data.audio_url;
        hideTypingIndicator();  // Ocultar el indicador de "escribiendo..."

        // Mostrar el mensaje del bot en el chat
        messagesDiv.innerHTML += `<div class="container_mensaje_user"><img class="iconoChat bot" src="/static/images/logoGrande.png" alt="ChatBot" /><div class="message bot">${botMessage}</div></div>`;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Reproducir el archivo de audio de la respuesta si está disponible
        if (audioUrl) {
            var audio = new Audio(audioUrl);
            audio.play();
        }
    });

    // Grabar y enviar audio mediante el botón de micrófono
    micButton.addEventListener('click', function() {
        if (!isRecording) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    isRecording = true;
                    micButton.innerHTML = '🔴';  // Cambia el icono cuando está grabando
                    userInput.value = '';  // Limpia el input de texto
                    userInput.disabled = true;  // Deshabilita el campo de texto

                    mediaRecorder.ondataavailable = function(event) {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = function() {
                        var audioBlob = new Blob(audioChunks, { 'type': 'audio/webm' });
                        audioChunks = [];
                        
                        // Crear un objeto URL para mostrar el audio en el chat
                        var audioUrl = URL.createObjectURL(audioBlob);
                        messagesDiv.innerHTML += `<div class="container_mensaje_user"><div class="message user"><audio controls><source src="${audioUrl}" type="audio/webm"></audio></div><img class="iconoChat user" src="/static/images/icono_usuario.png" alt="ChatUser" /></div>`;
                        
                        // Envía el audio grabado al servidor a través de socket para conversión
                        socket.emit('audio_message', audioBlob);
                        showTypingIndicator();  // Muestra el indicador de "escribiendo..."
                        userInput.disabled = false;  // Habilita el campo de texto nuevamente
                    };
                });
        } else {
            mediaRecorder.stop();
            isRecording = false;
            micButton.innerHTML = '🎤';  // Cambia el icono de nuevo al micrófono
        }
    });
});






