from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json

@dataclass
class LogEntry:
    timestamp: float
    truck_id: int
    status: str
    mode: str
    position_x: float
    position_y: float
    theta: float
    velocity: float
    event_description: str
    
    temperature: float = 0.0
    electrical_fault: bool = False
    hydraulic_fault: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    def to_csv_line(self) -> str:
        return (f"{self.timestamp:.3f},"
                f"{self.truck_id},"
                f"{self.status},"
                f"{self.mode},"
                f"{self.position_x:.2f},"
                f"{self.position_y:.2f},"
                f"{self.theta:.4f},"
                f"{self.velocity:.2f},"
                f"{self.temperature:.1f},"
                f"{int(self.electrical_fault)},"
                f"{int(self.hydraulic_fault)},"
                f'"{self.event_description}"\n')
    
    @staticmethod
    def csv_header() -> str:
        return ("timestamp,truck_id,status,mode,position_x,position_y,theta,"
                "velocity,temperature,electrical_fault,hydraulic_fault,"
                "event_description\n")
    
    def get_datetime_str(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    def __str__(self):
        return (f"[{self.get_datetime_str()}] Truck {self.truck_id} - "
                f"{self.status}/{self.mode} - "
                f"Pos({self.position_x:.1f}, {self.position_y:.1f}) - "
                f"{self.event_description}")
