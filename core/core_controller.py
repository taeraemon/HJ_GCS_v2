from PyQt5.QtCore import QTimer
from datetime import datetime
import time

from handler.handler_button import HandlerButton, HandlerButtonGroup
from handler.handler_ui import HandlerUI
from handler.handler_comm import HandlerComm
from handler.handler_log import HandlerLog
from handler.handler_ui import HandlerPlot, HandlerPlotGroup, HandlerLabel, HandlerLabelGroup
from utils.data_types import DataVehicle, ReceivedPacket



class CoreController:
    def __init__(self):
        # ============================
        # UI 및 핸들러 초기화
        # ============================
        self.ui = HandlerUI()

        # Controller 초기화 부분 예시
        self.umb_handler = HandlerComm(
            self,
            source="UMB",
            btn_connect=self.ui.PB_UMB_SER_CONN,
            label_rate=self.ui.LB_UMB_RATE,
        )

        self.tlm_handler = HandlerComm(
            self,
            source="TLM",
            btn_connect=self.ui.PB_TLM_SER_CONN,
            label_rate=self.ui.LB_TLM_RATE,
        )
        self.log_handler = HandlerLog()

        # 플롯 핸들러 (Qt Designer에서 설정한 objectName 기준)
        self.plot_group = HandlerPlotGroup(self.ui)
        self.label_group = HandlerLabelGroup(self.ui)

        # 버튼 핸들러 (솔레노이드 밸브 관련)
        self.button_group = HandlerButtonGroup(self.ui, comm=self.umb_handler)

        # UI와 컨트롤러 연결
        self.ui.set_controller(self)

        # ============================
        # 데이터 저장소 및 타이머
        # ============================
        # 마지막 수신된 데이터 저장
        self.last_umb_data = None
        self.last_tlm_data = None
        self.last_vehicle_data = None

        # 모든 데이터를 각각 저장
        self.umb_data_history = []  # UMB 데이터 저장 리스트
        self.tlm_data_history = []  # TLM 데이터 저장 리스트
        self.vehicle_data_history = []  # 통합된 데이터 저장 리스트 (GUI 업데이트용)
        self.last_plot_index = 0        # 마지막으로 plot에 반영한 데이터 인덱스

        # 데이터 소스 관리 변수 - 기본값을 'UMB'로 설정
        self.active_source = 'UMB'
        
        # 플롯 업데이트 타이머 설정 (10Hz)
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(100)  # 100ms = 10Hz

        # 로깅 버튼 이벤트 연결
        self.ui.PB_LOG.clicked.connect(self.on_log_button_clicked)

    def start(self):
        """UI 실행"""
        self.ui.show()

    def on_data_received(self, packet: ReceivedPacket, source: str):
        if source == 'UMB':
            self.last_umb_data = packet.data
            self.umb_data_history.append(packet.data)
            if len(self.umb_data_history) > 1000:
                self.umb_data_history.pop(0)
        elif source == 'TLM':
            self.last_tlm_data = packet.data
            self.tlm_data_history.append(packet.data)
            if len(self.tlm_data_history) > 1000:
                self.tlm_data_history.pop(0)

        self._log_data(packet, source)

        if self.active_source == source:
            self.process_vehicle_data(packet.data)

    def on_log_button_clicked(self):
        """로깅 버튼 클릭 이벤트 처리"""
        if not self.log_handler.is_logging:
            # 연결된 소스 목록 생성
            connected_sources = []
            if self.umb_handler.serial_connected:
                connected_sources.append('UMB')
            if self.tlm_handler.serial_connected:
                connected_sources.append('TLM')

            # 연결된 소스가 없으면 로깅 시작하지 않음
            if not connected_sources:
                self._append_debug_message("[CORE] No connected sources to log")
                return

            # 로깅 시작
            if self.log_handler.start_logging(connected_sources):
                self.ui.PB_LOG.setText("Logging...")
                self._append_debug_message(f"[CORE] Logging started for sources: {', '.join(connected_sources)}")
        else:
            # 로깅 중지
            if self.log_handler.stop_logging():
                self.ui.PB_LOG.setText("LOG")
                self._append_debug_message("[CORE] Logging stopped")

    def _log_data(self, packet: ReceivedPacket, source: str):
        """
        모든 데이터를 로깅하는 내부 메서드
        """
        self.log_handler.append(packet, source)
    
    def process_vehicle_data(self, vehicle_data):
        """
        통합된 DataVehicle 처리 - 데이터 관리
        수신된 데이터를 vehicle_data_history에 저장하는 역할
        실제 GUI 업데이트는 타이머에 의해 update_plots에서 처리됨
        """
        # 마지막 데이터 저장
        self.last_vehicle_data = vehicle_data
        
        # 데이터 저장 (최대 1000개 유지)
        self.vehicle_data_history.append(vehicle_data)
        if len(self.vehicle_data_history) > 1000:
            self.vehicle_data_history.pop(0)
            self.last_plot_index = max(0, self.last_plot_index - 1)

    def update_plots(self):
        """
        10Hz 타이머에 의해 주기적으로 호출됨
        - 새로운 데이터를 모두 plot에 반영
        - 상태 표시창 업데이트
        마지막으로 plot에 반영된 이후의 모든 데이터를 순차적으로 시각화
        """
        total_data = len(self.vehicle_data_history)
        if self.last_plot_index >= total_data:
            return

        self.plot_group.update_plot_from_history_all(self.vehicle_data_history)
        self.label_group.update_all(self.last_vehicle_data)
        self.button_group.update_all(self.last_vehicle_data)

        if self.last_vehicle_data:
            self.update_status_vehicle(ReceivedPacket(
                data=self.last_vehicle_data,
                timestamp=datetime.now(),
                source=self.active_source
            ), f"{self.active_source} Data")

    def set_active_source(self, source):
        """
        UI 소스 버튼 클릭 시 호출될 메서드
        액티브 소스를 변경하고 UI를 업데이트함
        """
        if source in ['UMB', 'TLM']:
            self.active_source = source
            self._append_debug_message(f"[CORE] Active Source changed to: {source}")
            
            # 마지막 수신된 데이터가 있으면 바로 UI 업데이트
            if source == 'UMB' and self.last_umb_data:
                self.process_vehicle_data(self.last_umb_data)
            elif source == 'TLM' and self.last_tlm_data:
                self.process_vehicle_data(self.last_tlm_data)

    def _append_debug_message(self, line):
        """
        TE_GCS_DEBUG에 한 줄씩 출력 (최대 100줄 유지)
        """
        text_edit = self.ui.TE_GCS_DEBUG
        existing_text = text_edit.toPlainText()
        lines = existing_text.split('\n')

        if len(lines) >= 100:
            lines = lines[-99:]

        curr_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        lines.append(f"{curr_time} : {line}")

        text_edit.setPlainText('\n'.join(lines).strip())
        text_edit.verticalScrollBar().setValue(text_edit.verticalScrollBar().maximum())

    def update_status_vehicle(self, packet: ReceivedPacket, message: str):
        """
        TE_VEHICLE_STATUS에 차량 상태 데이터를 JSON 형식으로 표시
        이전 내용을 지우고 현재 상태만 표시함
        """
        text_edit = self.ui.TE_VEHICLE_STATUS
        
        # 현재 스크롤바 위치 저장
        scrollbar = text_edit.verticalScrollBar()
        scroll_position = scrollbar.value()
        
        # 현재 시간 포맷
        curr_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # JSON 형식으로 데이터 표시
        json_like_data = (
            f"[{curr_time}] [CORE] {message}:\n"
            f"  timestamp: {packet.timestamp}\n"
            f"  source: {packet.source}\n"
            
            f"  boot time: {packet.data.boot_time}ms\n"
            f"  temp: {packet.data.temp}°C\n"
            f"  voltage: {packet.data.voltage}V\n"
            f"  sv: {packet.data.sv}\n"
            f"  mv: {packet.data.mv}\n"
            f"  va: {packet.data.va}\n"
            f"  tc: {packet.data.tc}\n"
            f"  ir: {packet.data.ir:.1f}deg\n"
            f"  ip: {packet.data.ip:.1f}deg\n"
            f"  iy: {packet.data.iy:.1f}deg\n"
            f"  fault: {packet.data.fault}\n"
        )
        
        # 이전 내용을 지우고 현재 상태만 표시
        text_edit.setPlainText(json_like_data)
        
        # 사용자가 수동으로 스크롤했으면 그 위치를 유지, 아니면 맨 위로 스크롤
        if scroll_position > 0:
            scrollbar.setValue(scroll_position)
