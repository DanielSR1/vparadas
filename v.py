import os
import time
import django
import snap7
from snap7.util import get_bool
from datetime import datetime
from producao.models import ParadasLinha

PLC_IP = "192.168.0.1"
RACK = 0
SLOT = 3
DB_NUMBER = 1
BYTE_INDEX = 0
BIT_INDEX = 1

def main():
    client = snap7.client.Client()
    try:
        client.connect(PLC_IP, RACK, SLOT)
        if client.get_connected():
            print(f"✅ Conectado ao PLC em {PLC_IP}")

            last_state = None
            parada_atual = None

            while True:
                try:
                    data = client.db_read(DB_NUMBER, BYTE_INDEX, 1)
                    current_state = get_bool(data, 0, BIT_INDEX)

                    # Detecta início da parada
                    if last_state is True and current_state is False:
                        if not parada_atual:  # garante que não há parada aberta
                            parada_atual = ParadasLinha.objects.create(
                                nome_linha="slitter",
                                inicio_parada=datetime.now(),
                            )
                            print(f"🔴 Linha PAROU às {parada_atual.inicio_parada}")

                    # Detecta fim da parada
                    elif last_state is False and current_state is True:
                        if parada_atual:  # só encerra se houver uma aberta
                            parada_atual.fim_parada = datetime.now()
                            parada_atual.save()
                            print(f"🟢 Linha VOLTOU às {parada_atual.fim_parada}")
                            parada_atual = None

                    last_state = current_state
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
