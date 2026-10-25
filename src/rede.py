"""Chamadas HTTP com repetição em caso de erro temporário. Só biblioteca padrão."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "sinal-do-satoshi/0.1 (+https://github.com/joaovpag/sinal-do-satoshi)"


class ErroFonte(Exception):
    """Falha de uma fonte. `parcial` guarda o que já tinha sido coletado."""

    def __init__(self, msg, parcial=None):
        super().__init__(msg)
        self.parcial = parcial or []


def pedir_json(url, params=None, corpo=None, timeout=20, tentativas=3):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": UA, "Accept": "application/json"}
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo).encode()
        headers["Content-Type"] = "application/json"
    ultimo = "sem resposta"
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, data=dados, headers=headers,
                                         method="POST" if dados else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            trecho = e.read()[:200].decode(errors="replace")
            ultimo = f"HTTP {e.code}: {trecho}"
            # 429 e 5xx são temporários; o resto (ex.: 403 bloqueio por país) não adianta repetir
            if e.code != 429 and e.code < 500:
                raise ErroFonte(ultimo)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            ultimo = f"{type(e).__name__}: {e}"
        time.sleep(2 * (i + 1))
    raise ErroFonte(ultimo)
