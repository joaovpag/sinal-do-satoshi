"""Download único do histórico longo. Roda sozinho na primeira coleta (quando falta o marcador).

- Preço diário e de 1h desde 2015 (Coinbase)
- Preço de 15 min dos últimos 2 anos (Coinbase)
- Histórico de funding de cada corretora que responder

Uso: DATA_DIR=dados python -m src.baixar_historico
"""
import json
import time

from src import historico
from src.coletores import derivativos, preco

INICIO_COINBASE = 1437350400  # 20/07/2015, início do BTC-USD na Coinbase
MARCADOR = ".historico_ok.json"


def main():
    agora = int(time.time())
    resumo = {"inicio": historico.iso(agora), "preco": {}, "funding": {}}
    desde = {"1d": INICIO_COINBASE, "1h": INICIO_COINBASE, "15m": (agora - 730 * 86400) // 900 * 900}
    for nome, d in desde.items():
        t = time.time()
        st = preco.atualizar(nome, agora, desde=d)
        resumo["preco"][nome] = {**st, "segundos": round(time.time() - t)}
        print(f"histórico preço {nome}: {resumo['preco'][nome]}")

    for nome, fn in derivativos.HISTORICOS:
        try:
            linhas = fn()
            n = historico.gravar(f"funding_hist/{nome}", linhas, derivativos.CAMPOS_HIST, ("ts_unix",), "ano")
            resumo["funding"][nome] = {"linhas": n, "desde": linhas[0]["ts"] if linhas else None}
        except Exception as e:
            resumo["funding"][nome] = {"erro": f"{type(e).__name__}: {e}"[:300]}
            historico.registrar_falha(nome, "funding_hist", e, agora)
        print(f"histórico funding {nome}: {resumo['funding'][nome]}")

    resumo["fim"] = historico.iso(int(time.time()))
    (historico.raiz() / MARCADOR).write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
