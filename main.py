# © 2025 MicroFire, All rights reserved.
# 萌ICP备20250202号

import sys
import time
import threading
import pyaudio
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QDialog, QGridLayout
from PyQt5.QtGui import QFont, QIcon, QFontDatabase
from PyQt5.QtCore import Qt
from datetime import datetime


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        layout = QGridLayout()

        self.label1 = QLabel("安静长出小树分贝:")
        self.input1 = QLineEdit()
        self.input1.setText("40")
        self.label2 = QLabel("嘈杂消失小树分贝:")
        self.input2 = QLineEdit()
        self.input2.setText("80")
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
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 设置花园窗口大小为400x300
        self.setGeometry(0, 0, 400, 300)
        # 添加圆角样式
        self.setStyleSheet("border-radius: 20px; background-color: #f0f8ff;")
        layout = QVBoxLayout()
        self.garden_label = QLabel()
        # 加载本地字体
        font_id = QFontDatabase.addApplicationFont("fonts/DingTalkJinBuTi.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                # 设置字体尺寸为50px
                font = QFont(font_families[0], 50)
                self.garden_label.setFont(font)
        self.garden_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.garden_label)
        self.setLayout(layout)
        self.draggable = True
        self.dragging_position = None

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.dragging_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.dragging_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.dragging_position = None
            event.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 设置主窗口大小为400x300
        self.setGeometry(100, 100, 400, 300)
        self.initUI()
        self.trees = 0
        self.recording = False
        self.decibel_threshold_grow = 40
        self.decibel_threshold_shrink = 80
        self.quiet_duration = 1
        self.start_time = 0
        self.garden_window = GardenWindow()
        self.garden_window.show()

    def initUI(self):
        self.setWindowTitle("安静花园养小树")
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()

        # 标题和标语
        title_label = QLabel("安静花园养小树")
        # 加载本地字体
        font_id = QFontDatabase.addApplicationFont("fonts/DingTalkJinBuTi.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], 24)
                title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        slogan_label = QLabel("保持安静，小树快快长！")
        if font_id != -1:
            font = QFont(font_families[0], 16)
            slogan_label.setFont(font)
        slogan_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(slogan_label)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.begin_button = QPushButton("BEGIN！")
        if font_id != -1:
            font = QFont(font_families[0], 16)
            self.begin_button.setFont(font)
        self.begin_button.clicked.connect(self.start_recording)
        self.over_button = QPushButton("OVER")
        if font_id != -1:
            font = QFont(font_families[0], 16)
            self.over_button.setFont(font)
        self.over_button.clicked.connect(self.stop_recording)
        self.over_button.setEnabled(False)
        button_layout.addWidget(self.begin_button)
        button_layout.addWidget(self.over_button)
        layout.addLayout(button_layout)

        # 分贝显示
        self.decibel_label = QLabel("当前分贝: 000")
        if font_id != -1:
            font = QFont(font_families[0], 16)
            self.decibel_label.setFont(font)
        self.decibel_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.decibel_label)

        # 设置图标
        self.settings_icon = QPushButton("⚙")
        if font_id != -1:
            font = QFont(font_families[0], 16)
            self.settings_icon.setFont(font)
        self.settings_icon.setStyleSheet("background-color: transparent; border: none;")
        self.settings_icon.clicked.connect(self.open_settings)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.settings_icon)
        layout.addLayout(button_layout)

        # 添加版权声明
        copyright_label = QLabel("© 2025 MicroFire, All rights reserved.\n萌ICP备20250202号")
        if font_id != -1:
            font = QFont(font_families[0], 8)
            copyright_label.setFont(font)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #666666;")
        layout.addWidget(copyright_label)

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

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.decibel_threshold_grow = int(dialog.input1.text())
            self.decibel_threshold_shrink = int(dialog.input2.text())
            self.quiet_duration = int(dialog.input3.text())

    def monitor_sound(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        EPSILON = 1e-10
        while self.recording:
            try:
                data = stream.read(1024)
                # 将音频数据类型转换为 np.int32
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.int32)
                if len(audio_data) == 0:
                    print("警告：读取到空的音频数据")
                    continue
            except Exception as e:
                print(f"读取音频数据时出错: {e}")
                continue

            print(f"音频数据最小值: {np.min(audio_data)}, 最大值: {np.max(audio_data)}")

            squared_audio = np.square(audio_data)
            mean_square = np.mean(squared_audio)
            print(f"均方值: {mean_square}")

            # 检查 mean_square 是否为负数或 NaN
            if np.isnan(mean_square) or mean_square < 0:
                print(f"警告：均方值异常，值为 {mean_square}")
                mean_square = 0

            is_invalid = (np.abs(mean_square) < EPSILON) | np.isnan(mean_square) | (mean_square < 0)
            rms = np.where(is_invalid, 0, np.sqrt(mean_square))

            if rms > 0:
                decibel = 20 * np.log10(rms)
                print(f"计算得到的分贝值: {decibel}")
            else:
                decibel = 0
            # 格式化分贝显示为三位数
            decibel_str = f"{decibel:.0f}".zfill(3)
            self.decibel_label.setText(f"当前分贝: {decibel_str}")

            if decibel < self.decibel_threshold_grow:
                if self.start_time == 0:
                    self.start_time = time.time()
                elif time.time() - self.start_time >= self.quiet_duration * 60:
                    self.trees += 1
                    self.update_garden()
                    self.start_time = 0
            elif decibel > self.decibel_threshold_shrink:
                if self.start_time == 0:
                    self.start_time = time.time()
                elif time.time() - self.start_time >= 60:
                    if self.trees > 0:
                        self.trees -= 1
                    self.update_garden()
                    self.start_time = 0
            else:
                self.start_time = 0

        stream.stop_stream()
        stream.close()
        p.terminate()

    def update_garden(self):
        garden_text = ""
        tree_count = 0
        if self.trees < 3:
            for _ in range(self.trees):
                garden_text += "🌲"
                tree_count += 1
                if tree_count % 5 == 0:
                    garden_text += "\n"
        else:
            full_trees = self.trees // 3
            remaining_trees = self.trees % 3
            for _ in range(full_trees):
                garden_text += "🌳"
                tree_count += 1
                if tree_count % 5 == 0:
                    garden_text += "\n"
            for _ in range(remaining_trees):
                garden_text += "🌲"
                tree_count += 1
                if tree_count % 5 == 0:
                    garden_text += "\n"
        self.garden_window.garden_label.setText(garden_text)

    def closeEvent(self, event):
        self.recording = False
        # 计算大树和小树的数量
        full_trees = self.trees // 3
        remaining_trees = self.trees % 3
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open('treenumber.txt', 'a') as file:
                file.write(f'{now} {full_trees} {remaining_trees}\n')
        except Exception as e:
            print(f"写入文件时出错: {e}")
        self.garden_window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
