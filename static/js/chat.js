    // static/js/chat.js
    let socket;
    document.addEventListener('DOMContentLoaded', function() {
        let socket = io();
        
        var sendButton = document.getElementById('send_button');
        var userInput = document.getElementById('user_input');
        var micButton = document.getElementById('mic_button');
        var messagesDiv = document.getElementById('messages');
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        var isRecording = false;
        var mediaRecorder;
        var audioChunks = [];
        // Almacenar todos los elementos de audio activos
        var activeAudios = [];

            // Detener todos los audios en reproducción
        function stopAllAudios() {
            activeAudios.forEach(audio => {
                audio.pause();
                audio.currentTime = 0;  // Reinicia el audio al inicio
            });
            activeAudios = [];  // Limpia la lista de audios activos
        }

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
                // Detener todos los audios activos antes de reproducir uno nuevo
                
                showTypingIndicator();
            }
        });

        // Recibir la respuesta del bot y mostrarla en el chat junto con el audio
        socket.on('bot_response', function(data) {
            var botMessage = data.response;
            var audioUrl = data.audio_url;
            var links = data.links;
            hideTypingIndicator();  // Ocultar el indicador de "escribiendo..."
            var htmlContent = `
                    <div class="container_mensaje_user">
                        <img class="iconoChat bot" src="/static/images/logoGrande.png" alt="ChatBot" />
                        <div class="message bot">${botMessage}
                `;
            // Mostrar el mensaje del bot en el chat
            contador = 0
                if (links.length > 0) {
                    links.forEach(link => {
                        contador += 1;
                        htmlContent += `<div><a href="${link}" style="color:blue" target="_blank" rel="noopener noreferrer">VIDEO ${contador}</a></div>`;
                    });
                }
                htmlContent += ` <p>¿Tienes alguna duda?. No dudes en preguntar, estoy aqui para ti.</p>
                </div>  
            </div>
        `;
            messagesDiv.innerHTML += htmlContent
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            // Reproducir el archivo de audio de la respuesta si está disponible
            if (audioUrl) {
                var audio = new Audio(audioUrl);
                /* audio.stop();//pausar el anterior */
                audio.play();
            }
        });
        /* Audio.prototype.stop = function() {
            this.pause();          // Pausa el audio
            this.currentTime = 0;  // Reinicia el audio al inicio
        }; */
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


    window.addEventListener('beforeunload', function() {
        if (socket) {
            socket.disconnect();  // Cierra la conexión de Socket.IO
            console.log("Conexión de Socket.IO cerrada");
        }
    });



