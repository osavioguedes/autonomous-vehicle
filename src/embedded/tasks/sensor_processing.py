import threading
import time
from typing import Callable, Optional
from src.models.sensor_data import SensorData, FilteredSensorData
from src.embedded.filters.moving_average import MovingAverageFilter
from src.embedded.sync.circular_buffer import CircularBuffer

class SensorProcessingTask(threading.Thread):
    
    def __init__(self,
                 sensor_reader: Callable[[], SensorData],
                 circular_buffer: CircularBuffer,
                 filter_order: int = 5,
                 sample_period: float = 0.1):
        super().__init__(name="SensorProcessing", daemon=True)
        
        self.sensor_reader = sensor_reader
        self.circular_buffer = circular_buffer
        self.sample_period = sample_period
        self._stop_event = threading.Event()
        
        self.filter_x = MovingAverageFilter(filter_order)
        self.filter_y = MovingAverageFilter(filter_order)
        self.filter_theta = MovingAverageFilter(filter_order)
        self.filter_velocity = MovingAverageFilter(filter_order)
        self.filter_temperature = MovingAverageFilter(filter_order)
    
    def run(self):
        print(f"[{self.name}] Tarefa iniciada (filtro ordem {self.filter_x.get_order()})")
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:

                sensor_data = self.sensor_reader()
                
                filtered_x = self.filter_x.filter(sensor_data.position_x)
                filtered_y = self.filter_y.filter(sensor_data.position_y)
                filtered_theta = self.filter_theta.filter(sensor_data.theta)
                filtered_velocity = self.filter_velocity.filter(sensor_data.velocity)
                filtered_temp = self.filter_temperature.filter(sensor_data.temperature)
                
                filtered_data = FilteredSensorData(
                    position_x=filtered_x,
                    position_y=filtered_y,
                    theta=filtered_theta,
                    velocity=filtered_velocity,
                    temperature=filtered_temp,
                    electrical_fault=sensor_data.electrical_fault,
                    hydraulic_fault=sensor_data.hydraulic_fault,
                    timestamp=time.time()
                )
                
                self.circular_buffer.write(filtered_data)
                
            except Exception as e:
                print(f"[{self.name}] Erro: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.sample_period - elapsed)
            time.sleep(sleep_time)
        
        print(f"[{self.name}] Tarefa finalizada")
    
    def stop(self):
        self._stop_event.set()
