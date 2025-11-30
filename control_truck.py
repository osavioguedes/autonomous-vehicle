import sys
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERRO: paho-mqtt não instalado")
    print("Instale com: pip install paho-mqtt")
    sys.exit(1)

import json
import time

def print_menu():
    print("\n" + "="*60)
    print("CONTROLADOR DO CAMINHÃO VIA MQTT".center(60))
    print("="*60)
    print("\nCOMANDOS DISPONÍVEIS:")
    print("  [1] Ativar modo AUTOMÁTICO")
    print("  [2] Ativar modo MANUAL")
    print("  [3] Parada de EMERGÊNCIA")
    print("  [4] Reset emergência")
    print("  [5] REARMAR sistema (limpar falhas)")
    print("  [6] Definir VELOCIDADE setpoint")
    print("  [7] Definir ROTA (waypoints)")
    print("  [8] Parar caminhão")
    print("  [9] Ver status")
    print("  [0] Sair")
    print("="*60)

def send_command(client, truck_id, command):
    topic = f"mine/truck/{truck_id}/command"
    payload = json.dumps({"type": command})
    client.publish(topic, payload, qos=1)
    print(f"✓ Comando '{command}' enviado para caminhão {truck_id}")

def send_setpoint(client, truck_id, velocity, angular=0.0):
    topic = f"mine/truck/{truck_id}/setpoint"
    payload = json.dumps({"velocity": velocity, "angular": angular})
    client.publish(topic, payload, qos=1)
    print(f"✓ Setpoint enviado: velocidade={velocity} m/s")

def send_route(client, truck_id, waypoints):
    topic = f"mine/truck/{truck_id}/route"
    payload = json.dumps({"waypoints": waypoints})
    client.publish(topic, payload, qos=1)
    print(f"✓ Rota enviada com {len(waypoints)} waypoints")

truck_state = {}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("\n✓ Conectado ao broker MQTT")

        truck_id = userdata
        client.subscribe(f"mine/truck/{truck_id}/state", qos=1)
        print(f"✓ Inscrito no estado do caminhão {truck_id}")
    else:
        print(f"\n✗ Falha na conexão (código {rc})")

def on_message(client, userdata, msg):
    global truck_state
    try:
        truck_state = json.loads(msg.payload.decode('utf-8'))
    except:
        pass

def show_status():
    if not truck_state:
        print("\n⚠ Nenhum dado recebido do caminhão ainda")
        return
    
    print("\n" + "-"*60)
    print("STATUS DO CAMINHÃO".center(60))
    print("-"*60)
    print(f"ID:                {truck_state.get('truck_id', 'N/A')}")
    print(f"Status:            {truck_state.get('status', 'N/A')}")
    print(f"Modo:              {truck_state.get('mode', 'N/A')}")
    print(f"Posição:           X={truck_state.get('x', 0):.2f}m  Y={truck_state.get('y', 0):.2f}m")
    print(f"Orientação:        {truck_state.get('theta', 0):.2f} rad")
    print(f"Velocidade:        {truck_state.get('velocity', 0):.2f} m/s")
    print(f"Temperatura:       {truck_state.get('temperature', 0):.1f}°C")
    print(f"Falha elétrica:    {'SIM' if truck_state.get('electrical_fault') else 'NÃO'}")
    print(f"Falha hidráulica:  {'SIM' if truck_state.get('hydraulic_fault') else 'NÃO'}")
    print(f"Emergência:        {'ACIONADA' if truck_state.get('emergency_stop') else 'NÃO'}")
    print("-"*60)

def main():

    truck_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    broker = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    
    print("="*60)
    print(f"Controlador do Caminhão {truck_id}".center(60))
    print(f"Broker: {broker}".center(60))
    print("="*60)
    
    try:
        client = mqtt.Client(
            client_id=f"controller_{truck_id}",
            userdata=truck_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id=f"controller_{truck_id}", userdata=truck_id)
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print("\nConectando ao broker MQTT...")
        client.connect(broker, 1883, 60)
        client.loop_start()
        time.sleep(1)
    except Exception as e:
        print(f"\n✗ Erro ao conectar: {e}")
        print("\nVerifique se o broker MQTT está rodando:")
        print("  mosquitto")
        sys.exit(1)
    
    try:
        while True:
            print_menu()
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '0':
                print("\nEncerrando...")
                break
            
            elif choice == '1':
                send_command(client, truck_id, "ENABLE_AUTOMATIC")
                time.sleep(0.5)
                show_status()
            
            elif choice == '2':
                send_command(client, truck_id, "DISABLE_AUTOMATIC")
                time.sleep(0.5)
                show_status()
            
            elif choice == '3':
                send_command(client, truck_id, "EMERGENCY_STOP")
                time.sleep(0.5)
                show_status()
            
            elif choice == '4':
                send_command(client, truck_id, "RESET_EMERGENCY")
                time.sleep(0.5)
                show_status()
            
            elif choice == '5':
                send_command(client, truck_id, "RESET_FAULT")
                time.sleep(0.5)
                show_status()
            
            elif choice == '6':
                try:
                    vel = float(input("Digite a velocidade desejada (m/s): "))
                    send_setpoint(client, truck_id, vel)
                except ValueError:
                    print("✗ Valor inválido")
            
            elif choice == '7':
                print("\nDefina waypoints (X Y, separados por vírgula)")
                print("Exemplo: 10 10, 20 20, 30 30")
                try:
                    waypoints_str = input("Waypoints: ")
                    waypoints = []
                    for wp in waypoints_str.split(','):
                        x, y = map(float, wp.strip().split())
                        waypoints.append([x, y])
                    send_route(client, truck_id, waypoints)
                except:
                    print("✗ Formato inválido")
            
            elif choice == '8':
                send_setpoint(client, truck_id, 0.0)
                print("✓ Comando de parada enviado (velocidade = 0)")
            
            elif choice == '9':
                show_status()
            
            else:
                print("✗ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
    
    finally:
        client.loop_stop()
        client.disconnect()
        print("Desconectado")

if __name__ == "__main__":
    main()
