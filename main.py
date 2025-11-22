"""
Sistema Embarcado Principal
Inicializa e coordena todas as tarefas do veículo autônomo
"""

import sys
import time
import queue
import signal
from config.settings import *
from src.embedded.sync.circular_buffer import CircularBuffer
from src.embedded.sync.shared_state import SharedState
from src.embedded.sync.event_manager import EventManager
from src.simulation.mine_simulator import MineSimulatorTask
from src.embedded.tasks.sensor_processing import SensorProcessingTask
from src.embedded.tasks.fault_monitoring import FaultMonitoringTask
from src.embedded.tasks.command_logic import CommandLogicTask
from src.embedded.tasks.navigation_control import NavigationControlTask
from src.embedded.tasks.data_collector import DataCollectorTask
from src.embedded.tasks.route_planner import RoutePlanningTask
from src.embedded.tasks.local_interface import LocalInterfaceTask
from src.embedded.communication.mqtt_client import MQTTClient


class EmbeddedSystem:
    """
    Sistema Embarcado do Caminhão
    Coordena todas as tarefas concorrentes
    """
    
    def __init__(self, truck_id: int = 1, enable_mqtt: bool = False):
        """
        Args:
            truck_id: Identificação do caminhão
            enable_mqtt: Habilitar comunicação MQTT
        """
        self.truck_id = truck_id
        self.enable_mqtt = enable_mqtt
        
        print("="*70)
        print(f"SISTEMA EMBARCADO - CAMINHÃO {truck_id}".center(70))
        print("="*70)
        print("\nInicializando componentes...")
        
        # Mecanismos de sincronização
        self.circular_buffer = CircularBuffer(BUFFER_CONFIG['size'])
        self.shared_state = SharedState(truck_id)
        self.event_manager = EventManager()
        
        # Filas de comunicação
        self.command_queue = queue.Queue(maxsize=50)
        self.waypoint_queue = queue.Queue(maxsize=10)
        
        # Simulação
        self.simulator = MineSimulatorTask(
            self.shared_state,
            simulation_period=TIMING_CONFIG['simulation_period']
        )
        
        # Tarefas
        self.tasks = []
        
        # Tarefa: Tratamento de Sensores
        sensor_task = SensorProcessingTask(
            sensor_reader=self.simulator.get_sensor_data,
            circular_buffer=self.circular_buffer,
            filter_order=FILTER_CONFIG['order'],
            sample_period=TIMING_CONFIG['sensor_processing_period']
        )
        self.tasks.append(sensor_task)
        
        # Tarefa: Monitoramento de Falhas
        fault_task = FaultMonitoringTask(
            sensor_reader=self.simulator.get_sensor_data,
            event_manager=self.event_manager,
            check_period=TIMING_CONFIG['fault_monitoring_period'],
            temp_threshold=FAULT_CONFIG['temperature_threshold']
        )
        self.tasks.append(fault_task)
        
        # Tarefa: Lógica de Comando
        command_task = CommandLogicTask(
            circular_buffer=self.circular_buffer,
            shared_state=self.shared_state,
            event_manager=self.event_manager,
            command_queue=self.command_queue,
            update_period=TIMING_CONFIG['command_logic_period']
        )
        self.tasks.append(command_task)
        
        # Tarefa: Controle de Navegação
        nav_task = NavigationControlTask(
            shared_state=self.shared_state,
            event_manager=self.event_manager,
            control_period=TIMING_CONFIG['control_period']
        )
        self.tasks.append(nav_task)
        
        # Tarefa: Coletor de Dados
        data_task = DataCollectorTask(
            shared_state=self.shared_state,
            event_manager=self.event_manager,
            log_dir=LOG_CONFIG['log_dir'],
            collection_period=TIMING_CONFIG['data_collection_period']
        )
        self.tasks.append(data_task)
        
        # Tarefa: Planejamento de Rota
        route_task = RoutePlanningTask(
            shared_state=self.shared_state,
            event_manager=self.event_manager,
            waypoint_queue=self.waypoint_queue,
            planning_period=TIMING_CONFIG['route_planning_period'],
            waypoint_threshold=ROUTE_CONFIG['waypoint_threshold']
        )
        self.tasks.append(route_task)
        
        # Tarefa: Interface Local
        interface_task = LocalInterfaceTask(
            shared_state=self.shared_state,
            data_collector=data_task,
            command_queue=self.command_queue,
            update_period=TIMING_CONFIG['interface_update_period']
        )
        self.tasks.append(interface_task)
        
        # MQTT (opcional)
        self.mqtt_client = None
        if enable_mqtt:
            self.mqtt_client = MQTTClient(
                truck_id=truck_id,
                broker_host=MQTT_CONFIG['broker_host'],
                broker_port=MQTT_CONFIG['broker_port'],
                qos=MQTT_CONFIG['qos']
            )
        
        print(f"\n✓ {len(self.tasks)} tarefas criadas")
        print(f"✓ Buffer circular: {BUFFER_CONFIG['size']} amostras")
        print(f"✓ Filtro média móvel: ordem {FILTER_CONFIG['order']}")
    
    def start(self):
        """Inicia todas as tarefas"""
        print("\nIniciando tarefas concorrentes...")
        
        # Inicia simulação
        self.simulator.start()
        time.sleep(0.5)  # Aguarda simulação estabilizar
        
        # Inicia tarefas
        for task in self.tasks:
            task.start()
            time.sleep(0.1)
        
        # Conecta MQTT
        if self.mqtt_client:
            # Registra callbacks para comandos recebidos via MQTT
            self.mqtt_client.register_callback('command', self._handle_mqtt_command)
            self.mqtt_client.register_callback('setpoint', self._handle_mqtt_setpoint)
            self.mqtt_client.register_callback('route', self._handle_mqtt_route)
            
            if self.mqtt_client.connect():
                print("✓ MQTT conectado")
            else:
                print("⚠ MQTT não disponível")
        
        print("\n" + "="*70)
        print("SISTEMA OPERACIONAL".center(70))
        print("="*70)
        print("\nPressione Ctrl+C para encerrar\n")
    
    def run(self):
        """Loop principal"""
        try:
            while True:
                # Verifica eventos de shutdown
                if self.event_manager.is_shutdown():
                    print("\nShutdown solicitado...")
                    break
                
                # Publica dados via MQTT
                if self.mqtt_client and self.mqtt_client.is_connected():
                    state = self.shared_state.get_state()
                    
                    # Publica estado completo (incluindo setpoints para debug)
                    self.mqtt_client.publish_state({
                        'truck_id': state.truck_id,
                        'status': state.status.name,
                        'mode': state.mode.name,
                        'x': state.position_x,
                        'y': state.position_y,
                        'theta': state.theta,
                        'velocity': state.velocity,
                        'velocity_setpoint': state.velocity_setpoint,
                        'angular_setpoint': state.angular_setpoint,
                        'acceleration_cmd': state.acceleration_cmd,
                        'steering_cmd': state.steering_cmd,
                        'temperature': state.temperature,
                        'electrical_fault': state.electrical_fault,
                        'hydraulic_fault': state.hydraulic_fault,
                        'emergency_stop': state.emergency_stop
                    })
                    
                    # Publica posição separadamente
                    self.mqtt_client.publish_position(
                        state.position_x,
                        state.position_y,
                        state.theta
                    )
                
                time.sleep(1.0)
        
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário")
    
    def _handle_mqtt_command(self, data: dict):
        """Processa comando recebido via MQTT"""
        from src.models.command import Command, CommandType
        
        try:
            cmd_type_str = data.get('type', '')
            print(f"[MQTT] Comando recebido: {cmd_type_str}")
            
            # Mapeia string para CommandType (aceita ambos formatos)
            cmd_map = {
                'AUTO': CommandType.ENABLE_AUTOMATIC,
                'ENABLE_AUTOMATIC': CommandType.ENABLE_AUTOMATIC,
                'MANUAL': CommandType.DISABLE_AUTOMATIC,
                'DISABLE_AUTOMATIC': CommandType.DISABLE_AUTOMATIC,
                'EMERGENCY': CommandType.EMERGENCY_STOP,
                'EMERGENCY_STOP': CommandType.EMERGENCY_STOP,
                'RESET': CommandType.RESET_EMERGENCY,
                'RESET_EMERGENCY': CommandType.RESET_EMERGENCY,
                'STOP': CommandType.STOP,
                'MOVE_FORWARD': CommandType.MOVE_FORWARD,
                'MOVE_BACKWARD': CommandType.MOVE_BACKWARD,
                'TURN_LEFT': CommandType.TURN_LEFT,
                'TURN_RIGHT': CommandType.TURN_RIGHT,
                'ACCELERATE': CommandType.ACCELERATE,
                'BRAKE': CommandType.BRAKE
            }
            
            if cmd_type_str in cmd_map:
                command = Command(
                    command_type=cmd_map[cmd_type_str],
                    value=data.get('value'),
                    timestamp=time.time(),
                    source="mqtt"
                )
                self.command_queue.put(command)
                print(f"[MQTT] Comando '{cmd_type_str}' adicionado à fila")
            else:
                print(f"[MQTT] Comando desconhecido: {cmd_type_str}")
                
        except Exception as e:
            print(f"[MQTT] Erro ao processar comando: {e}")
    
    def _handle_mqtt_setpoint(self, data: dict):
        """Processa setpoint recebido via MQTT"""
        try:
            velocity = data.get('velocity', 0.0)
            print(f"[MQTT] Setpoint de velocidade recebido: {velocity} m/s")
            self.shared_state.set_setpoints(velocity, None)
        except Exception as e:
            print(f"[MQTT] Erro ao processar setpoint: {e}")
    
    def _handle_mqtt_route(self, data: dict):
        """Processa rota recebida via MQTT"""
        try:
            waypoints = data.get('waypoints', [])
            print(f"[MQTT] Rota recebida com {len(waypoints)} waypoints")
            
            # Converte para lista de tuplas (aceita formato lista ou dict)
            route = []
            for wp in waypoints:
                if isinstance(wp, dict):
                    # Formato: {'x': 10, 'y': 20}
                    route.append((wp['x'], wp['y']))
                elif isinstance(wp, (list, tuple)) and len(wp) >= 2:
                    # Formato: [10, 20] ou (10, 20)
                    route.append((wp[0], wp[1]))
                else:
                    print(f"[MQTT] Waypoint inválido ignorado: {wp}")
            
            if route:
                self.waypoint_queue.put(route)
                print(f"[MQTT] Rota adicionada à fila de planejamento com {len(route)} waypoints")
            else:
                print(f"[MQTT] Nenhum waypoint válido na rota")
                
        except Exception as e:
            print(f"[MQTT] Erro ao processar rota: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        """Para todas as tarefas"""
        print("\nEncerrando sistema...")
        
        # Sinaliza shutdown
        self.event_manager.shutdown()
        time.sleep(0.5)
        
        # Para simulação
        self.simulator.stop()
        
        # Para tarefas
        for task in self.tasks:
            task.stop()
        
        # Aguarda finalização
        time.sleep(1.0)
        
        # Desconecta MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        print("Sistema encerrado")


def main():
    """Função principal"""
    # Argumentos
    truck_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    enable_mqtt = '--mqtt' in sys.argv
    
    # Cria sistema
    system = EmbeddedSystem(truck_id, enable_mqtt)
    
    # Handler para Ctrl+C
    def signal_handler(sig, frame):
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Inicia
    system.start()
    system.run()
    system.stop()


if __name__ == "__main__":
    main()
