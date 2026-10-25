"""Grava e lê o histórico em CSV, particionado por mês ou ano, sem duplicar linhas."""
import csv
import os
from datetime import datetime, timezone
from pathlib import Path


def raiz():
    return Path(os.environ.get("DATA_DIR", "dados"))


def iso(ts_unix):
    return datetime.fromtimestamp(int(ts_unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _arquivo(pasta, ts_unix, por):
    dt = datetime.fromtimestamp(int(ts_unix), tz=timezone.utc)
    nome = f"{dt.year}-{dt.month:02d}.csv" if por == "mes" else f"{dt.year}.csv"
    return raiz() / pasta / nome


def _ler(arquivo):
    if not arquivo.exists():
        return []
    with open(arquivo, newline="") as f:
        return list(csv.DictReader(f))


def gravar(pasta, linhas, campos, chave, por="mes"):
    """Junta `linhas` ao histórico. Linhas com a mesma chave são substituídas. Devolve quantas são novas."""
    grupos = {}
    for l in linhas:
        grupos.setdefault(_arquivo(pasta, l["ts_unix"], por), []).append(l)
    novas = 0
    for arquivo, lote in grupos.items():
        existentes = {tuple(str(r[c]) for c in chave): r for r in _ler(arquivo)}
        for l in lote:
            k = tuple(str(l[c]) for c in chave)
            if k not in existentes:
                novas += 1
            existentes[k] = {c: l.get(c, "") for c in campos}
        ordem = sorted(existentes.values(), key=lambda r: (int(r["ts_unix"]), str(r.get("fonte", ""))))
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = arquivo.with_suffix(".tmp")
        with open(tmp, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(ordem)
        tmp.replace(arquivo)
    return novas


def arquivos(pasta):
    p = raiz() / pasta
    return sorted(p.glob("*.csv")) if p.exists() else []


def ultimo_ts(pasta):
    for arquivo in reversed(arquivos(pasta)):
        linhas = _ler(arquivo)
        if linhas:
            return max(int(r["ts_unix"]) for r in linhas)
    return None


def ler_desde(pasta, desde_unix):
    saida = []
    for arquivo in reversed(arquivos(pasta)):
        linhas = _ler(arquivo)
        saida = [r for r in linhas if int(r["ts_unix"]) >= desde_unix] + saida
        if linhas and min(int(r["ts_unix"]) for r in linhas) < desde_unix:
            break
    return saida


CAMPOS_FALHA = ["ts", "fonte", "tipo", "erro"]


def registrar_falha(fonte, tipo, erro, agora):
    arquivo = raiz() / "falhas.csv"
    novo = not arquivo.exists()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_FALHA)
        if novo:
            w.writeheader()
        w.writerow({"ts": iso(agora), "fonte": fonte, "tipo": tipo, "erro": str(erro)[:300]})
