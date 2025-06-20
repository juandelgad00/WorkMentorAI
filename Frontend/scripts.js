// frontend/scripts.js
const API_URL = "http://localhost:8000";

// Estado global para almacenar datos del usuario
let userProfile = null;
let targetJob = "";
let simulatorHistory = [];
let mentorHistory = [];

// Elementos del DOM
const processBtn = document.getElementById('process-cv-btn');
const cvInput = document.getElementById('cv-upload');
const jobInput = document.getElementById('puesto-deseado');
const loader = document.getElementById('loader');
const resultsDashboard = document.getElementById('results-dashboard');

// --- INICIO DEL FLUJO ---
processBtn.addEventListener('click', handleCvProcessing);

async function handleCvProcessing() {
    // --- LÓGICA DE REINICIO AÑADIDA AL PRINCIPIO ---
    resultsDashboard.classList.add('hidden'); // Oculta el dashboard de resultados anteriores
    simulatorHistory = []; // Reinicia el historial del simulador
    mentorHistory = [];   // Reinicia el historial del mentor
    // Limpiamos los contenedores de resultados por si acaso
    document.getElementById('profile-content').innerHTML = '';
    document.getElementById('formacion-content').innerHTML = '<h3>Plan Formativo</h3><p>Haz clic para generar...</p>';
    document.getElementById('ofertas-content').innerHTML = '<h3>Ofertas Laborales</h3><p>Haz clic para generar...</p>';
    document.getElementById('carta-content').innerHTML = '<h3>Carta de Presentación</h3><p>Haz clic para generar...</p>';
    document.getElementById('simulador-chat-window').innerHTML = '';
    document.getElementById('mentor-chat-window').innerHTML = '';
    // --- FIN DE LA LÓGICA DE REINICIO ---

    const file = cvInput.files[0];
    targetJob = jobInput.value.trim();

    if (!file || !targetJob) {
        alert("Por favor, sube tu CV en PDF y escribe el puesto deseado.");
        return;
    }

    loader.style.display = 'block';
    processBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('puesto_deseado', targetJob);

    try {
        const response = await fetch(`${API_URL}/diagnosticar_cv/`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Error al procesar el CV.");
        }

        userProfile = await response.json();
        if (userProfile.error) {
            alert(`Error del servidor: ${userProfile.error}`);
            throw new Error("Análisis de CV fallido.");
        }
        userProfile.puesto_deseado = targetJob;
        
        displayProfile(userProfile);
        
        // Esta línea ahora mostrará el dashboard con los nuevos resultados
        resultsDashboard.classList.remove('hidden'); 
        activateRecommendationButtons();
        activateChat();

    } catch (error) {
        console.error("Error:", error);
        alert(`${error.message}`);
    } finally {
        loader.style.display = 'none';
        processBtn.disabled = false;
    }
}

function displayProfile(profile) {
    const content = document.getElementById('profile-content');
    
    // Función auxiliar para crear un bloque de experiencia o educación
    const createItemBlock = (item, type) => {
        const title = type === 'exp' ? item.cargo : item.titulo;
        const subtitle = type === 'exp' ? `${item.empresa} (${item.periodo || 'N/A'})` : `${item.institucion} (${item.año || 'N/A'})`;
        const description = item.descripcion || '';

        return `
            <div class="profile-item">
                <h5 class="item-title">${title}</h5>
                <p class="item-subtitle">${subtitle}</p>
                ${description ? `<p class="item-description">${description}</p>` : ''}
            </div>
        `;
    };

    let htmlResult = `
        <h3>${profile.nombre}</h3>
        <p class="contact-info">
            <strong>Email:</strong> ${profile.email} | <strong>Región:</strong> ${profile.region_colombia}
        </p>

        <h4 class="profile-subsection-title">Resumen Profesional Mejorado</h4>
        <div class="profile-summary">
            <p>${profile.resumen_mejorado.replace(/\n/g, '<br>')}</p>
        </div>

        <h4 class="profile-subsection-title">Habilidades Clave</h4>
        <div class="skills-list">
            ${profile.habilidades && profile.habilidades.length > 0 
                ? profile.habilidades.map(skill => `<span class="skill-item">${skill}</span>`).join('') 
                : '<p>No se especificaron habilidades en el CV.</p>'}
        </div>
    `;

    // Sección de Experiencia Laboral
    if (profile.experiencia && profile.experiencia.length > 0) {
        htmlResult += `<h4 class="profile-subsection-title">Experiencia Laboral</h4>`;
        profile.experiencia.forEach(exp => {
            htmlResult += createItemBlock(exp, 'exp');
        });
    }

    // Sección de Educación
    if (profile.educacion && profile.educacion.length > 0) {
        htmlResult += `<h4 class="profile-subsection-title">Educación</h4>`;
        profile.educacion.forEach(edu => {
            htmlResult += createItemBlock(edu, 'edu');
        });
    }

    content.innerHTML = htmlResult;
}

function activateRecommendationButtons() {
    const formacionDiv = document.getElementById('formacion-content');
    const ofertasDiv = document.getElementById('ofertas-content');
    const cartaDiv = document.getElementById('carta-content');

    formacionDiv.style.cursor = 'pointer';
    ofertasDiv.style.cursor = 'pointer';
    cartaDiv.style.cursor = 'pointer';

    formacionDiv.onclick = getTrainingPlan;
    ofertasDiv.onclick = getJobOffers;
    cartaDiv.onclick = getCoverLetter;
}

async function getTrainingPlan() {
    const content = document.getElementById('formacion-content');
    content.innerHTML = '<div class="mini-loader"></div>';
    try {
        const response = await fetch(`${API_URL}/recomendar_formacion/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ perfil: userProfile }),
        });
        const data = await response.json();
        content.innerHTML = `<h3>Plan Formativo</h3><pre>${data.plan_formativo}</pre>`;
    } catch (error) {
        content.innerHTML = '<h3>Plan Formativo</h3><p>Error al generar.</p>';
    }
}

async function getJobOffers() {
    const content = document.getElementById('ofertas-content');
    content.innerHTML = '<div class="mini-loader"></div>';
    try {
        const response = await fetch(`${API_URL}/buscar_ofertas/`, { // <-- Endpoint es el mismo
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            // <-- CAMBIO: Ahora enviamos el perfil Y el puesto deseado -->
            body: JSON.stringify({ perfil: userProfile, puesto_deseado: targetJob }),
        });
        const data = await response.json();
        // <-- CAMBIO: El texto del enlace ahora viene del backend -->
        content.innerHTML = `
            <h3>Ofertas Laborales</h3>
            <a href="${data.linkedin[0].split(': ')[1]}" target="_blank">${data.linkedin[0].split(': ')[0]}</a><br>
            <a href="${data.computrabajo[0].split(': ')[1]}" target="_blank">${data.computrabajo[0].split(': ')[0]}</a>`;
    } catch (error) {
        content.innerHTML = '<h3>Ofertas Laborales</h3><p>Error al generar.</p>';
    }
}

// Pega este código completo en tu archivo scripts.js, reemplazando la función existente.

async function getCoverLetter() {
    const contentDiv = document.getElementById('carta-content');
    contentDiv.innerHTML = '<div class="mini-loader"></div>';
    
    try {
        const response = await fetch(`${API_URL}/generar_carta/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ perfil: userProfile, puesto_deseado: targetJob }),
        });
        const data = await response.json();

        // 1. Verificamos si el backend devolvió un error
        if (data.error) {
            throw new Error(data.error);
        }

        // 2. Desestructuramos la respuesta del backend.
        // Si alguna de estas claves no existe, serán 'undefined'.
        const analisis = data.analisis_idoneidad;
        const cartas = data.cartas_ejemplo;

        // 3. ¡VALIDACIÓN CRUCIAL! Verificamos que los datos necesarios existen
        // antes de intentar usarlos. Esto evita el error "Cannot read properties of undefined".
        if (!analisis || !cartas) {
            throw new Error("La respuesta del servidor no tiene el formato esperado.");
        }

        // Función para crear una barra de calificación visual
        const createRatingBar = (label, score) => {
            const percentage = (score || 0) * 10; // Usar 0 si score es undefined
            return `
                <div class="rating-bar-container">
                    <span class="rating-label">${label}</span>
                    <div class="rating-bar-background">
                        <div class="rating-bar-foreground" style="width: ${percentage}%;">${score || 'N/A'}/10</div>
                    </div>
                </div>
            `;
        };

        // 4. Construimos el nuevo HTML con toda la información del análisis
        let htmlResult = `<h3>Análisis de Idoneidad para '${targetJob}'</h3>`;
        
        htmlResult += createRatingBar('Habilidades', analisis.calificacion_habilidades);
        htmlResult += createRatingBar('Experiencia', analisis.calificacion_experiencia);
        htmlResult += createRatingBar('Estudios', analisis.calificacion_estudios);

        htmlResult += `<h4 class="section-title">Puntos Fuertes</h4>`;
        htmlResult += `<ul class="feedback-list strong">`;
        // Usamos (analisis.puntos_fuertes || []) para evitar error si el array no existe
        (analisis.puntos_fuertes || []).forEach(item => { htmlResult += `<li>${item}</li>`; });
        htmlResult += `</ul>`;

        htmlResult += `<h4 class="section-title">Áreas de Mejora</h4>`;
        htmlResult += `<ul class="feedback-list weak">`;
        (analisis.puntos_debiles || []).forEach(item => { htmlResult += `<li>${item}</li>`; });
        htmlResult += `</ul>`;

        htmlResult += `<h4 class="section-title">Sugerencias Clave</h4>`;
        htmlResult += `<ul class="feedback-list suggestion">`;
        (analisis.sugerencias_mejora || []).forEach(item => { htmlResult += `<li>${item}</li>`; });
        htmlResult += `</ul>`;

        htmlResult += `<h3 style="margin-top: 30px;">Ejemplo de Carta de Presentación</h3>`;
        // Usamos (cartas.carta_es || "No se pudo generar la carta.") para evitar errores
        htmlResult += `<pre class="cover-letter-box">${cartas.carta_es || "No se pudo generar la carta."}</pre>`;
        
        contentDiv.innerHTML = htmlResult;

    } catch (error) {
        console.error("Error en getCoverLetter:", error);
        contentDiv.innerHTML = `<h3>Análisis y Carta</h3><p>Error al generar el contenido: ${error.message}</p>`;
    }
}


function activateChat() {
    document.getElementById('simulador-send-btn').onclick = () => sendMessage('simulador');
    document.getElementById('mentor-send-btn').onclick = () => sendMessage('mentor');
    
    document.getElementById('simulador-input').onkeypress = (e) => { if(e.key === 'Enter') sendMessage('simulador'); };
    document.getElementById('mentor-input').onkeypress = (e) => { if(e.key === 'Enter') sendMessage('mentor'); };
}

async function sendMessage(agentType) {
    const input = document.getElementById(`${agentType}-input`);
    const message = input.value.trim();
    if (!message) return;

    const chatWindow = document.getElementById(`${agentType}-chat-window`);
    const history = agentType === 'simulador' ? simulatorHistory : mentorHistory;

    // 1. Añade el mensaje del usuario a la UI y al estado del historial PRIMERO
    addMessageToChat(chatWindow, message, 'user');
    history.push({ role: 'user', content: message });
    input.value = '';

    try {
        // 2. Envía el historial COMPLETO, que ya incluye el último mensaje del usuario
        const response = await fetch(`${API_URL}/chat/${agentType}/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                perfil: userProfile,
                puesto_deseado: targetJob,
                historial: history, // <--- Se envía el historial ya actualizado
            })
        });
        const data = await response.json();
        const agentResponse = data.respuesta_agente;

        // 3. Añade la respuesta del agente a la UI y al estado del historial
        addMessageToChat(chatWindow, agentResponse, 'bot');
        history.push({ role: 'assistant', content: agentResponse });

    } catch (error) {
        const errorMessage = 'Error de conexión con el agente. Por favor, intenta de nuevo.';
        addMessageToChat(chatWindow, errorMessage, 'bot');
        // Opcional: eliminar el último mensaje del usuario del historial si la llamada falló
        history.pop(); 
    }
}

function addMessageToChat(chatWindow, text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', sender);
    messageDiv.innerText = text;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Lógica de Pestañas (Tabs)
function openTab(evt, tabName) {
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-button");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

async function getJobOffers() {
    const contentDiv = document.getElementById('ofertas-content');
    contentDiv.innerHTML = '<div class="mini-loader"></div>';

    try {
        const response = await fetch(`${API_URL}/buscar_ofertas/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ perfil: userProfile, puesto_deseado: targetJob }),
        });
        const data = await response.json();

        // Creamos el HTML para mostrar las listas de ofertas
        let htmlResult = '<h3>Ofertas Laborales</h3>';

        htmlResult += '<h4>En LinkedIn:</h4>';
        htmlResult += '<ul class="job-list">';
        if (data.linkedin && data.linkedin.length > 0) {
            data.linkedin.forEach(job => {
                htmlResult += `<li><a href="${job.link}" target="_blank">${job.puesto}</a><br><small>${job.empresa}</small></li>`;
            });
        } else {
            htmlResult += '<li>No se encontraron ofertas específicas.</li>';
        }
        htmlResult += '</ul>';

        htmlResult += '<h4>En CompuTrabajo:</h4>';
        htmlResult += '<ul class="job-list">';
        if (data.computrabajo && data.computrabajo.length > 0) {
            data.computrabajo.forEach(job => {
                htmlResult += `<li><a href="${job.link}" target="_blank">${job.puesto}</a><br><small>${job.empresa}</small></li>`;
            });
        } else {
            htmlResult += '<li>No se encontraron ofertas específicas.</li>';
        }
        htmlResult += '</ul>';

        contentDiv.innerHTML = htmlResult;

    } catch (error) {
        console.error("Error fetching job offers:", error);
        contentDiv.innerHTML = '<h3>Ofertas Laborales</h3><p>Error al generar las ofertas.</p>';
    }
}

// En frontend/scripts.js

async function getTrainingPlan() {
    const contentDiv = document.getElementById('formacion-content');
    contentDiv.innerHTML = '<div class="mini-loader"></div>';
    
    try {
        const response = await fetch(`${API_URL}/recomendar_formacion/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ perfil: userProfile, puesto_deseado: targetJob }),
        });
        const data = await response.json();

        if (data.error) {
            contentDiv.innerHTML = `<h3>Plan Formativo</h3><p>${data.error}</p>`;
            return;
        }

        // Función auxiliar para generar un bloque de recomendación
        const createRecommendationBlock = (reco) => {
            let linkHTML = '';
            if (reco.plataforma_sugerida) {
                // Generamos los links en el frontend
                const puestoEncoded = encodeURIComponent(targetJob);
                const links = {
                    youtube: `https://www.youtube.com/results?search_query=curso+de+${puestoEncoded}`,
                    sena: "https://oferta.senasofiaplus.edu.co/sofia-oferta/buscar-oferta-educativa.html",
                    coursera: `https://www.coursera.org/search?query=${puestoEncoded}`,
                    platzi: `https://platzi.com/search/?q=${puestoEncoded}`,
                    edx: `https://www.edx.org/search?q=${puestoEncoded}`,
                    blog: `https://www.google.com/search?q=mejores+blogs+de+${puestoEncoded}`
                };
                const url = links[reco.plataforma_sugerida] || '#';
                linkHTML = `<a href="${url}" target="_blank" class="recommendation-link">Explorar en ${reco.plataforma_sugerida}</a>`;
            }

            return `
                <div class="recommendation-item">
                    <h4>${reco.nombre}</h4>
                    <p>${reco.descripcion}</p>
                    ${linkHTML}
                </div>
            `;
        };
        
        let htmlResult = `<h3>Plan Formativo</h3>`;
        htmlResult += `<p class="intro-text">Para ser un excelente <strong>${targetJob}</strong>, te recomiendo enfocarte en: <strong>${data.habilidades_clave.join(', ')}</strong>.</p>`;

        if (data.opciones_gratuitas && data.opciones_gratuitas.length > 0) {
            htmlResult += `<h4 class="section-title">Opciones Gratuitas</h4>`;
            data.opciones_gratuitas.forEach(reco => {
                htmlResult += createRecommendationBlock(reco);
            });
        }
        
        if (data.opciones_bajo_costo && data.opciones_bajo_costo.length > 0) {
            htmlResult += `<h4 class="section-title">Opciones de Bajo Costo</h4>`;
            data.opciones_bajo_costo.forEach(reco => {
                htmlResult += createRecommendationBlock(reco);
            });
        }

        contentDiv.innerHTML = htmlResult;

    } catch (error) {
        console.error("Error fetching training plan:", error);
        contentDiv.innerHTML = '<h3>Plan Formativo</h3><p>Error al generar el plan.</p>';
    }
}

document.querySelector('.tab-button').click();