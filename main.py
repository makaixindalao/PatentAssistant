import sys
import os
import json
import ai
import logging
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDialog, QLabel, 
                            QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                            QFileDialog, QMessageBox, QComboBox, QFormLayout)

class Worker(QThread):
    # 信号参数：错误信息，生成内容，保存路径，是否成功
    finished = pyqtSignal(str, str, str, bool)

    def __init__(self, title, ideas, config, save_path):
        super().__init__()
        self.title = title
        self.ideas = ideas
        self.config = config
        self.save_path = save_path
        self._is_running = True  # 线程运行标志

    def stop(self):
        """安全停止线程"""
        self._is_running = False
        self.terminate()

    def run(self):
        try:
            if not self._is_running:
                return

            patent_doc = ai.generate_patent_document(self.title, self.ideas)

            if not self._is_running:
                return

            # 2. 处理文件名
            base_name = self.title[:10].strip().replace(" ", "_")
            filename = f"{base_name}_专利交底书.md"
            save_path = os.path.join(self.save_path, filename)

            # 3. 处理文件重名
            counter = 1
            while os.path.exists(save_path):
                new_name = f"{base_name}_专利交底书_{counter}.md"
                save_path = os.path.join(self.save_path, new_name)
                counter += 1
                if counter > 100:  # 防止无限循环
                    raise Exception("文件保存失败：尝试超过100次仍未找到可用文件名")

            # 4. 保存文件
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(patent_doc)

            # 5. 返回成功结果
            self.finished.emit("", patent_doc, save_path, True)

        except Exception as e:
            # 返回错误信息
            error_msg = f"生成过程失败：{str(e)}"
            self.finished.emit(error_msg, "", "", False)


class ConfigDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("API配置")
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        
        # 表单布局
        form = QFormLayout()
        self.url_input = QLineEdit(self.config['base_url'])
        self.key_input = QLineEdit(self.config['api_key'])
        self.key_input.setEchoMode(QLineEdit.Password)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "DeepSeek-R1"])
        self.model_combo.setCurrentText(self.config['model'])
        
        form.addRow("API地址:", self.url_input)
        form.addRow("API密钥:", self.key_input)
        form.addRow("模型选择:", self.model_combo)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_config)
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(form)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_config(self):
        new_config = {
            "base_url": self.url_input.text().strip(),
            "api_key": self.key_input.text().strip(),
            "model": self.model_combo.currentText()
        }
        
        if not all(new_config.values()):
            QMessageBox.warning(self, "错误", "所有配置项不能为空")
            return
            
        try:
            with open("config.json", "w") as f:
                json.dump({"openai_config": new_config}, f, indent=2)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def test_connection(self):
        from openai import OpenAI
        try:
            client = OpenAI(
                api_key=self.key_input.text().strip(),
                base_url=self.url_input.text().strip()
            )
            client.models.list()  # 简单API调用测试
            QMessageBox.information(self, "成功", "连接测试通过")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")

class PatentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.save_path = os.getcwd()  # 默认保存路径
        self.init_ui()
        self.worker = None
        self.setup_logging()
        self.config = self.load_config()
        self.progress = None

    def init_ui(self):
        # 主窗口设置
        self.setWindowTitle("专利文档生成系统 v1.0")
        self.setGeometry(300, 300, 600, 400)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 输入区域
        input_layout = QVBoxLayout()
        
        # 发明名称
        name_layout = QVBoxLayout()
        name_label = QLabel("发明名称：")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入包含技术特征和应用领域的名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)

        # 技术特点
        feature_layout = QVBoxLayout()
        feature_label = QLabel("技术特点：")
        self.feature_input = QTextEdit()
        self.feature_input.setPlaceholderText("请输入技术方案要点（支持多行输入）")
        self.feature_input.setMaximumHeight(100)
        feature_layout.addWidget(feature_label)
        feature_layout.addWidget(self.feature_input)

        # 路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel("保存路径：")
        self.path_display = QLabel(self.save_path)
        self.path_display.setStyleSheet("color: #666;")
        path_btn = QPushButton("更改路径")
        path_btn.clicked.connect(self.choose_directory)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_display)
        path_layout.addWidget(path_btn)
        path_layout.addStretch()

        # 按钮区域
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("开始生成")
        generate_btn.clicked.connect(self.generate_document)
        generate_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(self.open_file)
        open_btn.setStyleSheet("background-color: #2196F3; color: white;")

        btn_layout.addWidget(generate_btn)
        btn_layout.addWidget(open_btn)
        btn_layout.addStretch()

        # 组装主布局
        main_layout.addLayout(name_layout)
        main_layout.addLayout(feature_layout)
        main_layout.addLayout(path_layout)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

         # 添加菜单栏
        menu = self.menuBar()
        config_action = menu.addAction("配置")
        config_action.triggered.connect(self.show_config)

    def load_config(self):
        """加载配置文件并返回配置字典"""
        default_config = {
            "base_url": "https://aihubmix.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini"
        }
        
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
                return config_data.get("openai_config", default_config)
        except FileNotFoundError:
            logging.warning("配置文件未找到，使用默认配置")
            return default_config
        except json.JSONDecodeError:
            logging.error("配置文件格式错误，使用默认配置")
            return default_config
        except Exception as e:
            logging.error(f"配置加载异常: {str(e)}")
            return default_config
        
    def show_config(self):
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.config
            QMessageBox.information(self, "提示", "配置已更新，新配置将在下次生成时生效")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log', mode='a'),
                logging.StreamHandler()
            ]
        )

    def choose_directory(self):
        """选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.save_path)
        if directory:
            self.save_path = directory
            self.path_display.setText(directory)
            logging.info(f"保存路径已更改为：{directory}")

    def validate_input(self):
        """验证输入有效性"""
        name = self.name_input.text().strip()
        features = self.feature_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "输入错误", "发明名称不能为空！")
            self.name_input.setFocus()
            return False
        
        if not features:
            QMessageBox.warning(self, "输入错误", "技术特点不能为空！")
            self.feature_input.setFocus()
            return False
        
        return True

    def generate_document(self):
        current_config = self.config.copy()
        """生成文档主逻辑"""
        if not self.validate_input():
            return
        
        try:
             # 创建进度窗口
            self.progress = QMessageBox(self)
            self.progress.setWindowTitle("生成中...")
            self.progress.setBaseSize(100, 50)
            
            # 添加取消按钮
            self.progress.addButton("取消", QMessageBox.RejectRole)
            self.progress.buttonClicked.connect(self.on_cancel_clicked)
            
            # 显示窗口
            self.progress.show()
            
            # 启动工作线程
            self.worker = Worker(
                title=self.name_input.text().strip(),
                ideas=self.feature_input.toPlainText().strip(),
                config=current_config,  # 传递当前配置
                save_path=self.save_path
            )
            # self.worker = Worker(name, features, self.config, self.save_path)
            self.worker.finished.connect(self.handle_generation_result)
            self.worker.start()

        except Exception as e:
            self.progress.close()
            logging.error(f"生成错误：{str(e)}")
            self.closeEvent(e)
            QMessageBox.critical(
                self, "系统错误",
                f"发生未知错误：\n{str(e)}",
                buttons=QMessageBox.Ok
            )

    def on_cancel_clicked(self, button):
        """取消按钮点击处理"""
        self.cancel_generation()
        

    def start_close_animation(self):
        """启动关闭动画"""
        from PyQt5.QtCore import QPropertyAnimation
        
        self.animation = QPropertyAnimation(self.progress, b"windowOpacity")
        self.animation.setDuration(300)  # 300ms动画
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(lambda: self.progress.deleteLater())
        self.animation.start()

    def handle_generation_result(self, error_msg, content, save_path, success):
        """处理生成完成信号"""
        try:
            self.start_close_animation()
            
            # 处理生成结果
            if success:
                self.current_file = save_path
                self.statusBar().showMessage(f"文档已保存至：{save_path}", 5000)
                
                # 显示成功弹窗
                success_box = QMessageBox(self)
                success_box.setWindowTitle("生成成功")
                success_box.setText(f"文件已保存到：\n{save_path}")
                success_box.setIcon(QMessageBox.Information)
                success_box.exec_()
                
                # 自动打开文件
                if os.path.exists(save_path):
                    os.startfile(save_path)
            else:
                # 显示错误详情
                error_box = QMessageBox(self)
                error_box.setWindowTitle("生成失败")
                error_box.setText(f"错误信息：\n{error_msg}")
                error_box.setIcon(QMessageBox.Critical)
                error_box.exec_()
                
        except Exception as e:
            logging.error(f"结果处理异常: {str(e)}")
            QMessageBox.critical(
                self, 
                "系统错误", 
                f"结果处理失败：{str(e)}"
            )

    def closeEvent(self, event):
        """窗口关闭时安全终止线程"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)  # 等待2秒
        event.accept()

    def on_generate_finish(self, result, success, progress):
        self.movie.stop()
        progress.close()
        
        if success:
            logging.info(f"专利文档生成成功")
        else:
            QMessageBox.critical(self, "错误", f"生成失败: {result}")

        
        

    def open_file(self):
        """打开生成的文件"""
        if hasattr(self, 'current_file') and os.path.exists(self.current_file):
            os.startfile(self.current_file)
        else:
            QMessageBox.warning(self, "文件不存在", "请先生成文档或选择有效文件")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatentApp()
    window.show()
    sys.exit(app.exec_())
