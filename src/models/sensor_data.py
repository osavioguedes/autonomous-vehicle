from dataclasses import dataclass
from typing import Optional

@dataclass
class SensorData:

    position_x: float
    position_y: float
    theta: float
    velocity: float
    
    temperature: float
    electrical_fault: bool
    hydraulic_fault: bool
    
    timestamp: Optional[float] = None

@dataclass
class ActuatorData:
    acceleration: float
    steering: float
    
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        self.acceleration = max(-1.0, min(1.0, self.acceleration))
        self.steering = max(-1.0, min(1.0, self.steering))

@dataclass
class FilteredSensorData:
    position_x: float
    position_y: float
    theta: float
    velocity: float
    temperature: float
    electrical_fault: bool
    hydraulic_fault: bool
    timestamp: float
    
    @classmethod
    def from_sensor_data(cls, sensor_data: SensorData):
        return cls(
            position_x=sensor_data.position_x,
            position_y=sensor_data.position_y,
            theta=sensor_data.theta,
            velocity=sensor_data.velocity,
            temperature=sensor_data.temperature,
            electrical_fault=sensor_data.electrical_fault,
            hydraulic_fault=sensor_data.hydraulic_fault,
            timestamp=sensor_data.timestamp or 0.0
        )
