const video = document.getElementById('inputVideo');
const canvas = document.getElementById('overlay');
const emocionDetectada = document.getElementById('emotionText');
const emotionMessage = document.getElementById('emotionMessage');
const question = document.getElementById('question');
const emotionInputHidden = document.getElementById('emotionInputHidden');

const stopButton = document.getElementById('stopButton');
const repetirButton = document.getElementById('repetir');
let resultado = null

/* (async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    video.play()
})(); */

async function startCamera() {
    const emotionMessage = document.getElementById('emotionMessage');
    emotionMessage.style.display='none'
    stopButton.style.opacity=1;
    question.style.display='none'
    canvas.style.display = 'block'
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
        
        // Habilitar el botón "Detener captura" y deshabilitar "Repetir"
        stopButton.disabled = false;
        repetirButton.disabled = true;
        repetirButton.style.opacity=.5;
    } catch (error) {
        console.error("Error al iniciar la cámara:", error);
    }
}

// Inicia la cámara al cargar el script
startCamera();

// Función para detener la cámara
function stopCapture() {
    stopButton.disabled = true;
    repetirButton.style.opacity=1;
    stopButton.style.opacity=.5;
    repetirButton.disabled = false;
    // Apagar la cámara
    if (video.srcObject) {
        let stream = video.srcObject;
        let tracks = stream.getTracks();

        // Detener todos los tracks de video
        tracks.forEach(track => track.stop());
        video.srcObject = null;  // Quitar el stream del elemento de video
        canvas.style.display = 'none'
        console.log(resultado)
        console.log(resultado[0])
        console.log(resultado[0].expressions)
        expressions = resultado[0].expressions
        emocion = getDominantEmotion(expressions)
        console.log('expresions: ',emocion.maxEmotion)
        if(emocion.maxEmotion == '' || emocion.maxEmotion ==null ){
             emocionDetectada.textContent = 'No pude reconocer tu emoción :c'
        } else  if (emocion.maxEmotion == 'neutral'){
            emotionInputHidden.value = emocion.maxEmotion
            emocionDetectada.textContent = 'Tu rostro demuestra una estado neutral, no se distingue una emoción.'
        }else{
            emocionDetectada.textContent = 'Puedo ver que estas '+emocion.maxEmotion 
            emotionInputHidden.value = emocion.maxEmotion
            question.textContent = '¿Te parece si me cuentas un poco ...?'

        }
        emotionMessage.style.display='block'
        question.style.display='block'
    }

    // Deshabilitar el botón "Detener captura" y habilitar "Repetir"
    
}


function getDominantEmotion(expressions) {
    let maxEmotion = null;
    let maxValue = -Infinity;

    for (const [emotion, value] of Object.entries(expressions)) {
        if (value > maxValue) {
            maxEmotion = emotion;
            maxValue = value;
        }
    }

    return { maxEmotion, maxValue };
}


// Función para reiniciar la cámara
function repetir() {
    // Volver a encender la cámara
    startCamera();
}



async function onPlay() {
    await faceapi.loadSsdMobilenetv1Model(MODEL_URL)
    await faceapi.loadFaceLandmarkModel(MODEL_URL)
    await faceapi.loadFaceRecognitionModel(MODEL_URL)
    await faceapi.loadFaceExpressionModel(MODEL_URL)

    let fullFaceDescriptions = await faceapi.detectAllFaces(video)
        .withFaceLandmarks()
        .withFaceDescriptors()
        .withFaceExpressions();

    const dims = faceapi.matchDimensions(canvas, video, true);
    console.log(dims)
    const resizedResults = faceapi.resizeResults(fullFaceDescriptions, dims);
    resultado = resizedResults
    faceapi.draw.drawDetections(canvas, resizedResults);
    faceapi.draw.drawFaceLandmarks(canvas, resizedResults);
    faceapi.draw.drawFaceExpressions(canvas, resizedResults, 0.05);

    setTimeout(() => onPlay(), 100) 
}

  // Función que envía la emoción detectada al endpoint
async  function sendEmotion() {
    // Obtiene el valor de la emoción desde el elemento con id "emotionValue"
    const emotion = document.getElementById("emotionInputHidden").value;

    // Configura los datos para enviar al endpoint
    const data = { emotion: emotion };

    // Realiza la solicitud POST al endpoint deseado
    fetch('/sendEmotion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            console.error('Error al enviar la emoción');
        }
    })
    .catch(error => console.error('Error en la solicitud:', error));
}

