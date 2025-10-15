# producao/plc_monitor.py
import os
import time
import django
import snap7
from snap7.util import get_bool
from datetime import datetime
from producao.models import ParadasLinha

# --- Configuração do PLC ---
PLC_IP = "192.168.0.1"
RACK = 0
SLOT = 3
DB_NUMBER = 1
BYTE_INDEX = 0
BIT_INDEX = 1
SLEEP_TIME = 0.5   # tempo entre leituras (segundos)
CONFIRM_READS = 2  # número de leituras consecutivas para confirmar mudança

def main():
    client = snap7.client.Client()
    try:
        client.connect(PLC_IP, RACK, SLOT)
        if not client.get_connected():
            print("❌ Falha na conexão com o PLC.")
            return

        print(f"✅ Conectado ao PLC em {PLC_IP}")

        # Leitura inicial
        data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
        last_state = get_bool(data, 0, BIT_INDEX)
        parada_atual = None
        print(f"🔍 Estado inicial: {'RODANDO' if last_state else 'PARADO'}")

        stable_state = last_state
        confirm_count = 0  # contador de leituras consecutivas iguais

        while True:
            try:
                data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
                current_state = get_bool(data, 0, BIT_INDEX)

                # Verifica se o estado permaneceu igual ao anterior
                if current_state == stable_state:
                    confirm_count = 0  # nada mudou
                else:
                    # Estado diferente → incrementa contador de confirmação
                    confirm_count += 1

                    # Se confirmou a mudança (2 leituras seguidas com mesmo valor)
                    if confirm_count >= CONFIRM_READS:
                        confirm_count = 0
                        last_state, stable_state = stable_state, current_state

                        # --- Início de parada (linha rodava e parou) ---
                        if last_state is True and current_state is False:
                            parada_atual = ParadasLinha.objects.create(
                                nome_linha="slitter",
                                inicio_parada=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            )
                            print(f"🔴 Linha PAROU às {parada_atual.inicio_parada}")

                        # --- Fim da parada (linha estava parada e voltou a rodar) ---
                        elif last_state is False and current_state is True and parada_atual:
                            parada_atual.fim_parada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            parada_atual.save()
                            print(f"🟢 Linha VOLTOU às {parada_atual.fim_parada}")
                            parada_atual = None

                        # Atualiza o estado estável
                        stable_state = current_state

                time.sleep(SLEEP_TIME)

            except Exception as e:
                print(f"⚠️ Erro na leitura: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"❌ Ocorreu um erro ao conectar: {e}")

    finally:
        client.disconnect()
        print("🔌 Desconectado do PLC.")
