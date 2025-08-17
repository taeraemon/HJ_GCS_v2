from PyQt5.QtWidgets import QWidget, QPushButton

from handler.handler_comm import HandlerComm
from utils.data_types import DataVehicle



class HandlerButtonGroup:
    def __init__(self, ui: QWidget, *, comm: HandlerComm):
        
        self.comm = comm

        self.handlers = {
            "PB_PNID_SV_1": HandlerButton(ui.PB_PNID_SV_1, kind="SV", idx=0, comm=self.comm),
            "PB_PNID_SV_2": HandlerButton(ui.PB_PNID_SV_2, kind="SV", idx=1, comm=self.comm),
            "PB_PNID_SV_3": HandlerButton(ui.PB_PNID_SV_3, kind="SV", idx=2, comm=self.comm),
            "PB_PNID_SV_4": HandlerButton(ui.PB_PNID_SV_4, kind="SV", idx=3, comm=self.comm),
            "PB_PNID_SV_5": HandlerButton(ui.PB_PNID_SV_5, kind="SV", idx=4, comm=self.comm),
            "PB_PNID_SV_6": HandlerButton(ui.PB_PNID_SV_6, kind="SV", idx=5, comm=self.comm),
            "PB_PNID_SV_7": HandlerButton(ui.PB_PNID_SV_7, kind="SV", idx=6, comm=self.comm),
            "PB_PNID_SV_8": HandlerButton(ui.PB_PNID_SV_8, kind="SV", idx=7, comm=self.comm),

            "PB_PNID_MV_1": HandlerButton(ui.PB_PNID_MV_1, kind="MV", idx=0, comm=self.comm),
            "PB_PNID_MV_2": HandlerButton(ui.PB_PNID_MV_2, kind="MV", idx=1, comm=self.comm),
            "PB_PNID_MV_3": HandlerButton(ui.PB_PNID_MV_3, kind="MV", idx=2, comm=self.comm),
            "PB_PNID_MV_4": HandlerButton(ui.PB_PNID_MV_4, kind="MV", idx=3, comm=self.comm),
        }

    def update_all(self, data: DataVehicle):
        # Update QPushButton colors based on data.sv
        for i, state in enumerate(data.sv):
            label_name = f"PB_PNID_SV_{i+1}"
            if label_name in self.handlers:
                self.handlers[label_name].update_state(kind="SV", state=state)
        
        # Update QPushButton colors based on data.mv
        for i, state in enumerate(data.mv):
            label_name = f"PB_PNID_MV_{i+1}"
            if label_name in self.handlers:
                self.handlers[label_name].update_state(kind="MV", state=state)



class HandlerButton:
    def __init__(self, button_widget, *, kind: str, idx: int, comm: HandlerComm):
        """
        button_widget: QPushButton 인스턴스
        """
        self.button = button_widget
        self.kind = kind.upper()
        self.idx = idx
        self.comm = comm

        self.button.setCheckable(True)
        self.button.clicked.connect(self.on_clicked)

    def on_clicked(self):
        if not self.comm.serial_connected:
            return

        if self.kind == "SV":
            next_val = 1 if self.button.isChecked() else 0
            line = f":SV;{self.idx};{next_val}#\n"
            self.comm.send_str(line)

        elif self.kind == "MV":
            next_val = 180 if self.button.isChecked() else 0
            line = f":MV;{self.idx};{next_val}#\n"
            self.comm.send_str(line)

    def update_state(self, kind: str, state: int):
        if kind == "SV":
            """
            QPushButton의 배경색을 상태에 따라 변경
            state: 0이면 빨간색, 1이면 초록색
            """
            color = "green" if state == 1 else "red"
            self.button.setStyleSheet(f"background-color: {color};")
        elif kind == "MV":
            """
            QPushButton의 배경색을 상태에 따라 변경
            state: 90도 이하이면 빨간색, 90도 초과이면 초록색
            """
            color = "red" if state < 90 else "green"
            self.button.setStyleSheet(f"background-color: {color};")
