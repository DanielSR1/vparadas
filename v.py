# producao/plc_monitor.py
import os
import time
import django
import snap7
from snap7.util import get_bool
from datetime import datetime


from producao.models import ParadasLinha  # importa modelo

# --- Configuração do PLC ---
PLC_IP = "192.168.0.1"  # Substitua pelo IP do seu PLC
RACK = 0
SLOT = 3
DB_NUMBER = 1   # DB1
BYTE_INDEX = 0  # byte onde está o bit
BIT_INDEX = 1   # posição do bit dentro do byte (0 a 7)

def main():
    client = snap7.client.Client()
    try:
        client.connect(PLC_IP, RACK, SLOT)
        if client.get_connected():
            print(f"✅ Conectado ao PLC em {PLC_IP}")

            last_state = False
            parada_atual = None  # objeto em aberto
            
            while True:
                try:
                    data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
                    current_state = get_bool(data, 0, BIT_INDEX)

                    # Detecta início da parada (linha rodava e parou)
                    if last_state is False and current_state is True:
                        parada_atual = ParadasLinha.objects.create(
                            nome_linha="slitter",  # ajuste conforme necessário
                            inicio_parada=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        print(f"🔴 Linha PAROU às {parada_atual.inicio_parada}")
                        last_state = True

                    # Detecta fim da parada (linha estava parada e voltou a rodar)
                    if last_state is True and current_state is False and parada_atual:
                        parada_atual.fim_parada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        parada_atual.save()
                        print(f"🟢 Linha VOLTOU às {parada_atual.fim_parada}")
                        
                        
                    last_state = False
                    
                    time.sleep(0.5)

                except Exception as e:
                    print(f"⚠️ Erro na leitura: {e}")
                    time.sleep(1)

        else:
            print("❌ Falha na conexão com o PLC.")

    except Exception as e:
        print(f"❌ Ocorreu um erro ao conectar: {e}")
    finally:
        client.disconnect()

        print("🔌 Desconectado do PLC.")
