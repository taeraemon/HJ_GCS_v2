from PyQt5.QtCore import QObject, QTimer
from datetime import datetime
import csv
import os

from utils.data_types import DataVehicle, ReceivedPacket



class HandlerLog(QObject):
    def __init__(self):
        super().__init__()
        self.is_logging = False
        self.log_files = {
            'UMB': None,
            'TLM': None
        }
        self.log_writers = {
            'UMB': None,
            'TLM': None
        }
        
        # 버퍼 관련 변수
        self.buffers = {
            'UMB': [],
            'TLM': []
        }
        self.buffer_size = 100  # 버퍼 크기 (100개 데이터)
        self.flush_timer = QTimer()
        self.flush_timer.timeout.connect(self._flush_buffers)
        self.flush_interval = 1000  # 1초마다 버퍼 비우기
        
        # 각 소스별 CSV 헤더 정의
        self.headers = {
            'UMB': [
                'timestamp',
                'boot_time',
                'temp',
                'voltage',
                'sv1', 'sv2', 'sv3', 'sv4', 'sv5', 'sv6', 'sv7', 'sv8',
                'mv1', 'mv2', 'mv3', 'mv4',
                'va1', 'va2', 'va3', 'va4', 'va5', 'va6', 'va7', 'va8',
                'tc1', 'tc2', 'tc3', 'tc4', 'tc5', 'tc6',
                'ir',
                'ip',
                'iy',
                'fault'
            ],
            'TLM': [
                'timestamp',
                'boot_time',
                'temp',
                'voltage',
                'sv1', 'sv2', 'sv3', 'sv4', 'sv5', 'sv6', 'sv7', 'sv8',
                'mv1', 'mv2', 'mv3', 'mv4',
                'va1', 'va2', 'va3', 'va4', 'va5', 'va6', 'va7', 'va8',
                'tc1', 'tc2', 'tc3', 'tc4', 'tc5', 'tc6',
                'ir',
                'ip',
                'iy',
                'fault'
            ]
        }
        
        # 로그 디렉토리 생성
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def start_logging(self, connected_sources):
        """로깅 시작"""
        if self.is_logging:
            return False

        self.is_logging = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 연결된 소스에 대해서만 로그 파일 생성
        for source in connected_sources:
            filename = os.path.join(self.log_dir, f"{timestamp}_{source}.csv")
            self.log_files[source] = open(filename, 'w', newline='')
            self.log_writers[source] = csv.writer(self.log_files[source])
            
            # 소스별 헤더 작성
            if source in self.headers and self.headers[source]:
                self.log_writers[source].writerow(self.headers[source])
            else:
                # TODO: GSE 헤더가 정의되지 않은 경우 처리
                self._append_debug_message(f"[LOG] Warning: No header defined for {source}")
            
            # 버퍼 초기화
            self.buffers[source] = []
        
        # 버퍼 플러시 타이머 시작
        self.flush_timer.start(self.flush_interval)
        
        return True

    def stop_logging(self):
        """로깅 중지"""
        if not self.is_logging:
            return False

        # 버퍼 플러시 타이머 중지
        self.flush_timer.stop()
        
        # 남은 데이터 모두 파일에 쓰기
        self._flush_buffers(force=True)
        
        self.is_logging = False
        
        # 모든 로그 파일 닫기
        for source in ['UMB', 'TLM']:
            if self.log_files[source]:
                self.log_files[source].close()
                self.log_files[source] = None
                self.log_writers[source] = None
        
        return True

    def append(self, packet: ReceivedPacket, source: str):
        """데이터를 버퍼에 추가"""
        if not self.is_logging or source not in self.log_writers or not self.log_writers[source]:
            return

        # 소스별 데이터 처리
        if source in ['UMB', 'TLM']:
            # UMB와 TLM은 동일한 DataVehicle 구조 사용
            self._append_vehicle_data(packet, source)

    def _append_vehicle_data(self, packet: ReceivedPacket, source: str):
        """Vehicle 데이터를 버퍼에 추가"""
        data = packet.data
        self.buffers[source].append([
            packet.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
            data.boot_time,
            data.temp,
            data.voltage,
            data.sv[0], data.sv[1], data.sv[2], data.sv[3], data.sv[4], data.sv[5], data.sv[6], data.sv[7],
            data.mv[0], data.mv[1], data.mv[2], data.mv[3],
            data.va[0], data.va[1], data.va[2], data.va[3], data.va[4], data.va[5], data.va[6], data.va[7],
            data.tc[0], data.tc[1], data.tc[2], data.tc[3], data.tc[4], data.tc[5],
            data.ir,
            data.ip,
            data.iy,
            data.fault[0], data.fault[1], data.fault[2], data.fault[3], data.fault[4]
        ])

        # 버퍼가 가득 차면 파일에 쓰기
        if len(self.buffers[source]) >= self.buffer_size:
            self._flush_buffer(source)

    def _flush_buffer(self, source):
        """특정 소스의 버퍼를 파일에 쓰기"""
        if not self.buffers[source]:
            return

        # 버퍼의 모든 데이터를 파일에 쓰기
        self.log_writers[source].writerows(self.buffers[source])
        # 버퍼 비우기
        self.buffers[source] = []

    def _flush_buffers(self, force=False):
        """모든 버퍼를 파일에 쓰기"""
        for source in self.buffers:
            if force or len(self.buffers[source]) > 0:
                self._flush_buffer(source)

    def _append_debug_message(self, message):
        """디버그 메시지 출력 (TODO: 실제 구현 필요)"""
        print(message)  # 임시로 콘솔에 출력
