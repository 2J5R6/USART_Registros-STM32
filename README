# Sistema de Control de LEDs mediante UART y Web Serial API

![alt text](/Utils/image.png)
![Objetivos del Proyecto](/Utils/image-1.png)
![Ejemplo de Interfaz](/Utils/EjemploInterfaz.jpg)

## Descripción General

Este proyecto implementa un sistema de control remoto de LEDs RGB utilizando la comunicación serial UART entre un microcontrolador STM32F767 y una aplicación web. El sistema permite controlar LEDs individuales, activar diferentes modos predefinidos y recibir retroalimentación en tiempo real del estado del sistema.

## Estructura del Proyecto

### 1. Back-end: USART_LED.C++

El archivo `USART_LED.C++` contiene el código embebido que se ejecuta en el microcontrolador STM32F767. Este código implementa:

#### Configuración de Registros UART

La implementación utiliza programación a nivel de registro para configurar el periférico USART3:

- **Habilitación de relojes**: Se activa el reloj para GPIOD y USART3 mediante la escritura a los registros `RCC->AHB1ENR` y `RCC->APB1ENR`.
  ```cpp
  RCC->AHB1ENR |= (1<<3);              // Habilita el reloj para GPIOD
  RCC->APB1ENR |= (1<<18);             // Habilita el reloj para USART3 (bit 18)
  ```

- **Configuración de pines**: Los pines PD8 (TX) y PD9 (RX) se configuran como función alternativa 7 (USART3).
  ```cpp
  GPIOD->MODER &= ~((0b11<<18)|(0b11<<16));  // Limpia los bits de MODER para PD9 y PD8
  GPIOD->MODER |= (1<<19)|(1<<17);     // Establece como función alternativa (10)
  GPIOD->AFR[1] &= ~((0b1111<<4)|(0b1111<<0));  // Limpia los bits de función alternativa
  GPIOD->AFR[1] |= (0b111<<4)|(0b111<<0);    // Establece AF7 (0111) para USART3
  ```

- **Configuración de USART3**: Se configura la velocidad (baudrate), formato de datos y se habilitan las interrupciones.
  ```cpp
  USART3->BRR = 0x683;                // Baudrate 9600 para reloj de 16 MHz
  USART3->CR1 |= ((1<<5)|(0b11<<2));  // Habilita interrupción RXNE (bit 5), TX y RX (bits 2-3)
  USART3->CR1 |= (1<<0);              // Habilita USART (bit 0 de CR1)
  ```

#### Gestión de Interrupciones

El código implementa dos manejadores de interrupción principales:

1. **EXTI15_10_IRQHandler**: Gestiona las interrupciones del botón (PC13).
   ```cpp
   void EXTI15_10_IRQHandler(void){
       EXTI->PR |= 1<<13;  // Limpia el flag de interrupción pendiente
       
       // Determina el estado del botón y actualiza el modo
       if(((GPIOC->IDR & (1<<13)) >> 13) == 0){
           button_state = 1;  // Botón presionado
       } else {
           button_state = 0;  // Botón liberado
           
           // Cambio de modo al liberar el botón
           if(prev_button_state == 1) {
               mode = (mode + 1) % 5;
           }
       }
       
       flag = 1;  // Indica que se produjo un cambio
   }
   ```

2. **USART3_IRQHandler**: Gestiona la recepción de datos vía USART.
   ```cpp
   void USART3_IRQHandler(void){
       if(((USART3->ISR & 0x20) >> 5) == 1){  // Verifica si hay datos recibidos (RXNE=1)
           d = USART3->RDR;  // Lee el byte recibido
       }
   }
   ```

#### Transmisión y Recepción UART

El código implementa funciones específicas para la transmisión de datos:

- **USART_SendChar**: Envía un carácter individual, esperando a que el registro de transmisión esté libre.
  ```cpp
  void USART_SendChar(char c) {
      USART3->TDR = c;  // Carga el carácter en el registro de transmisión
      while(((USART3->ISR & 0x80) >> 7) == 0){}  // Espera hasta que TC=1 (transmisión completa)
  }
  ```

- **USART_SendString**: Envía una cadena completa, carácter por carácter, y finaliza con un retorno de carro ('\r').
  ```cpp
  void USART_SendString(char* str) {
      for(i = 0; i < strlen(str); i++) {
          USART_SendChar(str[i]);
      }
      USART_SendChar('\r');  // Termina con retorno de carro
  }
  ```

#### Sistema de Modos

El programa implementa 5 modos de operación para los LEDs:

- **Modo 0**: Todos los LEDs apagados (envía carácter '0')
- **Modo 1**: LED Rojo encendido (envía carácter '1')
- **Modo 2**: LED Azul encendido (envía carácter '2')
- **Modo 3**: LED Verde encendido (envía carácter '3')
- **Modo 4**: Todos los LEDs encendidos (envía carácter '4')

La función `updateLedBasedOnMode()` configura los LEDs según el modo actual y envía notificaciones por UART:

```cpp
void updateLedBasedOnMode() {
    // Apaga todos los LEDs primero
    GPIOB->ODR &= ~((1<<0) | (1<<7) | (1<<14));
    
    // Configura según el modo actual
    switch(mode) {
        case 0: // Modo 0: Ningún LED activo
            USART_SendChar('0');
            USART_SendString("TODOS LOS LEDS DESACTIVADOS (MODO 0)");
            break;
        case 1: // Modo 1: LED Rojo
            GPIOB->ODR |= (1<<14);
            USART_SendChar('1');
            USART_SendString("LED ROJO ACTIVADO (MODO 1)");
            break;
        // ...otros modos...
    }
}
```

#### Control Anti-rebote

El código implementa un sistema de anti-rebote por software para el botón PC13:

```cpp
if(debounce_count == 0) {
    // Procesa el cambio de estado del botón
    // ...acciones...
    
    // Inicia contador de anti-rebote
    debounce_count = 10;  // ~100ms con SysTick_ms(10)
}

// Decrementa el contador de anti-rebote
if(debounce_count > 0) {
    debounce_count--;
}
```

### 2. Front-end: script.js

El archivo `script.js` implementa la interfaz web usando la Web Serial API para comunicarse con el microcontrolador. A continuación se detallan sus componentes principales:

#### Establecimiento de Conexión Serial

La conexión con el dispositivo serial se implementa usando la API Web Serial de JavaScript:

```javascript
async function connectToSerial() {
  try {
    // Solicita al navegador mostrar una lista de puertos disponibles
    port = await navigator.serial.requestPort();
    
    // Configura y abre la conexión a 9600 baudios
    await port.open({ baudRate: 9600 });
    
    // Prepara streams para lectura/escritura
    const encoder = new TextEncoderStream();
    outputDone = encoder.readable.pipeTo(port.writable);
    outputStream = encoder.writable;
    
    // Inicia el bucle de lectura
    readLoop();
  } catch (error) {
    console.error("Error al conectar:", error);
  }
}
```

#### Bucle de Lectura de Datos

La función `readLoop()` implementa un bucle continuo que lee y procesa los datos que llegan del microcontrolador:

```javascript
async function readLoop() {
  const decoder = new TextDecoderStream();
  inputDone = port.readable.pipeTo(decoder.writable);
  reader = decoder.readable.getReader();

  while (true) {
    const { value, done } = await reader.read();
    
    if (done) break;
    
    if (value) {
      // Procesa caracteres especiales de inmediato (P, L, 0-4)
      // Procesa mensajes completos (terminados en \r)
    }
  }
}
```

#### Procesamiento de Comandos

La interfaz permite enviar comandos al microcontrolador para controlar los LEDs:

```javascript
async function sendCommand(input, isMultiChar = false) {
  try {
    const writer = outputStream.getWriter();
    
    // Mapeo lógico de comandos a caracteres simples
    // Envía el comando apropiado según el modo
    
    writer.releaseLock();
    return true;
  } catch (error) {
    console.error("Error al enviar:", error);
    return false;
  }
}
```

#### Sistema de Modos

La interfaz web implementa un sistema de modos que coincide con el del microcontrolador:

```javascript
function applyModeFromCommand(modeCommand) {
  // Mapeo de comandos a modos numéricos
  // Actualiza los LEDs visuales según el modo
  // Muestra información en la consola
}
```

#### Visualización de Estado

La interfaz actualiza visualmente el estado de los LEDs según los comandos enviados o recibidos:

```javascript
function updateLedVisual() {
  // Actualiza el color y brillo de cada LED visual
  redLedVisual.style.backgroundColor = ledState.red ? '#ff0000' : '#333';
  redLedVisual.style.boxShadow = ledState.red ? '0 0 20px #ff0000' : '0 0 10px rgba(0,0,0,0.5)';
  // ...otros LEDs...
}
```

### 3. Front-end: index.html

El archivo `index.html` implementa la interfaz de usuario con Bootstrap y Font Awesome:

- **Panel de conexión**: Permite establecer la conexión serial con el dispositivo.
- **Control de LEDs individuales**: Botones para encender y apagar cada LED.
- **Selección de modos**: Botones para activar diferentes modos predefinidos.
- **Consola de mensajes**: Muestra los mensajes enviados y recibidos.
- **Visualización de LEDs**: Representación visual del estado actual de los LEDs.

## Protocolo de Comunicación

La comunicación entre el microcontrolador y la interfaz web utiliza un protocolo simple basado en caracteres:

1. **Caracteres de control de LEDs**:
   - 'r'/'R': Enciende/apaga el LED Rojo
   - 'g'/'G': Enciende/apaga el LED Verde
   - 'b'/'B': Enciende/apaga el LED Azul
   - 'a'/'A': Enciende/apaga todos los LEDs

2. **Caracteres de modo**:
   - '0': Modo 0 - Todos los LEDs apagados
   - '1': Modo 1 - LED Rojo encendido
   - '2': Modo 2 - LED Azul encendido
   - '3': Modo 3 - LED Verde encendido
   - '4': Modo 4 - Todos los LEDs encendidos

3. **Notificaciones de estado**:
   - 'P': Botón presionado
   - 'L': Botón liberado
   - Mensajes terminados en '\r': Información adicional

## Instrucciones de Uso

1. Cargar el código `USART_LED.C++` en un microcontrolador STM32F767.
2. Abrir el archivo `index.html` en un navegador compatible con Web Serial API (Chrome, Edge).
3. Hacer clic en "Conectar Puerto Serial" y seleccionar el puerto del microcontrolador.
4. Usar los botones de control para manipular los LEDs o cambiar entre modos.
5. Observar los mensajes y cambios de estado en la consola.

## Notas Técnicas

- **Baudrate**: 9600 bps
- **Formato UART**: 8 bits de datos, 1 bit de parada, sin paridad
- **Pines STM32F767**:
  - PD8: USART3 TX
  - PD9: USART3 RX
  - PB0: LED Verde (LD1)
  - PB7: LED Azul (LD2)
  - PB14: LED Rojo (LD3)
  - PC13: Botón de usuario