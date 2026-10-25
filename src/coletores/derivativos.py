"""Funding rate e open interest do BTC perpétuo.

Diferente do preço, aqui coletamos de TODAS as fontes que responderem, uma linha por fonte:
cada corretora tem seu próprio funding e open interest, então trocar de fonte quebraria a série.
Funding é normalizado para "taxa equivalente a 8 horas" (funding_8h) para dar para comparar.
Open interest em BTC (oi_btc) e em dólares (oi_usd).
"""
import time

from src import historico
from src.rede import ErroFonte, pedir_json

CAMPOS = ["ts", "ts_unix", "fonte", "funding_8h", "funding_bruto", "intervalo_h", "oi_btc", "oi_usd", "preco_mark"]
CAMPOS_HIST = ["ts", "ts_unix", "fonte", "funding_bruto", "intervalo_h", "funding_8h"]


def _f(x):
    return None if x in (None, "") else float(x)


def _linha(fonte, slot, funding, intervalo_h, oi_btc, mark, oi_usd=None):
    funding = _f(funding)
    oi_btc, mark = _f(oi_btc), _f(mark)
    oi_usd = _f(oi_usd) if oi_usd not in (None, "") else (oi_btc * mark if oi_btc and mark else None)
    if funding is None or abs(funding) > 0.05:
        raise ValueError(f"{fonte}: funding fora do esperado ({funding})")
    return {"ts": historico.iso(slot), "ts_unix": slot, "fonte": fonte,
            "funding_8h": round(funding * 8 / intervalo_h, 10), "funding_bruto": funding,
            "intervalo_h": intervalo_h, "oi_btc": oi_btc, "oi_usd": oi_usd, "preco_mark": mark}


def _okx(path, params):
    d = pedir_json("https://www.okx.com" + path, params)
    if str(d.get("code")) != "0" or not d.get("data"):
        raise ErroFonte(f"okx {path}: {str(d)[:150]}")
    return d["data"]


def okx(slot):
    inst = {"instId": "BTC-USDT-SWAP"}
    fr = _okx("/api/v5/public/funding-rate", inst)[0]
    intervalo = 8
    if fr.get("fundingTime") and fr.get("nextFundingTime"):
        intervalo = round((int(fr["nextFundingTime"]) - int(fr["fundingTime"])) / 3_600_000) or 8
    oi = _okx("/api/v5/public/open-interest", {"instType": "SWAP", **inst})[0]
    mk = _okx("/api/v5/public/mark-price", {"instType": "SWAP", **inst})[0]
    return _linha("okx", slot, fr["fundingRate"], intervalo, oi.get("oiCcy"), mk.get("markPx"), oi.get("oiUsd"))


def bybit(slot):
    d = pedir_json("https://api.bybit.com/v5/market/tickers", {"category": "linear", "symbol": "BTCUSDT"})
    if d.get("retCode") != 0:
        raise ErroFonte(f"bybit: {str(d)[:150]}")
    t = d["result"]["list"][0]
    intervalo = int(t.get("fundingIntervalHour") or 8)
    return _linha("bybit", slot, t["fundingRate"], intervalo, t["openInterest"], t["markPrice"], t.get("openInterestValue"))


def deribit(slot):
    d = pedir_json("https://www.deribit.com/api/v2/public/ticker", {"instrument_name": "BTC-PERPETUAL"})
    r = d["result"]
    mark = float(r["mark_price"])
    # no perpétuo inverso da Deribit o open interest vem em dólares
    oi_usd = float(r["open_interest"])
    return _linha("deribit", slot, r["funding_8h"], 8, oi_usd / mark, mark, oi_usd)


def hyperliquid(slot):
    meta, ctxs = pedir_json("https://api.hyperliquid.xyz/info", corpo={"type": "metaAndAssetCtxs"})
    i = next(i for i, a in enumerate(meta["universe"]) if a["name"] == "BTC")
    c = ctxs[i]
    return _linha("hyperliquid", slot, c["funding"], 1, c["openInterest"], c["markPx"])


FONTES = [("okx", okx), ("bybit", bybit), ("deribit", deribit), ("hyperliquid", hyperliquid)]


def coletar(agora):
    slot = agora // 900 * 900
    linhas, erros = [], {}
    for nome, fn in FONTES:
        try:
            linhas.append(fn(slot))
        except Exception as e:  # qualquer falha de uma fonte não pode derrubar as outras
            erros[nome] = f"{type(e).__name__}: {e}"
            historico.registrar_falha(nome, "derivativos", erros[nome], agora)
    historico.gravar("derivativos", linhas, CAMPOS, ("ts_unix", "fonte"), "mes")
    return linhas, erros


# ---------- histórico de funding (download longo) ----------

def _com_intervalo(fonte, pares, intervalo_fixo=None):
    """pares = [(ts_ms, taxa)]. Calcula o intervalo pela distância entre pagamentos."""
    pares = sorted(set(pares))
    saida = []
    for i, (ts, taxa) in enumerate(pares):
        if intervalo_fixo:
            iv = intervalo_fixo
        else:
            iv = round((ts - pares[i - 1][0]) / 3_600_000) if i else 8
            iv = iv if iv in (1, 2, 4, 8) else 8
        t = int(ts) // 1000
        taxa = float(taxa)
        saida.append({"ts": historico.iso(t), "ts_unix": t, "fonte": fonte, "funding_bruto": taxa,
                      "intervalo_h": iv, "funding_8h": round(taxa * 8 / iv, 10)})
    return saida


def hist_okx(max_paginas=300):
    pares, after = [], None
    for _ in range(max_paginas):
        p = {"instId": "BTC-USDT-SWAP", "limit": 100}
        if after:
            p["after"] = after
        try:
            data = _okx("/api/v5/public/funding-rate-history", p)
        except ErroFonte as e:
            if pares and "data" in str(e):
                break
            raise
        pares += [(int(r["fundingTime"]), r.get("realizedRate") or r["fundingRate"]) for r in data]
        novo = min(int(r["fundingTime"]) for r in data)
        if after and novo >= int(after):
            break
        after = str(novo)
        time.sleep(0.25)
    return _com_intervalo("okx", pares)


def hist_bybit(max_paginas=150):
    pares, fim = [], None
    for _ in range(max_paginas):
        p = {"category": "linear", "symbol": "BTCUSDT", "limit": 200}
        if fim:
            p["endTime"] = fim
        d = pedir_json("https://api.bybit.com/v5/market/funding/history", p)
        if d.get("retCode") != 0:
            raise ErroFonte(f"bybit: {str(d)[:150]}")
        lista = d["result"]["list"]
        if not lista:
            break
        pares += [(int(r["fundingRateTimestamp"]), r["fundingRate"]) for r in lista]
        novo = min(int(r["fundingRateTimestamp"]) for r in lista) - 1
        if fim and novo >= fim:
            break
        fim = novo
        time.sleep(0.2)
    return _com_intervalo("bybit", pares)


def hist_deribit(inicio_ms=1546300800000, agora_ms=None, max_paginas=200):
    """Amostras de hora em hora da taxa equivalente a 8h (interest_8h), desde 2019."""
    agora_ms = agora_ms or int(time.time() * 1000)
    pares, t, janela = [], inicio_ms, 30 * 24 * 3_600_000
    for _ in range(max_paginas):
        if t >= agora_ms:
            break
        d = pedir_json("https://www.deribit.com/api/v2/public/get_funding_rate_history",
                       {"instrument_name": "BTC-PERPETUAL", "start_timestamp": t,
                        "end_timestamp": min(t + janela, agora_ms)})
        pares += [(int(r["timestamp"]), r["interest_8h"]) for r in d.get("result", [])]
        t += janela
        time.sleep(0.2)
    return _com_intervalo("deribit", pares, intervalo_fixo=8)


def hist_hyperliquid(inicio_ms=1672531200000, max_paginas=200):
    pares, t = [], inicio_ms
    for _ in range(max_paginas):
        lista = pedir_json("https://api.hyperliquid.xyz/info",
                           corpo={"type": "fundingHistory", "coin": "BTC", "startTime": t})
        if not lista:
            break
        pares += [(int(r["time"]), r["fundingRate"]) for r in lista]
        novo = max(int(r["time"]) for r in lista) + 1
        if novo <= t:
            break
        t = novo
        if len(lista) < 500:
            break
        time.sleep(0.2)
    return _com_intervalo("hyperliquid", pares, intervalo_fixo=1)


HISTORICOS = [("okx", hist_okx), ("bybit", hist_bybit), ("deribit", hist_deribit), ("hyperliquid", hist_hyperliquid)]
