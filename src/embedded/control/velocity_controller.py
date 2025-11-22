"""
Controlador de velocidade do veículo
"""

from src.embedded.control.pid_controller import PIDController


class VelocityController:
    """
    Controlador PID para velocidade linear do veículo
    
    Controla a velocidade através do comando de aceleração
    """
    
    def __init__(self, 
                 kp: float = 0.5, 
                 ki: float = 0.1, 
                 kd: float = 0.05,
                 max_accel: float = 1.0):
        """
        Args:
            kp: Ganho proporcional
            ki: Ganho integral
            kd: Ganho derivativo
            max_accel: Máximo comando de aceleração
        """
        self.pid = PIDController(
            kp=kp,
            ki=ki,
            kd=kd,
            output_min=-max_accel,
            output_max=max_accel,
            sample_time=0.05  # 50ms
        )
        self._enabled = False
    
    def compute(self, current_velocity: float, target_velocity: float) -> float:
        """
        Calcula comando de aceleração
        
        Args:
            current_velocity: Velocidade atual (m/s)
            target_velocity: Velocidade desejada (m/s)
            
        Returns:
            Comando de aceleração [-1.0, 1.0]
        """
        if not self._enabled:
            return 0.0
        
        return self.pid.compute(current_velocity, target_velocity)
    
    def enable(self, current_velocity: float) -> None:
        """
        Habilita controlador com bumpless transfer
        
        Args:
            current_velocity: Velocidade atual para transição suave
        """
        self._enabled = True
        self.pid.enable(current_velocity)
    
    def disable(self) -> None:
        """Desabilita controlador"""
        self._enabled = False
        self.pid.disable()
    
    def is_enabled(self) -> bool:
        """Verifica se está habilitado"""
        return self._enabled
    
    def reset(self) -> None:
        """Reseta estado do controlador"""
        self.pid.reset()
