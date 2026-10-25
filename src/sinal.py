"""Monta o signal.json. Na fundação o sinal é sempre SEGURA nível 1: ainda não há nada calibrado."""
import json

from src import historico

MOTIVO_TESTE = "Sistema em fase de testes: sinal ainda não calibrado"


def _num(x):
    return None if x in (None, "") else float(x)


def montar(agora, status_preco, linhas_deriv, erros_deriv, duracao_s):
    velas = historico.ler_desde("preco_15m", agora - 26 * 3600)
    preco = variacao = ultima = fonte_preco = None
    if velas:
        v = velas[-1]
        preco, ultima, fonte_preco = _num(v["close"]), v["ts"], v["fonte"]
        alvo = int(v["ts_unix"]) - 86400
        antiga = next((x for x in velas if int(x["ts_unix"]) >= alvo), None)
        if antiga and int(antiga["ts_unix"]) <= alvo + 900:
            variacao = round((preco / _num(antiga["close"]) - 1) * 100, 2)

    deriv = {l["fonte"]: {"funding_8h": l["funding_8h"], "oi_btc": l["oi_btc"], "oi_usd": l["oi_usd"]}
             for l in linhas_deriv}
    fundings = [l["funding_8h"] for l in linhas_deriv]
    atraso_min = round((agora - historico.ultimo_ts("preco_15m")) / 60) if velas else None

    fora = sorted(set(erros_deriv) | {e.split(":")[0] for s in status_preco.values() for e in s["erros"]})
    sinal_teste = {"acao": "SEGURA", "nivel": 1, "motivos": [MOTIVO_TESTE]}
    return {
        "versao": "0.1-fundacao",
        "status": "em_teste",
        "atualizado_em": historico.iso(agora),
        "preco_usd": preco,
        "preco_fonte": fonte_preco,
        "ultima_vela_15m": ultima,
        "atraso_dados_min": atraso_min,
        "variacao_24h_pct": variacao,
        "regime": None,
        "sinais": {"curto": sinal_teste, "medio": sinal_teste, "longo": sinal_teste},
        "derivativos": {
            "por_fonte": deriv,
            "funding_8h_medio": round(sum(fundings) / len(fundings), 8) if fundings else None,
            "oi_btc_total": round(sum(l["oi_btc"] or 0 for l in linhas_deriv), 2) if linhas_deriv else None,
        },
        "placar": None,
        "fontes_fora_do_ar": fora,
        "execucao": {"duracao_s": round(duracao_s, 1),
                     "velas_novas": {k: s["novas"] for k, s in status_preco.items()}},
    }


def salvar(dados):
    arquivo = historico.raiz() / "signal.json"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n")
