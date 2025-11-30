import threading
from typing import Optional, List
from collections import deque
from src.models.sensor_data import FilteredSensorData

class CircularBuffer:
    
    def __init__(self, size: int = 100):
        self._buffer = deque(maxlen=size)
        self._lock = threading.Lock()
        self._size = size
    
    def write(self, data: FilteredSensorData) -> None:
        with self._lock:
            self._buffer.append(data)
    
    def read_latest(self) -> Optional[FilteredSensorData]:
        with self._lock:
            if len(self._buffer) > 0:
                return self._buffer[-1]
            return None
    
    def read_last_n(self, n: int) -> List[FilteredSensorData]:
        with self._lock:

            return list(self._buffer)[-n:] if len(self._buffer) > 0 else []
    
    def read_all(self) -> List[FilteredSensorData]:
        with self._lock:
            return list(self._buffer)
    
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
    
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)
    
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0
    
    def is_full(self) -> bool:
        with self._lock:
            return len(self._buffer) >= self._size
