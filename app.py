# app.py (Backend de Flask)
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from pydub import AudioSegment
from huggingface_hub import InferenceClient
from translate import Translator
import base64
from flask_pymongo import PyMongo
from flask import session, redirect, url_for
from datetime import datetime , timedelta # Importa el módulo datetime
import re
from pydub.utils import which


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") #
socketio = SocketIO(app)



# Configurar la aplicación Flask y MongoDB
app.config["MONGO_URI"] =  os.getenv("MONGO_URI")     # Cambia esto a la URI de tu MongoDB
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Recibir datos del formulario
        user = request.form.get('user')
        password = request.form.get('password')
        
        # Buscar al usuario en la colección de MongoDB
        usuario = mongo.db.usuarios.find_one({"user": user, "password": password})
        
        if usuario:
            # Si las credenciales son correctas, iniciar sesión y redirigir al chat
            session['user'] = usuario['user']
            return redirect(url_for('emotion'))
        else:
            # Si las credenciales son incorrectas, mostrar un mensaje de error
            error = "Usuario o contraseña incorrectos"
            return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/emotion')
def emotion():
    usuario =   session['user'] 
    if usuario:
        # Si las credenciales son correctas, iniciar sesión y redirigir al chat
        return render_template('emotion.html')
    else:
        return render_template('login.html')

# Ruta para la página de reconocimiento de emociones
@app.route('/emotion_recognition')
def emotion_recognition():
    usuario =   session['user'] 
    if usuario:
        # Si las credenciales son correctas, iniciar sesión y redirigir al chat
        return render_template('emotion.html')
    else:
        return render_template('login.html')

@app.route('/webcam')
def webcam():
    usuario =   session['user'] 
    if usuario:
        # Si las credenciales son correctas, iniciar sesión y redirigir al chat
        return render_template('webcam.html')
    else:
        return render_template('login.html')
    
# Endpoint para recibir la imagen y devolver la emoción
@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    data = request.get_json()
    
    # Simulación de procesamiento: decodificar imagen base64
    image_data = data['image']
    # Aquí procesarías la imagen con tu modelo de reconocimiento de emociones
    # Simulamos la respuesta del modelo:
    emociones = ['feliz', 'triste', 'neutral', None]  # Simulamos algunas emociones
    emocion_detectada = 'feliz'  # Aquí puedes hacer que sea aleatorio o basado en el modelo

    # Simulamos que la emoción puede ser None (no se detecta nada)
    if emocion_detectada:
        return jsonify({"emocion": emocion_detectada})
    else:
        return jsonify({"emocion": None})
    

@app.route('/save_emotion', methods=['POST'])
def save_emotion():
    data = request.get_json()
    emocion = data.get('emocion', None)

    # Guardar la emoción en la sesión
    session['emocion'] = emocion
    return jsonify({"status": "success"})


@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400
    
    audio_file = request.files['audio']
    input_path = 'uploaded_audio.mp3'
    #output_path = 'converted_audio.wav'
    
    # Guardar el archivo MP3 temporalmente
    audio_file.save(input_path)

    # Convertir el MP3 a WAV usando pydub
    try:
        sound = AudioSegment.from_mp3(input_path)
        #sound.export(output_path, format="wav")
    except Exception as e:
        return jsonify({'error': f"Error al convertir a WAV: {str(e)}"}), 500

    # Usar speech_recognition para convertir el archivo WAV a texto
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(sound) as source:
            audio = recognizer.record(source)
        transcript = recognizer.recognize_google(audio)
        return jsonify({'transcript': transcript})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_db')
def test_db():
    try:
        result = mongo.db.users.find_one({"users":"oso2001"})  # Realizar una consulta básica para probar la conexión
        return "Conexión a MongoDB exitosa!"
    except Exception as e:
        return f"Error en la conexión a MongoDB: {e}"
    

@app.route('/pruebas')
def pruebas():
    return render_template('bk.html')

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
       # Generar un nombre de archivo seguro sin caracteres no permitidos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_path = os.path.join('static/grabaciones/', f'mensaje-{timestamp}.webm')
    wav_path = os.path.join('static/grabaciones/', f'mensaje-{timestamp}.wav')
    
    audio_file.save(original_path)
    
    try:
        # Convertir el archivo a WAV PCM, especificando 1 canal y 16 kHz para asegurar compatibilidad
        audio = AudioSegment.from_file(original_path)
        audio = audio.set_frame_rate(16000).set_channels(1)  # 16kHz, mono
        audio.export(wav_path, format="wav", parameters=["-ac", "1", "-ar", "16000", "-sample_fmt", "s16"])

        # Procesa el archivo convertido a texto
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="es-ES")
            return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"No se pudo procesar el audio: {e}"}), 500
    finally:
        # Limpieza opcional: Elimina los archivos temporales
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
    
# Ruta para la página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Recibir datos del formulario
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        user = request.form.get('user')
        password = request.form.get('password')
        # Verificar si el usuario ya existe en la colección
        usuario_existente = mongo.db.usuarios.find_one({"user": user})
        if usuario_existente:
            # Si el usuario ya existe, redirigir a la vista del chat
            session['user'] = user
            error = "Usuario no esta diponible."
            return render_template('registrar.html', error=error)
    
        else:
            # Si no existe, insertar un nuevo documento en la colección 'usuarios'
            nuevo_usuario = {
                "name": name,
                "age": age,
                "gender":gender,
                "user": user,
                "password": password
            }
            mongo.db.usuarios.insert_one(nuevo_usuario)
            
            # Guardar el nombre del usuario en la sesión
            session['user'] = user
            
            # Redirigir al chat después del registro
            return redirect(url_for('login'))
    
    return render_template('registrar.html')

# Ruta para el chat

@app.route('/sendEmotion', methods=['POST'])
def EmotionSend():
    user = session['user']
    if user:
        emotion = request.json.get("emotion")
        if emotion:
            session['emotion'] = emotion
        return redirect(url_for('chat'))
        
    else:
        return redirect(url_for('login'))

@app.route('/chat2', methods=['GET']) #para NO
def chatNo():
    if 'user' in session:
        user = session['user']
        mesajeInicial = ''
        fecha_hoy =  datetime.now().strftime("%Y-%m-%d")
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        mesajeInicial, alternativas = retornarMensasjeInicial(emotion='neutral', user=user)

        # Consultar mensajes de hoy y de ayer en MongoDB para el usuario actual
        mensajes_anteriores = list(mongo.db.mensajes.find({
            "fecha": {"$in": [fecha_hoy, fecha_ayer]},
            "user": user
        }).sort("fecha", 1).sort("hora", 1))

        # Renderizar el chat con los mensajes del día anterior y el mensaje de bienvenida
        return render_template('chat.html', user=user, mensajes_anteriores=mensajes_anteriores, mesajeInicial = mesajeInicial[0], alternativas = None )
    else:
        return redirect(url_for('login'))

@app.route('/chat', methods=['GET']) #para si
def chat():
    if 'user' in session:
        user = session['user']
        mesajeInicial = ''
        emotion = session.get('emotion')
        if emotion:
            mesajeInicial, alternativas = retornarMensasjeInicial(emotion=emotion, user=user)

        # Obtener la fecha de hoy y de ayer
        fecha_hoy =  datetime.now().strftime("%Y-%m-%d")
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Consultar mensajes de hoy y de ayer en MongoDB para el usuario actual
        mensajes_anteriores = list(mongo.db.mensajes.find({
            "fecha": {"$in": [fecha_hoy, fecha_ayer]},
            "user": user
        }).sort("fecha", 1).sort("hora", 1))

        # Renderizar el chat con los mensajes del día anterior y el mensaje de bienvenida
        return render_template('chat.html', user=user, mensajes_anteriores=mensajes_anteriores, mesajeInicial = mesajeInicial , alternativas= alternativas)
    else:
        return redirect(url_for('register'))

    
################################################################
#FUNCIONES:
################################################################
@socketio.on('message')
def handle_message(data):
    links = []
    respuestaEspañol = 'No entendi tu pregunta, vuelve a realizarla por favor.'
    user_message = data['message']
    user = session['user']
    try:
        guardarMensaje(user_message,user, 0)
        #guardo el promt del chat
        promt = traducir("es", "en",user_message )
        #hacemos el proceso de finituning
        user = session.get('user', 'user')
        emocion = session['emotion']
        print('pasooo: ', emocion)

        """ if user_message !='' and user_message != None:
            emocion = session['emotion']
            if emocion == 'sad': # and 'GRACIAS' in user_message.upper():
                print('pasooo33') """

        if re.search('gracia'.lower(), user_message.lower()):  #verificamos que pregunta posible esta llegando:
            respuestaEspañol = 'Me alegra haberte ayudado.'
        else:
            respuestaEspañol, links =  generearRespuestaSeleccion(emocion, user_message) 
            #guardarMensaje(respuestaEspañol,user, 1)
            print(" len links: ", len(links))
            print(" lista links: ", links)
            print('respuestaEspañol: ',respuestaEspañol) 

        if respuestaEspañol == '':
            print('kskksoncl paso')
               
            try:
                bot_reply = procesamientoNPL(promt)
                respuestaEspañol = traducir_español(bot_reply)
                #bot_reply = "MENSAJE DEL CHAT" #response['choices'][0]['text'].strip()

                # Convertir la respuesta del bot en audio usando gTTS
                ''' tts = gTTS(text=respuestaEspañol, lang='es')
                audio_filename = f"static/audio/response_{respuestaEspañol[:10]}.mp3"
                tts.save(audio_filename)
                guardarMensaje(respuestaEspañol,user, 1)'''
                # Enviar la respuesta y la URL del archivo de audio
            
            # emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})
            except ValueError:
                respuestaEspañol = 'No pude procesar la respuesta. Intentemos nuevamente'
                audio_filename = None
                links = []
                emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename, 'links':links})
            except Exception as e:
                respuestaEspañol = 'No pude procesar la respuesta. Intentemos nuevamente'
                audio_filename = None
                links = []
                emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename ,'links':links})


        tts = gTTS(text=respuestaEspañol, lang='es')
        audio_filename = f"static/audio/response_{respuestaEspañol[:10]}.mp3"
        tts.save(audio_filename)
        guardarMensaje(respuestaEspañol,user, 1)
        emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename, 'links':links})
    except Exception as e:
        respuestaEspañol = 'No pudimos procesar tu pregunta, intententemos nuevamente.'
        audio_filename = None
        links = []
        emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename, 'links':links})

    # Llamar a la API de OpenAI para obtener la respuesta del modelo
    #response = openai.Completion.create(    #    engine="text-davinci-003",    #    prompt=user_message,    #    max_tokens=150    #)
    

@socketio.on('audio_message')
def handle_audio_message(audio_data):
    # Guarda el audio temporalmente y convierte a WAV PCM
    ruta = 'static/grabaciones/'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    webm_path = os.path.join(ruta, f'audio_{timestamp}.webm')
    wav_path = os.path.join(ruta, f'audio_{timestamp}.wav')

    with open(webm_path, 'wb') as f:
        f.write(audio_data)

    audio = AudioSegment.from_file(webm_path)
    audio.set_frame_rate(16000).set_channels(1).export(wav_path, format="wav")

    # Conversión de audio a texto
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_text = recognizer.record(source)
            user_message = recognizer.recognize_google(audio_text, language="es-ES")

        # Respuesta del bot
        user = session.get('user', 'user')
        emocion = session['emotion']
        print('pasooo: ', emocion)
        guardarMensaje(user_message,user, 1) #GUARDAMOS LA PREGUNTA
        print('pasoiiii')

        if user_message !='' and user_message != None:
            emocion = session['emotion']
            if emocion == 'sad' and 'GRACIAS' in user_message.upper():
                print('pasooo')
                respuestaEspañol, links =  generearRespuestaSeleccion(emocion, user_message) 
                guardarMensaje(respuestaEspañol,user, 1)#GUARDAMOS LA RESPUESTA

            elif  'GRACIAS' in user_message.upper():  #verificamos que pregunta posible esta llegando:
                respuestaEspañol = 'Me alegra haberte ayudado. Si tienes alguna duda,no dudes en preguntarme.'
                tts = gTTS(text=respuestaEspañol, lang='es')
                audio_filename = f"static/audio/response_{respuestaEspañol[:10]}.mp3"
                tts.save(audio_filename)
                guardarMensaje(user_message,user, 1)
                emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})

            else:
                promt = traducir("es", "en", user_message)
                bot_reply = procesamientoNPL(promt)
                respuestaEspañol = traducir_español(bot_reply)
                guardarMensaje(respuestaEspañol,user, 1)
                audio_filename = f"static/audio/response_{timestamp}.mp3"
                # Genera el audio de la respuesta
                tts = gTTS(text=respuestaEspañol, lang='es')
                tts.save(audio_filename)
                
                emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})
    except Exception as e:
        emit('bot_response', {'response': f"Error en el procesamiento de audio: {e}", 'audio_url': None})
    finally:
        os.remove(webm_path)
        os.remove(wav_path)
                  
def procesamientoNPL(promt):
    #Preparamos variables para el promt
    try:
        user = session['user']
        usuario = mongo.db.usuarios.find_one({"user": user})
        edad_genero = 'You are an understanding and conversational friend.'
        EDAD = int(usuario['age'])
        if EDAD < 13:
            if usuario['gender'] == 'Hombre':
                edad_genero = f'''I am a {EDAD} year old boy, based on that give your answer.'''
            else:
                edad_genero = f'''I am a {EDAD} year old girl, based on that give your answer.'''
        elif EDAD>13 and EDAD < 20:
            if usuario['gender'] == 'Hombre':
                edad_genero = f'''I am a teenager of {EDAD} years old, based on that give your answer'''
            else:
                edad_genero = f'''I am a teenager of {EDAD} years old, based on that give your answer'''
        else:
            edad_genero =f'''I am a young man of {EDAD} years, based on that give your answer'''
     
        #traducimos
        edad_genero += edad_genero + ".My name is " + user
        adicionales = ["Usa Maximum 80 words",edad_genero, "Finaliza con la pregunta ¿Tienes alguna duda?" ] #Colocarlos en ingles
        promt = promt + "." + adicionales[0] + "." +adicionales[1]
        #PROCESAMIENTO NL (PNL)
        client = InferenceClient(api_key=os.getenv("api_key"))
        respuestaModelo = ''
        for message in client.chat_completion(
            #model="mistralai/Mistral-Nemo-Instruct-2407",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
            messages=[{"role": "user", "content": promt}],
            max_tokens=500,
            temperature=0.8,
            stream=True,
        ):
            respuestaModelo += message.choices[0].delta.content
        #------------------- SEGUNDA OPCION --------------------
        return respuestaModelo
    
    except Exception as a:
      respuestaModelo = 'No pude procesar tu pregunta. Intentemos nuevamente'
      return respuestaModelo

def traducir(lang_after , lang_before, texto):
    # Crear un traductor del español o quechua al inglés
    translator = Translator(from_lang=lang_after, to_lang=lang_before)
    # Texto que el usuario ingresa en español o quechua
    promt = texto 
    # Traducir el texto al inglés
    traduccion = translator.translate(promt)
    return traduccion

def traducir_español(textoENG):
    translator = Translator(from_lang="en", to_lang="es")
    # Dividir el texto en fragmentos de 490 caracteres o menos
    texto_usuario = textoENG 
    fragmentos = dividir_texto_por_caracteres(texto_usuario,  max_caracteres=490)
    # Traducir cada fragmento por separado y combinar los resultados
    traducciones = [translator.translate(fragmento) for fragmento in fragmentos]
    # Unir todas las traducciones en un solo texto
    traduccion_completa = ' '.join(traducciones)
    return traduccion_completa

def dividir_texto_por_caracteres(texto, max_caracteres=490):
    fragmentos = [texto[i:i + max_caracteres] for i in range(0, len(texto), max_caracteres)]
    return fragmentos

def convert_to_wav(audio_file, output_file):
    # Cargar el archivo de audio en cualquier formato
    sound = AudioSegment.from_file(audio_file)
    
    # Convertirlo a formato WAV
    sound.export(output_file, format="wav")
    #print(f"Archivo convertido guardado como: {output_file}")

def guardarMensaje(promt,user, tipo):
    current_datetime = datetime.now()
    fecha_actual = current_datetime.strftime("%Y-%m-%d")  # Formato de fecha: Año-Mes-Día
    hora_actual = current_datetime.strftime("%H:%M:%S")   # Formato de hora: Hora:Minutos:Segundos

    
    nuevo_usuario = {
        "user": user,
        "fecha":fecha_actual ,
        "hora":hora_actual ,
        "mensaje":promt,
        "tipo": tipo # 0:user - 1: bot
    }
    print('se guardamensaje')
    mongo.db.mensajes.insert_one(nuevo_usuario)

def diaHoraActual():
    current_datetime = datetime.now()
    fechaHora_actual = current_datetime.strftime("%Y-%m-%d %H-%M-%S")  # Formato de fecha: Año-Mes-Día
    return fechaHora_actual

def retornarMensasjeInicial(emotion, user):
    saludo = f''' Hola {user}. ¿En qué te puedo ayudar hoy?.'''
    mensajes = [ saludo]
    alternativas = None
    print("emotionemotion",emotion)
    mensajeInicialFeliz = [
        'Que bueno que te encuentres de buen estado anímico, continúa así, ¿Deseas que te ayude en alguna tarea o consejo académico?',
    ]
    mensajeInicialSad = [
        '¿Por qué crees que te sientes así? si me respondes de forma sincera, podré ayudarte de mejor manera y así puedas sentirte mejor.',
    ]
    if emotion == 'happy':

        mensajes = mensajeInicialFeliz[0]
        alternativas  = None
        

    elif emotion ==  'sad':
        alternativas  = ["Causa 1: Te sientes ansioso por los exámenes",
                        "Causa 2: Tienes estrés por carga Académica o sientes que me falta Tiempo para terminar tus tareas",
                        "Causa 3: ¿Algún problema familiar?"
                        ]
        mensajes = mensajeInicialSad[0]


    elif emotion == 'neutral':
        mensajeInicial = f'''Hola {user}. ¿En qué te puedo ayudar hoy?.  '''
    
    return mensajes, alternativas






def generearRespuestaSeleccion(emocion, promt):
    print('pasoo generearRespuestaSeleccion')
    palabrasClave1 = []
    palabrasClave2 = []
    palabrasClave3 = []
    RespuestasSadOp = [""]
    links = []
    if emocion == 'happy':
        PalabrasClave = ['academica,pregunta academica,consulta academicam,Te consultare una cosa sobre'] #consulta academica
    elif emocion == 'sad':
        opcion = '0'
        palabrasClave1 = ["ANSIOS", "ANSIEDAD", "ME SIENTO ANSIOS"]
        palabrasClave2 = ["ESTRESAD", "TRISTE Y ESTRESAD", "ESTRÉS", "ESTRES", "CARGA ACADEMICA", "FALTA DE TIEMPO"]
        palabrasClave3 = ["PROBLEMAS FAMILIARES", "FAMILIA"]

        for palabra in palabrasClave1:
            print('palabra: ', palabra , "frase: ", promt)
            if re.search(palabra.lower(), promt.lower()):
                opcion = '1'
                print(f"La palabra '{palabra}' está parcialmente contenida en la frase.")
        if opcion == '0':
            for palabra in palabrasClave2:
                print('palabra: ', palabra , "frase: ", promt)
                if re.search(palabra.lower(), promt.lower()):
                    opcion = '2'
                    print(f"La palabra '{palabra}' está parcialmente contenida en la frase.")
        if opcion == '0':
             for palabra in palabrasClave3:
                print('palabra: ', palabra , "frase: ", promt)
                if re.search(palabra.lower(), promt.lower()):
                    opcion = '3'
                    print(f"La palabra '{palabra}' está parcialmente contenida en la frase.") 

        print('opcion: ', opcion)
        if opcion == '1': 
            RespuestasSadOp = [ "La ansiedad por los exámenes es algo que muchos experimentamos, y hay técnicas que pueden ayudarte. Una de"+
                " ellas es la ‘Visualización Positiva’. Antes del examen, cierra los ojos y visualiza cómo entras en la sala "+
                " tranquilo, respondiendo las preguntas con confianza y sintiéndote aliviado al terminar. Repite esto varias veces"+
                "   para preparar tu mente. Otra técnica es la Caja de Respiración: inhala contando hasta 4, mantén el aire por 4,"+
                "     exhala por 4 y espera 4 antes de volver a inhalar. Esto calma tu sistema nervioso. También, asegúrate de dormir"+
                "       bien antes del examen; el descanso es clave."
                ,            
                "El estrés por la escuela es normal. Si sientes que no puedes con todo, prueba esta técnica: respira profundo, "+
                "sostén el aire por 4 segundos y exhala despacio. Esto te ayuda a calmar la mente. Divide las tareas en partes pequeñas " +
                "y hazlas una por una. Usa un horario sencillo para organizarte y date descansos cortos para estirarte o caminar. Hacer " +
                "ejercicio o practicar mindfulness (como cerrar los ojos y concentrarte en tu respiración) también ayuda. Hablar con amigos," +
                "  tus padres o un consejero puede ser útil si te sientes muy estresado."+
                "Te dejo unos links de relajacion para mayor detalle: "
                ,
                "A veces, la escuela puede hacernos sentir atrapados en un torbellino de tareas y exámenes. Para esos momentos, te sugiero probar" +
                  "la técnica del ‘Escaneo Corporal’. Es fácil y efectiva. Siéntate cómodo, cierra los ojos y empieza a concentrarte en tu cuerpo." +
                  "Imagina que una luz cálida pasa desde tu cabeza hasta tus pies, relajando cada parte. Comienza por tu frente, sigue por tus hombros," +
                  "tus brazos, y así hasta los dedos de los pies. Siente cómo se libera la tensión. ¿Te gustaría intentarlo? Y recuerda: está bien no" +
                  "tener todo bajo control siempre. Descansar es parte de ser eficiente"           +
                  "Te dejo unos links de relajacion para mayor detalle:"
                  ,
                "La carga académica puede ser muy exigente, y es normal sentirse bajo presión. Una técnica útil es la Visualización Guiada. Tómate "+
                "un momento para cerrar los ojos y visualiza un lugar que te haga sentir en paz: tal vez una playa, un bosque o tu rincón favorito en" +
                "  casa. Imagina cada detalle: el sonido de las olas, el olor de los árboles, o el calor del sol en tu piel. Dedica unos minutos a esta" +
                "    imagen. Te ayudará a liberar la tensión y a refrescar tu mente. ¿Listo para probarlo? Y recuerda: ser amable contigo mismo es clave;"   
                ]
            links =["https://www.youtube.com/watch?v=0zsE85khG6I", " https://www.youtube.com/watch?v=YrTHvcuWSxg "]
             
        elif opcion == '2':
            RespuestasSadOp = [   
                   "Entiendo cómo pueden sentirse los exámenes, ¡A veces parece que nos abruman! Pero aquí te comparto una técnica simple que "+
                   " puede ayudarte a calmar esos nervios y recuperar el control: la respiración profunda. ¿La conoces? Es genial para estos momentos." +
                   " Te explico cómo aplicarla con la técnica 4-7-8:" +
                   " Primero, inhala contando hasta 4, luego mantén el aire por 7 (¡sin soltarlo!), y" +
                   " finalmente exhala lentamente contando hasta 8. Esto ayuda a tu mente a relajarse," +
                   " y con un par de repeticiones más, sentirás que los nervios se disipan. " +
                   " ¿Listo para probarla y ver cómo cambia tu enfoque? Aplícala y luego cuéntame cómo te sientes" +
                   " Y recuerda: Está bien no ser perfecto. Es normal tener días más difíciles y no siempre poder con todo." +
                   "Te dejo un link para mayor detalle: https://www.youtube.com/watch?v=4hB_v2mJdGg "
                , 
                
                "El estrés por la escuela es normal. Si sientes que no puedes con todo, prueba esta técnica: respira profundo, "+
                "sostén el aire por 4 segundos y exhala despacio. Esto te ayuda a calmar la mente. Divide las tareas en partes pequeñas " +
                "y hazlas una por una. Usa un horario sencillo para organizarte y date descansos cortos para estirarte o caminar. Hacer " +
                "ejercicio o practicar mindfulness (como cerrar los ojos y concentrarte en tu respiración) también ayuda. Hablar con amigos," +
                "  tus padres o un consejero puede ser útil si te sientes muy estresado."+
                "Te dejo un link de relajacion para mayor detalle: https://www.youtube.com/watch?v=0zsE85khG6I "
                ,
                "A veces, la escuela puede hacernos sentir atrapados en un torbellino de tareas y exámenes. Para esos momentos, te sugiero probar" +
                  "la técnica del ‘Escaneo Corporal’. Es fácil y efectiva. Siéntate cómodo, cierra los ojos y empieza a concentrarte en tu cuerpo." +
                  "Imagina que una luz cálida pasa desde tu cabeza hasta tus pies, relajando cada parte. Comienza por tu frente, sigue por tus hombros," +
                  "tus brazos, y así hasta los dedos de los pies. Siente cómo se libera la tensión. ¿Te gustaría intentarlo? Y recuerda: está bien no" +
                  "tener todo bajo control siempre. Descansar es parte de ser eficiente"           +
                  "Te dejo unos links de relajacion para mayor detalle: https://www.youtube.com/watch?v=YrTHvcuWSxg "
                  ,
                "La carga académica puede ser muy exigente, y es normal sentirse bajo presión. Una técnica útil es la Visualización Guiada. Tómate "+
                "un momento para cerrar los ojos y visualiza un lugar que te haga sentir en paz: tal vez una playa, un bosque o tu rincón favorito en" +
                "  casa. Imagina cada detalle: el sonido de las olas, el olor de los árboles, o el calor del sol en tu piel. Dedica unos minutos a esta" +
                "    imagen. Te ayudará a liberar la tensión y a refrescar tu mente. ¿Listo para probarlo? Y recuerda: ser amable contigo mismo es clave;"   
                ]
            links =["https://www.youtube.com/watch?v=4hB_v2mJdGg", "https://www.youtube.com/watch?v=0zsE85khG6I", "https://www.youtube.com/watch?v=YrTHvcuWSxg"]
        elif opcion == '3':
            RespuestasSadOp = [    
                   "Sé que los problemas familiares pueden sentirse muy pesados y afectar tu bienestar. Una estrategia útil es la ‘Meditación de Compasión’. Encuentra un lugar tranquilo, cierra los ojos y respira profundo. Visualiza a ti mismo enviándote compasión y entendimiento, como si estuvieras abrazando tu propio dolor. Luego, imagina enviando esa misma compasión a tu familia, incluso si es difícil. Esto no resuelve los problemas, pero puede ayudarte a liberar la tensión emocional. También, un paseo al aire libre puede despejar tu mente y darte claridad. Y nunca olvides que hablar con alguien que te apoye es fundamental." +
                   "Te dejo un link con algunos videos graciosos para que rias un rato: https://www.youtube.com/watch?v=5x1v2l8OAnk&ab_channel=LosTitis-CuentosyCancionesdeMotivaci%C3%B3nInfantil ",
                   "Lamento que estés pasando por una situación tan difícil. Los problemas familiares pueden ser muy estresantes, especialmente cuando intentas mantener el enfoque en otras áreas de tu vida. A veces, hablar con alguien en quien confíes o escribir sobre lo que sientes puede aliviar la carga. Recuerda, no tienes que enfrentar esto solo, busca a un docente, tutor o ayuda profesional para contarle lo que te pasa." +
                   "Espero que este consejo te sea útil, recuerda que estoy aquí para ayudarte. "+
                    "Para que rias un poquito, te dejo unos chistes:"
            ]
            links =["https://www.youtube.com/watch?v=5x1v2l8OAnk&ab_channel=LosTitis-CuentosyCancionesdeMotivaci%C3%B3nInfantil "]

    else: #neutro
        respuesta = 'Respuesta para neutro'
    print("RespuestasSadOp[0]; ",RespuestasSadOp[0])
    
    return RespuestasSadOp[0], links

def respuestasSegundoNivelAfirmativo (bandera, opcion, emocion): #Cuando indica que si le ayudo la respuesta anterior
    if bandera.upper() == 'SI':
        if emocion == 'sad':
            if opcion == '1':
                respuestas = ["¡Me alegra mucho escuchar eso! A veces, pequeños pasos son suficientes para darle a nuestra mente un respiro y ganar confianza. Felicidades por darte el tiempo de probar una técnica para calmarte."
                            , "Recuerda que esta sensación de calma que alcanzaste ahora es una prueba de que tienes la capacidad de gestionar tus emociones en momentos difíciles. Si en algún momento vuelves a sentirte ansioso, piensa en esta experiencia y repite lo que te ayudó."
                            , "¿Te gustaría aprender alguna otra estrategia para futuras ocasiones? Siempre puedes fortalecer tus habilidades para enfrentar desafíos y lograr tus metas."

                ]
            elif opcion == '2':
                respuestas = ["¿Sabías que estudiar en bloques de tiempo puede ayudarte a concentrarte mejor y evitar el agobio? Esta es una técnica increíblemente útil y, además, sencilla de aplicar. Usar bloques cortos de tiempo hace que estudiar se sienta más manejable y menos pesado."
                            , "Una de las técnicas más recomendadas es el método Pomodoro: consiste en estudiar durante 25 minutos y luego darte un descanso de 5. Estos pequeños descansos ayudan a tu cerebro a descansar y a procesar mejor la información, evitando que te sientas agotado."
                            ,"Como decía Einstein: 'No soy tan inteligente; simplemente trabajo en los problemas más tiempo que los demás.' No se trata de cuántas horas estudias, sino de cómo organizas ese tiempo para aprovecharlo al máximo."
                            ,"Con un buen plan, puedes lograr mucho más en menos tiempo y con menos esfuerzo. Si quieres estructurar bien tu tiempo, te propongo que armes un horario simple con bloques de estudio y descanso. Así, podrás ver cuánto tiempo tienes y cómo aprovecharlo mejor." ]
            
            elif opcion == '3':
                respuestas = "Genial, me alegro aver ayudado. ¿Deseas que te ayude en alguna tarea o consejo académico?"

            

        

        

if __name__ == '__main__':
    # Detecta si está en el entorno de desarrollo
    if os.getenv("FLASK_ENV") == "development":
        socketio.run(app, debug=True)  # Ejecuta con el servidor de desarrollo en local
    else:
        # En producción, `gunicorn` manejará la ejecución de la aplicación,
        # así que no es necesario ejecutar `socketio.run()` aquí.
        pass
