"""
Controlador de posição angular (orientação) do veículo
"""

import math
from src.embedded.control.pid_controller import PIDController


class AngularController:
    """
    Controlador PID para posição angular do veículo
    
    Controla a orientação através do comando de direção
    """
    
    def __init__(self, 
                 kp: float = 1.0, 
                 ki: float = 0.05, 
                 kd: float = 0.2,
                 max_steering: float = 1.0):
        """
        Args:
            kp: Ganho proporcional
            ki: Ganho integral
            kd: Ganho derivativo
            max_steering: Máximo comando de direção
        """
        self.pid = PIDController(
            kp=kp,
            ki=ki,
            kd=kd,
            output_min=-max_steering,
            output_max=max_steering,
            sample_time=0.05  # 50ms
        )
        self._enabled = False
    
    def compute(self, current_angle: float, target_angle: float) -> float:
        """
        Calcula comando de direção
        
        Args:
            current_angle: Ângulo atual (radianos)
            target_angle: Ângulo desejado (radianos)
            
        Returns:
            Comando de direção [-1.0, 1.0]
        """
        if not self._enabled:
            return 0.0
        
        # Normaliza erro de ângulo para [-pi, pi]
        error = self._normalize_angle(target_angle - current_angle)
        
        # PID trabalha com erro normalizado
        # Ajusta o setpoint para que o erro seja calculado corretamente
        adjusted_current = 0.0  # Referência zero
        adjusted_target = error  # Erro como setpoint
        
        return self.pid.compute(adjusted_current, adjusted_target)
    
    def _normalize_angle(self, angle: float) -> float:
        """
        Normaliza ângulo para [-pi, pi]
        
        Args:
            angle: Ângulo em radianos
            
        Returns:
            Ângulo normalizado
        """
        return math.atan2(math.sin(angle), math.cos(angle))
    
    def enable(self, current_angle: float) -> None:
        """
        Habilita controlador com bumpless transfer
        
        Args:
            current_angle: Ângulo atual para transição suave
        """
        self._enabled = True
        self.pid.enable(0.0)  # Inicia com erro zero
    
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
