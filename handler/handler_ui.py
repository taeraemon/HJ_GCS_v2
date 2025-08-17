from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtWidgets import QWidget
import pyqtgraph as pg
import os
import time

from utils.data_types import DataVehicle

# TODO : plot clear method



# ===== UI 파일 로딩 =====
UI_PATH = os.path.join(os.path.dirname(__file__), "../GCS.ui")
form_class = uic.loadUiType(UI_PATH)[0]

# ===== UI 핸들러 클래스 =====
class HandlerUI(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.setFixedSize(1920, 1080)

        self.controller = None    # CoreController 연결용
        self._connect_ui_events() # 버튼 클릭 등 이벤트 연결
        self.refresh_umb_ports()  # 프로그램 시작 시 1회 호출
        self.refresh_tlm_ports()  # TLM 포트 목록 갱신

    # ===== 컨트롤러 연결 함수 =====
    def set_controller(self, controller):
        self.controller = controller

    # ===== UI 이벤트 연결 함수 (내부용) =====
    def _connect_ui_events(self):
        self.PB_UMB_SER_CONN.clicked.connect(self.on_umb_serial_connect_clicked)
        self.PB_UMB_SER_REFRESH.clicked.connect(self.refresh_umb_ports)
        self.PB_TLM_SER_CONN.clicked.connect(self.on_tlm_serial_connect_clicked)
        self.PB_TLM_SER_REFRESH.clicked.connect(self.refresh_tlm_ports)
        
        # Source 버튼 클릭 이벤트 연결
        self.PB_UMB_SOURCE.clicked.connect(self.on_umb_source_clicked)
        self.PB_TLM_SOURCE.clicked.connect(self.on_tlm_source_clicked)

        # 버튼 초기 상태 설정
        self.PB_UMB_SER_CONN.setCheckable(True)
        self.PB_TLM_SER_CONN.setCheckable(True)
        
        # 초기 상태에서 UMB Source 버튼이 선택됨
        self.PB_UMB_SOURCE.setChecked(True)
        self.PB_TLM_SOURCE.setChecked(False)

    # ===== UMB 시리얼 연결 처리 =====
    def on_umb_serial_connect_clicked(self):
        if self.controller:
            if self.PB_UMB_SER_CONN.isChecked():
                port = self.CB_UMB_SER_PORT.currentData()
                baud = int(self.LE_UMB_SER_BAUD.text())
                success = self.controller.umb_handler.connect_serial(port, baud)
                if not success:
                    self.PB_UMB_SER_CONN.setChecked(False)
            else:
                self.controller.umb_handler.connect_serial("", 0)  # 연결 해제

    # ===== TLM 시리얼 연결 처리 =====
    def on_tlm_serial_connect_clicked(self):
        if self.controller:
            if self.PB_TLM_SER_CONN.isChecked():
                port = self.CB_TLM_SER_PORT.currentData()
                baud = int(self.LE_TLM_SER_BAUD.text())
                success = self.controller.tlm_handler.connect_serial(port, baud)
                if not success:
                    self.PB_TLM_SER_CONN.setChecked(False)
            else:
                self.controller.tlm_handler.connect_serial("", 0)  # 연결 해제

    # ===== UMB 시리얼 포트 목록 갱신 =====
    def refresh_umb_ports(self):
        self.CB_UMB_SER_PORT.clear()
        port_list = QSerialPortInfo.availablePorts()
        for port in port_list:
            self.CB_UMB_SER_PORT.addItem(f"{port.portName()} - {port.description()}", port.portName())
        if not port_list:
            self.CB_UMB_SER_PORT.addItem("No Ports")

    # ===== TLM 시리얼 포트 목록 갱신 =====
    def refresh_tlm_ports(self):
        self.CB_TLM_SER_PORT.clear()
        port_list = QSerialPortInfo.availablePorts()
        for port in port_list:
            self.CB_TLM_SER_PORT.addItem(f"{port.portName()} - {port.description()}", port.portName())
        if not port_list:
            self.CB_TLM_SER_PORT.addItem("No Ports")

    # ===== UMB/TLM 소스 선택 버튼 처리 =====
    def on_umb_source_clicked(self):
        # UMB Source 버튼이 클릭되었을 때
        is_checked = self.PB_UMB_SOURCE.isChecked()
        if is_checked:
            # UMB가 선택되면 TLM은 해제
            self.PB_TLM_SOURCE.setChecked(False)
            # 컨트롤러에 액티브 소스 변경 알림
            if self.controller:
                self.controller.set_active_source('UMB')
        else:
            # UMB가 해제되면 TLM 선택
            self.PB_TLM_SOURCE.setChecked(True)
            # 컨트롤러에 액티브 소스 변경 알림
            if self.controller:
                self.controller.set_active_source('TLM')
    
    def on_tlm_source_clicked(self):
        # TLM Source 버튼이 클릭되었을 때
        is_checked = self.PB_TLM_SOURCE.isChecked()
        if is_checked:
            # TLM이 선택되면 UMB는 해제
            self.PB_UMB_SOURCE.setChecked(False)
            # 컨트롤러에 액티브 소스 변경 알림
            if self.controller:
                self.controller.set_active_source('TLM')
        else:
            # TLM이 해제되면 UMB 선택
            self.PB_UMB_SOURCE.setChecked(True)
            # 컨트롤러에 액티브 소스 변경 알림
            if self.controller:
                self.controller.set_active_source('UMB')



class HandlerPlot:
    def __init__(self, plot_widget, title, unit=None, window=500, data_field=None):
        self.window = window
        self.data_field = data_field

        self.plot_widget = plot_widget
        self.plot_widget.setBackground('w')

        self.axis_left = pg.AxisItem(orientation='left')
        self.axis_left.setLabel(title, units=unit)
        self.axis_left.enableAutoSIPrefix(False)

        self.plot_widget.setAxisItems({'left': self.axis_left})
        self.plot_widget.setLabel('bottom', 'Samples')
        self.plot_widget.getAxis('bottom').setStyle(showValues=False)

        # self.plot_widget.showGrid(x=True, y=True)
        # self.plot_widget.setYRange(-45, 45)

        self.curve = self.plot_widget.plot(pen='b')

        # class 내부 초기화용
        self._last_plot_time = time.time()  # 처음엔 대충 현재시간

    def update_plot_from_history(self, data_list: list[DataVehicle]):
        # 최근 100개만 사용
        recent_data = data_list[-self.window:]

        # 타이틀에 따라 해당 속성 추출
        y_data = [getattr(d, self.data_field) for d in recent_data]

        x_data = list(range(len(y_data)))

        self.curve.setData(x_data, y_data)



class HandlerPlotGroup:
    def __init__(self, ui: QWidget):
        self.handlers = {
            "ir": HandlerPlot(ui.PLOT_IMU_R, "Roll",  "deg", data_field="ir"),
            "ip": HandlerPlot(ui.PLOT_IMU_P, "Pitch", "deg", data_field="ip"),
            "iy": HandlerPlot(ui.PLOT_IMU_Y, "Yaw",   "deg", data_field="iy"),

            # "imu_gyr_x": HandlerPlot(ui.PLOT_IMU_GYR_X, "Gyro X", "rad/s", data_field="imu_gyr_x"),
            # "imu_gyr_y": HandlerPlot(ui.PLOT_IMU_GYR_Y, "Gyro Y", "rad/s", data_field="imu_gyr_y"),
            # "imu_gyr_z": HandlerPlot(ui.PLOT_IMU_GYR_Z, "Gyro Z", "rad/s", data_field="imu_gyr_z"),

            # "imu_acc_x": HandlerPlot(ui.PLOT_IMU_ACC_X, "Acc X", "m/s²", data_field="imu_acc_x"),
            # "imu_acc_y": HandlerPlot(ui.PLOT_IMU_ACC_Y, "Acc Y", "m/s²", data_field="imu_acc_y"),
            # "imu_acc_z": HandlerPlot(ui.PLOT_IMU_ACC_Z, "Acc Z", "m/s²", data_field="imu_acc_z"),
        }

    def update_plot_from_history_all(self, data_list: list[DataVehicle]):
        self.handlers["ir"].update_plot_from_history(data_list)
        self.handlers["ip"].update_plot_from_history(data_list)
        self.handlers["iy"].update_plot_from_history(data_list)

        # self.handlers["imu_gyr_x"].update_plot_from_history(data_list)
        # self.handlers["imu_gyr_y"].update_plot_from_history(data_list)
        # self.handlers["imu_gyr_z"].update_plot_from_history(data_list)

        # self.handlers["imu_acc_x"].update_plot_from_history(data_list)
        # self.handlers["imu_acc_y"].update_plot_from_history(data_list)
        # self.handlers["imu_acc_z"].update_plot_from_history(data_list)



class HandlerLabelGroup:
    def __init__(self, ui: QWidget):
        self.handlers = {
            "LB_PNID_VA_1": HandlerLabel(ui.LB_PNID_VA_1, "{:.2f}"),
            "LB_PNID_VA_2": HandlerLabel(ui.LB_PNID_VA_2, "{:.2f}"),
            "LB_PNID_VA_3": HandlerLabel(ui.LB_PNID_VA_3, "{:.2f}"),
            "LB_PNID_VA_4": HandlerLabel(ui.LB_PNID_VA_4, "{:.2f}"),
            "LB_PNID_VA_5": HandlerLabel(ui.LB_PNID_VA_5, "{:.2f}"),
            "LB_PNID_VA_6": HandlerLabel(ui.LB_PNID_VA_6, "{:.2f}"),
            "LB_PNID_VA_7": HandlerLabel(ui.LB_PNID_VA_7, "{:.2f}"),
            "LB_PNID_VA_8": HandlerLabel(ui.LB_PNID_VA_8, "{:.2f}"),

            "LB_PNID_TC_1": HandlerLabel(ui.LB_PNID_TC_1, "{:.2f}"),
            "LB_PNID_TC_2": HandlerLabel(ui.LB_PNID_TC_2, "{:.2f}"),
            "LB_PNID_TC_3": HandlerLabel(ui.LB_PNID_TC_3, "{:.2f}"),
            "LB_PNID_TC_4": HandlerLabel(ui.LB_PNID_TC_4, "{:.2f}"),
            "LB_PNID_TC_5": HandlerLabel(ui.LB_PNID_TC_5, "{:.2f}"),
            "LB_PNID_TC_6": HandlerLabel(ui.LB_PNID_TC_6, "{:.2f}"),
        }

    def update_all(self, data: DataVehicle):
        # Update QLabel values based on data.va
        for i, value in enumerate(data.va):
            label_name = f"LB_PNID_VA_{i+1}"
            if label_name in self.handlers:
                self.handlers[label_name].update(value)

        # Update QLabel values based on data.tc
        for i, value in enumerate(data.tc):
            label_name = f"LB_PNID_TC_{i+1}"
            if label_name in self.handlers:
                self.handlers[label_name].update(value)



class HandlerLabel:
    def __init__(self, label_widget, fmt="{:}"):
        """
        label_widget: QLabel 인스턴스
        fmt: 출력 포맷 (예: "{:.2f}°", "{:.3f} m", "{} sats")
        """
        self.label = label_widget
        self.fmt = fmt

    def update(self, value):
        """
        QLabel에 값을 포맷하여 출력
        """
        try:
            self.label.setText(self.fmt.format(value))
        except Exception as e:
            self.label.setText("ERR")
