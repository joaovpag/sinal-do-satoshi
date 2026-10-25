"""Velas de preço do BTC em USD. Primária: Coinbase. Reserva: Kraken."""
import time

from src import historico
from src.rede import ErroFonte, pedir_json

GRAN = {"15m": 900, "1h": 3600, "1d": 86400}
POR = {"15m": "mes", "1h": "ano", "1d": "ano"}
CAMPOS = ["ts", "ts_unix", "open", "high", "low", "close", "volume", "fonte"]
# Quanto buscar para trás quando ainda não há histórico (o download longo cobre o resto)
JANELA_INICIAL = {"15m": 3 * 86400, "1h": 30 * 86400, "1d": 400 * 86400}


def _linha(t, o, h, l, c, v, fonte):
    vals = [float(x) for x in (o, h, l, c, v)]
    if min(vals[:4]) <= 0 or not (vals[2] <= min(vals[0], vals[3]) and vals[1] >= max(vals[0], vals[3])):
        raise ValueError(f"vela inválida em {t}: {vals}")
    return {"ts": historico.iso(t), "ts_unix": int(t), "open": vals[0], "high": vals[1],
            "low": vals[2], "close": vals[3], "volume": vals[4], "fonte": fonte}


def parse_coinbase(data):
    if not isinstance(data, list):
        raise ErroFonte(f"coinbase: resposta inesperada {str(data)[:120]}")
    # formato: [time, low, high, open, close, volume]
    return [_linha(r[0], r[3], r[2], r[1], r[4], r[5], "coinbase") for r in data]


def coinbase(gran, inicio, fim):
    linhas, t = [], inicio
    while t <= fim:
        fim_lote = min(t + 299 * gran, fim)
        try:
            data = pedir_json("https://api.exchange.coinbase.com/products/BTC-USD/candles",
                              {"granularity": gran, "start": historico.iso(t), "end": historico.iso(fim_lote)})
            linhas += parse_coinbase(data)
        except (ErroFonte, ValueError, IndexError, TypeError) as e:
            raise ErroFonte(f"coinbase: {e}", parcial=linhas)
        t = fim_lote + gran
        time.sleep(0.15)
    return linhas


def parse_kraken(data):
    if data.get("error"):
        raise ErroFonte(f"kraken: {data['error']}")
    res = data["result"]
    chave = next(k for k in res if k != "last")
    # formato: [time, open, high, low, close, vwap, volume, count]
    return [_linha(r[0], r[1], r[2], r[3], r[4], r[6], "kraken") for r in res[chave]]


def kraken(gran, inicio):
    """A Kraken só devolve as últimas 720 velas."""
    try:
        data = pedir_json("https://api.kraken.com/0/public/OHLC",
                          {"pair": "XBTUSD", "interval": gran // 60, "since": inicio - 1})
        return parse_kraken(data)
    except (ErroFonte, ValueError, KeyError, StopIteration, IndexError, TypeError) as e:
        raise ErroFonte(f"kraken: {e}")


def atualizar(nome, agora, desde=None):
    """Completa o histórico `preco_<nome>` até a última vela fechada."""
    gran = GRAN[nome]
    pasta = f"preco_{nome}"
    ultimo = historico.ultimo_ts(pasta)
    inicio = ultimo + gran if ultimo else (desde or (agora - JANELA_INICIAL[nome]) // gran * gran)
    ultima_fechada = agora // gran * gran - gran
    status = {"novas": 0, "fonte": None, "erros": []}
    if inicio > ultima_fechada:
        return status

    linhas = []
    try:
        linhas = coinbase(gran, inicio, ultima_fechada)
        status["fonte"] = "coinbase"
    except ErroFonte as e:
        status["erros"].append(str(e))
        historico.registrar_falha("coinbase", f"preco_{nome}", e, agora)
        linhas = e.parcial
        resto = (max(int(l["ts_unix"]) for l in linhas) + gran) if linhas else inicio
        try:
            linhas += kraken(gran, resto)
            status["fonte"] = "kraken"
        except ErroFonte as e2:
            status["erros"].append(str(e2))
            historico.registrar_falha("kraken", f"preco_{nome}", e2, agora)

    linhas = [l for l in linhas if inicio <= l["ts_unix"] <= ultima_fechada]
    if linhas:
        primeira = min(l["ts_unix"] for l in linhas)
        if primeira > inicio and ultimo:
            historico.registrar_falha(status["fonte"] or "-", f"lacuna_{nome}",
                                      f"faltam velas de {historico.iso(inicio)} a {historico.iso(primeira - gran)}", agora)
    status["novas"] = historico.gravar(pasta, linhas, CAMPOS, ("ts_unix",), POR[nome])
    return status
