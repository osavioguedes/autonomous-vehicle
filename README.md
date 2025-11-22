# Sistema de Controle de Veículo Autônomo de Mineração

Sistema embarcado para caminhões autônomos de mineração com tarefas concorrentes, controladores PID, comunicação MQTT e interface gráfica de gestão.

---

## 🚀 Execução Rápida

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Sistema Completo (4 Terminais)

**Terminal 1 - Broker MQTT:**
```bash
mosquitto
```

**Terminal 2 - Sistema Central (Interface Gráfica):**
```bash
python central_system.py
```

**Terminal 3 - Caminhão:**
```bash
python main.py 1 --mqtt
```

**Terminal 4 - Controlador (Enviar Comandos):**
```bash
python control_truck.py 1
```

### 3. Testar Movimento
No Terminal 4:
1. Digite `1` → Ativar modo automático
2. Digite `6` → Definir rota
3. Digite `80 50` → Waypoint (x=80m, y=50m)

O caminhão aparecerá no mapa e começará a se mover! 🚚💨

---

## ⚙️ Funcionalidades Implementadas

### Tarefas Concorrentes (9)
- **Simulação da Mina**: Dinâmica do veículo com inércia
- **Tratamento de Sensores**: Filtro média móvel (M=5)
- **Monitoramento de Falhas**: Temperatura, elétrica, hidráulica
- **Lógica de Comando**: Estados e transições de modo
- **Controle de Navegação**: PID velocidade + angular com bumpless transfer
- **Planejamento de Rota**: Navegação por waypoints
- **Coletor de Dados**: Logging CSV estruturado
- **Interface Local**: Comandos do operador (silenciosa via MQTT)

### Sincronização
- **Mutex**: Buffer circular, estado compartilhado
- **Condition Variables**: Eventos entre tarefas
- **Queue Thread-Safe**: Comandos e waypoints

### Controladores PID
- **Velocidade**: Kp=0.5, Ki=0.1, Kd=0.05
- **Angular**: Kp=1.0, Ki=0.05, Kd=0.2
- **Bumpless Transfer**: Transição suave manual→automático
- **Anti-Windup**: Limitação do termo integral

### Comunicação MQTT
- `mine/truck/{id}/state` - Estado completo (publicação)
- `mine/truck/{id}/position` - Posição GPS (publicação)
- `mine/truck/{id}/command` - Comandos remotos (subscrição)
- `mine/truck/{id}/route` - Rotas (subscrição)

### Interface Gráfica
- Mapa 100m × 75m em tempo real
- Caminhões representados por triângulos coloridos:
  - 🟢 Verde = RUNNING
  - 🟡 Amarelo = STOPPED
  - 🔴 Vermelho = EMERGENCY/FAULT
- Controles: Modo, Emergência, Setpoints, Rotas
- Informações: Status, Posição, Velocidade, Temperatura

---

## 📁 Estrutura do Projeto

```
autonomous-vehicle/
├── main.py                    # Sistema embarcado
├── central_system.py          # Interface gráfica
├── control_truck.py           # Controlador interativo via MQTT
├── config/settings.py         # Parâmetros do sistema
├── src/
│   ├── embedded/tasks/        # 7 tarefas concorrentes
│   ├── embedded/sync/         # Mutex, CV, Queues
│   ├── embedded/control/      # PID controllers
│   ├── embedded/filters/      # Média móvel
│   ├── embedded/communication/# MQTT client
│   ├── simulation/            # Dinâmica + ruído
│   ├── central/               # GUI Tkinter
│   └── models/                # Estruturas de dados
└── data/logs/                 # Logs CSV
```

---

## 🎮 Comandos do Controlador

No `control_truck.py`:
- **1** - Ativar modo AUTOMÁTICO
- **2** - Ativar modo MANUAL
- **3** - Parada de EMERGÊNCIA
- **4** - Reset emergência
- **5** - Definir velocidade setpoint
- **6** - Definir rota (waypoints)
- **7** - Parar caminhão
- **8** - Ver status atual

---

## 📊 Dados e Logs

### Logs CSV (`data/logs/truck_{id}.csv`)
```csv
timestamp,truck_id,status,mode,position_x,position_y,theta,velocity,temperature,electrical_fault,hydraulic_fault,event_description
1700000000.123,1,RUNNING,AUTOMATIC_REMOTE,50.5,37.8,0.785,3.5,45.2,False,False,"Status normal"
```

---

## 🔧 Configuração

Edite `config/settings.py` para ajustar:
- Períodos das tarefas
- Parâmetros PID
- Ordem do filtro
- Limites de velocidade
- Thresholds de falha
- Configurações MQTT

---

## 🐛 Solução de Problemas

**Erro: "paho-mqtt não instalado"**
```bash
pip install paho-mqtt
```

**Broker MQTT não conecta**
```bash
# Instalar Mosquitto (Windows)
choco install mosquitto

# Iniciar serviço
net start mosquitto

# Ou rodar manualmente
mosquitto
```

**Caminhão não aparece no mapa**
- Verifique se mosquitto está rodando
- Confirme que usou `--mqtt` no comando
- Aguarde 2-3 segundos para sincronização

---

## 📦 Dependências

```
numpy
matplotlib
paho-mqtt
```

---

**Desenvolvido para Automação em Tempo Real** 🎓