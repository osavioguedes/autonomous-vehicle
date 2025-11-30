import threading
import time
import queue
import os
from typing import Optional
from src.models.log_entry import LogEntry
from src.embedded.sync.shared_state import SharedState
from src.embedded.sync.event_manager import EventManager, EventType

class DataCollectorTask(threading.Thread):
    
    def __init__(self,
                 shared_state: SharedState,
                 event_manager: EventManager,
                 log_dir: str = "data/logs",
                 collection_period: float = 1.0):
        super().__init__(name="DataCollector", daemon=True)
        
        self.shared_state = shared_state
        self.event_manager = event_manager
        self.log_dir = log_dir
        self.collection_period = collection_period
        self._stop_event = threading.Event()
        
        self.log_queue = queue.Queue()
        
        os.makedirs(log_dir, exist_ok=True)
        
        state = shared_state.get_state()
        self.log_file = os.path.join(log_dir, f"truck_{state.truck_id}.csv")
        self._init_log_file()
    
    def _init_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write(LogEntry.csv_header())
    
    def run(self):
        print(f"[{self.name}] Tarefa iniciada (log: {self.log_file})")
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:

                state = self.shared_state.get_state()
                
                log_entry = LogEntry(
                    timestamp=time.time(),
                    truck_id=state.truck_id,
                    status=state.status.name,
                    mode=state.mode.name,
                    position_x=state.position_x,
                    position_y=state.position_y,
                    theta=state.theta,
                    velocity=state.velocity,
                    event_description="Status normal",
                    temperature=state.temperature,
                    electrical_fault=state.electrical_fault,
                    hydraulic_fault=state.hydraulic_fault
                )
                
                log_entry = self._check_events(log_entry)
                
                self._write_log(log_entry)
                
                try:
                    self.log_queue.put_nowait(log_entry)
                except queue.Full:

                    try:
                        self.log_queue.get_nowait()
                        self.log_queue.put_nowait(log_entry)
                    except queue.Empty:
                        pass
                
            except Exception as e:
                print(f"[{self.name}] Erro: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.collection_period - elapsed)
            time.sleep(sleep_time)
        
        print(f"[{self.name}] Tarefa finalizada")
    
    def _check_events(self, log_entry: LogEntry) -> LogEntry:
        event = self.event_manager.check_event(EventType.MODE_CHANGED)
        if event:
            mode = event.data.get("mode", "UNKNOWN")
            log_entry.event_description = f"Modo alterado para {mode}"
            return log_entry
        
        event = self.event_manager.check_event(EventType.EMERGENCY_STOP)
        if event:
            log_entry.event_description = "EMERGÊNCIA ACIONADA"
            return log_entry
        
        event = self.event_manager.check_event(EventType.EMERGENCY_RESET)
        if event:
            log_entry.event_description = "Emergência resetada"
            return log_entry
        
        event = self.event_manager.check_event(EventType.TARGET_REACHED)
        if event:
            log_entry.event_description = "Destino alcançado"
            return log_entry
        
        return log_entry
    
    def _write_log(self, log_entry: LogEntry):
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry.to_csv_line())
        except Exception as e:
            print(f"[{self.name}] Erro ao escrever log: {e}")
    
    def get_latest_logs(self, n: int = 10) -> list:
        logs = []
        for _ in range(min(n, self.log_queue.qsize())):
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs
    
    def stop(self):
        self._stop_event.set()
