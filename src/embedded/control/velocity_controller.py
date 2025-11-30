from src.embedded.control.pid_controller import PIDController

class VelocityController:
    
    def __init__(self, 
                 kp: float = 0.5, 
                 ki: float = 0.1, 
                 kd: float = 0.05,
                 max_accel: float = 1.0):
        self.pid = PIDController(
            kp=kp,
            ki=ki,
            kd=kd,
            output_min=-max_accel,
            output_max=max_accel,
            sample_time=0.05
        )
        self._enabled = False
    
    def compute(self, current_velocity: float, target_velocity: float) -> float:
        if not self._enabled:
            return 0.0
        
        return self.pid.compute(current_velocity, target_velocity)
    
    def enable(self, current_velocity: float) -> None:
        self._enabled = True
        self.pid.enable(current_velocity)
    
    def disable(self) -> None:
        self._enabled = False
        self.pid.disable()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def reset(self) -> None:
        self.pid.reset()
