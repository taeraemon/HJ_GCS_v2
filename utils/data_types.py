from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

@dataclass
class DataVehicle:
    boot_time: int = 0.0
    temp:      float = 0.0
    voltage:   float = 0.0

    sv: List[int]   = field(default_factory=lambda: [-1]   * 8)
    mv: List[float] = field(default_factory=lambda: [-1.0] * 4)
    va: List[float] = field(default_factory=lambda: [-1.0] * 8)
    tc: List[float] = field(default_factory=lambda: [-1.0] * 6)

    ir: float = 0.0
    ip: float = 0.0
    iy: float = 0.0

    fault: List[int] = field(default_factory=lambda: [-1] * 5)

    # TODO : implement another data
    # TODO : optimize data structure

    # igx: float = 0.0
    # igy: float = 0.0
    # igz: float = 0.0
    # iax: float = 0.0
    # iay: float = 0.0
    # iaz: float = 0.0

    # gps_fix_type: int = 0
    # gps_sat: int = 0
    # gps_time: str = ""
    # gps_lat: float = 0.0
    # gps_lon: float = 0.0
    # gps_alt: float = 0.0


@dataclass
class ReceivedPacket:
    data: DataVehicle
    timestamp: datetime
    source: str

def parse_csv_to_vehicle(line: str, source: str) -> ReceivedPacket:
    try:
        parts = line.strip().split(',')
        if len(parts) < 10:
            raise ValueError("Incomplete CSV data")

        data_vehicle = DataVehicle(
            boot_time = int(parts[0]),
            temp      = float(parts[1]),
            voltage   = float(parts[2]),
            sv        = [int(x) for x in parts[3:11]],
            mv        = [float(x) for x in parts[11:15]],
            va        = [float(x) for x in parts[15:23]],
            tc        = [float(x) for x in parts[23:29]],
            ir        = float(parts[29]),
            ip        = float(parts[30]),
            iy        = float(parts[31]),
            fault     = [int(x) for x in parts[32:37]]
        )

        return ReceivedPacket(
            data=data_vehicle,
            timestamp=datetime.now(),
            source=source
        )
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {e}")
