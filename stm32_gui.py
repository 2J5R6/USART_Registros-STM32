import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QComboBox, QTextEdit, 
                           QLabel, QGroupBox, QFrame, QScrollArea, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
        self.setWindowTitle("UART LED PYTHON GUI CONTROL")
        self.setWindowIcon(QIcon("Utils/icon.png"))
        self.setMinimumSize(1000, 700)
        self.serial_port = None
        self.serial_thread = None
        self.setup_styles()
        self.initUI()

    def setup_styles(self):
        # Set dark theme colors
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #1a1a2e);
            }
            QGroupBox {
                background-color: rgba(0, 0, 0, 40%);
                border:  solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                color: #e2e2e2;
                font-weight: bold;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                transform: scale(1.05);
            }
            QTextEdit {
                background-color: rgba(0, 0, 0, 60%);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: #4cc9f0;
                font-family: 'Consolas';
                border-radius: 4px;
            }
            QComboBox {
                padding: 5px;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QLabel {
                color: #e2e2e2;
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
            background: rgba(0, 0, 0, 0.5);
            padding: 15px;
            border-radius: 10px;
            color: white;
            font-size: 24px;
            font-weight: bold;
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
        self.status_indicator.setStyleSheet("color: #d90429; font-size: 20px;")
        self.status_label = QLabel("Disconnected")
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        
        conn_controls = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4361ee;")
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
        for color, style in [("Red", "#d90429"), ("Blue", "#4361ee"), ("Green", "#2a9d8f")]:
            layout = QHBoxLayout()
            on_btn = QPushButton(f"{color} ON")
            off_btn = QPushButton(f"{color} OFF")
            
            on_btn.setStyleSheet(f"background-color: {style}; color: white;")
            off_btn.setStyleSheet(f"background-color: transparent; color: {style}; border: 2px solid {style}")
            
            layout.addWidget(on_btn)
            layout.addWidget(off_btn)
            led_layout.addLayout(layout)

        # Add All LEDs controls
        all_layout = QHBoxLayout()
        all_on = QPushButton("All ON")
        all_off = QPushButton("All OFF")
        all_on.setStyleSheet("background-color: #7209b7; color: white;")
        all_off.setStyleSheet("background-color: transparent; color: #7209b7; border: 2px solid #7209b7")
        all_layout.addWidget(all_on)
        all_layout.addWidget(all_off)
        led_layout.addLayout(all_layout)
        
        led_group.setLayout(led_layout)
        left_panel.addWidget(led_group)

        # Mode Control with Roman numerals
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout()
        
        mode_labels = ["O", "I", "II", "III", "IV"]
        mode_colors = ["#6c757d", "#dc3545", "#0d6efd", "#198754", "#ffc107"]
        
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
        send_button.setStyleSheet("background-color: #4cc9f0;")
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
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        content.addWidget(console_group, stretch=1)

        # Add content to main layout
        main_layout.addLayout(content)

        # Add LED visualization
        visual_group = QGroupBox("LED Visualization")
        visual_layout = QHBoxLayout()
        
        for color in ["Red", "Blue", "Green"]:
            led_widget = QFrame()
            led_widget.setFixedSize(50, 50)
            led_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: #333;
                    border: 2px solid {color.lower()};
                    border-radius: 25px;
                }}
            """)
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
                self.status_indicator.setStyleSheet("color: #2a9d8f; font-size: 20px;")
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
            self.status_indicator.setStyleSheet("color: #d90429; font-size: 20px;")
            self.status_label.setText("Disconnected")
            self.console.append("Disconnected")

    def send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(command.encode('ascii'))
                self.console.append(f"Sent: {command}")
            except Exception as e:
                self.console.append(f"Error sending: {str(e)}")
        else:
            self.console.append("Not connected to any port")

    def handle_received_data(self, data):
        self.console.append(f"Received: {data}")

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
