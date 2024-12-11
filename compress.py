import sys
from PyQt5.QtWidgets import (QApplication,QMainWindow,QPushButton,QFileDialog,QMessageBox)
from PyQt5.QtWidgets import QWidget,QLabel,QVBoxLayout,QHBoxLayout,QSpinBox,QDoubleSpinBox
from PyQt5.QtCore import Qt,QThread,pyqtSignal
import cv2
import os
import numpy as np
class CompressThread(QThread):
  progress_signal=pyqtSignal(str)
  finished_signal=pyqtSignal()
  def __init__(self,input_dir,output_dir,quality,scale):
    super().__init__()
    self.input_dir=input_dir
    self.output_dir=output_dir
    self.quality=quality
    self.scale=scale
  def run(self):
    self.batch_compress(self.input_dir,self.output_dir,self.quality,self.scale)
    self.finished_signal.emit()
  def batch_compress(self,input_dir,output_dir,quality,scale):
    MAX_SIZE_MB=5
    MAX_SIZE_BYTES=MAX_SIZE_MB*1024*1024
    try:
      if not os.path.exists(output_dir):
        os.makedirs(output_dir)
      for file in os.listdir(input_dir):
        input_path=os.path.join(input_dir,file)
        safe_filename=file.encode('utf-8').decode('utf-8')
        output_path=os.path.join(output_dir,os.path.splitext(safe_filename)[0])
        if os.path.isdir(input_path):
          self.batch_compress(input_path,output_path,quality,scale)
        elif file.lower().endswith(('.jpg','.jpeg','.png','.dng')):
          try: 
            output_path=os.path.join(output_dir,os.path.splitext(safe_filename)[0]+'.png')
            img=cv2.imdecode(np.fromfile(input_path,dtype=np.uint8),cv2.IMREAD_COLOR)
            if img is None:
              print(f"无法读取文件{file}")
              continue
            width=int(img.shape[1]*scale)
            height=int(img.shape[0]*scale)
            resized_img=cv2.resize(img,(width,height))
            _,encoded_img=cv2.imencode('.jpg',resized_img,[int(cv2.IMWRITE_JPEG_QUALITY),quality])
            os.makedirs(os.path.dirname(output_path),exist_ok=True)
            with open(output_path,'wb') as f:
              f.write(encoded_img.tobytes())
            print(f"成功处理图片:{file}")
            print(f"原始尺寸：{img.shape[1]}x{img.shape[0]}")
            print(f"压缩尺寸：{width}x{height}")
          except Exception as e:
            print(f"处理文件{file}时发生错误：{e}")
    except Exception as e:
      print(f"发生错误:{str(e)}")

class ImageCompressorUI(QMainWindow):
  def __init__(self):
    super().__init__()
    self.initUI()
  def initUI(self):
    self.setWindowTitle('图片压缩工具')
    self.setGeometry(300,300,600,400) 
    central_widget=QWidget()
    self.setCentralWidget(central_widget)
    layout=QVBoxLayout()
    input_layout=QHBoxLayout()
    self.input_label=QLabel('输入文件夹:',self)
    self.input_path=QLabel('未选择',self)
    self.input_btn=QPushButton('选择文件夹',self)
    self.input_btn.clicked.connect(self.select_input_folder)
    input_layout.addWidget(self.input_label)
    input_layout.addWidget(self.input_path)
    input_layout.addWidget(self.input_btn)
    
    output_layout=QHBoxLayout()
    self.output_label=QLabel('输出文件夹:',self)
    self.output_path=QLabel('未选择',self)
    self.output_btn=QPushButton('选择文件夹',self)
    self.output_btn.clicked.connect(self.select_output_folder)
    output_layout.addWidget(self.output_label)
    output_layout.addWidget(self.output_path)
    output_layout.addWidget(self.output_btn)
    
    params_layout=QHBoxLayout()
    self.quality_label=QLabel('压缩质量:',self)
    self.quality_spin=QSpinBox(self)
    self.quality_spin.setRange(1,100)
    self.quality_spin.setValue(80)
    self.scale_label=QLabel('压缩比例:',self)
    self.scale_spin=QDoubleSpinBox(self)
    self.scale_spin.setRange(0.1,1.0)
    self.scale_spin.setValue(0.5)

    params_layout.addWidget(self.quality_label)
    params_layout.addWidget(self.quality_spin)
    params_layout.addWidget(self.scale_label)
    params_layout.addWidget(self.scale_spin)

    self.start_btn=QPushButton('开始压缩',self)
    self.start_btn.clicked.connect(self.start_compression)
    self.start_btn.setFixedHeight(30)
    
    self.log_label=QLabel('日志:',self)
    self.log_output=QLabel('等待开始...',self)
    self.log_output.setAlignment(Qt.AlignLeft|Qt.AlignTop)
    self.log_output.setWordWrap(True)
    self.log_output.setFixedHeight(100)
    self.log_output.setStyleSheet("""QLabel{
      background-color: #f0f0f0;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 5px;
    }""")
    layout.addStretch(1)
    layout.addWidget(self.start_btn)
    layout.addStretch(1)
    layout.addWidget(self.log_label)
    layout.addWidget(self.log_output)
    central_widget.setLayout(layout)

    layout.addLayout(input_layout)
    layout.addLayout(output_layout)
    layout.addLayout(params_layout)
    layout.addWidget(self.start_btn)
    layout.addWidget(self.log_label)
    layout.addWidget(self.log_output)

  def select_input_folder(self):
      folder_dialog=QFileDialog.getExistingDirectory(self,'选择输入文件夹','.')
      if folder_dialog:
          self.input_path.setText(folder_dialog)
  def select_output_folder(self):
      folder_dialog=QFileDialog.getExistingDirectory(self,'选择输出文件夹','.')
      if folder_dialog:
          self.output_path.setText(folder_dialog)
  def start_compression(self):
      input_dir=self.input_path.text()
      output_dir=self.output_path.text()
      quality=self.quality_spin.value()
      scale=self.scale_spin.value()
      self.log_output.setText('开始压缩...')
      self.thread=CompressThread(input_dir,output_dir,quality,scale)
      self.thread.progress_signal.connect(self.update_log)
      self.thread.finished_signal.connect(self.compression_finished)
      self.thread.start()
  def update_log(self,message):
      self.log_output.append(message)
  def compression_finished(self):
      self.log_output.setText('压缩完成!')  

if __name__=='__main__':
    app=QApplication(sys.argv)
    window=ImageCompressorUI()
    window.show()
    sys.exit(app.exec_())


