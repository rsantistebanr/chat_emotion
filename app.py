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
        mesajeInicial = retornarMensasjeInicial(emotion='neutral', user=user)
        # Consultar mensajes de hoy y de ayer en MongoDB para el usuario actual
        mensajes_anteriores = list(mongo.db.mensajes.find({
            "fecha": {"$in": [fecha_hoy, fecha_ayer]},
            "user": user
        }).sort("fecha", 1).sort("hora", 1))

        # Renderizar el chat con los mensajes del día anterior y el mensaje de bienvenida
        return render_template('chat.html', user=user, mensajes_anteriores=mensajes_anteriores, mesajeInicial = mesajeInicial )
    else:
        return redirect(url_for('login'))

@app.route('/chat', methods=['GET']) #para si
def chat():
    if 'user' in session:
        user = session['user']
        mesajeInicial = ''
        emotion = session.get('emotion')
        if emotion:
            mesajeInicial = retornarMensasjeInicial(emotion=emotion, user=user)

        # Obtener la fecha de hoy y de ayer
        fecha_hoy =  datetime.now().strftime("%Y-%m-%d")
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Consultar mensajes de hoy y de ayer en MongoDB para el usuario actual
        mensajes_anteriores = list(mongo.db.mensajes.find({
            "fecha": {"$in": [fecha_hoy, fecha_ayer]},
            "user": user
        }).sort("fecha", 1).sort("hora", 1))

        # Renderizar el chat con los mensajes del día anterior y el mensaje de bienvenida
        return render_template('chat.html', user=user, mensajes_anteriores=mensajes_anteriores, mesajeInicial = mesajeInicial )
    else:
        return redirect(url_for('register'))

    
################################################################
#FUNCIONES:
################################################################
@socketio.on('message')
def handle_message(data):
    user_message = data['message']
    user = session['user']
    # Llamar a la API de OpenAI para obtener la respuesta del modelo
    #response = openai.Completion.create(    #    engine="text-davinci-003",    #    prompt=user_message,    #    max_tokens=150    #)

    #guardo el promt del chat
    promt = traducir("es", "en",user_message )

    guardarMensaje(promt,user, 0)            
   
    bot_reply = procesamientoNPL(promt)
    try:
        respuestaEspañol = traducir_español(bot_reply)
        #bot_reply = "MENSAJE DEL CHAT" #response['choices'][0]['text'].strip()

        # Convertir la respuesta del bot en audio usando gTTS
        tts = gTTS(text=respuestaEspañol, lang='es')
        audio_filename = f"static/audio/response_{user_message[:10]}.mp3"
        tts.save(audio_filename)
        guardarMensaje(respuestaEspañol,user, 1)
        # Enviar la respuesta y la URL del archivo de audio
        emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})
    except ValueError:
        emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})
    except Exception as e:
        emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})


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
        if user_message !='' and user_message != None:
            guardarMensaje(user_message,user, 0)

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
                #edad_genero = f''' Soy un niño de {EDAD} años, en base a eso da tu repuesta.'''
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
        adicionales = ["Maximum 300 words",edad_genero ] #Colocarlos en ingles
        promt = promt + "." + adicionales[0] + "." +adicionales[1]
        #PROCESAMIENTO NL (PNL)
        client = InferenceClient(api_key=os.getenv("api_key"))
        respuestaModelo = ''
        for message in client.chat_completion(
            #model="mistralai/Mistral-Nemo-Instruct-2407",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1", 
            messages=[{"role": "user", "content": promt}],
            max_tokens=600,
            temperature=0.7,
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
    mongo.db.mensajes.insert_one(nuevo_usuario)

def diaHoraActual():
    current_datetime = datetime.now()
    fechaHora_actual = current_datetime.strftime("%Y-%m-%d %H-%M-%S")  # Formato de fecha: Año-Mes-Día
    return fechaHora_actual

def retornarMensasjeInicial(emotion, user):
    mensajeInicial = f''' Hola {user}. ¿En qué te puedo ayudar hoy?.'''

    if emotion == 'happy':
        mensajeInicial = f''' {user}, veo que estás feliz, eso es muy bueno, debes mantener ese buen estado de ánimo.  
                            ¿Cuentáme en que te puedo ayudar?'''
    elif emotion ==  'sad':
        mensajeInicial = f'''¿Esa tristeza a que se debe?, cuéntame lo que te pasa para poder ayudarte, {user}.  
                            ¿Cuentáme en que te puedo ayudar?.¿Talvez te cuento un chiste para que te alegres un poco, o un cuento corto?'''
    elif emotion == 'neutral':
        mensajeInicial = f'''Hola {user}. ¿En qué te puedo ayudar hoy?.  '''
    
    return mensajeInicial

if __name__ == '__main__':
    # Detecta si está en el entorno de desarrollo
    if os.getenv("FLASK_ENV") == "development":
        socketio.run(app, debug=True)  # Ejecuta con el servidor de desarrollo en local
    else:
        # En producción, `gunicorn` manejará la ejecución de la aplicación,
        # así que no es necesario ejecutar `socketio.run()` aquí.
        pass
