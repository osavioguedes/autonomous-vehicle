from collections import deque
from typing import Optional

class MovingAverageFilter:
    
    def __init__(self, order: int = 5):
        self._order = order
        self._samples = deque(maxlen=order)
        self._sum = 0.0
    
    def filter(self, value: float) -> float:

        if len(self._samples) == self._order:
            self._sum -= self._samples[0]
        
        self._samples.append(value)
        self._sum += value
        
        return self._sum / len(self._samples)
    
    def reset(self) -> None:
        self._samples.clear()
        self._sum = 0.0
    
    def is_ready(self) -> bool:
        return len(self._samples) == self._order
    
    def get_order(self) -> int:
        return self._order

class MultiChannelMovingAverage:
    
    def __init__(self, num_channels: int, order: int = 5):
        self._filters = [MovingAverageFilter(order) for _ in range(num_channels)]
        self._num_channels = num_channels
    
    def filter(self, values: list) -> list:
        if len(values) != self._num_channels:
            raise ValueError(f"Expected {self._num_channels} values, got {len(values)}")
        
        return [self._filters[i].filter(values[i]) for i in range(self._num_channels)]
    
    def reset(self) -> None:
        for f in self._filters:
            f.reset()
    
    def is_ready(self) -> bool:
        return all(f.is_ready() for f in self._filters)
