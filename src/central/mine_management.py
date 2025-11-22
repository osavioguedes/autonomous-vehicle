"""
Sistema Central de Gestão da Mina
Interface gráfica com mapa em tempo real
"""

import tkinter as tk
from tkinter import ttk
import json
import time
from typing import Dict, Tuple, List
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


class MineManagementGUI:
    """
    Interface gráfica para gestão da mina
    
    Funcionalidades:
    - Mapa em tempo real com todos os caminhões
    - Mostrar posição, status e modo de cada caminhão
    - Permitir alterar setpoints
    - Enviar comandos e rotas
    """
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        """
        Args:
            broker_host: Endereço do broker MQTT
            broker_port: Porta do broker
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Estado dos caminhões
        self.trucks: Dict[int, dict] = {}
        self.selected_truck_id: int = None  # ID do caminhão selecionado
        
        # GUI
        self.root = tk.Tk()
        self.root.title("Sistema de Gestão da Mina")
        self.root.geometry("1200x900")
        
        # Frames condicionais
        self.manual_frame = None
        self.auto_frame = None
        
        self._setup_gui()
        
        # MQTT
        self.mqtt_client = None
        if MQTT_AVAILABLE:
            self._setup_mqtt()
    
    def _setup_gui(self):
        """Configura interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title = ttk.Label(main_frame, text="SISTEMA DE GESTÃO DA MINA", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Canvas para mapa
        self.canvas = tk.Canvas(main_frame, width=800, height=500, bg='#2a2a2a')
        self.canvas.grid(row=1, column=0, padx=5, pady=5)
        
        # Frame de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controle", padding="10")
        control_frame.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.N, tk.W, tk.E))
        
        # Lista de caminhões
        ttk.Label(control_frame, text="Caminhões Ativos:").grid(row=0, column=0, pady=2)
        self.truck_listbox = tk.Listbox(control_frame, height=6, width=30)
        self.truck_listbox.grid(row=1, column=0, pady=2)
        self.truck_listbox.bind('<<ListboxSelect>>', self._on_truck_select)
        
        # Informações do caminhão selecionado
        info_frame = ttk.LabelFrame(control_frame, text="Informações", padding="5")
        info_frame.grid(row=2, column=0, pady=3, sticky=(tk.W, tk.E))
        
        self.info_labels = {}
        labels = ['Status:', 'Modo:', 'Posição:', 'Velocidade:', 'Temperatura:']
        for i, label in enumerate(labels):
            ttk.Label(info_frame, text=label).grid(row=i, column=0, sticky=tk.W)
            self.info_labels[label] = ttk.Label(info_frame, text="-")
            self.info_labels[label].grid(row=i, column=1, sticky=tk.W, padx=5)
        
        # Controles
        cmd_frame = ttk.LabelFrame(control_frame, text="Comandos", padding="5")
        cmd_frame.grid(row=3, column=0, pady=3, sticky=(tk.W, tk.E))
        
        ttk.Button(cmd_frame, text="Modo Automático", 
                  command=self._send_auto_command).grid(row=0, column=0, pady=2, sticky=tk.W+tk.E)
        ttk.Button(cmd_frame, text="Modo Manual", 
                  command=self._send_manual_command).grid(row=1, column=0, pady=2, sticky=tk.W+tk.E)
        ttk.Button(cmd_frame, text="Emergência", 
                  command=self._send_emergency).grid(row=2, column=0, pady=2, sticky=tk.W+tk.E)
        
        # Controle Manual (inicialmente oculto)
        self.manual_frame = ttk.LabelFrame(control_frame, text="Controle Manual", padding="5")
        
        # Direcionais
        ttk.Button(self.manual_frame, text="↑ Frente", width=12,
                  command=self._send_forward).grid(row=0, column=1, pady=2)
        ttk.Button(self.manual_frame, text="← Esquerda", width=12,
                  command=self._send_left).grid(row=1, column=0, padx=2)
        ttk.Button(self.manual_frame, text="→ Direita", width=12,
                  command=self._send_right).grid(row=1, column=2, padx=2)
        ttk.Button(self.manual_frame, text="↓ Ré", width=12,
                  command=self._send_backward).grid(row=2, column=1, pady=2)
        
        # Aceleração/Freio
        accel_frame = ttk.Frame(self.manual_frame)
        accel_frame.grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(accel_frame, text="⚡ Acelerar", width=12,
                  command=self._send_accelerate).grid(row=0, column=0, padx=2)
        ttk.Button(accel_frame, text="🛑 Freiar", width=12,
                  command=self._send_brake).grid(row=0, column=1, padx=2)
        
        # Modo Automático - Waypoints (inicialmente oculto)
        self.auto_frame = ttk.LabelFrame(control_frame, text="Modo Automático - Waypoints", padding="5")
        
        # Lista de waypoints
        ttk.Label(self.auto_frame, text="Waypoints:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        self.waypoints_listbox = tk.Listbox(self.auto_frame, height=4, width=25)
        self.waypoints_listbox.grid(row=1, column=0, columnspan=2, pady=2, rowspan=2)
        
        # Adicionar waypoint (ao lado)
        ttk.Label(self.auto_frame, text="X (m):").grid(row=1, column=2, sticky=tk.W, padx=(10,2))
        self.waypoint_x_entry = ttk.Entry(self.auto_frame, width=8)
        self.waypoint_x_entry.grid(row=1, column=3, padx=2)
        
        ttk.Label(self.auto_frame, text="Y (m):").grid(row=2, column=2, sticky=tk.W, padx=(10,2))
        self.waypoint_y_entry = ttk.Entry(self.auto_frame, width=8)
        self.waypoint_y_entry.grid(row=2, column=3, padx=2)
        
        ttk.Button(self.auto_frame, text="➕ Adicionar", 
                  command=self._add_waypoint).grid(row=3, column=0, pady=5, sticky=tk.W+tk.E)
        ttk.Button(self.auto_frame, text="❌ Remover", 
                  command=self._remove_waypoint).grid(row=3, column=1, pady=5, sticky=tk.W+tk.E)
        ttk.Button(self.auto_frame, text="🚀 Enviar Rota", 
                  command=self._send_route).grid(row=4, column=0, columnspan=4, pady=5, sticky=tk.W+tk.E)
        
        # Lista interna de waypoints
        self.waypoints = []
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Aguardando conexão MQTT...", 
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Desenha grid no mapa
        self._draw_map_grid()
        
        # Atualização periódica
        self._update_display()
    
    def _setup_mqtt(self):
        """Configura cliente MQTT"""
        try:
            self.mqtt_client = mqtt.Client(
                client_id="mine_management",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
        except (AttributeError, TypeError):
            self.mqtt_client = mqtt.Client(client_id="mine_management")
        
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        try:
            self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.status_bar.config(text=f"Erro MQTT: {e}")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        """Callback de conexão MQTT"""
        if rc == 0:
            self.status_bar.config(text=f"Conectado ao broker MQTT ({self.broker_host})")
            # Subscreve a todos os caminhões
            client.subscribe("mine/truck/+/state", qos=1)
            client.subscribe("mine/truck/+/position", qos=1)
        else:
            self.status_bar.config(text=f"Falha na conexão MQTT (código {rc})")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback de mensagem MQTT"""
        try:
            # Extrai ID do caminhão do tópico
            parts = msg.topic.split('/')
            truck_id = int(parts[2])
            
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if truck_id not in self.trucks:
                self.trucks[truck_id] = {}
                print(f"✓ Caminhão {truck_id} conectado")
            
            if msg.topic.endswith('/state'):
                self.trucks[truck_id].update(payload)
            elif msg.topic.endswith('/position'):
                self.trucks[truck_id].update(payload)
            
            self.trucks[truck_id]['last_update'] = time.time()
            
        except Exception as e:
            print(f"[ERRO] Falha ao processar mensagem MQTT: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_map_grid(self):
        """Desenha grade no mapa"""
        # Grade de 100x100m, cada célula = 10m
        for i in range(0, 800, 80):  # 10 células
            self.canvas.create_line(i, 0, i, 500, fill='#3a3a3a')
            self.canvas.create_line(0, i*0.625, 800, i*0.625, fill='#3a3a3a')
        
        # Legenda
        self.canvas.create_text(400, 10, text="Mapa da Mina (100m x 75m)", 
                               fill='white', font=('Arial', 12, 'bold'))
    
    def _update_display(self):
        """Atualiza display periodicamente"""
        # Salva seleção atual
        current_selection = self.truck_listbox.curselection()
        selected_index = current_selection[0] if current_selection else None
        
        # Atualiza lista de caminhões
        self.truck_listbox.delete(0, tk.END)
        restore_index = None
        for idx, (truck_id, data) in enumerate(sorted(self.trucks.items())):
            status = data.get('status', 'UNKNOWN')
            self.truck_listbox.insert(tk.END, f"Caminhão {truck_id} - {status}")
            
            # Se este caminhão estava selecionado, guarda índice
            if self.selected_truck_id == truck_id:
                restore_index = idx
        
        # Restaura seleção
        if restore_index is not None:
            self.truck_listbox.selection_set(restore_index)
            self.truck_listbox.see(restore_index)
        elif selected_index is not None and selected_index < self.truck_listbox.size():
            self.truck_listbox.selection_set(selected_index)
        
        # Atualiza mapa
        self._draw_trucks()
        
        # Atualiza informações do caminhão selecionado
        self._update_selected_truck_info()
        
        # Agenda próxima atualização
        self.root.after(500, self._update_display)
    
    def _draw_trucks(self):
        """Desenha caminhões no mapa"""
        import math
        
        # Limpa caminhões anteriores
        self.canvas.delete('truck')
        
        for truck_id, data in self.trucks.items():
            x = data.get('x', 0)
            y = data.get('y', 0)
            theta = data.get('theta', 0)  # Orientação em radianos
            
            # Converte coordenadas (0-100m) para pixels (0-800 x 0-500)
            # 100m x 75m -> 800px x 500px (aproximado)
            px = x * 8
            py = y * 6.67  # Ajustado para altura de 500px
            
            # Cor baseada no status
            status = data.get('status', 'UNKNOWN')
            if status == 'RUNNING':
                color = 'green'
            elif status == 'FAULT' or status == 'EMERGENCY':
                color = 'red'
            else:
                color = 'yellow'
            
            # Desenha caminhão como triângulo apontando na direção theta
            # Tamanho do triângulo
            size = 15
            
            # Calcula os 3 pontos do triângulo
            # Ponta frontal (direção do movimento)
            front_x = px + size * math.cos(theta)
            front_y = py + size * math.sin(theta)
            
            # Cantos traseiros (120 graus à esquerda e direita)
            left_x = px + (size * 0.6) * math.cos(theta + 2.4)  # 140 graus
            left_y = py + (size * 0.6) * math.sin(theta + 2.4)
            
            right_x = px + (size * 0.6) * math.cos(theta - 2.4)
            right_y = py + (size * 0.6) * math.sin(theta - 2.4)
            
            # Desenha triângulo
            points = [front_x, front_y, left_x, left_y, right_x, right_y]
            self.canvas.create_polygon(points, fill=color, outline='white', 
                                      width=2, tags='truck')
            
            # ID do caminhão acima
            self.canvas.create_text(px, py-25, text=f"T{truck_id}", 
                                   fill='white', font=('Arial', 10, 'bold'), tags='truck')
    
    def _on_truck_select(self, event):
        """Callback de seleção de caminhão"""
        selection = self.truck_listbox.curselection()
        if not selection:
            return
        
        # Extrai ID
        text = self.truck_listbox.get(selection[0])
        truck_id = int(text.split()[1])
        
        # Salva ID selecionado
        self.selected_truck_id = truck_id
        
        # Atualiza informações
        if truck_id in self.trucks:
            data = self.trucks[truck_id]
            self.info_labels['Status:'].config(text=data.get('status', '-'))
            self.info_labels['Modo:'].config(text=data.get('mode', '-'))
            x = data.get('x', 0)
            y = data.get('y', 0)
            self.info_labels['Posição:'].config(text=f"({x:.1f}, {y:.1f})")
            self.info_labels['Velocidade:'].config(text=f"{data.get('velocity', 0):.1f} m/s")
            self.info_labels['Temperatura:'].config(text=f"{data.get('temperature', 0):.1f}°C")
            
            # Mostra/oculta controles baseado no modo
            self._update_control_visibility(data.get('mode', '-'))
    
    def _update_selected_truck_info(self):
        """Atualiza informações do caminhão selecionado"""
        if self.selected_truck_id and self.selected_truck_id in self.trucks:
            data = self.trucks[self.selected_truck_id]
            self.info_labels['Status:'].config(text=data.get('status', '-'))
            self.info_labels['Modo:'].config(text=data.get('mode', '-'))
            x = data.get('x', 0)
            y = data.get('y', 0)
            self.info_labels['Posição:'].config(text=f"({x:.1f}, {y:.1f})")
            self.info_labels['Velocidade:'].config(text=f"{data.get('velocity', 0):.1f} m/s")
            self.info_labels['Temperatura:'].config(text=f"{data.get('temperature', 0):.1f}°C")
    
    def _update_control_visibility(self, mode: str):
        """Mostra/oculta controles baseado no modo do caminhão"""
        if mode == 'MANUAL':
            # Mostra controle manual
            self.manual_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))
            # Oculta controle automático
            self.auto_frame.grid_remove()
        elif mode == 'AUTOMATIC':
            # Oculta controle manual
            self.manual_frame.grid_remove()
            # Mostra controle automático
            self.auto_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))
        else:
            # Oculta ambos se modo desconhecido
            self.manual_frame.grid_remove()
            self.auto_frame.grid_remove()
    
    def _get_selected_truck_id(self) -> int:
        """Retorna ID do caminhão selecionado"""
        # Usa o ID salvo
        return self.selected_truck_id
    
    def _send_auto_command(self):
        """Envia comando para ativar modo automático"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "ENABLE_AUTOMATIC"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Modo AUTOMÁTICO enviado para caminhão {truck_id}")
            # Atualiza visibilidade dos controles
            self._update_control_visibility('AUTOMATIC')
    
    def _send_manual_command(self):
        """Envia comando para modo manual"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "DISABLE_AUTOMATIC"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Modo MANUAL enviado para caminhão {truck_id}")
            # Atualiza visibilidade dos controles
            self._update_control_visibility('MANUAL')
    
    def _send_emergency(self):
        """Envia comando de emergência"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "EMERGENCY_STOP"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"⚠ EMERGÊNCIA enviada para caminhão {truck_id}")
    
    def _send_setpoint(self):
        """Envia novo setpoint de velocidade"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if not self.mqtt_client:
            return
        
        try:
            velocity = float(self.velocity_entry.get())
            payload = json.dumps({"velocity": velocity, "angular": 0.0})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/setpoint", payload, qos=1)
            self.status_bar.config(text=f"Setpoint enviado para caminhão {truck_id}")
        except ValueError:
            self.status_bar.config(text="Erro: velocidade inválida")
    
    def _send_forward(self):
        """Envia comando para frente"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "MOVE_FORWARD"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando FRENTE enviado")
    
    def _send_backward(self):
        """Envia comando para ré"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "MOVE_BACKWARD"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando RÉ enviado")
    
    def _send_left(self):
        """Envia comando para esquerda"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "TURN_LEFT"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando ESQUERDA enviado")
    
    def _send_right(self):
        """Envia comando para direita"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "TURN_RIGHT"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando DIREITA enviado")
    
    def _send_accelerate(self):
        """Envia comando para acelerar"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "ACCELERATE"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando ACELERAR enviado")
    
    def _send_brake(self):
        """Envia comando para freiar"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        if self.mqtt_client:
            payload = json.dumps({"type": "BRAKE"})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/command", payload, qos=1)
            self.status_bar.config(text=f"✓ Comando FREIAR enviado")
    
    def _add_waypoint(self):
        """Adiciona waypoint à lista"""
        try:
            x = float(self.waypoint_x_entry.get())
            y = float(self.waypoint_y_entry.get())
            
            # Valida limites do mapa
            if not (0 <= x <= 100 and 0 <= y <= 75):
                self.status_bar.config(text="⚠ Waypoint fora dos limites (0-100m, 0-75m)")
                return
            
            self.waypoints.append([x, y])
            self.waypoints_listbox.insert(tk.END, f"({x:.1f}, {y:.1f})")
            
            # Limpa campos
            self.waypoint_x_entry.delete(0, tk.END)
            self.waypoint_y_entry.delete(0, tk.END)
            
            self.status_bar.config(text=f"✓ Waypoint adicionado: ({x:.1f}, {y:.1f})")
        except ValueError:
            self.status_bar.config(text="⚠ Valores inválidos para waypoint")
    
    def _remove_waypoint(self):
        """Remove waypoint selecionado"""
        selection = self.waypoints_listbox.curselection()
        if not selection:
            self.status_bar.config(text="⚠ Selecione um waypoint para remover")
            return
        
        index = selection[0]
        self.waypoints.pop(index)
        self.waypoints_listbox.delete(index)
        self.status_bar.config(text="✓ Waypoint removido")
    
    def _send_route(self):
        """Envia rota completa com waypoints"""
        truck_id = self._get_selected_truck_id()
        if not truck_id:
            self.status_bar.config(text="⚠ Selecione um caminhão primeiro")
            return
        
        if not self.waypoints:
            self.status_bar.config(text="⚠ Adicione waypoints antes de enviar rota")
            return
        
        if self.mqtt_client:
            payload = json.dumps({"waypoints": self.waypoints})
            self.mqtt_client.publish(f"mine/truck/{truck_id}/route", payload, qos=1)
            self.status_bar.config(text=f"✓ Rota com {len(self.waypoints)} waypoints enviada")
    
    def run(self):
        """Inicia a interface"""
        self.root.mainloop()
    
    def cleanup(self):
        """Limpa recursos"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()


def main():
    """Função principal"""
    app = MineManagementGUI()
    try:
        app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
