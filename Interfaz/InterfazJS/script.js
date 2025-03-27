/**
 * Script para Control de LEDs RGB STM32F767
 * 
 * Este script maneja la comunicación Web Serial con un microcontrolador STM32F767
 * para controlar LEDs RGB y monitorear cambios de estado de un pulsador.
 * 
 * @author Julian Rosas
 * @date Marzo 2025
 */

// Variables para comunicación Serial
let port;
let reader;
let inputDone;
let outputDone;
let outputStream;
let isConnected = false;
let messageCount = 0;
let connectionAttempts = 0;
let autoReconnect = false;

// Buffer para datos recibidos hasta detectar un \r
let receiveBuffer = ""; 

// Estado de los LEDs
let ledState = {
  red: false,
  green: false,
  blue: false
};

// Estado actual del sistema
let currentMode = 4; // Iniciamos en modo 4 (todos apagados)
let lastButtonState = 0;

// Referencias a elementos del DOM
const connectBtn = document.getElementById("connectBtn");
const sendBtn = document.getElementById("sendBtn");
const charToSend = document.getElementById("charToSend");
const receivedData = document.getElementById("receivedData");
const connectionStatus = document.getElementById("connectionStatus");
const connectionIndicator = document.getElementById("connectionIndicator");
const clearConsoleBtn = document.getElementById("clearConsoleBtn");
const msgCounter = document.getElementById("msgCounter");
const autoScrollToggle = document.getElementById("autoScrollToggle");

// Botones de LEDs
const redOnBtn = document.getElementById("redOnBtn");
const redOffBtn = document.getElementById("redOffBtn");
const greenOnBtn = document.getElementById("greenOnBtn");
const greenOffBtn = document.getElementById("greenOffBtn");
const blueOnBtn = document.getElementById("blueOnBtn");
const blueOffBtn = document.getElementById("blueOffBtn");
const allOnBtn = document.getElementById("allOnBtn");
const allOffBtn = document.getElementById("allOffBtn");

// Visualizaciones de LEDs
const redLedVisual = document.getElementById("redLedVisual");
const greenLedVisual = document.getElementById("greenLedVisual");
const blueLedVisual = document.getElementById("blueLedVisual");

/**
 * Actualiza la visualización de los LEDs en la interfaz
 * basado en el estado guardado en el objeto ledState
 */
function updateLedVisual() {
  // LED Rojo
  redLedVisual.style.backgroundColor = ledState.red ? '#ff0000' : '#333';
  redLedVisual.style.boxShadow = ledState.red ? '0 0 20px #ff0000' : '0 0 10px rgba(0,0,0,0.5)';
  
  // LED Verde
  greenLedVisual.style.backgroundColor = ledState.green ? '#00ff00' : '#333';
  greenLedVisual.style.boxShadow = ledState.green ? '0 0 20px #00ff00' : '0 0 10px rgba(0,0,0,0.5)';
  
  // LED Azul
  blueLedVisual.style.backgroundColor = ledState.blue ? '#0000ff' : '#333';
  blueLedVisual.style.boxShadow = ledState.blue ? '0 0 20px #0000ff' : '0 0 10px rgba(0,0,0,0.5)';
}

/**
 * Actualiza el estado de los LEDs basado en un mensaje recibido
 * @param {string} message - Mensaje recibido del microcontrolador
 */
function updateLedStateFromMessage(message) {
  // Añadida depuración adicional
  console.log("Procesando mensaje para LEDs:", message);
  
  try {
    // Si el mensaje contiene información de modo y LED
    if (message.includes("MODE:") && message.includes("LED:")) {
      // Extraer el modo
      const modeMatch = message.match(/MODE:(\d+)/);
      if (modeMatch && modeMatch[1]) {
        const modeNumber = parseInt(modeMatch[1], 10);
        
        // Extraer información del LED
        const ledInfo = message.split("LED:")[1].trim();
        
        // Resetear todos los estados de LEDs primero
        ledState.red = false;
        ledState.green = false;
        ledState.blue = false;
        
        // Configurar según el modo detectado
        // IMPORTANTE: Estos estados deben coincidir con la configuración física de los LEDs
        switch (ledInfo) {
          case "RED":
            ledState.red = true;
            break;
          case "BLUE":
            ledState.blue = true;
            break;
          case "GREEN":
            ledState.green = true;
            break;
          case "ALL":
            ledState.red = ledState.green = ledState.blue = true;
            break;
          // NONE - todos quedan apagados (ya están apagados por defecto)
        }
        
        // Actualizar la visualización
        updateLedVisual();
        
        // Convertir el número de modo a su representación romana
        let modeRoman = "";
        switch (modeNumber) {
          case 1: modeRoman = "I"; break;    // Modo 1 = I (Rojo)
          case 2: modeRoman = "II"; break;   // Modo 2 = II (Azul)
          case 3: modeRoman = "III"; break;  // Modo 3 = III (Verde)
          case 4: modeRoman = "IV"; break;   // Modo 4 = IV (Todos)
          case 0: modeRoman = "O"; break;    // Modo 0 = O (Ninguno)
          default: modeRoman = modeNumber.toString(); break;
        }
        
        // Actualizamos la variable global del modo actual
        currentMode = modeNumber;
        
        // Actualizar el indicador de modo actual en la interfaz
        const currentModeDisplay = document.getElementById("currentModeDisplay");
        if (currentModeDisplay) {
          currentModeDisplay.textContent = modeRoman;
        }
        
        // Agregar mensaje formateado para el modo
        addToConsole(`Modo ${modeRoman} (${modeNumber}): ${getLedStatusText()}`, "mode");
      }
    }
    // Si el mensaje contiene información sobre el botón
    else if (message.includes("BTN:")) {
      const btnMatch = message.match(/BTN:(\d+)/);
      if (btnMatch && btnMatch[1]) {
        const buttonState = parseInt(btnMatch[1], 10);
        lastButtonState = buttonState;
        addToConsole(`Botón ${buttonState ? 'presionado' : 'liberado'}`, buttonState ? "button-press" : "button-release");
      }
    }
  } catch (error) {
    console.error("Error al procesar mensaje LED:", error);
    addToConsole(`Error al procesar mensaje: ${error.message}`, "error");
  }
}

/**
 * Genera un texto descriptivo del estado de los LEDs
 * @returns {string} Texto que describe qué LEDs están encendidos
 */
function getLedStatusText() {
  const activeLeds = [];
  if (ledState.red) activeLeds.push("Rojo");
  if (ledState.green) activeLeds.push("Verde");
  if (ledState.blue) activeLeds.push("Azul");
  
  if (activeLeds.length === 0) return "Todos los LEDs apagados";
  if (activeLeds.length === 3) return "Todos los LEDs encendidos";
  
  return `LED ${activeLeds.join(" y ")} encendido${activeLeds.length > 1 ? 's' : ''}`;
}

/**
 * Manejador para el botón de conexión/desconexión
 */
connectBtn.addEventListener("click", async () => {
  if (isConnected) {
    await disconnectFromSerial();
  } else {
    await connectToSerial();
  }
});

/**
 * Establece la conexión con el puerto serial
 */
async function connectToSerial() {
  try {
    connectionAttempts++;
    
    // Solicita al navegador que muestre la lista de puertos disponibles
    port = await navigator.serial.requestPort();
    
    // Configura y abre la conexión a 9600 baudios
    await port.open({ baudRate: 9600 });
    
    // Actualiza interfaz y estado
    isConnected = true;
    connectBtn.innerHTML = '<i class="fas fa-unlink me-2"></i>Desconectar';
    connectionStatus.textContent = "Conectado";
    connectionIndicator.classList.add("connected");
    
    // Inicia lecturas
    readLoop();
    
    // Prepara el stream de salida
    const encoder = new TextEncoderStream();
    outputDone = encoder.readable.pipeTo(port.writable);
    outputStream = encoder.writable;
    
    addToConsole(`Conexión establecida a 9600 baudios`, "system");
    connectionAttempts = 0;
  } catch (error) {
    console.error("Error al conectar:", error);
    addToConsole(`Error de conexión: ${error.message}`, "error");
    
    // Si hay más de 3 intentos fallidos, sugerir revisar hardware
    if (connectionAttempts >= 3) {
      addToConsole("Múltiples fallos de conexión. Verifique que el dispositivo esté conectado correctamente.", "error");
    }
  }
}

/**
 * Cierra la conexión con el puerto serial
 */
async function disconnectFromSerial() {
  try {
    // Cierra el lector si existe
    if (reader) {
      await reader.cancel();
      await inputDone.catch(() => {});
      reader.releaseLock();
      reader = null;
    }
    
    // Cierra el escritor si existe
    if (outputStream) {
      await outputStream.getWriter().close();
      await outputDone;
      outputStream = null;
    }
    
    // Cierra el puerto
    if (port) {
      await port.close();
      port = null;
    }
    
    // Actualiza interfaz y estado
    isConnected = false;
    connectBtn.innerHTML = '<i class="fas fa-link me-2"></i>Conectar Puerto Serial';
    connectionStatus.textContent = "Desconectado";
    connectionIndicator.classList.remove("connected");
    addToConsole("Desconectado del puerto serial", "system");
    
  } catch (error) {
    console.error("Error al desconectar:", error);
    addToConsole(`Error al desconectar: ${error.message}`, "error");
  }
}

/**
 * Agrega un mensaje a la consola con formato
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de mensaje (system, error, sent, received, mode)
 */
function addToConsole(message, type = "received") {
  const timestamp = new Date().toLocaleTimeString();
  const entry = document.createElement("div");
  
  // Formato según el tipo de mensaje
  switch (type) {
    case "system":
      entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span><span style="color:#4cc9f0;"><i class="fas fa-info-circle me-1"></i>${message}</span>`;
      break;
    
    case "error":
      entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span><span style="color:#ff5a5f;"><i class="fas fa-exclamation-circle me-1"></i>${message}</span>`;
      break;
    
    case "sent":
      entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span><span style="color:#c1f69a;"><i class="fas fa-paper-plane me-1"></i>Enviado: ${message}</span>`;
      break;
      
    case "mode":
      entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span><span style="color:#ffd166;"><i class="fas fa-sliders-h me-1"></i>${message}</span>`;
      break;
      
    default:
      // Mensajes de botón
      if (message.includes("Botón")) {
        entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span><i class="fas fa-hand-pointer me-1"></i>${message}`;
      }
      // Otros mensajes
      else {
        entry.innerHTML = `<span class="console-timestamp">[${timestamp}]</span>${message}`;
      }
  }
  
  // Agrega la entrada a la consola
  receivedData.appendChild(entry);
  
  // Actualiza contador de mensajes
  messageCount++;
  msgCounter.textContent = `${messageCount} mensajes`;
  
  // Auto-scroll si está activado
  if (autoScrollToggle.checked) {
    receivedData.scrollTop = receivedData.scrollHeight;
  }
}

// Botón para limpiar la consola
clearConsoleBtn.addEventListener("click", () => {
  receivedData.innerHTML = "";
  messageCount = 0;
  msgCounter.textContent = `${messageCount} mensajes`;
  addToConsole("Consola limpiada", "system");
});

/**
 * Envía un carácter al dispositivo
 * Este método ya no se usa directamente - se mantiene por compatibilidad
 * @deprecated Use sendCommand instead
 * @param {string} char - Carácter a enviar 
 */
async function sendCharacter(char) {
  // Redireccionar a sendCommand para asegurar consistencia
  return await sendCommand(char);
}

/**
 * Aplica el modo seleccionado por comando
 * Esta función es fundamental para garantizar la coherencia entre los comandos recibidos
 * y la visualización de LEDs en la interfaz
 * 
 * @param {string} modeCommand - Comando de modo (1, 2, 3, 4, 0) o su equivalente romano (I, II, III, IV, O)
 */
function applyModeFromCommand(modeCommand) {
  // Variables para almacenar el modo y su representación visual
  let newMode = -1;
  let modeDisplay = "";
  
  // MAPEO CORRECTO DE MODOS:
  // 1 o I: Modo 1 - LED Rojo
  // 2 o II: Modo 2 - LED Azul
  // 3 o III: Modo 3 - LED Verde
  // 4 o IV: Modo 4 - Todos los LEDs
  // 0 o O: Modo 0 - Ningún LED

  // Convertimos el comando al número de modo correspondiente
  switch (modeCommand) {
    case "I":
    case "1": 
      newMode = 1; 
      modeDisplay = "I";
      break;
    case "II":
    case "2": 
      newMode = 2; 
      modeDisplay = "II";
      break;
    case "III":
    case "3": 
      newMode = 3; 
      modeDisplay = "III";
      break;
    case "IV":
    case "4": 
      newMode = 4; 
      modeDisplay = "IV";
      break;
    case "O":
    case "0": 
      newMode = 0; 
      modeDisplay = "O";
      break;
  }
  
  // Sólo procedemos si se reconoció un modo válido
  if (newMode >= 0) {
    currentMode = newMode;
    
    // Aplicar el estado de LED correspondiente al modo
    // Resetear primero todos los LEDs (importante para evitar estados incoherentes)
    ledState.red = ledState.blue = ledState.green = false;
    
    // Aplicar según el modo específico
    // IMPORTANTE: Los estados de LEDs deben coincidir con el hardware real
    switch (newMode) {
      case 1: // Modo 1 - LED Rojo
        ledState.red = true;
        break;
      case 2: // Modo 2 - LED Azul
        ledState.blue = true;
        break;
      case 3: // Modo 3 - LED Verde
        ledState.green = true;
        break;
      case 4: // Modo 4 - Todos los LEDs
        ledState.red = ledState.blue = ledState.green = true;
        break;
      case 0: // Modo 0 - Ningún LED
        // Ya están todos apagados por el reset anterior
        break;
    }
    
    // Actualizar visualización en la interfaz
    updateLedVisual();
    
    // Actualizar el indicador de modo actual en la interfaz
    const currentModeDisplay = document.getElementById("currentModeDisplay");
    if (currentModeDisplay) {
      currentModeDisplay.textContent = modeDisplay;
    }
    
    // Mostrar en consola para fines de depuración
    addToConsole(`Modo ${modeDisplay} (${newMode}) activado: ${getLedStatusText()}`, "mode");
    
    return true;
  }
  
  return false;
}

// Evento para enviar carácter personalizado
sendBtn.addEventListener("click", async () => {
  if (!isConnected) {
    addToConsole("Primero debes conectar el puerto serial.", "error");
    return;
  }
  
  const char = charToSend.value;
  if (char.length === 0) {
    addToConsole("Ingresa al menos un carácter", "error");
    return;
  }
  
  // Verificar si es un comando de modo
  const modeCommands = ["I", "II", "III", "IV", "O"];
  if (modeCommands.includes(char)) {
    if (await sendCharacter(char)) {
      applyModeFromCommand(char);
      charToSend.value = '';
      charToSend.focus();
    }
  } else if (await sendCharacter(char)) {
    charToSend.value = ''; // Limpia el input si se envió correctamente
    charToSend.focus();    // Enfoca de nuevo para más entradas
  }
});

// Eventos para los botones de control de LED rojo
redOnBtn.addEventListener("click", async () => {
  if (await sendCharacter('r')) {
    ledState.red = true;
    updateLedVisual();
  }
});

redOffBtn.addEventListener("click", async () => {
  if (await sendCharacter('R')) {
    ledState.red = false;
    updateLedVisual();
  }
});

// Eventos para los botones de control de LED verde
greenOnBtn.addEventListener("click", async () => {
  if (await sendCharacter('g')) {
    ledState.green = true;
    updateLedVisual();
  }
});

greenOffBtn.addEventListener("click", async () => {
  if (await sendCharacter('G')) {
    ledState.green = false;
    updateLedVisual();
  }
});

// Eventos para los botones de control de LED azul
blueOnBtn.addEventListener("click", async () => {
  if (await sendCharacter('b')) {
    ledState.blue = true;
    updateLedVisual();
  }
});

blueOffBtn.addEventListener("click", async () => {
  if (await sendCharacter('B')) {
    ledState.blue = false;
    updateLedVisual();
  }
});

// Eventos para los botones de control de todos los LEDs
allOnBtn.addEventListener("click", async () => {
  if (await sendCharacter('a')) {
    ledState.red = ledState.green = ledState.blue = true;
    updateLedVisual();
  }
});

allOffBtn.addEventListener("click", async () => {
  if (await sendCharacter('A')) {
    ledState.red = ledState.green = ledState.blue = false;
    updateLedVisual();
  }
});

/**
 * Envía carácter o comando de modo al dispositivo
 * @param {string} input - Carácter o comando a enviar
 * @param {boolean} isMultiChar - Indica si es un comando multi-carácter
 */
async function sendCommand(input, isMultiChar = false) {
  if (!isConnected) {
    addToConsole("No hay conexión con el dispositivo", "error");
    return false;
  }
  
  try {
    const writer = outputStream.getWriter();
    
    // MAPEO CORRECTO DE COMANDOS A CARACTERES:
    // Para modos romanos o numéricos, enviamos el carácter correcto
    // Lógica corregida: Envía el carácter exacto según el modo
    let charToSend = input;
    
    if (isMultiChar) {
      switch (input) {
        case 'I':
        case '1':
          charToSend = '1';
          addToConsole('Enviando: "1" (Modo 1 - LED Rojo)', "sent");
          break;
        case 'II':
        case '2':
          charToSend = '2';
          addToConsole('Enviando: "2" (Modo 2 - LED Azul)', "sent");
          break;
        case 'III':
        case '3':
          charToSend = '3';
          addToConsole('Enviando: "3" (Modo 3 - LED Verde)', "sent");
          break;
        case 'IV':
        case '4':
          charToSend = '4';
          addToConsole('Enviando: "4" (Modo 4 - Todos los LEDs)', "sent");
          break;
        case 'O':
        case '0':
          charToSend = '0';
          addToConsole('Enviando: "0" (Modo 0 - Ningún LED)', "sent");
          break;
      }
      await writer.write(charToSend);
    } else {
      // Para caracteres individuales, los enviamos normalmente
      await writer.write(input);
      addToConsole(`Enviando: "${input}"`, "sent");
    }
    
    writer.releaseLock();
    return true;
  } catch (error) {
    console.error("Error al enviar:", error);
    addToConsole(`Error al enviar datos: ${error.message}`, "error");
    return false;
  }
}

// Elimina el viejo manejador de eventos para evitar duplicaciones
const oldSendBtnListener = sendBtn.onclick;
if (oldSendBtnListener) {
  sendBtn.removeEventListener('click', oldSendBtnListener);
}

// Evento para enviar carácter o comando personalizado (único, no duplicado)
sendBtn.addEventListener("click", async () => {
  if (!isConnected) {
    addToConsole("Primero debes conectar el puerto serial.", "error");
    return;
  }
  
  const input = charToSend.value.trim();
  if (input.length === 0) {
    addToConsole("Ingresa al menos un carácter", "error");
    return;
  }
  
  // Verificar si es un comando de modo
  const isMultiChar = ['II', 'III', 'IV'].includes(input);
  
  // Según el tipo de comando, enviamos el carácter correcto
  if (input === 'I') {
    if (await sendCommand('I')) {
      applyModeFromCommand('I');
    }
  } 
  else if (input === 'II' || input === '2') {
    if (await sendCommand('2')) {
      applyModeFromCommand('II');
    }
  }
  else if (input === 'III' || input === '3') {
    if (await sendCommand('3')) {
      applyModeFromCommand('III');
    }
  }
  else if (input === 'IV' || input === '4') {
    if (await sendCommand('4')) {
      applyModeFromCommand('IV');
    }
  }
  else if (input === 'O') {
    if (await sendCommand('O')) {
      applyModeFromCommand('O');
    }
  }
  // Otros comandos (r, R, g, G, b, B, a, A, etc)
  else if (await sendCommand(input)) {
    // Para comandos de control LED, actualizamos la visualización
    switch(input) {
      case 'r': 
        ledState.red = true; 
        updateLedVisual();
        break;
      case 'R': 
        ledState.red = false; 
        updateLedVisual();
        break;
      case 'g': 
        ledState.green = true; 
        updateLedVisual();
        break;
      case 'G': 
        ledState.green = false; 
        updateLedVisual();
        break;
      case 'b': 
        ledState.blue = true; 
        updateLedVisual();
        break;
      case 'B': 
        ledState.blue = false; 
        updateLedVisual();
        break;
      case 'a': 
        ledState.red = ledState.green = ledState.blue = true; 
        updateLedVisual();
        break;
      case 'A': 
        ledState.red = ledState.green = ledState.blue = false; 
        updateLedVisual();
        break;
    }
  }

  // Limpiar el campo y enfocar para nuevos comandos
  charToSend.value = '';
  charToSend.focus();
});

/**
 * Bucle de lectura continua del puerto serial
 * Esta función se encarga de recibir y procesar todos los datos del microcontrolador
 */
async function readLoop() {
  // Configura el decodificador de texto
  const decoder = new TextDecoderStream();
  inputDone = port.readable.pipeTo(decoder.writable);
  reader = decoder.readable.getReader();

  try {
    // Bucle infinito hasta desconexión
    while (true) {
      const { value, done } = await reader.read();
      
      if (done) {
        console.log("[readLoop] finalizado");
        reader.releaseLock();
        break;
      }
      
      if (value) {
        // Añade al buffer existente
        receiveBuffer += value;
        
        // Añadida depuración para ver caracteres recibidos
        console.log("Recibido:", value, "Buffer actual:", receiveBuffer);
        
        // Procesa caracteres especiales directamente sin acumular
        let i = 0;
        while (i < receiveBuffer.length) {
          const char = receiveBuffer[i];
          
          // Detecta estado del botón (P=Pressed/L=Liberado)
          if (char === 'P' || char === 'L') {
            const isPressed = char === 'P';
            addToConsole(`Botón ${isPressed ? 'presionado' : 'liberado'}`, isPressed ? "button-press" : "button-release");
            lastButtonState = isPressed ? 1 : 0;
            
            // Elimina el carácter del buffer
            receiveBuffer = receiveBuffer.substring(0, i) + receiveBuffer.substring(i + 1);
            continue;
          }
          
          // MAPEO CORRECTO DE CARACTERES A MODOS:
          // '1' -> Modo 1 - LED Rojo (I)
          // '2' -> Modo 2 - LED Azul (II)
          // '3' -> Modo 3 - LED Verde (III)
          // '4' -> Modo 4 - Todos los LEDs (IV)
          // '0' -> Modo 0 - Ningún LED (O)
          
          // Procesamos los caracteres de modo según un mapeo consistente
          const modeMapping = {
            '0': { mode: 0, roman: 'O', desc: 'Ningún LED' },
            '1': { mode: 1, roman: 'I', desc: 'Rojo' },
            '2': { mode: 2, roman: 'II', desc: 'Azul' },
            '3': { mode: 3, roman: 'III', desc: 'Verde' },
            '4': { mode: 4, roman: 'IV', desc: 'Todos los LEDs' }
          };
          
          if (modeMapping[char]) {
            const modeInfo = modeMapping[char];
            addToConsole(`Recibido del micro: '${char}' - Modo ${modeInfo.roman} (${modeInfo.mode}) - LED ${modeInfo.desc}`, "received");
            
            // Aplicamos el modo usando el número, que es más fiable
            applyModeFromCommand(modeInfo.mode.toString());
            
            // Elimina el carácter ya procesado del buffer
            receiveBuffer = receiveBuffer.substring(0, i) + receiveBuffer.substring(i + 1);
            continue;
          }
          
          i++;
        }
        
        // Procesa mensajes completos (terminados en \r)
        let carriageReturnIndex = receiveBuffer.indexOf('\r');
        while (carriageReturnIndex !== -1) {
          // Extrae el mensaje completo hasta \r
          let fullMessage = receiveBuffer.slice(0, carriageReturnIndex);
          
          if (fullMessage.trim().length > 0) {
            // Si el mensaje contiene información de modo o botón, lo procesa especialmente
            if (fullMessage.includes("MODE:") || fullMessage.includes("BTN:")) {
              updateLedStateFromMessage(fullMessage);
            } else {
              // Para otros mensajes, simple visualización
              addToConsole(fullMessage, "received");
            }
          }
          
          // Elimina el mensaje procesado del buffer
          receiveBuffer = receiveBuffer.slice(carriageReturnIndex + 1);
          
          // Busca el siguiente \r
          carriageReturnIndex = receiveBuffer.indexOf('\r');
        }
      }
    }
  } catch (error) {
    console.error('Error en readLoop:', error);
    addToConsole(`Error en la comunicación: ${error.message}`, "error");
  }
  
  // Si llegamos aquí, hubo una desconexión o error
  if (isConnected) {
    isConnected = false;
    connectBtn.innerHTML = '<i class="fas fa-link me-2"></i>Conectar Puerto Serial';
    connectionStatus.textContent = "Desconectado";
    connectionIndicator.classList.remove("connected");
    addToConsole("La conexión serial se ha interrumpido", "error");
    
    // Intenta reconectar automáticamente si está habilitada esta opción
    if (autoReconnect) {
      addToConsole("Intentando reconexión automática en 3 segundos...", "system");
      setTimeout(connectToSerial, 3000);
    }
  }
}

// Soporte para enviar caracteres con la tecla Enter
charToSend.addEventListener("keyup", (event) => {
  if (event.key === "Enter") {
    sendBtn.click();
  }
});

// Manejo del cierre del puerto al salir de la página
window.addEventListener("unload", async () => {
  if (isConnected) {
    await disconnectFromSerial();
  }
});

// Agregar mensaje de inicio en la consola
addToConsole("Sistema de control de LEDs RGB iniciado. Conecte un dispositivo.", "system");
addToConsole("Compatible con STM32F767 ejecutando el firmware USART_LED.", "system");

// Actualiza los event listeners de los botones de modo para usar sendCommand con el flag isMultiChar
document.querySelectorAll('.mode-btn').forEach(button => {
  const modeValue = button.textContent.trim();
  const isMultiChar = ['II', 'III', 'IV'].includes(modeValue);
  
  button.onclick = async function() {
    if (isConnected) {
      if (await sendCommand(modeValue, isMultiChar)) {
        applyModeFromCommand(modeValue);
      }
    } else {
      addToConsole("Primero debes conectar el puerto serial.", "error");
    }
  };
});

// Actualiza los event listeners de los botones de modo
document.addEventListener("DOMContentLoaded", function() {
  // Elimina los antiguos event listeners para evitar duplicación
  document.querySelectorAll('.mode-btn').forEach(button => {
    const clonedBtn = button.cloneNode(true);
    button.parentNode.replaceChild(clonedBtn, button);
  });
  
  // Configura los nuevos event listeners con la lógica corregida
  document.querySelectorAll('.mode-btn').forEach(button => {
    const modeValue = button.getAttribute('data-mode');
    
    button.addEventListener('click', async function() {
      if (isConnected) {
        // Mapeamos directamente cada modo a su carácter correspondiente
        let commandToSend = '';
        
        switch(modeValue) {
          case 'I': commandToSend = '1'; break;
          case 'II': commandToSend = '2'; break;
          case 'III': commandToSend = '3'; break;
          case 'IV': commandToSend = '4'; break;
          case 'O': commandToSend = '0'; break;
        }
        
        if (commandToSend) {
          // Enviamos el carácter y aplicamos el modo correspondiente
          if (await sendCommand(commandToSend, true)) {
            applyModeFromCommand(modeValue);
          }
        }
      } else {
        addToConsole("Primero debes conectar el puerto serial.", "error");
      }
    });
  });
  
  // Actualiza los manejadores de eventos para los botones de control específico de LED
  // Estos envían comandos directos para controlar LEDs individuales sin cambiar el modo
  redOnBtn.onclick = async () => {
    if (isConnected && await sendCommand('r')) {
      ledState.red = true;
      updateLedVisual();
    }
  };
  
  redOffBtn.onclick = async () => {
    if (isConnected && await sendCommand('R')) {
      ledState.red = false;
      updateLedVisual();
    }
  };
  
  greenOnBtn.onclick = async () => {
    if (isConnected && await sendCommand('g')) {
      ledState.green = true;
      updateLedVisual();
    }
  };
  
  greenOffBtn.onclick = async () => {
    if (isConnected && await sendCommand('G')) {
      ledState.green = false;
      updateLedVisual();
    }
  };
  
  blueOnBtn.onclick = async () => {
    if (isConnected && await sendCommand('b')) {
      ledState.blue = true;
      updateLedVisual();
    }
  };
  
  blueOffBtn.onclick = async () => {
    if (isConnected && await sendCommand('B')) {
      ledState.blue = false;
      updateLedVisual();
    }
  };
  
  allOnBtn.onclick = async () => {
    if (isConnected && await sendCommand('a')) {
      ledState.red = ledState.green = ledState.blue = true;
      updateLedVisual();
    }
  };
  
  allOffBtn.onclick = async () => {
    if (isConnected && await sendCommand('A')) {
      ledState.red = ledState.green = ledState.blue = false;
      updateLedVisual();
    }
  };
});
