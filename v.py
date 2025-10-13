# views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ParadasLinha, MotivosParadas
import csv
from datetime import datetime, timedelta

def tabela_paradas(request):
    """Renderiza a tabela com as paradas atuais (sem motivo definido)."""
    paradas = ParadasLinha.objects.all().order_by("-inicio_parada")
    return render(request, 'producao/tabela_paradas.html', {'paradas': paradas})


@csrf_exempt
def registrar_motivo(request):
    """Move uma parada de ParadasLinha para MotivosParadas, sem duplicar."""
    if request.method == "POST":
        nome_linha = (request.POST.get("nome_linha") or "").strip()
        inicio_parada = (request.POST.get("inicio_parada") or "").strip()
        fim_parada = request.POST.get("fim_parada")
        motivo = (request.POST.get("motivo") or "").strip()

        # Normaliza valor do fim_parada
        if fim_parada in ["None", "", None]:
            fim_parada_db = None
        else:
            fim_parada_db = fim_parada.strip()

        # 1️⃣ Verifica se já existe o mesmo registro em MotivosParadas
        ja_existe = MotivosParadas.objects.filter(
            nome_linha=nome_linha,
            inicio_parada=inicio_parada,
            fim_parada=fim_parada_db
        ).exists()

        if ja_existe:
            print(f"[INFO] Registro duplicado ignorado: {nome_linha} | {inicio_parada}")
            return JsonResponse({"status": "duplicado"})

        # 2️⃣ Cria novo registro em MotivosParadas
        MotivosParadas.objects.create(
            nome_linha=nome_linha,
            inicio_parada=inicio_parada,
            fim_parada=fim_parada_db,
            motivo=motivo,
        )
        print(f"[OK] Novo motivo registrado: {nome_linha} | {motivo}")

        # 3️⃣ Tenta excluir da tabela ParadasLinha (sem exigir igualdade exata de fim_parada)
        deletados, _ = ParadasLinha.objects.filter(
            nome_linha=nome_linha,
            inicio_parada=inicio_parada
        ).delete()

        if deletados > 0:
            print(f"[OK] {deletados} registro(s) removido(s) de ParadasLinha.")
        else:
            print(f"[WARN] Nenhum registro removido de ParadasLinha para {nome_linha}.")

        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "erro"}, status=400)


def exportar_csv(request, filtro):
    """Exporta os registros de MotivosParadas filtrados por período."""
    hoje = datetime.now()

    # Define o intervalo de tempo
    if filtro == "7dias":
        inicio = hoje - timedelta(days=7)
    elif filtro == "1mes":
        inicio = hoje - timedelta(days=30)
    elif filtro == "6meses":
        inicio = hoje - timedelta(days=180)
    elif filtro == "1ano":
        inicio = hoje - timedelta(days=365)
    else:
        inicio = None

    # Função auxiliar para converter strings em datetime
    def parse_datetime(dt_str):
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    registros = MotivosParadas.objects.all()

    # Filtra por data de início da parada, se necessário
    if inicio:
        registros = [
            r for r in registros
            if parse_datetime(str(r.inicio_parada)) and parse_datetime(str(r.inicio_parada)) >= inicio
        ]

    # Gera o CSV para download
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="motivos_paradas_{filtro}.csv"'

    writer = csv.writer(response, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["ID", "Nome da Linha", "Inicio da Parada", "Fim da Parada", "Motivo"])

    for r in registros:
        writer.writerow([
            r.id,
            str(r.nome_linha),
            str(r.inicio_parada),
            str(r.fim_parada) if r.fim_parada else "",
            str(r.motivo)
        ])

    return response
