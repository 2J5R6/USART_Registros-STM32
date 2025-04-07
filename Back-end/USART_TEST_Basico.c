/**
 * USART Test Básico para STM32F767
 * 
 * Este programa proporciona un test simple para verificar:
 * - Comunicación UART
 * - Interrupción del botón PC13
 * - Control básico de LEDs
 *
 * Comunicación directa a través de registros sin funciones intrínsecas.
 */
#include "stm32f7xx.h"
#include <stdio.h>
#include <string.h>

// Variables globales con nombres descriptivos
volatile uint8_t boton_presionado = 0;   // Bandera para indicar que el botón fue presionado
volatile uint8_t contador_antirrebote = 0;   // Contador para anti-rebote del botón
char buffer_tx[100];                   // Buffer para mensajes a transmitir
volatile char caracter_recibido = 0;   // Carácter recibido por UART

/**
 * @brief Inicializa todos los GPIO necesarios usando registros directos
 */
void GPIO_Inicializar(void) {
    // Habilitar relojes para GPIOB (LEDs), GPIOC (botón) y GPIOD (USART3)
    RCC->AHB1ENR |= (1<<1) | (1<<2) | (1<<3);
    
    // ----- Configuración de LEDs en GPIOB (PB0, PB7, PB14) -----
    
    // Limpiar bits de modo para PB0, PB7, PB14
    GPIOB->MODER &= ~((0x3<<0) | (0x3<<14) | (0x3<<28));
    
    // Configurar como salidas (01)
    GPIOB->MODER |= ((0x1<<0) | (0x1<<14) | (0x1<<28));
    
    // Configurar velocidad alta (11)
    GPIOB->OSPEEDR |= ((0x3<<0) | (0x3<<14) | (0x3<<28));
    
    // Configurar como push-pull (0) - default
    GPIOB->OTYPER &= ~((1<<0) | (1<<7) | (1<<14));
    
    // Sin pull-up/pull-down (00)
    GPIOB->PUPDR &= ~((0x3<<0) | (0x3<<14) | (0x3<<28));
    
    // ----- Configuración del botón PC13 -----
    
    // Configurar PC13 como entrada (00) - ya es el valor por defecto
    GPIOC->MODER &= ~(0x3<<26);
    
    // Configurar con pull-down (10)
    GPIOC->PUPDR &= ~(0x3<<26);
    GPIOC->PUPDR |= (0x2<<26);
    
    // ----- Configuración de pines USART3: PD8(TX) y PD9(RX) -----
    
    // Configurar como función alternativa (10)
    GPIOD->MODER &= ~((0x3<<16) | (0x3<<18));
    GPIOD->MODER |= ((0x2<<16) | (0x2<<18));
    
    // Seleccionar AF7 (0111) para USART3
    GPIOD->AFR[1] &= ~((0xF<<0) | (0xF<<4));
    GPIOD->AFR[1] |= ((0x7<<0) | (0x7<<4));
}

/**
 * @brief Inicializa USART3 con baudrate 9600 usando registros directos
 */
void USART3_Inicializar(void) {
    // Habilitar reloj para USART3
    RCC->APB1ENR |= (1<<18);
    
    // Configurar baudrate = 16MHz / 9600 = 1667 (0x683)
    USART3->BRR = 0x683;
    
    // Habilitar USART, transmisor, receptor e interrupción por recepción
    // Bit 0: UE - USART Enable
    // Bit 2: RE - Receiver Enable
    // Bit 3: TE - Transmitter Enable
    // Bit 5: RXNEIE - Interrupt Enable on Receive Data Not Empty
    USART3->CR1 = (1<<0) | (1<<2) | (1<<3) | (1<<5);
    
    // Habilitar interrupción en NVIC
    NVIC_EnableIRQ(USART3_IRQn);
}

/**
 * @brief Inicializa la interrupción externa para el botón PC13
 */
void EXTI_Inicializar(void) {
    // Habilitar reloj para SYSCFG
    RCC->APB2ENR |= (1<<14);
    
    // Conectar PC13 a EXTI13
    SYSCFG->EXTICR[3] &= ~(0xF<<4);  // Limpiar bits para EXTI13
    SYSCFG->EXTICR[3] |= (0x2<<4);   // PC13 -> EXTI13 (2 = Puerto C)
    
    // Configurar disparo por flanco descendente
    EXTI->RTSR &= ~(1<<13);  // Deshabilitar flanco ascendente
    EXTI->FTSR |= (1<<13);   // Habilitar flanco descendente
    
    // Habilitar la interrupción
    EXTI->IMR |= (1<<13);
    
    // Habilitar en NVIC con alta prioridad
    NVIC_EnableIRQ(EXTI15_10_IRQn);
    NVIC_SetPriority(EXTI15_10_IRQn, 0);
}

/**
 * @brief Envía un carácter por USART3 usando registros directos
 * @param c Carácter a enviar
 */
void USART_EnviarCaracter(char c) {
    // Esperar a que el registro de transmisión esté vacío (TXE=1)
    while((USART3->ISR & (1<<7)) == 0);
    
    // Enviar el carácter
    USART3->TDR = c;
}

/**
 * @brief Envía una cadena por USART3
 * @param str Cadena a enviar
 */
void USART_EnviarCadena(const char* str) {
    // Recorrer la cadena hasta el terminador nulo
    while(*str != '\0') {
        USART_EnviarCaracter(*str++);
    }
    
    // Enviar el retorno de carro y nueva línea
    USART_EnviarCaracter('\r');
    USART_EnviarCaracter('\n');
}

/**
 * @brief Retardo simple usando un bucle de ciclos
 * @param ciclos Número de ciclos a retardar
 */
void Retardo(uint32_t ciclos) {
    volatile uint32_t i;
    for(i = 0; i < ciclos; i++) {
        // Este es un bucle vacío que consume ciclos de CPU
        // El calificador volatile evita que el compilador lo optimice
    }
}

/**
 * @brief Apaga todos los LEDs de manera atómica
 */
void LED_ApagarTodos(void) {
    // Usa BSRR para resetear los bits (escribiendo 1 en posición+16)
    GPIOB->BSRR = (1<<(0+16)) | (1<<(7+16)) | (1<<(14+16));
}

/**
 * @brief Enciende el LED especificado
 * @param led 0=Verde(PB0), 1=Azul(PB7), 2=Rojo(PB14), 3=Todos
 */
void LED_Encender(uint8_t led) {
    // Primero apagar todos para partir de un estado conocido
    LED_ApagarTodos();
    
    // Encender según parámetro
    switch(led) {
        case 0:  // Verde - PB0
            GPIOB->BSRR = (1<<0);
            break;
            
        case 1:  // Azul - PB7
            GPIOB->BSRR = (1<<7);
            break;
            
        case 2:  // Rojo - PB14
            GPIOB->BSRR = (1<<14);
            break;
            
        case 3:  // Todos
            GPIOB->BSRR = (1<<0) | (1<<7) | (1<<14);
            break;
            
        default:
            // No hacer nada en caso de valor inválido
            break;
    }
}

/**
 * @brief Hace parpadear un LED específico varias veces
 * @param led LED a parpadear (0=Verde, 1=Azul, 2=Rojo, 3=Todos)
 * @param veces Número de veces a parpadear
 */
void LED_Parpadear(uint8_t led, uint8_t veces) {
    uint8_t i;
    for(i = 0; i < veces; i++) {
        LED_Encender(led);
        Retardo(1000000);
        LED_ApagarTodos();
        Retardo(1000000);
    }
}

/**
 * @brief Procesa un comando recibido
 * @param comando Carácter de comando recibido
 */
void ProcesarComando(char comando) {
    switch(comando) {
        case '0':  // Apagar todos
            LED_ApagarTodos();
            USART_EnviarCadena("Todos los LEDs apagados");
            break;
            
        case '1':  // LED Verde (PB0)
            LED_Encender(0);
            USART_EnviarCadena("LED Verde encendido");
            break;
            
        case '2':  // LED Azul (PB7)
            LED_Encender(1);
            USART_EnviarCadena("LED Azul encendido");
            break;
            
        case '3':  // LED Rojo (PB14)
            LED_Encender(2);
            USART_EnviarCadena("LED Rojo encendido");
            break;
            
        case '4':  // Todos los LEDs
            LED_Encender(3);
            USART_EnviarCadena("Todos los LEDs encendidos");
            break;
            
        case 'b':  // Secuencia de parpadeo
            USART_EnviarCadena("Secuencia de parpadeo");
            LED_Parpadear(0, 2);  // Verde
            LED_Parpadear(1, 2);  // Azul
            LED_Parpadear(2, 2);  // Rojo
            break;
            
        case 'h':  // Comando de ayuda
        case '?':
            USART_EnviarCadena("\r\n--- Comandos disponibles ---");
            USART_EnviarCadena("0: Apagar todos los LEDs");
            USART_EnviarCadena("1: Encender LED Verde");
            USART_EnviarCadena("2: Encender LED Azul");
            USART_EnviarCadena("3: Encender LED Rojo");
            USART_EnviarCadena("4: Encender todos los LEDs");
            USART_EnviarCadena("b: Secuencia de parpadeo");
            USART_EnviarCadena("h o ?: Mostrar esta ayuda");
            break;
            
        default:
            // Eco del carácter recibido
            sprintf(buffer_tx, "Comando recibido: '%c'", comando);
            USART_EnviarCadena(buffer_tx);
            break;
    }
}

// Manejadores de interrupciones - se declaran extern "C" para C++
extern "C" {
    /**
     * @brief Manejador de interrupción para líneas EXTI 10-15 (incluye PC13)
     */
    void EXTI15_10_IRQHandler(void) {
        // Verificar si la interrupción es de EXTI13
        if(EXTI->PR & (1<<13)) {
            // Limpiar el flag pendiente escribiendo 1
            EXTI->PR = (1<<13);
            
            // Verificar si el botón está presionado (nivel alto con pull-down)
            if(GPIOC->IDR & (1<<13)) {
                // Activar bandera de botón presionado
                boton_presionado = 1;
                
                // Notificar por UART
                USART_EnviarCadena("Boton PC13 presionado!");
                
                // Secuencia visual para indicar pulsación
                LED_Encender(3);     // Todos encendidos
                Retardo(500000);
                LED_ApagarTodos();
                
                // Encender LEDs secuencialmente
                uint8_t i;
                for(i = 0; i < 3; i++) {
                    LED_Encender(i);
                    Retardo(300000);
                }
                LED_ApagarTodos();
                
                // Inicializar contador anti-rebote
                contador_antirrebote = 10;
            }
        }
    }
    
    /**
     * @brief Manejador de interrupción para USART3
     */
    void USART3_IRQHandler(void) {
        // Verificar si hay datos recibidos (RXNE=1)
        if(USART3->ISR & (1<<5)) {
            // Leer el dato recibido
            caracter_recibido = (uint8_t)(USART3->RDR);
            
            // Procesar el comando recibido - función ya definida en línea 196
            ProcesarComando(caracter_recibido);
        }
    }
}

/**
 * @brief Punto de entrada principal
 */
int main(void) {
    // Inicializar periféricos
    GPIO_Inicializar();
    USART3_Inicializar();
    EXTI_Inicializar();
    
    // Apagar todos los LEDs al inicio
    LED_ApagarTodos();
    
    // Enviar mensaje de bienvenida después de una pequeña espera
    Retardo(2000000);
    USART_EnviarCadena("");  // Línea en blanco
    USART_EnviarCadena("****************************");
    USART_EnviarCadena("* STM32F767 TEST BÁSICO   *");
    USART_EnviarCadena("* USART + LEDs + Botón    *");
    USART_EnviarCadena("****************************");
    USART_EnviarCadena("");
    USART_EnviarCadena("Presione 'h' o '?' para ayuda");
    USART_EnviarCadena("");
    
    // Secuencia visual de inicio
    LED_Parpadear(0, 1);  // Verde
    LED_Parpadear(1, 1);  // Azul
    LED_Parpadear(2, 1);  // Rojo
    LED_Encender(3);      // Todos encendidos
    Retardo(1000000);
    LED_ApagarTodos();
    
    // Bucle principal
    while(1) {
        // Procesamiento del botón con anti-rebote
        if(boton_presionado && contador_antirrebote == 0) {
            boton_presionado = 0;  // Limpiar bandera
            
            // Acciones adicionales al procesar botón
            USART_EnviarCadena("Acción de botón procesada en bucle principal");
        }
        
        // Decrementar contador de anti-rebote si está activo
        if(contador_antirrebote > 0) {
            contador_antirrebote--;
        }
        
        // Esperar por la siguiente interrupción - instrucción de bajo consumo
        // Esta instrucción pone al procesador en modo sleep hasta que ocurra una interrupción
        asm("wfi");
    }
}
