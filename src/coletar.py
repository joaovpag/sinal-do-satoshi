"""Execução de cada 15 minutos: preço + derivativos + signal.json.

Uso: DATA_DIR=dados python -m src.coletar
"""
import time

from src import historico, sinal
from src.coletores import derivativos, preco


def main():
    inicio = time.time()
    agora = int(inicio)
    status_preco = {}
    for nome in ("15m", "1h", "1d"):
        try:
            status_preco[nome] = preco.atualizar(nome, agora)
        except Exception as e:  # nunca deixar uma parte derrubar a execução inteira
            status_preco[nome] = {"novas": 0, "fonte": None, "erros": [f"preco_{nome}: {e}"]}
            historico.registrar_falha("preco", f"preco_{nome}", e, agora)
        print(f"preço {nome}: {status_preco[nome]}")

    linhas, erros = derivativos.coletar(agora)
    print(f"derivativos: {[l['fonte'] for l in linhas]} ok; erros: {erros}")

    dados = sinal.montar(agora, status_preco, linhas, erros, time.time() - inicio)
    sinal.salvar(dados)
    print(f"preço atual: {dados['preco_usd']} | fora do ar: {dados['fontes_fora_do_ar']}")


if __name__ == "__main__":
    main()
