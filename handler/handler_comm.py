from PyQt5.QtCore import QIODevice, QObject, QTimer
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime
import json


from utils.data_types import DataVehicle, parse_csv_to_vehicle, ReceivedPacket



class HandlerComm(QObject):
    def __init__(self, controller, *, source: str, btn_connect, label_rate):
        super().__init__()
        self.controller = controller
        self.source = source
        self.btn_connect = btn_connect
        self.label_rate = label_rate

        self.serial_port = QSerialPort()
        self.serial_connected = False
        self.buffer = b""

        # 수신 속도(Hz) 측정
        self.packet_count = 0
        self.last_packet_count = 0
        self.last_update_time = datetime.now()

        self.rate_timer = QTimer()
        self.rate_timer.timeout.connect(self._update_rate)
        self.rate_timer.start(1000)  # 1초 간격

    # ---------- public ----------
    def connect_serial(self, port_name, baudrate):
        """
        시리얼 포트 연결/해제 처리 (토글)
        """
        if not self.serial_connected:
            self.serial_port.setPortName(port_name)
            self.serial_port.setBaudRate(baudrate)
            self.serial_port.setDataBits(QSerialPort.Data8)
            self.serial_port.setParity(QSerialPort.NoParity)
            self.serial_port.setStopBits(QSerialPort.OneStop)
            self.serial_port.setFlowControl(QSerialPort.NoFlowControl)

            if self.serial_port.open(QIODevice.ReadWrite):
                self.serial_connected = True
                self.btn_connect.setText("Connected!")
                self.serial_port.readyRead.connect(self._handle_ready_read)

                # 속도 카운터 초기화
                self.packet_count = 0
                self.last_packet_count = 0
                self.last_update_time = datetime.now()
                return True
            else:
                QMessageBox.critical(self.controller.ui, "Error",
                                     f"Failed to open {self.source} serial port.")
                return False
        else:
            # 이미 연결된 경우 -> 해제
            self.serial_connected = False
            try:
                self.serial_port.readyRead.disconnect(self._handle_ready_read)
            except Exception:
                pass
            self.serial_port.close()
            self.btn_connect.setText("Connect\nSerial")
            self.label_rate.setText("0.0 Hz")
            return False

    # ---------- internal ----------
    def _update_rate(self):
        """
        1초마다 호출되어 데이터 수신 속도를 계산하고 UI에 표시
        """
        if not self.serial_connected:
            self.label_rate.setText("0.0 Hz")
            return

        current_time = datetime.now()
        elapsed = (current_time - self.last_update_time).total_seconds()
        if elapsed <= 0:
            return

        # 지난 1초간 처리된 패킷 수
        delta = self.packet_count - self.last_packet_count
        rate = delta / elapsed
        self.label_rate.setText(f"{rate:.1f} Hz")

        # 다음 계산을 위해 기준 갱신
        self.last_packet_count = self.packet_count
        self.last_update_time = current_time

    def _handle_ready_read(self):
        """
        시리얼 버퍼에 데이터가 있을 때 호출됨
        """
        # line 단위 수신을 전제(송신측에서 \n로 라인 종료)
        while self.serial_port.canReadLine():
            try:
                raw = self.serial_port.readLine()
                # PyQt5 일부 플랫폼에서 readLine()이 QByteArray를 반환
                if hasattr(raw, "data"):
                    raw = raw.data()
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                if ',' in line:
                    self._handle_csv_packet(line)
                else:
                    self._append_debug_message(line)
            except Exception as e:
                self._append_debug_message(f"[{self.source}] Error while reading serial data: {e}")

    def _handle_csv_packet(self, line: str):
        """
        CSV 형식: 예) 1.23,2.34,3.45,...,13.37
        """
        try:
            packet = parse_csv_to_vehicle(line, source=self.source)
            self.packet_count += 1
            # 컨트롤러가 공통 콜백으로 데이터 처리
            self.controller.on_data_received(packet, source=self.source)
        except ValueError as e:
            self._append_debug_message(f"[{self.source}] {e}")
        except Exception as e:
            self._append_debug_message(f"[{self.source}] Unexpected CSV error: {e}")

    def _append_debug_message(self, line: str):
        """
        컨트롤러의 공통 디버그 출력 메서드 호출
        """
        self.controller._append_debug_message(line)

    def send_bytes(self, data: bytes) -> bool:
        """
        시리얼로 raw bytes 전송. (프로토콜/인코딩은 상위에서 결정)
        """
        if not self.serial_connected or not self.serial_port.isOpen():
            self._append_debug_message(f"[{self.source}] Not connected. Cannot send bytes.")
            return False
        try:
            self.serial_port.write(data)
            self.serial_port.flush()
            return True
        except Exception as e:
            self._append_debug_message(f"[{self.source}] Send error: {e}")
            return False

    def send_str(self, s: str, add_newline: bool = True) -> bool:
        return self.send_bytes((s + ("\n" if add_newline else "")).encode("utf-8"))
