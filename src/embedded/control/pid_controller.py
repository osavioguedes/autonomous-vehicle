"""
Controlador PID (Proporcional-Integral-Derivativo)
Implementa controle com anti-windup e bumpless transfer
"""

import time
from typing import Optional


class PIDController:
    """
    Controlador PID genérico
    
    Implementa:
    - Controle PID clássico
    - Anti-windup (limitação do termo integral)
    - Bumpless transfer (transição suave manual->automático)
    """
    
    def __init__(self, 
                 kp: float = 1.0, 
                 ki: float = 0.0, 
                 kd: float = 0.0,
                 output_min: float = -1.0,
                 output_max: float = 1.0,
                 sample_time: float = 0.1):
        """
        Args:
            kp: Ganho proporcional
            ki: Ganho integral
            kd: Ganho derivativo
            output_min: Limite inferior da saída
            output_max: Limite superior da saída
            sample_time: Tempo de amostragem (s)
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.sample_time = sample_time
        
        # Estado interno
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None
        self._enabled = False
        self._setpoint = 0.0
    
    def compute(self, measured_value: float, setpoint: float) -> float:
        """
        Calcula saída do controlador PID
        
        Args:
            measured_value: Valor medido (process variable)
            setpoint: Valor desejado (setpoint)
            
        Returns:
            Sinal de controle
        """
        current_time = time.time()
        
        # Primeira execução
        if self._last_time is None:
            self._last_time = current_time
            self._last_error = setpoint - measured_value
            return 0.0
        
        # Calcula dt
        dt = current_time - self._last_time
        if dt < self.sample_time:
            return self._last_output  # Aguarda tempo de amostragem
        
        # Calcula erro
        error = setpoint - measured_value
        
        # Termo proporcional
        p_term = self.kp * error
        
        # Termo integral (com anti-windup)
        self._integral += error * dt
        # Limita integral para evitar windup
        max_integral = (self.output_max - self.output_min) / (2.0 * self.ki) if self.ki != 0 else 1e6
        self._integral = max(-max_integral, min(max_integral, self._integral))
        i_term = self.ki * self._integral
        
        # Termo derivativo
        d_term = 0.0
        if dt > 0:
            d_term = self.kd * (error - self._last_error) / dt
        
        # Saída total
        output = p_term + i_term + d_term
        
        # Limita saída
        output = max(self.output_min, min(self.output_max, output))
        
        # Atualiza estado
        self._last_error = error
        self._last_time = current_time
        self._last_output = output
        self._setpoint = setpoint
        
        return output
    
    def enable(self, current_value: float) -> None:
        """
        Habilita controlador com bumpless transfer
        
        Args:
            current_value: Valor atual para inicialização suave
        """
        self._enabled = True
        self._setpoint = current_value  # Bumpless transfer
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None
    
    def disable(self) -> None:
        """Desabilita controlador"""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Verifica se controlador está habilitado"""
        return self._enabled
    
    def reset(self) -> None:
        """Reseta estado interno do controlador"""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None
    
    def set_gains(self, kp: float = None, ki: float = None, kd: float = None) -> None:
        """Atualiza ganhos do controlador"""
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd
    
    def get_setpoint(self) -> float:
        """Retorna setpoint atual"""
        return self._setpoint
