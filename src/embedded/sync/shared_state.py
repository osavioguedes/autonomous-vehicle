import threading
import copy
from src.models.vehicle_state import VehicleState, OperationMode, VehicleStatus

class SharedState:
    
    def __init__(self, truck_id: int):
        self._state = VehicleState(truck_id=truck_id)
        self._lock = threading.Lock()
    
    def get_state(self) -> VehicleState:
        with self._lock:
            return copy.deepcopy(self._state)
    
    def update_state(self, **kwargs) -> None:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
    
    def set_position(self, x: float, y: float, theta: float, velocity: float) -> None:
        with self._lock:
            self._state.position_x = x
            self._state.position_y = y
            self._state.theta = theta
            self._state.velocity = velocity
    
    def set_actuators(self, acceleration: float, steering: float) -> None:
        with self._lock:
            self._state.acceleration_cmd = acceleration
            self._state.steering_cmd = steering
    
    def set_mode(self, mode: OperationMode) -> None:
        with self._lock:
            self._state.mode = mode
    
    def set_status(self, status: VehicleStatus) -> None:
        with self._lock:
            self._state.status = status
    
    def set_setpoints(self, velocity_sp: float = None, angular_sp: float = None) -> None:
        with self._lock:
            if velocity_sp is not None:
                self._state.velocity_setpoint = velocity_sp
            if angular_sp is not None:
                self._state.angular_setpoint = angular_sp
    
    def set_target(self, target_x: float = None, target_y: float = None) -> None:
        with self._lock:
            if target_x is not None:
                self._state.target_x = target_x
            if target_y is not None:
                self._state.target_y = target_y
    
    def set_faults(self, temperature: float = None, 
                   electrical: bool = None, 
                   hydraulic: bool = None,
                   emergency: bool = None) -> None:
        with self._lock:
            if temperature is not None:
                self._state.temperature = temperature
            if electrical is not None:
                self._state.electrical_fault = electrical
            if hydraulic is not None:
                self._state.hydraulic_fault = hydraulic
            if emergency is not None:
                self._state.emergency_stop = emergency
    
    def is_automatic(self) -> bool:
        with self._lock:
            return self._state.is_automatic()
    
    def is_manual(self) -> bool:
        with self._lock:
            return self._state.is_manual()
    
    def has_fault(self) -> bool:
        with self._lock:
            return self._state.has_fault()
    
    def get_position(self) -> tuple:
        with self._lock:
            return (self._state.position_x, 
                    self._state.position_y, 
                    self._state.theta, 
                    self._state.velocity)
    
    def get_actuators(self) -> tuple:
        with self._lock:
            return (self._state.acceleration_cmd, 
                    self._state.steering_cmd)
    
    def get_setpoints(self) -> tuple:
        with self._lock:
            return (self._state.velocity_setpoint, 
                    self._state.angular_setpoint)
