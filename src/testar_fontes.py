"""Testa cada fonte de dados a partir do servidor do GitHub e grava um relatório.

Responde: a fonte funciona daqui? quanto tempo demora? quanto histórico devolve?
Saída: dados/relatorios/fontes.json e um resumo na página da execução do GitHub.
"""
import json
import os
import time

from src import historico
from src.coletores import derivativos, preco
from src.rede import pedir_json


def _velas(linhas):
    return {"velas": len(linhas), "primeira": linhas and min(l["ts"] for l in linhas),
            "ultima": linhas and max(l["ts"] for l in linhas)}


def _hist(linhas):
    return {"registros": len(linhas), "mais_antigo": linhas[0]["ts"] if linhas else None,
            "mais_recente": linhas[-1]["ts"] if linhas else None}


def testes(agora):
    slot = agora // 900 * 900
    return [
        ("coinbase preço 15m (últimas 3h)", lambda: _velas(preco.coinbase(900, agora - 3 * 3600, agora))),
        ("coinbase preço 1d (2015)", lambda: _velas(preco.coinbase(86400, 1437350400, 1437350400 + 200 * 86400))),
        ("kraken preço 15m", lambda: _velas(preco.kraken(900, agora - 3 * 3600))),
        ("kraken preço 1d (profundidade)", lambda: _velas(preco.kraken(86400, 1437350400))),
        ("okx funding + open interest", lambda: derivativos.okx(slot)),
        ("bybit funding + open interest", lambda: derivativos.bybit(slot)),
        ("deribit funding + open interest", lambda: derivativos.deribit(slot)),
        ("hyperliquid funding + open interest", lambda: derivativos.hyperliquid(slot)),
        ("okx histórico de funding", lambda: _hist(derivativos.hist_okx(max_paginas=40))),
        ("bybit histórico de funding", lambda: _hist(derivativos.hist_bybit(max_paginas=3))),
        ("deribit histórico de funding (jan/2019)",
         lambda: _hist(derivativos.hist_deribit(agora_ms=1546300800000 + 3 * 86400000))),
        ("hyperliquid histórico de funding", lambda: _hist(derivativos.hist_hyperliquid(max_paginas=1))),
        ("onde roda o servidor", lambda: {k: v for k, v in pedir_json("https://ipinfo.io/json").items()
                                          if k in ("country", "region", "org")}),
    ]


def main():
    agora = int(time.time())
    resultados = []
    for nome, fn in testes(agora):
        t = time.time()
        try:
            r = {"teste": nome, "ok": True, "detalhe": fn()}
        except Exception as e:
            r = {"teste": nome, "ok": False, "detalhe": f"{type(e).__name__}: {e}"[:300]}
        r["segundos"] = round(time.time() - t, 2)
        resultados.append(r)
        print(("OK   " if r["ok"] else "FALHA") + f" {nome}: {r['detalhe']}")

    rel = {"testado_em": historico.iso(agora), "resultados": resultados}
    destino = historico.raiz() / "relatorios" / "fontes.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(rel, ensure_ascii=False, indent=2, default=str) + "\n")

    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a") as f:
            f.write("## Teste das fontes\n\n| Fonte | Resultado | Tempo |\n|---|---|---|\n")
            for r in resultados:
                det = json.dumps(r["detalhe"], ensure_ascii=False, default=str).replace("|", "/")[:180]
                f.write(f"| {r['teste']} | {'✅' if r['ok'] else '❌'} {det} | {r['segundos']}s |\n")


if __name__ == "__main__":
    main()
