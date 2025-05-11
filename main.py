# © 2025 MicroFire, All rights reserved.
# 萌ICP备20250202号
import sys
import time
import threading
import pyaudio
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QDialog, \
    QGridLayout, QProgressBar
from PyQt5.QtGui import QFont, QIcon, QFontDatabase, QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        layout = QGridLayout()
        self.label1 = QLabel("安静长出小树分贝:")
        self.input1 = QLineEdit()
        self.input1.setText("57")
        self.label2 = QLabel("嘈杂消失小树分贝:")
        self.input2 = QLineEdit()
        self.input2.setText("60")
        self.label3 = QLabel("安静保持时长（分钟）:")
        self.input3 = QLineEdit()
        self.input3.setText("1")
        layout.addWidget(self.label1, 0, 0)
        layout.addWidget(self.input1, 0, 1)
        layout.addWidget(self.label2, 1, 0)
        layout.addWidget(self.input2, 1, 1)
        layout.addWidget(self.label3, 2, 0)
        layout.addWidget(self.input3, 2, 1)
        # 添加保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button, 3, 0, 1, 2)
        self.setLayout(layout)


class GardenWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 设置窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setGeometry(0, 0, 400, 300)

        layout = QVBoxLayout()

        # 添加 + 按钮
        self.move_button = QLabel("➕")
        self.move_button.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.move_button.setStyleSheet("font-size: 20px; padding: 5px; cursor: pointer;")
        layout.addWidget(self.move_button)

        self.garden_label = QLabel()
        font_id = QFontDatabase.addApplicationFont("fonts/DingTalkJinBuTi.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], 50)
                self.garden_label.setFont(font)
        self.garden_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.garden_label)

        self.setLayout(layout)

        self.draggable = True
        self.dragging_position = None

        # 连接鼠标事件到按钮
        self.move_button.mousePressEvent = self.button_mousePressEvent
        self.move_button.mouseMoveEvent = self.button_mouseMoveEvent
        self.move_button.mouseReleaseEvent = self.button_mouseReleaseEvent

        # 连接鼠标事件到花园标签
        self.garden_label.mousePressEvent = self.tree_mousePressEvent
        self.garden_label.mouseMoveEvent = self.tree_mouseMoveEvent
        self.garden_label.mouseReleaseEvent = self.tree_mouseReleaseEvent

    def button_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def button_mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.dragging_position)
            event.accept()

    def button_mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_position = None
            event.accept()

    def tree_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def tree_mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.dragging_position)
            event.accept()

    def tree_mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_position = None
            event.accept()


class MainWindow(QWidget):
    # 自定义信号
    update_decibel_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    update_garden_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 300)
        self.quiet_duration = 1
        self.initUI()
        self.small_trees = 0
        self.medium_trees = 0
        self.big_trees = 0
        self.palm_trees = 0
        self.recording = False
        self.decibel_threshold_grow = 57
        self.decibel_threshold_shrink = 60
        self.start_time = 0
        self.garden_window = GardenWindow()
        self.garden_window.show()
        self.progress_value = 0

        # 连接信号和槽
        self.update_decibel_signal.connect(self.update_decibel_label)
        self.update_progress_signal.connect(self.update_progress_bar)
        self.update_garden_signal.connect(self.update_garden)

    def initUI(self):
        self.setWindowTitle("安静花园养小树")
        # 设置背景颜色
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QColor(204, 232, 207)))
        self.setPalette(palette)

        layout = QVBoxLayout()

        # 标题和标语
        title_layout = QHBoxLayout()
        title_label = QLabel("安静花园养小树")
        font_id = QFontDatabase.addApplicationFont("fonts/DingTalkJinBuTi.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], 36)
                font.setBold(True)
                title_label.setFont(font)
                title_label.setStyleSheet("color: green;")
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(QLabel("🌿"))
        title_layout.addWidget(title_label)
        title_layout.addWidget(QLabel("🌿"))
        layout.addLayout(title_layout)

        slogan_label = QLabel("保持安静，小树快快长！")
        if font_id != -1:
            font = QFont(font_families[0], 18)
            slogan_label.setFont(font)
        slogan_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(slogan_label)

        # 分贝显示和进度条
        status_layout = QVBoxLayout()

        self.decibel_value_label = QLabel("")
        if font_id != -1:
            font = QFont(font_families[0], 18)
            self.decibel_value_label.setFont(font)
        self.decibel_value_label.setStyleSheet("background-color: white; border-radius: 15px; padding: 10px;")
        self.decibel_value_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.decibel_value_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.quiet_duration * 60)
        self.progress_bar.setValue(0)
        # 修改进度条颜色为绿色
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: white; border: none; border-radius: 15px; height: 30px; } QProgressBar::chunk { background-color: green; border-radius: 15px; }")
        # 禁止显示进度条上的文本
        self.progress_bar.setTextVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addLayout(status_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.begin_button = QPushButton("BEGIN")
        if font_id != -1:
            font = QFont(font_families[0], 18)
            self.begin_button.setFont(font)
        self.begin_button.setStyleSheet(
            "background-color: white; border: 2px solid black; border-radius: 15px; padding: 10px 20px;")
        self.begin_button.clicked.connect(self.start_recording)
        self.over_button = QPushButton("OVER")
        if font_id != -1:
            font = QFont(font_families[0], 18)
            self.over_button.setFont(font)
        self.over_button.setStyleSheet(
            "background-color: white; border: 2px solid black; border-radius: 15px; padding: 10px 20px;")
        self.over_button.clicked.connect(self.stop_recording)
        self.over_button.setEnabled(False)
        self.settings_icon = QPushButton("SET")
        if font_id != -1:
            font = QFont(font_families[0], 18)
            self.settings_icon.setFont(font)
        self.settings_icon.setStyleSheet(
            "background-color: white; border: 2px solid black; border-radius: 15px; padding: 10px 20px;")
        self.settings_icon.clicked.connect(self.open_settings)
        button_layout.addWidget(self.begin_button)
        button_layout.addWidget(self.over_button)
        button_layout.addWidget(self.settings_icon)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def start_recording(self):
        self.recording = True
        self.begin_button.setEnabled(False)
        self.over_button.setEnabled(True)
        threading.Thread(target=self.monitor_sound).start()

    def stop_recording(self):
        self.recording = False
        self.begin_button.setEnabled(True)
        self.over_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_value = 0

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.decibel_threshold_grow = int(dialog.input1.text())
            self.decibel_threshold_shrink = int(dialog.input2.text())
            self.quiet_duration = int(dialog.input3.text())
            self.progress_bar.setRange(0, self.quiet_duration * 60)

    def monitor_sound(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            EPSILON = 1e-10
            while self.recording:
                try:
                    data = stream.read(1024)
                    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.int32)
                    if len(audio_data) == 0:
                        print("警告：读取到空的音频数据")
                        continue
                except Exception as e:
                    print(f"读取音频数据时出错: {e}")
                    continue
                squared_audio = np.square(audio_data)
                mean_square = np.mean(squared_audio)
                if np.isnan(mean_square) or mean_square < 0:
                    mean_square = 0
                is_invalid = (np.abs(mean_square) < EPSILON) | np.isnan(mean_square) | (mean_square < 0)
                rms = np.where(is_invalid, 0, np.sqrt(mean_square))
                if rms > 0:
                    decibel = 20 * np.log10(rms)
                else:
                    decibel = 0
                decibel_str = f"{decibel:.0f}".zfill(3)
                # 发射更新分贝标签的信号
                self.update_decibel_signal.emit(f"当前分贝: {decibel_str}pb")

                if decibel < self.decibel_threshold_grow:
                    if self.start_time == 0:
                        self.start_time = time.time()
                    elapsed_time = time.time() - self.start_time
                    self.progress_value = elapsed_time
                    # 发射更新进度条的信号
                    self.update_progress_signal.emit(int(elapsed_time))
                    if elapsed_time >= self.quiet_duration * 60:
                        self.small_trees += 1
                        self.convert_trees()
                        # 发射更新花园的信号
                        self.update_garden_signal.emit()
                        self.start_time = 0
                        self.progress_value = 0
                        self.update_progress_signal.emit(0)
                elif decibel > self.decibel_threshold_shrink:
                    if self.start_time == 0:
                        self.start_time = time.time()
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time >= 60:
                        if self.small_trees > 0:
                            self.small_trees -= 1
                        self.convert_trees()
                        # 发射更新花园的信号
                        self.update_garden_signal.emit()
                        self.start_time = 0
                        self.progress_value = 0
                        self.update_progress_signal.emit(0)
                else:
                    self.start_time = 0
                    self.progress_value = 0
                    self.update_progress_signal.emit(0)
        except Exception as e:
            print(f"打开音频流时出错: {e}")
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            p.terminate()

    def convert_trees(self):
        while self.small_trees >= 3:
            self.small_trees -= 3
            self.medium_trees += 1
        while self.medium_trees >= 5:
            self.medium_trees -= 5
            self.big_trees += 1
        while self.big_trees >= 2:
            self.big_trees -= 2
            self.palm_trees += 1

    def update_garden(self):
        garden_text = ""
        tree_count = 0
        for _ in range(self.palm_trees):
            garden_text += "🌴"
            tree_count += 1
            if tree_count % 5 == 0:
                garden_text += "\n"
        for _ in range(self.big_trees):
            garden_text += "🌳"
            tree_count += 1
            if tree_count % 5 == 0:
                garden_text += "\n"
        for _ in range(self.medium_trees):
            garden_text += "🎄"
            tree_count += 1
            if tree_count % 5 == 0:
                garden_text += "\n"
        for _ in range(self.small_trees):
            garden_text += "🌲"
            tree_count += 1
            if tree_count % 5 == 0:
                garden_text += "\n"
        self.garden_window.garden_label.setText(garden_text)

    def update_decibel_label(self, text):
        self.decibel_value_label.setText(text)

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def closeEvent(self, event):
        self.recording = False
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open('treesnumber.txt', 'a') as file:
                file.write(f'{now} {self.palm_trees} {self.big_trees} {self.medium_trees} {self.small_trees}\n')
        except Exception as e:
            print(f"写入文件时出错: {e}")
        self.garden_window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
