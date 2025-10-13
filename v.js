function enviarMotivo(nome_linha, inicio_parada, fim_parada, motivo) {
    fetch("{% url 'registrar_motivo' %}", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": "{{ csrf_token }}"
        },
        body: new URLSearchParams({
            nome_linha: nome_linha,
            inicio_parada: inicio_parada,
            fim_parada: fim_parada,
            motivo: motivo
        })
    }).then(response => response.json())
      .then(data => {
          if (data.status === "ok") {
              // Remove a linha da tabela sem recarregar tudo
              const row = document.querySelector(
                  `tr:has(td:first-child:contains('${nome_linha}'))`
              );
              if (row) row.remove();
          }
      });
}
