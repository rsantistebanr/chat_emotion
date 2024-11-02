    // static/js/chat.js
    let socket;
    document.addEventListener('DOMContentLoaded', function() {
        if (!socket) {
            socket = io();  // Solo asigna si `socket` no está definido
        }
        /* socketio = SocketIO(app, ping_timeout=30, ping_interval=10) */
        
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
                audio.play();
            }
        });
    









        // Grabar y enviar audio mediante el botón de micrófono
        if (!('webkitSpeechRecognition' in window)) {
            alert("Lo siento, tu navegador no soporta la API de Web Speech");
          } else {
            recognition = new webkitSpeechRecognition();
            recognition.lang = "es-ES"; // Configura el idioma
            recognition.interimResults = false; // Solo resultados finales
            recognition.maxAlternatives = 1;
          
            // Evento al hacer clic en el botón del micrófono
            micButton.addEventListener('click', function() {
              if (!isRecording) {
                try {
                  recognition.start(); // Intenta iniciar el reconocimiento
                  isRecording = true;
                  micButton.innerHTML = '🔴'; // Cambia el icono cuando está grabando
                  userInput.value = ''; // Limpia el input de texto
                  userInput.disabled = true; // Deshabilita el campo de texto
                } catch (error) {
                  console.error("Error al iniciar el reconocimiento de voz: ", error);
                }
              } else {
                try {
                  recognition.stop(); // Intenta detener el reconocimiento
                  isRecording = false;
                  micButton.innerHTML = '🎤'; // Cambia el icono de nuevo al micrófono
                  userInput.disabled = false; // Habilita el campo de texto
                } catch (error) {
                  console.error("Error al detener el reconocimiento de voz: ", error);
                }
              }
            });
          
            // Evento que se dispara cuando se reconoce el audio
            recognition.onresult = (event) => {
              const transcript = event.results[0][0].transcript;
              
              // Mostrar el texto transcrito en el chat (simulando un mensaje del usuario)
              messagesDiv.innerHTML += `<div class="container_mensaje_user">
                                          <div class="message user">${transcript}</div>
                                          <img class="iconoChat user" src="/static/images/icono_usuario.png" alt="ChatUser" />
                                        </div>`;
          
              // Envía el texto transcrito al servidor a través del socket
              socket.emit('message',  {'message': transcript});
              
              // Muestra el indicador de "escribiendo..."
              showTypingIndicator();
            };
          
            // Maneja errores
            recognition.onerror = (event) => {
              console.error("Error de reconocimiento de voz: ", event.error);
              if (event.error === "aborted" || event.error === "not-allowed") {
                isRecording = false; // Reinicia el estado si el reconocimiento es abortado o no permitido
                micButton.innerHTML = '🎤'; // Cambia el icono de nuevo al micrófono
                userInput.disabled = false; // Habilita el campo de texto
              }
            };
          
            // Evento que se dispara cuando el reconocimiento de voz termina
            recognition.onend = () => {
              console.log("Reconocimiento de voz finalizado");
              isRecording = false;
              micButton.innerHTML = '🎤'; // Cambia el icono de nuevo al micrófono
              userInput.disabled = false; // Habilita el campo de texto
            };
          }
    });


    window.addEventListener('beforeunload', function() {
        if (socket) {
            socket.disconnect();  // Cierra la conexión de Socket.IO
            console.log("Conexión de Socket.IO cerrada");
        }
    });



