import math
from src.embedded.control.pid_controller import PIDController

class AngularController:
    
    def __init__(self, 
                 kp: float = 1.0, 
                 ki: float = 0.05, 
                 kd: float = 0.2,
                 max_steering: float = 1.0):
        self.pid = PIDController(
            kp=kp,
            ki=ki,
            kd=kd,
            output_min=-max_steering,
            output_max=max_steering,
            sample_time=0.05
        )
        self._enabled = False
    
    def compute(self, current_angle: float, target_angle: float) -> float:
        if not self._enabled:
            return 0.0
        
        error = self._normalize_angle(target_angle - current_angle)
        
        adjusted_current = 0.0
        adjusted_target = error
        
        return self.pid.compute(adjusted_current, adjusted_target)
    
    def _normalize_angle(self, angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))
    
    def enable(self, current_angle: float) -> None:
        self._enabled = True
        self.pid.enable(0.0)
    
    def disable(self) -> None:
        self._enabled = False
        self.pid.disable()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def reset(self) -> None:
        self.pid.reset()
