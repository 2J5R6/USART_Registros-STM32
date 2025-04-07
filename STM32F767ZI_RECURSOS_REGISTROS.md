# Guía de Recursos para Programación a Nivel de Registros en STM32F767ZI

## Documentos de Referencia Esenciales

| Documento | Descripción | Enlace |
|-----------|-------------|--------|
| **Reference Manual (RM0410)** | Documentación detallada de todos los periféricos y sus registros | [ST - RM0410](https://www.st.com/resource/en/reference_manual/dm00224583-stm32f76xxx-and-stm32f77xxx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf) |
| **Programming Manual (PM0253)** | Información sobre el núcleo Cortex-M7, instrucciones y registros de bajo nivel | [ST - PM0253](https://www.st.com/resource/en/programming_manual/dm00237416-stm32f7-series-and-stm32h7-series-cortexm7-processor-programming-manual-stmicroelectronics.pdf) |
| **Datasheet STM32F767ZI** | Características eléctricas, pinout, mapas de memoria | [ST - Datasheet](https://www.st.com/resource/en/datasheet/stm32f767zi.pdf) |

## Instrucciones Especiales del Procesador

### Instrucciones de Bajo Consumo

El STM32F767ZI basado en Cortex-M7 soporta varias instrucciones para gestión de energía:

| Función | Descripción | Comportamiento |
|---------|-------------|----------------|
| `__WFI()` | Wait For Interrupt | Pone el procesador en modo de bajo consumo hasta que ocurra una interrupción habilitada |
| `__WFE()` | Wait For Event | Pone el procesador en modo de bajo consumo hasta un evento o interrupción |
| `__SEV()` | Send Event | Genera un evento para despertar otros procesadores |
| `__ISB()` | Instruction Synchronization Barrier | Vacía el pipeline de instrucciones |
| `__DSB()` | Data Synchronization Barrier | Garantiza que todas las operaciones de memoria se completen |
| `__DMB()` | Data Memory Barrier | Garantiza el orden de las operaciones de acceso a memoria |

## Registros Clave por Periférico

### Registros GPIO

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `GPIOx->MODER` | Modo de los pines (entrada/salida/alternativo/analógico) | 00: Entrada, 01: Salida, 10: Función alternativa, 11: Analógico |
| `GPIOx->OTYPER` | Tipo de salida | 0: Push-pull, 1: Open-drain |
| `GPIOx->OSPEEDR` | Velocidad de los pines | 00: Baja, 01: Media, 10: Alta, 11: Muy alta |
| `GPIOx->PUPDR` | Pull-up/Pull-down | 00: Ninguna, 01: Pull-up, 10: Pull-down |
| `GPIOx->IDR` | Registro de entrada | Lectura del estado de los pines |
| `GPIOx->ODR` | Registro de salida | Escritura para establecer estados de salida |
| `GPIOx->BSRR` | Bit set/reset register | Bits 0-15: Set, Bits 16-31: Reset |
| `GPIOx->AFR[0]` | Función alternativa (pines 0-7) | 4 bits por pin |
| `GPIOx->AFR[1]` | Función alternativa (pines 8-15) | 4 bits por pin |

### Registros USART

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `USARTx->CR1` | Control register 1 | Bit 0: UE (Enable), Bits 2-3: RE/TE (Rx/Tx enable), Bit 5: RXNEIE (interrupción Rx) |
| `USARTx->CR2` | Control register 2 | Bits 12-13: STOP (bits de parada) |
| `USARTx->BRR` | Baud rate register | BRR = fck/(8*(2-OVER8)*baudrate) |
| `USARTx->ISR` | Interrupt & status register | Bit 5: RXNE, Bit 6: TC, Bit 7: TXE |
| `USARTx->RDR` | Receive data register | Datos recibidos (8 o 9 bits) |
| `USARTx->TDR` | Transmit data register | Datos a enviar (8 o 9 bits) |

### Registros Timer

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `TIMx->CR1` | Control register 1 | Bit 0: CEN (enable), Bit 1: UDIS, Bit 4: DIR (dirección) |
| `TIMx->PSC` | Prescaler | Valor de división de frecuencia |
| `TIMx->ARR` | Auto-reload register | Valor de recarga para conteo |
| `TIMx->CNT` | Counter | Valor actual del contador |
| `TIMx->CCRx` | Capture/Compare | Valor de comparación para PWM o captura |
| `TIMx->DIER` | DMA/Interrupt enable | Bit 0: UIE (update interrupt) |
| `TIMx->SR` | Status register | Bit 0: UIF (update flag) |

### Registros ADC

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `ADCx->CR1` | Control register 1 | Bits 24-25: RES (resolución), Bit 5: EOCIE (interrupción) |
| `ADCx->CR2` | Control register 2 | Bit 0: ADON (enable), Bit 30: SWSTART (inicio manual) |
| `ADCx->SMPR1/2` | Sample time registers | 3 bits por canal |
| `ADCx->SQR1/2/3` | Sequence registers | Configuración de la secuencia de conversión |
| `ADCx->DR` | Data register | Resultado de la conversión (12 bits alineados a la derecha) |

### Registros RCC (Reset and Clock Control)

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `RCC->CR` | Clock control register | Bits 0, 16, 24: HSI/HSE/PLL enable |
| `RCC->PLLCFGR` | PLL configuration | Configuración del PLL |
| `RCC->CFGR` | Clock configuration | Selección de fuente de reloj del sistema |
| `RCC->AHB1ENR` | AHB1 peripheral clock enable | Habilita relojes para periféricos (GPIOs, DMA, etc.) |
| `RCC->APB1ENR` | APB1 peripheral clock enable | Habilita relojes para periféricos en APB1 |
| `RCC->APB2ENR` | APB2 peripheral clock enable | Habilita relojes para periféricos en APB2 |

### Registros EXTI (Interrupciones Externas)

| Registro | Descripción | Bits Importantes |
|----------|-------------|------------------|
| `EXTI->IMR` | Interrupt mask register | Habilita líneas de interrupción |
| `EXTI->RTSR` | Rising edge trigger | Habilita disparo por flanco de subida |
| `EXTI->FTSR` | Falling edge trigger | Habilita disparo por flanco de bajada |
| `EXTI->PR` | Pending register | Indica interrupciones pendientes |

## Instrucciones para Encontrar Información Específica

1. **Buscar registros de un periférico**:
   * Abre el manual de referencia RM0410
   * Localiza en el índice el capítulo correspondiente al periférico (ej. "USART")
   * Busca la sección de registros, generalmente titulada "[periférico] registers"

2. **Comprender una función específica**:
   * Identifica los registros y bits involucrados en el manual
   * Examina ejemplos en "code snippets" o aplicaciones de ejemplo oficiales

3. **Depurar problemas**:
   * Verifica los registros de estado del periférico (xxxSR o xxxISR)
   * Comprueba que has habilitado el reloj del periférico en los registros RCC
   * Confirma que la configuración de pines es correcta para la función deseada

## Consejos para Programación a Nivel de Registros

1. **Siempre habilita primero el reloj del periférico**
   ```c
   RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN; // Habilita reloj para GPIOB
   ```

2. **Usa operaciones AND y OR para modificar bits específicos sin afectar otros**
   ```c
   // Para modificar bits específicos sin afectar otros:
   registro &= ~(máscara);  // Limpiar bits
   registro |= valor;       // Establecer bits
   ```

3. **Utiliza definiciones de bits en lugar de valores "mágicos"**
   ```c
   // Mejor esto:
   USART3->CR1 |= USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;
   
   // En lugar de esto:
   USART3->CR1 |= (1<<0) | (1<<3) | (1<<2);
   ```

4. **Recuerda limpiar flags de interrupción después de atenderlas**
   ```c
   // Ejemplo para EXTI:
   if(EXTI->PR & EXTI_PR_PR13) {
       EXTI->PR |= EXTI_PR_PR13;  // Limpiar flag
       // Manejar la interrupción...
   }
   ```
