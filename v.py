# producao/plc_monitor.py
import os
import time
import django
import snap7
from snap7.util import get_bool
from datetime import datetime
from producao.models import ParadasLinha  # importa modelo

# --- Configuração do PLC ---
PLC_IP = "192.168.0.1"
RACK = 0
SLOT = 3
DB_NUMBER = 1
BYTE_INDEX = 0
BIT_INDEX = 1

def monitor_plc(client, last_state=None, parada_atual=None):
    try:
        data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
        current_state = get_bool(data, 0, BIT_INDEX)

        # Detecta início da parada
        if last_state is True and current_state is False and parada_atual is None:
            try:
                parada_atual = ParadasLinha.objects.create(
                    nome_linha="slitter",
                    inicio_parada=datetime.now(),
                )
                print(f"🔴 Linha PAROU às {parada_atual.inicio_parada}")
            except Exception as e:
                print(f"❌ Erro ao criar parada: {e}")

        # Detecta fim da parada
        if last_state is False and current_state is True and parada_atual:
            try:
                parada_atual.fim_parada = datetime.now()
                parada_atual.save()
                print(f"🟢 Linha VOLTOU às {parada_atual.fim_parada}")
            except Exception as e:
                print(f"❌ Erro ao salvar parada: {e}")
            # Aqui substituímos o 'break' por 'return' para encerrar a recursão
            return

        # Atualiza o estado e chama recursivamente
        time.sleep(0.5)
        monitor_plc(client, last_state=current_state, parada_atual=parada_atual)

    except Exception as e:
        print(f"⚠️ Erro na leitura: {e}")
        time.sleep(1)
        monitor_plc(client, last_state=last_state, parada_atual=parada_atual)


def main():
    client = snap7.client.Client()
    try:
        client.connect(PLC_IP, RACK, SLOT)
        if client.get_connected():
            print(f"✅ Conectado ao PLC em {PLC_IP}")
            monitor_plc(client)  # inicia a recursão
        else:
            print("❌ Falha na conexão com o PLC.")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao conectar: {e}")
    finally:
        client.disconnect()
        print("🔌 Desconectado do PLC.")
