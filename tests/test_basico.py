"""Testes sem internet: leitura das respostas das APIs e gravação do histórico.

Rodar: python -m unittest discover -s tests
"""
import os
import tempfile
import unittest
from unittest import mock


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class TestParsers(Base):
    def test_coinbase(self):
        from src.coletores.preco import parse_coinbase
        # [time, low, high, open, close, volume]
        l = parse_coinbase([[1700000900, 99, 110, 100, 105, 12.5]])[0]
        self.assertEqual((l["open"], l["high"], l["low"], l["close"]), (100, 110, 99, 105))

    def test_kraken(self):
        from src.coletores.preco import parse_kraken
        d = {"error": [], "result": {"XXBTZUSD": [[1700000900, "100", "110", "99", "105", "103", "7.1", 50]],
                                     "last": 1700000900}}
        l = parse_kraken(d)[0]
        self.assertEqual((l["close"], l["volume"], l["fonte"]), (105, 7.1, "kraken"))

    def test_vela_invalida(self):
        from src.coletores.preco import parse_coinbase
        with self.assertRaises(ValueError):
            parse_coinbase([[1700000900, 120, 110, 100, 105, 1]])  # low > high

    def test_funding_normalizado(self):
        from src.coletores import derivativos
        meta = {"universe": [{"name": "ETH"}, {"name": "BTC"}]}
        ctx = [{}, {"funding": "0.0000125", "openInterest": "1000", "markPx": "60000"}]
        with mock.patch.object(derivativos, "pedir_json", return_value=[meta, ctx]):
            l = derivativos.hyperliquid(1700000000)
        self.assertAlmostEqual(l["funding_8h"], 0.0001)
        self.assertEqual(l["oi_usd"], 60_000_000)

    def test_intervalo_funding(self):
        from src.coletores.derivativos import _com_intervalo
        h = 3_600_000
        linhas = _com_intervalo("x", [(0, "0.0001"), (8 * h, "0.0001"), (12 * h, "0.00005")])
        self.assertEqual([l["intervalo_h"] for l in linhas], [8, 8, 4])
        self.assertAlmostEqual(linhas[2]["funding_8h"], 0.0001)


class TestHistorico(Base):
    def test_sem_duplicar(self):
        from src import historico
        from src.coletores.preco import CAMPOS, parse_coinbase
        a = parse_coinbase([[1700000000, 99, 110, 100, 105, 1], [1700000900, 99, 110, 100, 106, 1]])
        self.assertEqual(historico.gravar("p", a, CAMPOS, ("ts_unix",)), 2)
        b = parse_coinbase([[1700000900, 99, 110, 100, 107, 1], [1700001800, 99, 110, 100, 108, 1]])
        self.assertEqual(historico.gravar("p", b, CAMPOS, ("ts_unix",)), 1)
        self.assertEqual(historico.ultimo_ts("p"), 1700001800)
        linhas = historico.ler_desde("p", 0)
        self.assertEqual([float(l["close"]) for l in linhas], [105, 107, 108])

    def test_atualizar_com_reserva(self):
        """Coinbase cai no meio; o que já veio é mantido e a Kraken completa o resto."""
        from src import historico
        from src.coletores import preco
        from src.rede import ErroFonte
        agora = 1700000000 // 900 * 900 + 10
        v = lambda t, f: {"ts": historico.iso(t), "ts_unix": t, "open": 1, "high": 1, "low": 1,
                          "close": 1, "volume": 1, "fonte": f}
        base = agora // 900 * 900 - 10 * 900
        parcial = [v(base + i * 900, "coinbase") for i in range(4)]

        def cb(*_):
            raise ErroFonte("caiu", parcial=list(parcial))
        resto = [v(base + i * 900, "kraken") for i in range(4, 12)]  # inclui vela ainda aberta
        with mock.patch.object(preco, "coinbase", cb), mock.patch.object(preco, "kraken", return_value=resto):
            st = preco.atualizar("15m", agora, desde=base)
        self.assertEqual(st["fonte"], "kraken")
        linhas = historico.ler_desde("preco_15m", 0)
        self.assertEqual(len(linhas), 10)  # velas abertas descartadas
        self.assertTrue((historico.raiz() / "falhas.csv").exists())


class TestSinal(Base):
    def test_signal_em_teste(self):
        from src import historico, sinal
        from src.coletores.preco import CAMPOS
        agora = 1700100000
        t0 = agora // 900 * 900 - 100 * 900
        linhas = [{"ts": historico.iso(t0 + i * 900), "ts_unix": t0 + i * 900, "open": 100, "high": 120,
                   "low": 90, "close": 100 + i, "volume": 1, "fonte": "coinbase"} for i in range(100)]
        historico.gravar("preco_15m", linhas, CAMPOS, ("ts_unix",))
        d = sinal.montar(agora, {"15m": {"novas": 1, "fonte": "coinbase", "erros": []}}, [], {"okx": "x"}, 1.0)
        self.assertEqual(d["preco_usd"], 199)
        self.assertEqual(d["variacao_24h_pct"], round((199 / 103 - 1) * 100, 2))
        self.assertEqual(d["sinais"]["curto"]["acao"], "SEGURA")
        self.assertEqual(d["fontes_fora_do_ar"], ["okx"])


if __name__ == "__main__":
    unittest.main()
