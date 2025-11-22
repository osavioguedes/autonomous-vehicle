"""
Filtro de média móvel para tratamento de sensores
Remove ruído aplicando média das últimas M amostras
"""

from collections import deque
from typing import Optional


class MovingAverageFilter:
    """
    Filtro de média móvel de ordem M
    Calcula a média das últimas M amostras para reduzir ruído
    """
    
    def __init__(self, order: int = 5):
        """
        Args:
            order: Ordem do filtro (M = número de amostras para média)
        """
        self._order = order
        self._samples = deque(maxlen=order)
        self._sum = 0.0
    
    def filter(self, value: float) -> float:
        """
        Aplica o filtro a um novo valor
        
        Args:
            value: Valor a ser filtrado
            
        Returns:
            Valor filtrado (média das últimas M amostras)
        """
        # Se o buffer está cheio, remove o valor mais antigo da soma
        if len(self._samples) == self._order:
            self._sum -= self._samples[0]
        
        # Adiciona novo valor
        self._samples.append(value)
        self._sum += value
        
        # Retorna média
        return self._sum / len(self._samples)
    
    def reset(self) -> None:
        """Limpa o histórico do filtro"""
        self._samples.clear()
        self._sum = 0.0
    
    def is_ready(self) -> bool:
        """Verifica se o filtro tem amostras suficientes"""
        return len(self._samples) == self._order
    
    def get_order(self) -> int:
        """Retorna a ordem do filtro"""
        return self._order


class MultiChannelMovingAverage:
    """
    Filtro de média móvel para múltiplos canais
    Útil para filtrar vários sensores simultaneamente
    """
    
    def __init__(self, num_channels: int, order: int = 5):
        """
        Args:
            num_channels: Número de canais (sensores)
            order: Ordem do filtro
        """
        self._filters = [MovingAverageFilter(order) for _ in range(num_channels)]
        self._num_channels = num_channels
    
    def filter(self, values: list) -> list:
        """
        Filtra múltiplos valores simultaneamente
        
        Args:
            values: Lista de valores (um por canal)
            
        Returns:
            Lista de valores filtrados
        """
        if len(values) != self._num_channels:
            raise ValueError(f"Expected {self._num_channels} values, got {len(values)}")
        
        return [self._filters[i].filter(values[i]) for i in range(self._num_channels)]
    
    def reset(self) -> None:
        """Reseta todos os filtros"""
        for f in self._filters:
            f.reset()
    
    def is_ready(self) -> bool:
        """Verifica se todos os filtros estão prontos"""
        return all(f.is_ready() for f in self._filters)
