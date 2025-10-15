# producao/plc_monitor.py
import os
import time
import django
import snap7
from snap7.util import get_bool
from datetime import datetime

from producao.models import ParadasLinha  # importa modelo

# --- Configuração do PLC ---
PLC_IP = "192.168.0.1"  # IP do PLC
RACK = 0
SLOT = 3
DB_NUMBER = 1   # DB1
BYTE_INDEX = 0  # byte onde está o bit
BIT_INDEX = 1   # posição do bit dentro do byte (0 a 7)
DEBOUNCE_TIME = 2  # segundos mínimos entre mudanças de estado (evita duplicações)

def main():
    client = snap7.client.Client()
    try:
        client.connect(PLC_IP, RACK, SLOT)

        if not client.get_connected():
            print("❌ Falha na conexão com o PLC.")
            return

        print(f"✅ Conectado ao PLC em {PLC_IP}")

        # --- Inicializa o estado anterior antes do loop ---
        data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
        last_state = get_bool(data, 0, BIT_INDEX)
        parada_atual = None
        last_change_time = time.time()

        print(f"🔍 Estado inicial: {'RODANDO' if last_state else 'PARADO'}")

        while True:
            try:
                data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
                current_state = get_bool(data, 0, BIT_INDEX)

                # Só processa se o estado mudou
                if current_state != last_state:
                    now = time.time()

                    # Evita detectar duas transições muito próximas (debounce)
                    if now - last_change_time >= DEBOUNCE_TIME:
                        last_change_time = now

                        # --- Início de parada (linha rodava e parou) ---
                        if last_state is True and current_state is False:
                            parada_atual = ParadasLinha.objects.create(
                                nome_linha="slitter",  # ajuste conforme necessário
                                inicio_parada=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            )
                            print(f"🔴 Linha PAROU às {parada_atual.inicio_parada}")

                        # --- Fim da parada (linha estava parada e voltou a rodar) ---
                        elif last_state is False and current_state is True and parada_atual:
                            parada_atual.fim_parada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            parada_atual.save()
                            print(f"🟢 Linha VOLTOU às {parada_atual.fim_parada}")
                            parada_atual = None

                        # Atualiza o estado anterior
                        last_state = current_state

                    else:
                        print("⏳ Mudança ignorada (debounce ativo, possível oscilação).")

                time.sleep(0.5)

            except Exception as e:
                print(f"⚠️ Erro na leitura: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"❌ Ocorreu um erro ao conectar: {e}")

    finally:
        client.disconnect()
        print("🔌 Desconectado do PLC.")
