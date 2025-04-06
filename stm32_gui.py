import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QComboBox, QTextEdit, 
                           QLabel, QGroupBox, QFrame, QScrollArea, QLineEdit,
                           QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPalette, QFont, QIcon, QPixmap

class SerialThread(QThread):
    received = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running:
            if self.serial_port.is_open and self.serial_port.in_waiting:
                data = self.serial_port.read().decode('ascii')
                self.received.emit(data)
            self.msleep(10)

class LedControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USART LED PYTHON GUI CONTROL")
        self.setWindowIcon(QIcon("Utils/icon.png"))
        self.setMinimumSize(1000, 700)
        self.serial_port = None
        self.serial_thread = None
        self.led_widgets = {}  # Diccionario para almacenar referencias a los LED widgets
        self.led_animations = {}  # Para guardar las animaciones
        self.setup_styles()
        self.initUI()

    def setup_styles(self):
        # Set light theme colors
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f5f7;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                color: #333333;
                font-weight: bold;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
                background-color: #007aff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0066d6;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                color: #333333;
                font-family: 'Consolas';
                border-radius: 4px;
            }
            QComboBox {
                padding: 5px;
                border-radius: 4px;
                background: white;
                color: #333333;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
            }
        """)

    def load_and_resize_image(self, path, width=100, height=100):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            # If image not found, create a placeholder
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.lightGray)
        return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Add Pin Information Section
        pin_info_group = QGroupBox("USART Pin Configuration")
        pin_layout = QVBoxLayout()
        
        pin_info = QLabel("""
            USART3 Pin Configuration:
            • TX: PD8 (STM32F767 Pin)
            • RX: PD9 (STM32F767 Pin)
            • Baudrate: 9600
            • Data: 8 bits
            • Stop: 1 bit
            • Parity: None
        """)
        pin_info.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                color: #333333;
                border: 1px solid #e0e0e0;
            }
        """)
        
        pin_layout.addWidget(pin_info)
        pin_info_group.setLayout(pin_layout)
        
        # Add pin info at the top of the interface
        main_layout.addWidget(pin_info_group)

        # Header with logo
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)

        # Logo - Moved to left side
        logo_label = QLabel()
        logo_pixmap = self.load_and_resize_image("Utils/image.png", 200, 200)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setStyleSheet("background: transparent;")

        # Title - Now after logo
        header = QLabel("GRUPO MICROS MEC-C")
        header.setStyleSheet("""
            background: white;
            padding: 15px;
            border-radius: 10px;
            color: #333333;
            font-size: 24px;
            font-weight: bold;
            border: 1px solid #e0e0e0;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Changed order and alignment
        header_layout.addWidget(logo_label, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(header, stretch=4)

        main_layout.addWidget(header_container)

        # Main content container
        content = QHBoxLayout()

        # Left panel - Controls
        left_panel = QVBoxLayout()

        # Connection group with status indicator
        connection_group = QGroupBox("Connection Status")
        conn_layout = QVBoxLayout()

        status_layout = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ff3b30; font-size: 20px;")
        self.status_label = QLabel("Disconnected")
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)

        conn_controls = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #007aff; color: white;")
        self.connect_button.clicked.connect(self.toggle_connection)

        conn_controls.addWidget(self.port_combo)
        conn_controls.addWidget(self.connect_button)

        conn_layout.addLayout(status_layout)
        conn_layout.addLayout(conn_controls)
        connection_group.setLayout(conn_layout)
        left_panel.addWidget(connection_group)

        # LED Controls with improved styling
        led_group = QGroupBox("LED Control")
        led_layout = QVBoxLayout()

        # Create LED controls with better visual style
        led_commands = {
            "Red": ('r', 'R'),
            "Blue": ('b', 'B'),
            "Green": ('g', 'G')
        }

        for color, (on_cmd, off_cmd) in led_commands.items():
            layout = QHBoxLayout()
            style = {"Red": "#ff3b30", "Blue": "#007aff", "Green": "#34c759"}[color]
            
            on_btn = QPushButton(f"{color} ON")
            off_btn = QPushButton(f"{color} OFF")
            
            # Conectar los botones con sus comandos respectivos
            on_btn.clicked.connect(lambda checked, cmd=on_cmd: self.send_command(cmd))
            off_btn.clicked.connect(lambda checked, cmd=off_cmd: self.send_command(cmd))

            on_btn.setStyleSheet(f"background-color: {style}; color: white;")
            off_btn.setStyleSheet(f"background-color: transparent; color: {style}; border: 2px solid {style}")

            layout.addWidget(on_btn)
            layout.addWidget(off_btn)
            led_layout.addLayout(layout)

        # Add All LEDs controls
        all_layout = QHBoxLayout()
        all_on = QPushButton("All ON")
        all_off = QPushButton("All OFF")
        
        # Conectar los botones de todos los LEDs
        all_on.clicked.connect(lambda: self.send_command('a'))
        all_off.clicked.connect(lambda: self.send_command('A'))
        
        all_on.setStyleSheet("background-color: #5856d6; color: white;")
        all_off.setStyleSheet("background-color: transparent; color: #5856d6; border: 2px solid #5856d6")
        all_layout.addWidget(all_on)
        all_layout.addWidget(all_off)
        led_layout.addLayout(all_layout)

        led_group.setLayout(led_layout)
        left_panel.addWidget(led_group)

        # Mode Control with Roman numerals
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout()

        mode_labels = ["O", "I", "II", "III", "IV"]
        mode_colors = ["#6c757d", "#ff3b30", "#007aff", "#34c759", "#ffcc00"]

        for i, (label, color) in enumerate(zip(mode_labels, mode_colors)):
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    min-width: 60px;
                }}
                QPushButton:hover {{
                    background-color: {color}99;
                }}
            """)
            btn.clicked.connect(lambda checked, m=i: self.send_command(str(m)))
            mode_layout.addWidget(btn)

        mode_group.setLayout(mode_layout)
        left_panel.addWidget(mode_group)

        # Add Command Sending Section
        command_group = QGroupBox("Send Command")
        command_layout = QVBoxLayout()

        # Command selector combo box
        self.command_combo = QComboBox()
        self.command_combo.addItem("Select a command...")

        # LED Control Commands
        self.command_combo.addItem("r - Turn Red LED ON")
        self.command_combo.addItem("R - Turn Red LED OFF")
        self.command_combo.addItem("g - Turn Green LED ON")
        self.command_combo.addItem("G - Turn Green LED OFF")
        self.command_combo.addItem("b - Turn Blue LED ON")
        self.command_combo.addItem("B - Turn Blue LED OFF")
        self.command_combo.addItem("a - Turn All LEDs ON")
        self.command_combo.addItem("A - Turn All LEDs OFF")

        # Mode Commands
        self.command_combo.addItem("1 - Mode 1: Red LED")
        self.command_combo.addItem("2 - Mode 2: Blue LED")
        self.command_combo.addItem("3 - Mode 3: Green LED")
        self.command_combo.addItem("4 - Mode 4: All LEDs")
        self.command_combo.addItem("0 - Mode 0: No LEDs")

        # Input layout
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command...")
        send_button = QPushButton("Send")
        send_button.setStyleSheet("background-color: #007aff; color: white;")
        send_button.clicked.connect(self.send_custom_command)

        # Connect combo box to input
        self.command_combo.currentTextChanged.connect(self.update_command_input)

        input_layout.addWidget(self.command_input)
        input_layout.addWidget(send_button)

        command_layout.addWidget(self.command_combo)
        command_layout.addLayout(input_layout)
        command_group.setLayout(command_layout)

        left_panel.addWidget(command_group)

        # Add left panel to content
        content.addLayout(left_panel, stretch=1)

        # Right panel - Console
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #e0e0e0;
                font-family: 'Consolas';
                border-radius: 4px;
            }
        """)
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        content.addWidget(console_group, stretch=1)

        # Add content to main layout
        main_layout.addLayout(content)

        # Add LED visualization
        visual_group = QGroupBox("LED Visualization")
        visual_layout = QHBoxLayout()

        led_colors = {
            "Red": "#ff3b30",
            "Blue": "#007aff",
            "Green": "#34c759"
        }

        for color, style in led_colors.items():
            led_widget = QFrame()
            led_widget.setFixedSize(50, 50)
            led_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {style};
                    border-radius: 25px;
                }}
            """)
            self.led_widgets[color.lower()] = led_widget  # Guardar referencia
            visual_layout.addWidget(led_widget)

        visual_group.setLayout(visual_layout)
        main_layout.addWidget(visual_group)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def toggle_connection(self):
        if self.serial_port is None or not self.serial_port.is_open:
            try:
                port = self.port_combo.currentText()
                self.serial_port = serial.Serial(port, 9600, timeout=1)
                self.serial_thread = SerialThread(self.serial_port)
                self.serial_thread.received.connect(self.handle_received_data)
                self.serial_thread.start()
                self.connect_button.setText("Disconnect")
                self.status_indicator.setStyleSheet("color: #34c759; font-size: 20px;")
                self.status_label.setText("Connected")
                self.console.append("Connected to " + port)
            except Exception as e:
                self.console.append(f"Error: {str(e)}")
        else:
            if self.serial_thread:
                self.serial_thread.running = False
                self.serial_thread.wait()
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            self.connect_button.setText("Connect")
            self.status_indicator.setStyleSheet("color: #ff3b30; font-size: 20px;")
            self.status_label.setText("Disconnected")
            self.console.append("Disconnected")

    def send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(command.encode('ascii'))
                self.console.append(f"Sent: {command}")
                # Para comandos de modo, usamos la visualización específica de modo
                if command in ['0', '1', '2', '3', '4']:
                    self.handle_mode_visualization(command)
                else:
                    self.update_led_visual(command)
            except Exception as e:
                self.console.append(f"Error sending: {str(e)}")
        else:
            self.console.append("Not connected to any port")

    def create_glow_effect(self, color):
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(0)
        effect.setColor(QColor(color))
        effect.setOffset(0, 0)
        return effect

    def animate_glow(self, effect, start=0, end=20, duration=1000):
        animation = QPropertyAnimation(effect, b"blurRadius")
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        return animation

    def update_led_visual(self, command):
        """Actualiza la visualización de los LEDs con efecto glow"""
        if command in ['r', 'R', 'g', 'G', 'b', 'B', 'a', 'A']:
            color_map = {
                'r': ('red', True, '#ff3b30'),
                'R': ('red', False, '#ff3b30'),
                'g': ('green', True, '#34c759'),
                'G': ('green', False, '#34c759'),
                'b': ('blue', True, '#007aff'),
                'B': ('blue', False, '#007aff')
            }

            # Manejar comandos individuales
            if command in color_map:
                color, is_on, style_color = color_map[command]
                led_widget = self.led_widgets[color]
                
                # Detener animación existente si hay alguna
                if color in self.led_animations and self.led_animations[color]:
                    self.led_animations[color].stop()

                if is_on:
                    # Crear y aplicar efecto glow
                    glow = self.create_glow_effect(style_color)
                    led_widget.setGraphicsEffect(glow)
                    
                    # Crear y guardar la animación
                    animation = self.animate_glow(glow)
                    animation.setLoopCount(-1)  # Repetir infinitamente
                    self.led_animations[color] = animation
                    animation.start()
                else:
                    # Quitar efecto al apagar
                    led_widget.setGraphicsEffect(None)
                    self.led_animations[color] = None

                # Actualizar color de fondo
                led_widget.setStyleSheet(f"""
                    QFrame {{
                        background-color: {style_color if is_on else 'white'};
                        border: 2px solid {style_color};
                        border-radius: 25px;
                    }}
                """)

            # Manejar comandos "todos"
            elif command in ['a', 'A']:
                for color, led in self.led_widgets.items():
                    style_color = {"red": "#ff3b30", "blue": "#007aff", "green": "#34c759"}[color]
                    
                    if command == 'a':  # Encender todos
                        glow = self.create_glow_effect(style_color)
                        led.setGraphicsEffect(glow)
                        animation = self.animate_glow(glow)
                        animation.setLoopCount(-1)
                        self.led_animations[color] = animation
                        animation.start()
                        led.setStyleSheet(f"""
                            QFrame {{
                                background-color: {style_color};
                                border: 2px solid {style_color};
                                border-radius: 25px;
                            }}
                        """)
                    else:  # Apagar todos
                        if color in self.led_animations and self.led_animations[color]:
                            self.led_animations[color].stop()
                        led.setGraphicsEffect(None)
                        led.setStyleSheet(f"""
                            QFrame {{
                                background-color: white;
                                border: 2px solid {style_color};
                                border-radius: 25px;
                            }}
                        """)

    def handle_received_data(self, data):
        self.console.append(f"Received: {data}")
        
        # Manejar datos recibidos del STM32
        if data in ['0', '1', '2', '3', '4']:  # Modos
            self.handle_mode_visualization(data)
        elif data in ['r', 'R', 'g', 'G', 'b', 'B', 'a', 'A']:  # Comandos LED directos
            self.update_led_visual(data)
        elif data == 'P':  # Botón presionado
            self.console.append("Button Pressed")
            # No necesitamos hacer nada más aquí
        elif data == 'L':  # Botón liberado - aquí es donde el modo cambia
            self.console.append("Button Released")
            # Aquí enviamos un comando para consultar el estado actual
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(b's')  # 's' para solicitar estado
        elif data.startswith("MODE:"):  # Respuesta de estado del modo
            try:
                mode = data.split(":")[1].strip()
                self.handle_mode_visualization(mode)
            except:
                self.console.append("Error parsing mode data")
        elif data.startswith("LED:"):  # Respuesta de estado de LEDs
            try:
                led_state = data.split(":")[1].strip()
                if led_state == "RED":
                    self.update_led_visual('r')
                elif led_state == "BLUE":
                    self.update_led_visual('b')
                elif led_state == "GREEN":
                    self.update_led_visual('g')
                elif led_state == "ALL":
                    self.update_led_visual('a')
                elif led_state == "NONE":
                    self.update_led_visual('A')
            except:
                self.console.append("Error parsing LED state data")

    def handle_mode_visualization(self, mode):
        """Maneja la visualización de LEDs según el modo recibido"""
        # Primero apagamos todos los LEDs
        self.update_led_visual('A')
        
        # Actualizamos según el modo
        mode_actions = {
            '0': 'A',  # Modo 0: Todos apagados
            '1': 'r',  # Modo 1: LED Rojo
            '2': 'b',  # Modo 2: LED Azul
            '3': 'g',  # Modo 3: LED Verde
            '4': 'a'   # Modo 4: Todos encendidos
        }
        
        if mode in mode_actions:
            self.update_led_visual(mode_actions[mode])

    def update_command_input(self, text):
        if " - " in text:
            command = text.split(" - ")[0].strip()
            self.command_input.setText(command)

    def send_custom_command(self):
        command = self.command_input.text().strip()
        if command:
            self.send_command(command)
            self.command_input.clear()
        else:
            self.console.append("Please enter a command")

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.running = False
            self.serial_thread.wait()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LedControl()
    window.show()
    sys.exit(app.exec())