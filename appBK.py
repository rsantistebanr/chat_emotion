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

from flask_pymongo import PyMongo
from flask import session, redirect, url_for
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)



# Configurar la aplicación Flask y MongoDB
#app.config["MONGO_URI"] =  os.getenv("MONGO_URI")     # Cambia esto a la URI de tu MongoDB
app.config["MONGO_URI"] = "mongodb+srv://bd_admin:F.vkaz.4Vm3Z.P5@cluster0.nhzv0.mongodb.net/usuariosChat?retryWrites=true&w=majority&appName=Cluster0"     # Cambia esto a la URI de tu MongoDB
mongo = PyMongo(app)

# Configurar la API de OpenAI
#openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat')
def index():
    return render_template('chat.html')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login',  methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/emotion')
def emotion():
    return render_template('emotion.html')

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
        print(f"Transcripción: {transcript}")
        return jsonify({'transcript': transcript})
    except Exception as e:
        print(f"Error al procesar el archivo de audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_db')
def test_db():
    try:
        result = mongo.db.users.find_one({"users":"oso2001"})  # Realizar una consulta básica para probar la conexión
        print("mongo db: ",result)
        return "Conexión a MongoDB exitosa!"
    except Exception as e:
        return f"Error en la conexión a MongoDB: {e}"
    
    
################################################################
#FUNCIONES:
################################################################
@socketio.on('message')
def handle_message(data):
    user_message = data['message']
    
    # Llamar a la API de OpenAI para obtener la respuesta del modelo
    #response = openai.Completion.create(    #    engine="text-davinci-003",    #    prompt=user_message,    #    max_tokens=150    #)

    #traducimos
    adicionales = ["Maximo 200 palabras", "Soy un joven de 20 años, en base a eso da tu repuesta."]

    #2. CONVIERTO A INGLES
    promt = traducir("en", "es",user_message , adicionales)

    bot_reply = procesamientoNPL(promt)
    respuestaEspañol = traducir_español(bot_reply)
    #bot_reply = "MENSAJE DEL CHAT" #response['choices'][0]['text'].strip()

    # Convertir la respuesta del bot en audio usando gTTS
    tts = gTTS(text=bot_reply, lang='es')
    audio_filename = f"static/audio/response_{user_message[:10]}.mp3"
    tts.save(audio_filename)
    
    # Enviar la respuesta y la URL del archivo de audio
    emit('bot_response', {'response': respuestaEspañol, 'audio_url': audio_filename})

def procesamientoNPL(promt):
    #PROCESAMIENTO NL (PNL)
    client = InferenceClient(api_key="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")
    respuestaModelo = ''
    for message in client.chat_completion(
        model="mistralai/Mistral-Nemo-Instruct-2407",
        messages=[{"role": "user", "content": promt}],
        max_tokens=500,
        stream=True,
    ):
        respuestaModelo += message.choices[0].delta.content
        #print(message.choices[0].delta.content, end="")
    return respuestaModelo

def traducir(lang_after , lang_before, texto,adicionales):
    # Crear un traductor del español o quechua al inglés
    translator = Translator(from_lang=lang_after, to_lang=lang_before)
    # Texto que el usuario ingresa en español o quechua
    texto_usuario = texto
    promt = texto_usuario + " " + adicionales[0] + ". "+ adicionales[1]
    # Traducir el texto al inglés
    traduccion = translator.translate(promt)
    return traduccion

def traducir_español(textoENG):
    translator = Translator(from_lang="en", to_lang="es")
    # Dividir el texto en fragmentos de 490 caracteres o menos
    texto_usuario = textoENG 
    fragmentos = dividir_texto_por_caracteres(texto_usuario,  max_caracteres=490)
    print('cantidad de partes: ', len(fragmentos))
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
    print(f"Archivo convertido guardado como: {output_file}")


if __name__ == '__main__':
    socketio.run(app, debug=True)
