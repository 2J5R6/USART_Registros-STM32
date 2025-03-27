#include <stdio.h>
#include "stm32f7xx.h"
#include <string.h>

// Variables globales para control de estados
uint8_t flag = 0, i;
uint8_t button_state = 0;  // Variable para seguimiento del estado del botón (0=liberado, 1=presionado)
uint8_t prev_button_state = 0; // Estado anterior del botón para detectar cambios
uint8_t mode = 0;  // Iniciamos en modo 0 (todos apagados) para consistencia
uint8_t button_pressed_once = 0; // Variable para verificar si el botón se presionó al menos una vez
uint8_t debounce_count = 0; // Contador para anti-rebote
unsigned char d;    // Variable para almacenar el carácter recibido por USART
char text[20];      // Buffer para mensajes a enviar por USART

/**
 * @brief Función de espera basada en SysTick con precisión de ciclos
 * @param n Número de ciclos a esperar
 */
void SysTick_Wait(uint32_t n){
    SysTick->LOAD = n - 1;       // Configuramos el valor de recarga (16000 para 1ms @ 16MHz)
    SysTick->VAL = 0;            // Reiniciamos el contador actual
    while (((SysTick->CTRL & 0x00010000) >> 16) == 0); // Esperamos hasta que el flag de conteo se active (bit 16)
}

/**
 * @brief Función de retardo en milisegundos usando SysTick
 * @param x Número de milisegundos a esperar
 */
void SysTick_ms(uint32_t x){
    for (uint32_t i = 0; i < x; i++){  // Repetimos x veces (x ms)
        SysTick_Wait(16000);           // 1ms con reloj de 16MHz
    }
}

extern "C"{
    /**
     * @brief Manejador de interrupción para EXTI líneas 10-15 (incluye botón PC13)
     * 
     * Esta función se ejecuta automáticamente cuando se produce una interrupción
     * en las líneas EXTI 10-15, que incluye el botón conectado a PC13.
     */
    void EXTI15_10_IRQHandler(void){
        EXTI->PR |= 1<<13;  // Limpiamos el bit pendiente para EXTI13
        
        // Guardamos el estado anterior del botón
        prev_button_state = button_state;
        
        // El botón está en PC13, cuando se presiona, su valor es BAJO (0)
        if(((GPIOC->IDR & (1<<13)) >> 13) == 0){ // Verificamos si PC13 está en BAJO (botón presionado)
            button_state = 1;   // Indicamos que el botón está presionado
        } else {
            button_state = 0;   // Indicamos que el botón está liberado
            
            // Solo cambiamos el modo cuando se libera el botón después de haber sido presionado
            if(prev_button_state == 1) {
                // Ciclamos el modo: 0->1->2->3->4->0...
                mode = (mode + 1) % 5;
            }
        }
        
        // Activamos la bandera para procesar en el bucle principal
        flag = 1;
    }

    /**
     * @brief Manejador de interrupción para USART3
     * 
     * Se ejecuta automáticamente cuando se recibe un byte por USART3
     */
    void USART3_IRQHandler(void){
        if(((USART3->ISR & 0x20) >> 5) == 1){  // Verificamos si los datos recibidos están listos para ser leídos (flag RXNE = 1)
            d = USART3->RDR;  // Leemos el buffer de recepción USART
        }
    }
}

/**
 * @brief Envía un carácter a través de USART3
 * @param c Carácter a enviar
 */
void USART_SendChar(char c) {
    USART3->TDR = c;                        // Cargamos el carácter en el registro de transmisión
    while(((USART3->ISR & 0x80) >> 7) == 0){}  // Esperamos hasta que se complete la transmisión (flag TC = 1)
}

/**
 * @brief Envía una cadena de texto a través de USART3
 * @param str Puntero a la cadena de texto a enviar
 */
void USART_SendString(char* str) {
    for(i = 0; i < strlen(str); i++) {  // Recorremos cada carácter de la cadena
        USART_SendChar(str[i]);         // Enviamos el carácter actual
    }
    USART_SendChar('\r');  // Terminamos con retorno de carro para indicar fin de mensaje
}

/**
 * @brief Actualiza los LEDs basado en el modo actual y envía el modo
 * 
 * MODO 0: Ningún LED encendido      -> Envía '0'
 * MODO 1: LED Rojo encendido        -> Envía '1'
 * MODO 2: LED Azul encendido        -> Envía '2'
 * MODO 3: LED Verde encendido       -> Envía '3'
 * MODO 4: Todos los LEDs encendidos -> Envía '4'
 */
void updateLedBasedOnMode() {
    // Primero apagamos todos los LEDs
    GPIOB->ODR &= ~((1<<0) | (1<<7) | (1<<14));
    
    // Enviamos el modo actual para debug
    sprintf(text, "MODE CHANGE: %d", mode);
    USART_SendString(text);
    
    // Configuramos los LEDs según el modo actual
    switch(mode) {
        case 0: // Modo 0: Ningún LED activo
            // Ya están apagados por la línea inicial
            sprintf(text, "MODE:0,LED:NONE");
            USART_SendChar('0');
            USART_SendString("TODOS LOS LEDS DESACTIVADOS (MODO 0)");
            break;
            
        case 1: // Modo 1: LED Rojo encendido (PB14)
            GPIOB->ODR |= (1<<14);
            sprintf(text, "MODE:1,LED:RED");
            USART_SendChar('1');
            USART_SendString("LED ROJO ACTIVADO (MODO 1)");
            break;
            
        case 2: // Modo 2: LED Azul encendido (PB7)
            GPIOB->ODR |= (1<<7);
            sprintf(text, "MODE:2,LED:BLUE");
            USART_SendChar('2');
            USART_SendString("LED AZUL ACTIVADO (MODO 2)");
            break;
            
        case 3: // Modo 3: LED Verde encendido (PB0)
            GPIOB->ODR |= (1<<0);
            sprintf(text, "MODE:3,LED:GREEN");
            USART_SendChar('3');
            USART_SendString("LED VERDE ACTIVADO (MODO 3)");
            break;
            
        case 4: // Modo 4: Todos los LEDs encendidos
            GPIOB->ODR |= ((1<<0) | (1<<7) | (1<<14));
            sprintf(text, "MODE:4,LED:ALL");
            USART_SendChar('4');
            USART_SendString("TODOS LOS LEDS ACTIVADOS (MODO 4)");
            break;
    }
    
    // Notificamos el cambio de modo mediante USART
    USART_SendString(text);
}

int main(){
    //-------------------------------------------------------------------------
    // Configuración de GPIOs
    //-------------------------------------------------------------------------
    RCC->AHB1ENR |= ((1<<1)|(1<<2));  // Habilitamos relojes para GPIOB y GPIOC
    
    // Configuramos los pines de LEDs según la documentación STM32F7:
    // PB0 = LED Verde (LD1), PB7 = LED Azul (LD2), PB14 = LED Rojo (LD3)
    
    // Configuramos los modos de los pines para LEDs
    GPIOB->MODER &= ~((0b11<<0) | (0b11<<14) | (0b11<<28));  // Limpiamos los bits de modo para PB0, PB7, PB14
    GPIOB->MODER |= ((1<<0) | (1<<14) | (1<<28));            // Configuramos PB0, PB7, PB14 como salidas (01)
    
    GPIOC->MODER &= ~(0b11<<26);  // Configuramos PC13 como entrada (00) para el botón
    
    // Configuramos tipo de salida
    GPIOB->OTYPER &= ~((1<<0) | (1<<7) | (1<<14));  // Configuramos salidas como push-pull (0)
    
    // Configuramos velocidad
    GPIOB->OSPEEDR |= ((1<<1) | (1<<0) | (1<<15) | (1<<14) | (1<<29) | (1<<28));  // Alta velocidad para LEDs
    
    // Configuramos resistencias pull-up/down
    GPIOB->PUPDR &= ~((0b11<<0) | (0b11<<14) | (0b11<<28));  // Sin pull-up/down para LEDs
    
    GPIOC->OSPEEDR |= ((1<<27) | (1<<26));  // Alta velocidad para PC13
    GPIOC->PUPDR &= ~(0b11<<26);            // Limpiamos PUPDR para PC13
    GPIOC->PUPDR |= (1<<27);                // Configuramos PC13 con pull-up (10)
    
    // Apagamos todos los LEDs inicialmente
    GPIOB->ODR &= ~((1<<0) | (1<<7) | (1<<14));
    
    //-------------------------------------------------------------------------
    // Configuración del SysTick
    //-------------------------------------------------------------------------
    SysTick->LOAD = 0x00FFFFFF;  // Valor máximo de recarga
    SysTick->CTRL |= (0b101);    // Habilitamos SysTick con reloj del procesador (bits 0 y 2)
    
    //-------------------------------------------------------------------------
    // Configuración de interrupciones EXTI para el botón PC13
    //-------------------------------------------------------------------------
    RCC->APB2ENR |= (1<<14);           // Habilitamos reloj para SYSCFG
    SYSCFG->EXTICR[3] &= ~(0b1111<<4); // Limpiamos los bits de selección de puerto
    SYSCFG->EXTICR[3] |= (1<<5);       // Seleccionamos GPIOC para EXTI13 (0010)
    EXTI->IMR |= (1<<13);              // Habilitamos la interrupción para la línea EXTI13
    EXTI->RTSR |= (1<<13);             // Habilitamos disparo por flanco de subida (liberación del botón)
    EXTI->FTSR |= (1<<13);             // Habilitamos disparo por flanco de bajada (presión del botón)
    NVIC_EnableIRQ(EXTI15_10_IRQn);    // Habilitamos la interrupción EXTI15_10 en el NVIC
    
    //-------------------------------------------------------------------------
    // Configuración USART3 (PD9=RX, PD8=TX)
    //-------------------------------------------------------------------------
    RCC->AHB1ENR |= (1<<3);              // Habilitamos reloj para GPIOD
    GPIOD->MODER &= ~((0b11<<18)|(0b11<<16));  // Limpiamos los bits de modo para PD9 y PD8
    GPIOD->MODER |= (1<<19)|(1<<17);     // Configuramos PD9 y PD8 como función alternativa (10)
    GPIOD->AFR[1] &= ~((0b1111<<4)|(0b1111<<0));  // Limpiamos los bits de función alternativa
    GPIOD->AFR[1] |= (0b111<<4)|(0b111<<0);    // Establecemos USART3 (AF7) como función alternativa
    
    RCC->APB1ENR |= (1<<18);            // Habilitamos reloj para USART3
    USART3->BRR = 0x683;                // Configuramos baudrate a 9600 para reloj de 16 MHz (HSI)
    USART3->CR1 |= ((1<<5)|(0b11<<2));  // Habilitamos interrupción RXNE, transmisor y receptor
    USART3->CR1 |= (1<<0);              // Habilitamos USART
    NVIC_EnableIRQ(USART3_IRQn);        // Habilitamos la interrupción USART3 en el NVIC
    
    // Enviamos mensaje inicial para indicar que el sistema está listo
    USART_SendString("STM32 Ready");
    
    // Iniciamos con todos los LEDs apagados (no aplicamos ningún modo específico aún)
    GPIOB->ODR &= ~((1<<0) | (1<<7) | (1<<14));
    
    // Iniciamos en modo 0 (todos apagados)
    mode = 0;
    updateLedBasedOnMode(); // Enviamos estado inicial
    
    while(1){
        // Verificamos si el estado del botón ha cambiado
        if(flag == 1){
            flag = 0;  // Reiniciamos la bandera
            
            // Implementamos anti-rebote por software
            if(debounce_count == 0) {
                // Enviamos diferentes letras según el estado del botón
                if(button_state == 1){
                    // Cuando el botón está presionado
                    USART_SendChar('P');  // Enviamos 'P' para indicar presionado
                    
                    // Enviamos mensaje de estado del botón
                    sprintf(text, "BTN:%d", button_state);
                    USART_SendString(text);
                    
                    // Iniciamos contador de anti-rebote
                    debounce_count = 10;
                } 
                else {
                    // Cuando el botón está liberado
                    USART_SendChar('L');  // Enviamos 'L' para indicar liberado
                    
                    // Actualizamos los LEDs según el modo actual
                    updateLedBasedOnMode();
                    
                    // Iniciamos contador de anti-rebote
                    debounce_count = 20;
                }
            }
        }
        
        // Decrementar contador de anti-rebote si está activo
        if(debounce_count > 0) {
            debounce_count--;
        }
        
        // Control de LEDs basado en caracteres recibidos por USART:
        // 'r'/'R' controlan el LED ROJO (PB14)
        if(d == 'r'){
            GPIOB->ODR |= (1<<14);  // Encendemos LED ROJO (PB14)
            d = 0;                  // Reiniciamos el carácter recibido
        }
        else if(d == 'R'){
            GPIOB->ODR &= ~(1<<14); // Apagamos LED ROJO
            d = 0;
        }
        
        // 'g'/'G' controlan el LED VERDE (PB0)
        else if(d == 'g'){
            GPIOB->ODR |= (1<<0);   // Encendemos LED VERDE (PB0)
            d = 0;
        }
        else if(d == 'G'){
            GPIOB->ODR &= ~(1<<0);  // Apagamos LED VERDE
            d = 0;
        }
        
        // 'b'/'B' controlan el LED AZUL (PB7)
        else if(d == 'b'){
            GPIOB->ODR |= (1<<7);   // Encendemos LED AZUL (PB7)
            d = 0;
        }
        else if(d == 'B'){
            GPIOB->ODR &= ~(1<<7);  // Apagamos LED AZUL
            d = 0;
        }
        
        // 'a'/'A' controlan todos los LEDs
        else if(d == 'a'){
            GPIOB->ODR |= ((1<<0) | (1<<7) | (1<<14)); // Encendemos todos los LEDs
            d = 0;
        }
        else if(d == 'A'){
            GPIOB->ODR &= ~((1<<0) | (1<<7) | (1<<14)); // Apagamos todos los LEDs
            d = 0;
        }
        
        // Control de modos via comandos recibidos
        if(d == '1') {
            mode = 1;  // Modo 1 - LED Rojo
            updateLedBasedOnMode();
            d = 0;
        }
        else if(d == '2') {
            mode = 2;  // Modo 2 - LED Azul
            updateLedBasedOnMode();
            d = 0;
        }
        else if(d == '3') {
            mode = 3;  // Modo 3 - LED Verde
            updateLedBasedOnMode();
            d = 0;
        }
        else if(d == '4') {
            mode = 4;  // Modo 4 - Todos los LEDs
            updateLedBasedOnMode();
            d = 0;
        }
        else if(d == '0') {
            mode = 0;  // Modo 0 - Ningún LED
            updateLedBasedOnMode();
            d = 0;
        }
        
        // Pequeño retardo para reducir el uso de CPU
        SysTick_ms(10);
    }
}