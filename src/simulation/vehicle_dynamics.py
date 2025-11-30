import math
from dataclasses import dataclass
from typing import Tuple

@dataclass
class VehicleParameters:
    max_velocity: float = 10.0
    max_angular_velocity: float = 1.0
    tau_velocity: float = 0.5
    tau_angular: float = 0.3
    dt: float = 0.1

class VehicleDynamics:
    
    def __init__(self, params: VehicleParameters = None):
        self.params = params or VehicleParameters()
        
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.velocity = 0.0
        self.angular_velocity = 0.0
    
    def set_position(self, x: float, y: float, theta: float) -> None:
        self.x = x
        self.y = y
        self.theta = theta
    
    def update(self, accel_cmd: float, steer_cmd: float) -> Tuple[float, float, float, float]:
        dt = self.params.dt
        
        accel_cmd = max(-1.0, min(1.0, accel_cmd))
        steer_cmd = max(-1.0, min(1.0, steer_cmd))
        
        target_velocity = accel_cmd * self.params.max_velocity
        target_angular = steer_cmd * self.params.max_angular_velocity
        
        self.velocity += (target_velocity - self.velocity) * dt / self.params.tau_velocity
        self.angular_velocity += (target_angular - self.angular_velocity) * dt / self.params.tau_angular
        
        self.x += self.velocity * math.cos(self.theta) * dt
        self.y += self.velocity * math.sin(self.theta) * dt
        self.theta += self.angular_velocity * dt
        
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        return self.x, self.y, self.theta, self.velocity
    
    def get_state(self) -> Tuple[float, float, float, float]:
        return self.x, self.y, self.theta, self.velocity
    
    def reset(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.velocity = 0.0
        self.angular_velocity = 0.0
    
    def emergency_stop(self) -> None:
        self.velocity = 0.0
        self.angular_velocity = 0.0
