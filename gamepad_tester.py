"""
Gamepad Tester Pro v12.0 - Рабочая версия
Автор: Alex Software (mrSaT13)
GitHub: https://github.com/mrSaT13
"""

import sys
import pygame
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QSlider,
    QScrollArea, QTabWidget, QProgressBar, QGroupBox, QComboBox,
    QSystemTrayIcon, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QKeySequence, QShortcut, QAction

try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False


class DS4Controller:
    def __init__(self):
        self.device = None
        self.is_ds4 = False
        self.is_ds5 = False
        self.connection_type = "none"
        
    def connect(self):
        if not HID_AVAILABLE:
            return False
        devices = [(0x054C, 0x09CC, "ds4"), (0x054C, 0x05C4, "ds4"), (0x054C, 0x0BA0, "ds5")]
        for vid, pid, ctrl_type in devices:
            try:
                self.device = hid.device()
                self.device.open(vid, pid)
                self.device.set_nonblocking(True)
                self.is_ds4 = (ctrl_type == "ds4")
                self.is_ds5 = (ctrl_type == "ds5")
                self.connection_type = "usb"
                return True
            except:
                self.device = None
        return False
        
    def disconnect(self):
        if self.device:
            try: self.device.close()
            except: pass
            self.device = None
        self.connection_type = "none"
            
    def get_battery(self):
        if not self.device:
            return None, None
        try:
            if self.connection_type == "bluetooth":
                report = self.device.get_feature_report(0x11, 49)
                if report and len(report) > 53:
                    battery_byte = report[53]
                    level = battery_byte & 0x0F
                    charging = bool(battery_byte & 0x10)
                    levels = [0, 10, 40, 60, 80, 100]
                    return levels[min(level, 5)], charging
            else:
                report = self.device.get_feature_report(0x05, 49)
                if report and len(report) > 42:
                    battery_byte = report[42]
                    level = battery_byte & 0x0F
                    charging = bool(battery_byte & 0x10)
                    levels = [0, 10, 40, 60, 80, 100]
                    return levels[min(level, 5)], charging
        except:
            pass
        return None, None
        
    def read_data(self):
        if not self.device:
            return None
        try:
            data = self.device.read(78 if self.connection_type == "bluetooth" else 64, timeout_ms=5)
            if data and len(data) >= 60:
                return data
        except:
            pass
        return None


class NintendoController:
    def __init__(self):
        self.device = None
        self.controller_type = "none"
        
    def connect(self, pid=None):
        if not HID_AVAILABLE:
            return False
        devices = [(0x057E, 0x2006, "joycon_left"), (0x057E, 0x2007, "joycon_right"), (0x057E, 0x2009, "pro_controller")]
        for vid, dev_pid, ctrl_type in devices:
            if pid and pid != dev_pid:
                continue
            try:
                self.device = hid.device()
                self.device.open(vid, dev_pid)
                self.device.set_nonblocking(True)
                self.controller_type = ctrl_type
                return True
            except:
                self.device = None
        return False
        
    def disconnect(self):
        if self.device:
            try: self.device.close()
            except: pass
            self.device = None
        self.controller_type = "none"
        
    def get_battery(self):
        if not self.device:
            return None, False
        try:
            report = self.device.get_feature_report(0x80, 49)
            if report and len(report) > 5:
                battery_byte = report[5]
                level = battery_byte & 0x0F
                levels = [0, 25, 50, 75, 100]
                return levels[min(level, 4)], False
        except:
            pass
        return None, False
        
    def read_imu(self):
        if not self.device:
            return None
        try:
            data = self.device.read(49, timeout_ms=10)
            if data and len(data) >= 25:
                accel_x = int.from_bytes(data[13:15], 'little', signed=True) / 100.0
                accel_y = int.from_bytes(data[15:17], 'little', signed=True) / 100.0
                accel_z = int.from_bytes(data[17:19], 'little', signed=True) / 100.0
                gyro_x = int.from_bytes(data[19:21], 'little', signed=True) / 100.0
                gyro_y = int.from_bytes(data[21:23], 'little', signed=True) / 100.0
                gyro_z = int.from_bytes(data[23:25], 'little', signed=True) / 100.0
                return {'accel': (accel_x, accel_y, accel_z), 'gyro': (gyro_x, gyro_y, gyro_z)}
        except:
            pass
        return None
        
    def enable_ir_camera(self):
        if not self.device or self.controller_type != "joycon_right":
            return False
        try:
            report = bytes([0x01, 0x31, 0x01, 0x40, 0x01])
            self.device.write(report)
            return True
        except:
            return False
            
    def disable_ir_camera(self):
        if not self.device:
            return False
        try:
            report = bytes([0x01, 0x31, 0x01, 0x40, 0x00])
            self.device.write(report)
            return True
        except:
            return False


def get_all_gamepads():
    gamepads = []
    try:
        if not pygame.get_init():
            pygame.init()
            pygame.joystick.init()
        pygame.event.pump()
        count = pygame.joystick.get_count()
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                if not joy.get_init():
                    joy.init()
                name = joy.get_name()
                buttons = joy.get_numbuttons()
                axes = joy.get_numaxes()
                hats = joy.get_numhats()
                gamepads.append({'index': i, 'name': name, 'buttons': buttons, 'axes': axes, 'hats': hats})
            except Exception as e:
                print(f"Gamepad error: {e}")
    except Exception as e:
        print(f"get_all_gamepads error: {e}")
    return gamepads


class BatteryWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 65)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border-radius: 10px;
                border: 2px solid #3a3a4e;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.icon = QLabel("🔋")
        self.icon.setStyleSheet("QLabel { font-size: 28px; }")
        layout.addWidget(self.icon)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        self.percent_label = QLabel("--%")
        self.percent_label.setStyleSheet("QLabel { color: #00ff88; font-size: 18px; font-weight: bold; }")
        info_layout.addWidget(self.percent_label)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("QLabel { color: #666688; font-size: 9px; }")
        info_layout.addWidget(self.status_label)
        layout.addLayout(info_layout)
        
    def update_battery(self, percent: int, charging: bool):
        if percent is None:
            self.percent_label.setText("--%")
            self.status_label.setText("")
            return
        self.percent_label.setText(f"{percent}%")
        if charging:
            self.status_label.setText("⚡ Заряд")
            self.status_label.setStyleSheet("QLabel { color: #00ff88; font-size: 9px; }")
            self.icon.setText("🔌")
        else:
            self.status_label.setText("Батарея")
            self.status_label.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
            self.icon.setText("🔋")
        if percent > 60:
            color = "#00ff88"
        elif percent > 30:
            color = "#ffaa00"
        else:
            color = "#ff4757"
        self.percent_label.setStyleSheet(f"QLabel {{ color: {color}; font-size: 18px; font-weight: bold; }}")


class ButtonWidget(QFrame):
    def __init__(self, btn_id: int, parent=None):
        super().__init__(parent)
        self.btn_id = btn_id
        self.is_pressed = False
        self.setFixedSize(60, 60)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2a2a3e, stop:1 #3a3a4e);
                border-radius: 10px;
                border: 2px solid #4a4a5e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel(f"B{self.btn_id}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("QLabel { color: #8888aa; font-size: 12px; font-weight: bold; }")
        layout.addWidget(self.label)
        
    def set_active(self, active: bool):
        if active:
            self.setStyleSheet("""
                QFrame {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, stop:0 #00ff88, stop:1 #1a1a2e);
                    border-radius: 10px;
                    border: 3px solid #00ff88;
                }
                QLabel { color: #ffffff; font-size: 12px; font-weight: bold; }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2a2a3e, stop:1 #3a3a4e);
                    border-radius: 10px;
                    border: 2px solid #4a4a5e;
                }
                QLabel { color: #8888aa; font-size: 12px; font-weight: bold; }
            """)


class StickWidget(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setFixedSize(160, 190)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { color: #00d4ff; font-size: 12px; font-weight: bold; }")
        layout.addWidget(title_label)
        self.stick_area = QFrame()
        self.stick_area.setFixedSize(120, 120)
        self.stick_area.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, stop:0 #1a1a2e, stop:1 #2a2a3e);
                border-radius: 60px;
                border: 3px solid #3a3a4e;
            }
        """)
        layout.addWidget(self.stick_area, alignment=Qt.AlignmentFlag.AlignCenter)
        self.indicator = QFrame(self.stick_area)
        self.indicator.setFixedSize(30, 30)
        self.indicator.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, stop:0 #00d4ff, stop:1 #0066ff);
                border-radius: 15px;
                border: 3px solid #00d4ff;
            }
        """)
        self.indicator.move(45, 45)
        self.indicator.show()
        self.values_label = QLabel("X:0.00 Y:0.00")
        self.values_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.values_label.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(self.values_label)
        
    def set_values(self, x: float, y: float):
        offset_x = int(x * 40)
        offset_y = int(-y * 40)
        self.indicator.move(45 + offset_x, 45 + offset_y)
        self.values_label.setText(f"X:{x:+.2f} Y:{y:+.2f}")
        if abs(x) > 0.1 or abs(y) > 0.1:
            self.indicator.setStyleSheet("""
                QFrame {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, stop:0 #00ff88, stop:1 #00aa55);
                    border-radius: 15px;
                    border: 3px solid #00ff88;
                }
            """)
        else:
            self.indicator.setStyleSheet("""
                QFrame {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, stop:0 #00d4ff, stop:1 #0066ff);
                    border-radius: 15px;
                    border: 3px solid #00d4ff;
                }
            """)


class TriggerWidget(QFrame):
    def __init__(self, name: str, color: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.color = color
        self.value = 0.0
        self.setFixedSize(45, 140)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label = QLabel(self.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"QLabel {{ color: {self.color}; font-size: 12px; font-weight: bold; }}")
        layout.addWidget(name_label)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{ background: #1a1a2e; width: 8px; border-radius: 4px; }}
            QSlider::handle:vertical {{ background: {self.color}; height: 16px; border-radius: 4px; margin: 0 -4px; }}
            QSlider::sub-page:vertical {{ background: {self.color}; border-radius: 4px; }}
        """)
        layout.addWidget(self.slider)
        self.value_label = QLabel("0%")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(self.value_label)
        
    def set_value(self, val: float):
        percent = int(val * 100)
        self.slider.setValue(percent)
        self.value_label.setText(f"{percent}%")


class TestReportWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.buttons_total = 0
        self.buttons_pressed_set = set()
        
    def setup_ui(self):
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border-radius: 15px;
                border: 2px solid #3a3a4e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        title = QLabel("📊 Отчёт о тестах")
        title.setStyleSheet("QLabel { color: #00d4ff; font-size: 16px; font-weight: bold; }")
        layout.addWidget(title)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("QFrame { background: #3a3a4e; }")
        line.setFixedHeight(2)
        layout.addWidget(line)
        self.btn_total_label = QLabel("🔘 Нажато: 0 / 0")
        self.btn_total_label.setStyleSheet("QLabel { color: #00ff88; font-size: 11px; font-weight: bold; }")
        layout.addWidget(self.btn_total_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setFixedHeight(30)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #0f0f1a;
                border-radius: 8px;
                border: 2px solid #3a3a4e;
                text-align: center;
                font-weight: bold;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff4757, stop:0.5 #ffaa00, stop:1 #00ff88);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress)
        tests_layout = QVBoxLayout()
        tests_layout.setSpacing(6)
        self.test_labels = {}
        tests = [
            ("buttons", "🔘 Кнопки"),
            ("sticks", "🕹 Сти"),
            ("triggers", "🎯 Триггеры"),
            ("vibration", "🔊 Вибрация"),
        ]
        for key, text in tests:
            lbl = QLabel(f"{text} - ❌")
            lbl.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
            tests_layout.addWidget(lbl)
            self.test_labels[key] = lbl
        layout.addLayout(tests_layout)
        self.status_label = QLabel("❌ Тесты не пройдены")
        self.status_label.setStyleSheet("QLabel { color: #ff4757; font-size: 12px; font-weight: bold; }")
        layout.addWidget(self.status_label)
        self.comment = QLabel("")
        self.comment.setWordWrap(True)
        self.comment.setStyleSheet("QLabel { color: #8888aa; font-size: 10px; }")
        layout.addWidget(self.comment)
        layout.addStretch()
        
    def update_buttons(self, pressed_ids: list, total: int):
        self.buttons_total = total
        for btn_id in pressed_ids:
            self.buttons_pressed_set.add(btn_id)
        unique_pressed = len(self.buttons_pressed_set)
        self.btn_total_label.setText(f"🔘 Нажато: {unique_pressed} / {total}")
        if unique_pressed > 0:
            self.test_labels["buttons"].setText("🔘 Кнопки - ✅")
            self.test_labels["buttons"].setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
        self.calculate_score()
        
    def reset_all(self):
        self.buttons_pressed_set = set()
        self.btn_total_label.setText(f"🔘 Нажато: 0 / {self.buttons_total}")
        for key, lbl in self.test_labels.items():
            lbl.setText(f"{lbl.text().split(' - ')[0]} - ❌")
            lbl.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
        self.calculate_score()
        
    def set_stick_tested(self, tested: bool):
        if tested:
            self.test_labels["sticks"].setText("🕹 Сти - ✅")
            self.test_labels["sticks"].setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
        self.calculate_score()
        
    def set_triggers_tested(self, tested: bool):
        if tested:
            self.test_labels["triggers"].setText("🎯 Триггеры - ✅")
            self.test_labels["triggers"].setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
        self.calculate_score()
        
    def set_vibration_tested(self, tested: bool):
        if tested:
            self.test_labels["vibration"].setText("🔊 Вибрация - ✅")
            self.test_labels["vibration"].setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
        self.calculate_score()
        
    def set_gyro_tested(self, tested: bool):
        if tested:
            self.test_labels["gyro"].setText("🌀 Гироскоп - ✅")
            self.test_labels["gyro"].setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
        self.calculate_score()
        
    def calculate_score(self):
        passed = 0
        total = len(self.test_labels)
        for key, lbl in self.test_labels.items():
            if "✅" in lbl.text():
                passed += 1
        percentage = int((passed / total) * 100) if total > 0 else 0
        self.progress.setValue(percentage)
        if percentage >= 100:
            self.status_label.setText("✅ Все тесты пройдены!")
            self.status_label.setStyleSheet("QLabel { color: #00ff88; font-size: 12px; font-weight: bold; }")
            self.comment.setText("🎉 Геймпад полностью исправен!")
        elif percentage >= 50:
            self.status_label.setText("⚠ Частичное прохождение")
            self.status_label.setStyleSheet("QLabel { color: #ffaa00; font-size: 12px; font-weight: bold; }")
            self.comment.setText("⚠ Некоторые тесты не пройдены.")
        else:
            self.status_label.setText("❌ Тесты не пройдены")
            self.status_label.setStyleSheet("QLabel { color: #ff4757; font-size: 12px; font-weight: bold; }")
            self.comment.setText("❌ Менее 50% тестов пройдено.")


class VibrationWidget(QFrame):
    def __init__(self, joystick, report_widget, parent=None):
        super().__init__(parent)
        self.joystick = joystick
        self.report_widget = report_widget
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #2a2a3e;
                border-radius: 15px;
                border: 2px solid #4a4a5e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        title = QLabel("🔊 Вибрация")
        title.setStyleSheet("QLabel { color: #ff6b6b; font-size: 15px; font-weight: bold; }")
        layout.addWidget(title)
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(10)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Левый"))
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_motor = QSlider(Qt.Orientation.Horizontal)
        self.left_motor.setRange(0, 100)
        self.left_motor.setValue(50)
        self.left_motor.setStyleSheet("""
            QSlider::groove:horizontal { background: #1a1a2e; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #4a9eff; width: 14px; border-radius: 3px; margin: -4px 0; }
        """)
        left_layout.addWidget(self.left_motor)
        sliders_layout.addLayout(left_layout)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Правый"))
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_motor = QSlider(Qt.Orientation.Horizontal)
        self.right_motor.setRange(0, 100)
        self.right_motor.setValue(50)
        self.right_motor.setStyleSheet("""
            QSlider::groove:horizontal { background: #1a1a2e; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ff6b6b; width: 14px; border-radius: 3px; margin: -4px 0; }
        """)
        right_layout.addWidget(self.right_motor)
        sliders_layout.addLayout(right_layout)
        layout.addLayout(sliders_layout)
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("▶ Тест")
        self.test_btn.setFixedSize(70, 30)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a9eff, stop:1 #2979ff);
                color: white; font-size: 11px; font-weight: bold; border-radius: 8px; border: none;
            }
        """)
        self.test_btn.clicked.connect(self.toggle_vibration)
        btn_layout.addWidget(self.test_btn)
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(30, 30)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #ee5a5a);
                color: white; font-size: 11px; font-weight: bold; border-radius: 8px; border: none;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_vibration)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        self.status = QLabel("Готов")
        self.status.setStyleSheet("QLabel { color: #8888aa; font-size: 10px; }")
        layout.addWidget(self.status)
        
    def set_joystick(self, joystick):
        self.joystick = joystick
        
    def toggle_vibration(self):
        # ПРОСТОЙ ВАРИАНТ - через pygame (работает у всех)
        if self.joystick:
            try:
                if not self.joystick.get_init():
                    self.joystick.init()
                if hasattr(self.joystick, 'rumble'):
                    left = self.left_motor.value() / 100.0
                    right = self.right_motor.value() / 100.0
                    self.joystick.rumble(int(left * 65535), int(right * 65535), 3000)
                    self.status.setText("✅ Вибрация (3 сек)")
                    self.status.setStyleSheet("QLabel { color: #00ff88; font-size: 10px; }")
                    if self.report_widget:
                        self.report_widget.set_vibration_tested(True)
                else:
                    self.status.setText("❌ Нет rumble")
                    self.status.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
            except Exception as e:
                print(f"Vibration error: {e}")
                self.status.setText(f"❌ Ошибка: {str(e)}")
                self.status.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
        else:
            self.status.setText("❌ Нет геймпада")
            self.status.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
            
    def stop_vibration(self):
        if self.joystick and hasattr(self.joystick, 'rumble'):
            try:
                self.joystick.rumble(0, 0, 0)
                self.status.setText("⏹ Стоп")
                self.status.setStyleSheet("QLabel { color: #8888aa; font-size: 10px; }")
            except:
                pass


class GyroWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #2a2a3e;
                border-radius: 15px;
                border: 2px solid #4a4a5e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        title = QLabel("🌀 Гироскоп / Акселерометр")
        title.setStyleSheet("QLabel { color: #9b59b6; font-size: 15px; font-weight: bold; }")
        layout.addWidget(title)
        self.visual = QFrame()
        self.visual.setFixedSize(100, 100)
        self.visual.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, stop:0 #1a1a2e, stop:1 #2a2a3e);
                border-radius: 50px;
                border: 3px solid #4a4a5e;
            }
        """)
        layout.addWidget(self.visual, alignment=Qt.AlignmentFlag.AlignCenter)
        self.center_dot = QFrame(self.visual)
        self.center_dot.setFixedSize(12, 12)
        self.center_dot.setStyleSheet("QFrame { background: #9b59b6; border-radius: 6px; }")
        self.center_dot.move(44, 44)
        self.gyro_label = QLabel("Gyro: X:0 Y:0 Z:0")
        self.gyro_label.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(self.gyro_label)
        self.accel_label = QLabel("Accel: X:0 Y:0 Z:0")
        self.accel_label.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(self.accel_label)
        self.status = QLabel("⚠ Требуется DS4/DS5/Joy-Con + hidapi")
        self.status.setStyleSheet("QLabel { color: #ffaa00; font-size: 9px; }")
        layout.addWidget(self.status)
        
    def set_gyro(self, gx: float, gy: float, gz: float):
        self.gyro_label.setText(f"Gyro: X:{gx:+.1f} Y:{gy:+.1f} Z:{gz:+.1f}")
        offset_x = int(gx * 20)
        offset_y = int(-gy * 20)
        self.center_dot.move(44 + offset_x, 44 + offset_y)
        
    def set_accel(self, ax: float, ay: float, az: float):
        self.accel_label.setText(f"Accel: X:{ax:+.1f} Y:{ay:+.1f} Z:{az:+.1f}")


class IRCameraWidget(QFrame):
    def __init__(self, nintendo, parent=None):
        super().__init__(parent)
        self.nintendo = nintendo
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #2a2a3e;
                border-radius: 15px;
                border: 2px solid #4a4a5e;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        title = QLabel("📷 ИК-камера")
        title.setStyleSheet("QLabel { color: #e74c3c; font-size: 15px; font-weight: bold; }")
        layout.addWidget(title)
        info = QLabel("Только Joy-Con Right")
        info.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(info)
        self.camera_view = QFrame()
        self.camera_view.setFixedSize(120, 90)
        self.camera_view.setStyleSheet("""
            QFrame {
                background: #000000;
                border-radius: 8px;
                border: 2px solid #4a4a5e;
            }
        """)
        layout.addWidget(self.camera_view, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout = QHBoxLayout()
        self.on_btn = QPushButton("▶ Вкл")
        self.on_btn.setFixedSize(70, 30)
        self.on_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e74c3c, stop:1 #c0392b);
                color: white; font-size: 11px; font-weight: bold; border-radius: 8px; border: none;
            }
        """)
        self.on_btn.clicked.connect(self.enable_camera)
        btn_layout.addWidget(self.on_btn)
        self.off_btn = QPushButton("⏹ Выкл")
        self.off_btn.setFixedSize(70, 30)
        self.off_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #555566, stop:1 #444455);
                color: white; font-size: 11px; font-weight: bold; border-radius: 8px; border: none;
            }
        """)
        self.off_btn.clicked.connect(self.disable_camera)
        btn_layout.addWidget(self.off_btn)
        layout.addLayout(btn_layout)
        self.status = QLabel("Выключена")
        self.status.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
        layout.addWidget(self.status)
        
    def set_nintendo(self, nintendo):
        self.nintendo = nintendo
        
    def enable_camera(self):
        if self.nintendo and self.nintendo.controller_type == "joycon_right":
            success = self.nintendo.enable_ir_camera()
            if success:
                self.status.setText("✅ Включена")
                self.status.setStyleSheet("QLabel { color: #00ff88; font-size: 9px; }")
                self.camera_view.setStyleSheet("""
                    QFrame {
                        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, stop:0 #330000, stop:1 #000000);
                        border-radius: 8px;
                        border: 2px solid #e74c3c;
                    }
                """)
            else:
                self.status.setText("❌ Ошибка")
                self.status.setStyleSheet("QLabel { color: #ff4757; font-size: 9px; }")
        else:
            self.status.setText("❌ Не Joy-Con R")
            self.status.setStyleSheet("QLabel { color: #ff4757; font-size: 9px; }")
        
    def disable_camera(self):
        if self.nintendo:
            self.nintendo.disable_ir_camera()
            self.status.setText("Выключена")
            self.status.setStyleSheet("QLabel { color: #8888aa; font-size: 9px; }")
            self.camera_view.setStyleSheet("""
                QFrame {
                    background: #000000;
                    border-radius: 8px;
                    border: 2px solid #4a4a5e;
                }
            """)


class GamepadTester(QMainWindow):
    def __init__(self):
        super().__init__()
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        self.joystick_index = 0
        self.ds4 = DS4Controller()
        self.nintendo = NintendoController()
        self.button_widgets = {}
        self.stick_tested = False
        self.triggers_tested = False
        self.gyro_tested = False
        self.setup_ui()
        self.setup_tray()
        self.detect_gamepad()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gamepad_state)
        self.timer.start(16)
        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self.update_battery)
        self.battery_timer.start(2000)
        self.gyro_timer = QTimer()
        self.gyro_timer.timeout.connect(self.update_gyro)
        self.gyro_timer.start(50)
        self.setup_shortcuts()
        
    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 212, 255))
        painter.setPen(QColor(0, 212, 255))
        painter.drawRoundedRect(4, 8, 24, 16, 4, 4)
        painter.drawEllipse(8, 12, 4, 4)
        painter.drawEllipse(20, 12, 4, 4)
        painter.end()
        tray_icon = QSystemTrayIcon(QIcon(pixmap), self)
        tray_menu = QMenu()
        show_action = QAction("🎮 Развернуть", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        quit_action = QAction("❌ Выход", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.setToolTip("Gamepad Tester Pro")
        tray_icon.activated.connect(self.on_tray_activated)
        tray_icon.show()
        self.tray_icon = tray_icon
        
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
            
    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        
    def setup_shortcuts(self):
        shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        shortcut_f5.activated.connect(self.detect_gamepad)
        shortcut_esc = QShortcut(QKeySequence("Esc"), self)
        shortcut_esc.activated.connect(self.showMinimized)
        shortcut_f1 = QShortcut(QKeySequence("F1"), self)
        shortcut_f1.activated.connect(self.show_help)
        
    def show_help(self):
        self.tabs.setCurrentIndex(2)
        
    def setup_ui(self):
        self.setWindowTitle("🎮 Gamepad Tester Pro v12.0")
        self.setMinimumSize(1400, 850)
        self.setStyleSheet("""
            QMainWindow {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1.2, stop:0 #0f0f1a, stop:1 #1a1a2e);
            }
        """)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        header = QHBoxLayout()
        header.addStretch()
        title = QLabel("🎮 Gamepad Tester Pro")
        title.setStyleSheet("QLabel { color: #00d4ff; font-size: 32px; font-weight: bold; }")
        header.addWidget(title)
        header.addStretch()
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border-radius: 8px;
                border: 2px solid #00ff88;
                padding: 5px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(10)
        status_layout.addWidget(QLabel("🕹️"))
        self.device_combo = QComboBox()
        self.device_combo.setFixedSize(300, 32)
        self.device_combo.setStyleSheet("""
            QComboBox {
                background: #2a2a3e;
                color: #ffffff;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background: #1a1a2e;
                color: #ffffff;
                border: 2px solid #3a3a4e;
                selection-background-color: #2a2a3e;
            }
        """)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        status_layout.addWidget(self.device_combo)
        header.addWidget(status_frame)
        self.battery_widget = BatteryWidget()
        self.battery_widget.hide()
        header.addWidget(self.battery_widget)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(45, 45)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00d4ff, stop:1 #0066ff);
                color: white; font-size: 20px; font-weight: bold; border-radius: 10px; border: none;
            }
        """)
        refresh_btn.clicked.connect(self.detect_gamepad)
        header.addWidget(refresh_btn)
        main_layout.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background: transparent; border: none; }
            QTabBar::tab {
                background: #1a1a2e; color: #8888aa; padding: 12px 30px;
                margin-right: 5px; border-radius: 10px 10px 0 0; font-size: 14px; font-weight: bold;
            }
            QTabBar::tab:selected { background: #2a2a3e; color: #00d4ff; }
            QTabBar::tab:hover { background: #2a2a3e; }
        """)
        gamepad_tab = QWidget()
        gamepad_tab.setStyleSheet("background: transparent;")
        self.gamepad_layout = QHBoxLayout(gamepad_tab)
        self.gamepad_layout.setSpacing(20)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(15)
        scroll.setWidget(self.content)
        self.gamepad_layout.addWidget(scroll, stretch=1)
        self.test_report = TestReportWidget()
        self.gamepad_layout.addWidget(self.test_report)
        self.tabs.addTab(gamepad_tab, "🎮 Геймпад")
        tests_tab = QWidget()
        tests_tab.setStyleSheet("background: transparent;")
        tests_layout = QHBoxLayout(tests_tab)
        tests_layout.setSpacing(15)
        self.vibration_widget = VibrationWidget(None, self.test_report)
        self.gyro_widget = GyroWidget()
        self.ir_camera_widget = IRCameraWidget(self.nintendo)
        tests_layout.addWidget(self.vibration_widget)
        tests_layout.addWidget(self.gyro_widget)
        tests_layout.addWidget(self.ir_camera_widget)
        tests_layout.addStretch()
        shortcuts_label = QLabel("⌨️ F5 - Обновить | Esc - Свернуть | F1 - Помощь")
        shortcuts_label.setStyleSheet("QLabel { color: #00d4ff; font-size: 11px; font-weight: bold; }")
        tests_layout.addWidget(shortcuts_label)
        export_btn = QPushButton("📤 Экспорт отчёта")
        export_btn.setFixedSize(150, 35)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f39c12, stop:1 #e67e22);
                color: white; font-size: 12px; font-weight: bold; border-radius: 8px; border: none;
            }
        """)
        export_btn.clicked.connect(self.export_report)
        tests_layout.addWidget(export_btn)
        self.tabs.addTab(tests_tab, "🔊 Тесты")
        self.about_widget = AboutWidget()
        self.tabs.addTab(self.about_widget, "ℹ О программе")
        main_layout.addWidget(self.tabs)
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_btn = QPushButton("🔄 Сброс всех тестов")
        reset_btn.setFixedSize(200, 40)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #ee5a5a);
                color: white; font-size: 13px; font-weight: bold; border-radius: 10px; border: none;
            }
        """)
        reset_btn.clicked.connect(self.reset_all)
        reset_layout.addWidget(reset_btn)
        main_layout.addLayout(reset_layout)
        
    def on_device_changed(self, index):
        print(f"=== on_device_changed: индекс {index} ===")
        self.joystick_index = index
        self.refresh_joystick()
        
    def refresh_joystick(self):
        print(f"=== refresh_joystick вызван ===")
        gamepads = get_all_gamepads()
        if self.joystick_index < len(gamepads):
            gp = gamepads[self.joystick_index]
            print(f"Переключаемся на: {gp['name']}")
            try:
                if self.joystick:
                    self.joystick.quit()
                self.joystick = pygame.joystick.Joystick(gp['index'])
                self.joystick.init()
                name = gp['name']
                is_ds = "DUALSHOCK" in name.upper() or "DUALSENSE" in name.upper() or "PS4" in name.upper() or "PS5" in name.upper() or "Wireless" in name
                is_nintendo = "Pro Controller" in name or "Joy-Con" in name or "Nintendo" in name
                is_joycon_right = "Joy-Con (R)" in name or "Joy-Con Right" in name or ("Joy-Con" in name and "L/R" in name)
                print(f"  is_ds={is_ds}, is_nintendo={is_nintendo}, is_joycon_right={is_joycon_right}")
                conn_info = ""
                if is_ds:
                    print("  → Отключаем Nintendo, подключаем DS4")
                    self.nintendo.disconnect()
                    if self.ds4.connect():
                        conn_info = " 📶 BT" if self.ds4.connection_type == "bluetooth" else " 🔌 USB"
                    self.ir_camera_widget.hide()
                    self.reset_all()
                elif is_nintendo:
                    print("  → Отключаем DS4, подключаем Nintendo")
                    self.ds4.disconnect()
                    if self.nintendo.connect():
                        conn_info = " 🎮 Nintendo"
                        self.ir_camera_widget.set_nintendo(self.nintendo)
                        if is_joycon_right or self.nintendo.controller_type == "joycon_right":
                            self.ir_camera_widget.show()
                        else:
                            self.ir_camera_widget.hide()
                    self.reset_all()
                else:
                    print("  → Другой геймпад")
                    self.ds4.disconnect()
                    self.nintendo.disconnect()
                    self.ir_camera_widget.hide()
                    self.reset_all()
                self.device_combo.setItemText(self.joystick_index, f"✅ {name}{conn_info}")
                self.vibration_widget.set_joystick(self.joystick)
                self.create_visual(name, gp['buttons'], gp['axes'], gp['hats'])
                print("  → Готово!")
            except Exception as e:
                print(f"Ошибка refresh_joystick: {e}")
                
    def detect_gamepad(self):
        print("=== detect_gamepad вызван ===")
        self.device_combo.clear()
        gamepads = get_all_gamepads()
        print(f"Найдено геймпадов: {len(gamepads)}")
        for gp in gamepads:
            print(f"  - {gp['name']}: {gp['buttons']} кн., {gp['axes']} осей")
        if not gamepads:
            self.device_combo.addItem("Нет устройств")
            self.clear_visual()
            self.joystick = None
            return
        for gp in gamepads:
            self.device_combo.addItem(f"{gp['name']} ({gp['buttons']} кн.)")
        if self.joystick_index < len(gamepads):
            self.device_combo.setCurrentIndex(self.joystick_index)
            gp = gamepads[self.joystick_index]
            self.joystick = pygame.joystick.Joystick(gp['index'])
            self.joystick.init()
            name = gp['name']
            buttons = gp['buttons']
            axes = gp['axes']
            hats = self.joystick.get_numhats()
            is_ds = "DUALSHOCK" in name.upper() or "DUALSENSE" in name.upper() or "PS4" in name.upper() or "PS5" in name.upper() or "Wireless" in name
            is_nintendo = "Pro Controller" in name or "Joy-Con" in name or "Nintendo" in name
            is_joycon_right = "Joy-Con (R)" in name or "Joy-Con Right" in name or ("Joy-Con" in name and "L/R" in name)
            conn_info = ""
            if is_ds:
                self.nintendo.disconnect()
                if self.ds4.connect():
                    conn_info = " 📶 BT" if self.ds4.connection_type == "bluetooth" else " 🔌 USB"
                self.ir_camera_widget.hide()
            elif is_nintendo:
                self.ds4.disconnect()
                if self.nintendo.connect():
                    conn_info = " 🎮 Nintendo"
                    self.ir_camera_widget.set_nintendo(self.nintendo)
                    if is_joycon_right or self.nintendo.controller_type == "joycon_right":
                        self.ir_camera_widget.show()
                    else:
                        self.ir_camera_widget.hide()
            else:
                self.ds4.disconnect()
                self.nintendo.disconnect()
                self.ir_camera_widget.hide()
            self.device_combo.setItemText(self.joystick_index, f"✅ {name}{conn_info}")
            self.vibration_widget.set_joystick(self.joystick)
            self.create_visual(name, buttons, axes, hats)
        else:
            self.joystick = None
            
    def clear_visual(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def create_visual(self, name: str, buttons: int, axes: int, hats: int):
        self.clear_visual()
        gp_container = QWidget()
        gp_container.setStyleSheet("background: transparent;")
        gp_layout = QHBoxLayout(gp_container)
        gp_layout.setSpacing(25)
        gp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setSpacing(12)
        self.left_stick = StickWidget("Левый")
        self.right_stick = StickWidget("Правый")
        left_layout.addWidget(self.left_stick)
        left_layout.addWidget(self.right_stick)
        gp_layout.addWidget(left)
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(10)
        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("""
            QLabel {
                color: #ffffff; font-size: 13px; font-weight: bold;
                padding: 6px 12px; background: #1a1a2e; border-radius: 8px; border: 2px solid #3a3a4e;
            }
        """)
        center_layout.addWidget(name_lbl)
        btn_grid = QGridLayout()
        btn_grid.setSpacing(6)
        btn_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_widgets = {}
        cols = 5
        for i in range(buttons):
            row = i // cols
            col = i % cols
            btn = ButtonWidget(i)
            btn_grid.addWidget(btn, row, col)
            self.button_widgets[i] = btn
        center_layout.addLayout(btn_grid)
        gp_layout.addWidget(center)
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.setSpacing(12)
        self.lt_slider = TriggerWidget("LT", "#ff6b6b")
        self.rt_slider = TriggerWidget("RT", "#ff6b6b")
        right_layout.addWidget(self.lt_slider)
        right_layout.addWidget(self.rt_slider)
        info_box = QFrame()
        info_box.setStyleSheet("QFrame { background: #1a1a2e; border-radius: 8px; border: 2px solid #3a3a4e; }")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(4)
        info_title = QLabel("📊 Инфо")
        info_title.setStyleSheet("QLabel { color: #00d4ff; font-size: 12px; font-weight: bold; }")
        info_layout.addWidget(info_title)
        self.info_labels = {}
        for key, text in [("buttons", "Кнопки"), ("axes", "Оси"), ("hats", "HAT")]:
            lbl = QLabel(f"{text}: 0")
            lbl.setStyleSheet("QLabel { color: #8888aa; font-size: 10px; }")
            info_layout.addWidget(lbl)
            self.info_labels[key] = lbl
        self.info_labels["buttons"].setText(f"Кнопки: {buttons}")
        self.info_labels["axes"].setText(f"Оси: {axes}")
        self.info_labels["hats"].setText(f"HAT: {hats}")
        right_layout.addWidget(info_box)
        right_layout.addStretch()
        gp_layout.addWidget(right)
        self.content_layout.addWidget(gp_container)
        if "gyro" not in self.test_report.test_labels:
            lbl = QLabel("🌀 Гироскоп - ❌")
            lbl.setStyleSheet("QLabel { color: #ff4757; font-size: 10px; }")
            self.test_report.test_labels["gyro"] = lbl
            self.test_report.layout().addWidget(lbl)
        self.test_report.update_buttons([], buttons)
        
    def update_gamepad_state(self):
        if not self.joystick:
            return
        try:
            pygame.event.pump()
            if not self.joystick.get_init():
                if self.joystick_index < self.device_combo.count():
                    current_text = self.device_combo.itemText(self.joystick_index)
                    self.device_combo.setItemText(self.joystick_index, current_text.split(" ")[0] + " ⚪ Отключён")
                return
            pressed_ids = []
            try:
                num_buttons = self.joystick.get_numbuttons()
                for btn_id, widget in self.button_widgets.items():
                    if btn_id < num_buttons:
                        pressed = self.joystick.get_button(btn_id)
                        widget.set_active(pressed)
                        if pressed:
                            pressed_ids.append(btn_id)
            except:
                pass
            self.test_report.update_buttons(pressed_ids, self.test_report.buttons_total)
            try:
                axes = self.joystick.get_numaxes()
                if axes >= 4:
                    lx = self.joystick.get_axis(0)
                    ly = self.joystick.get_axis(1)
                    self.left_stick.set_values(lx, ly)
                    rx = self.joystick.get_axis(2)
                    ry = self.joystick.get_axis(3)
                    self.right_stick.set_values(rx, ry)
                    if not self.stick_tested:
                        if abs(lx) > 0.3 or abs(ly) > 0.3 or abs(rx) > 0.3 or abs(ry) > 0.3:
                            self.stick_tested = True
                            self.test_report.set_stick_tested(True)
                    if axes >= 6:
                        lt = self.joystick.get_axis(4)
                        rt = self.joystick.get_axis(5)
                        lt_val = max(0, lt) if lt > 0 else (lt + 1) / 2 if lt < 0 else 0
                        rt_val = max(0, rt) if rt > 0 else (rt + 1) / 2 if rt < 0 else 0
                        self.lt_slider.set_value(lt_val)
                        self.rt_slider.set_value(rt_val)
                        if not self.triggers_tested:
                            if lt_val > 0.3 or rt_val > 0.3:
                                self.triggers_tested = True
                                self.test_report.set_triggers_tested(True)
            except:
                pass
        except:
            if self.joystick_index < self.device_combo.count():
                current_text = self.device_combo.itemText(self.joystick_index)
                self.device_combo.setItemText(self.joystick_index, current_text.split(" ")[0] + " ⚪ Отключён")
                
    def update_battery(self):
        if self.ds4.device and self.ds4.connection_type != "none":
            percent, charging = self.ds4.get_battery()
            if percent is not None:
                self.battery_widget.update_battery(percent, charging)
                return
        if self.nintendo.device and self.nintendo.controller_type != "none":
            percent, charging = self.nintendo.get_battery()
            if percent is not None:
                self.battery_widget.update_battery(percent, charging)
                
    def update_gyro(self):
        if self.ds4.device and self.ds4.connection_type != "none":
            data = self.ds4.read_data()
            if data and len(data) >= 60:
                try:
                    gyro_x = int.from_bytes(data[13:15], 'little', signed=True) / 256.0
                    gyro_y = int.from_bytes(data[15:17], 'little', signed=True) / 256.0
                    gyro_z = int.from_bytes(data[17:19], 'little', signed=True) / 256.0
                    accel_x = int.from_bytes(data[19:21], 'little', signed=True) / 256.0
                    accel_y = int.from_bytes(data[21:23], 'little', signed=True) / 256.0
                    accel_z = int.from_bytes(data[23:25], 'little', signed=True) / 256.0
                    if gyro_x != 0 or gyro_y != 0 or gyro_z != 0:
                        self.gyro_widget.set_gyro(gyro_x, gyro_y, gyro_z)
                        self.gyro_widget.set_accel(accel_x, accel_y, accel_z)
                        self.gyro_widget.status.setText("✅ DS4/DS5 IMU")
                        self.gyro_widget.status.setStyleSheet("QLabel { color: #00ff88; font-size: 9px; }")
                        if not self.gyro_tested:
                            self.gyro_tested = True
                            self.test_report.set_gyro_tested(True)
                        return
                except Exception as e:
                    print(f"DS4 gyro error: {e}")
        if self.nintendo.device and self.nintendo.controller_type != "none":
            imu_data = self.nintendo.read_imu()
            if imu_data:
                gyro = imu_data['gyro']
                accel = imu_data['accel']
                self.gyro_widget.set_gyro(gyro[0], gyro[1], gyro[2])
                self.gyro_widget.set_accel(accel[0], accel[1], accel[2])
                self.gyro_widget.status.setText("✅ Joy-Con IMU")
                self.gyro_widget.status.setStyleSheet("QLabel { color: #00ff88; font-size: 9px; }")
                if not self.gyro_tested:
                    self.gyro_tested = True
                    self.test_report.set_gyro_tested(True)
                    
    def export_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Экспорт отчёта", "", "Text Files (*.txt)")
        if filename:
            try:
                gp_name = "Неизвестно"
                gp_index = self.device_combo.currentIndex()
                if gp_index >= 0 and gp_index < self.device_combo.count():
                    gp_name = self.device_combo.itemText(gp_index)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("🎮 Gamepad Tester Pro - Отчёт о тестах\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Устройство: {gp_name}\n")
                    f.write(f"Дата: {time.strftime('%d.%m.%Y %H:%M')}\n\n")
                    f.write("📊 Результаты тестов:\n")
                    for key, lbl in self.test_report.test_labels.items():
                        f.write(f"  {lbl.text()}\n")
                    f.write(f"\n{self.test_report.status_label.text()}\n")
                    f.write(f"\n{self.test_report.comment.text()}\n")
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("Создано в Gamepad Tester Pro v12.0\n")
                    f.write("Автор: Alex Software (mrSaT13)\n")
                    f.write("GitHub: https://github.com/mrSaT13\n")
                print(f"Отчёт сохранён: {filename}")
            except Exception as e:
                print(f"Ошибка экспорта: {e}")
                
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F5:
            self.detect_gamepad()
        elif event.key() == Qt.Key.Key_Escape:
            self.showMinimized()
            
    def reset_all(self):
        self.test_report.reset_all()
        self.stick_tested = False
        self.triggers_tested = False
        self.gyro_tested = False
        
    def quit_app(self):
        if self.joystick:
            try:
                self.joystick.rumble(0, 0, 0)
            except:
                pass
        self.ds4.disconnect()
        self.nintendo.disconnect()
        pygame.quit()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()


class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        title = QLabel("🎮 Gamepad Tester Pro v12.0")
        title.setStyleSheet("QLabel { color: #00d4ff; font-size: 32px; font-weight: bold; }")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        author = QLabel("Автор: Alex Software (mrSaT13)")
        author.setStyleSheet("QLabel { color: #00ff88; font-size: 14px; font-weight: bold; }")
        layout.addWidget(author, alignment=Qt.AlignmentFlag.AlignCenter)
        github_link = QLabel('<a href="https://github.com/mrSaT13" style="color: #00d4ff; text-decoration: none;">🔗 GitHub: github.com/mrSaT13</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet("QLabel { color: #00d4ff; font-size: 12px; }")
        layout.addWidget(github_link, alignment=Qt.AlignmentFlag.AlignCenter)
        instr_group = QGroupBox("📖 Инструкция")
        instr_group.setStyleSheet("""
            QGroupBox {
                color: #00d4ff;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #3a3a4e;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
        """)
        instr_layout = QVBoxLayout()
        instr_layout.setSpacing(8)
        instructions = [
            "1. Подключите геймпад по USB или Bluetooth",
            "2. Выберите устройство в зелёной рамке 🕹️",
            "3. Нажимайте кнопки - они подсвечиваются зелёным",
            "4. Двигайте стики - индикатор показывает положение",
            "5. Во вкладке 'Тесты' проверьте вибрацию, гироскоп",
            "6. Отчёт справа показывает прогресс тестов (20% за каждый тест)",
            "",
            "⌨️ Горячие клавиши:",
            "  F5 - Обновить список устройств",
            "  Esc - Свернуть программу",
            "  F1 - Открыть эту справку",
        ]
        for instr in instructions:
            lbl = QLabel(instr)
            lbl.setStyleSheet("QLabel { color: #aaaaaa; font-size: 12px; }")
            instr_layout.addWidget(lbl)
        instr_group.setLayout(instr_layout)
        layout.addWidget(instr_group)
        sensors_group = QGroupBox("📡 Тестируемые датчики")
        sensors_group.setStyleSheet("""
            QGroupBox {
                color: #00ff88;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #3a3a4e;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
        """)
        sensors_layout = QVBoxLayout()
        sensors_layout.setSpacing(5)
        sensors = [
            "🔘 Кнопки (все цифровые)",
            "🕹 Аналоговые стики (2 оси каждый)",
            "🎯 Аналоговые триггеры (LT/RT)",
            "🔊 Вибрация (2 мотора)",
            "🌀 Гироскоп (DS4/DS5/Joy-Con + hidapi)",
            "📈 Акселерометр (DS4/DS5/Joy-Con + hidapi)",
            "📷 ИК-камера (Joy-Con R + hidapi)",
        ]
        for sensor in sensors:
            lbl = QLabel(sensor)
            lbl.setStyleSheet("QLabel { color: #aaaaaa; font-size: 11px; }")
            sensors_layout.addWidget(lbl)
        sensors_group.setLayout(sensors_layout)
        layout.addWidget(sensors_group)
        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = GamepadTester()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    window.setFocus()
    app.processEvents()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
