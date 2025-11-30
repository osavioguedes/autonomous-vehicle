import threading
import time
import random
from typing import Callable

class RandomFaultGenerator(threading.Thread):
    
    def __init__(self,
                 inject_electrical_fault: Callable[[bool], None],
                 inject_hydraulic_fault: Callable[[bool], None],
                 check_period: float = 10.0,
                 electrical_fault_probability: float = 0.05,
                 hydraulic_fault_probability: float = 0.05):
        super().__init__(name="RandomFaultGenerator", daemon=True)
        
        self.inject_electrical_fault = inject_electrical_fault
        self.inject_hydraulic_fault = inject_hydraulic_fault
        self.check_period = check_period
        self.electrical_fault_probability = electrical_fault_probability
        self.hydraulic_fault_probability = hydraulic_fault_probability
        
        self._stop_event = threading.Event()
        self._electrical_fault_active = False
        self._hydraulic_fault_active = False
    
    def run(self):
        print(f"[{self.name}] Tarefa iniciada - monitorando falhas aleatórias")
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:
                if not self._electrical_fault_active and random.random() < self.electrical_fault_probability:
                    self.inject_electrical_fault(True)
                    self._electrical_fault_active = True
                    print(f"[{self.name}] ⚡ FALHA ELÉTRICA gerada! Requer rearme manual.")
                
                if not self._hydraulic_fault_active and random.random() < self.hydraulic_fault_probability:
                    self.inject_hydraulic_fault(True)
                    self._hydraulic_fault_active = True
                    print(f"[{self.name}] 🔧 FALHA HIDRÁULICA gerada! Requer rearme manual.")
                
            except Exception as e:
                print(f"[{self.name}] Erro: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.check_period - elapsed)
            time.sleep(sleep_time)
        
        print(f"[{self.name}] Tarefa finalizada")
    
    def clear_all_faults(self):
        if self._electrical_fault_active:
            self.inject_electrical_fault(False)
            self._electrical_fault_active = False
            print(f"[{self.name}] Falha elétrica removida (rearme manual)")
        
        if self._hydraulic_fault_active:
            self.inject_hydraulic_fault(False)
            self._hydraulic_fault_active = False
            print(f"[{self.name}] Falha hidráulica removida (rearme manual)")
    
    def stop(self):
        self._stop_event.set()
