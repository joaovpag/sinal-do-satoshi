# Sinal do Satoshi

Uso pessoal, não comercial. Diz **COMPRA, SEGURA ou VENDE** Bitcoin em três horizontes, com confiança de 1 a 5, e foco em proteger contra quedas.

- Planejamento completo: [`docs/sinal-do-satoshi.md`](docs/sinal-do-satoshi.md)
- Etapa atual (Fundação): [`docs/fundacao.md`](docs/fundacao.md)

## Como funciona agora

O GitHub Actions roda a cada 15 minutos (`.github/workflows/coleta.yml`):

1. Coleta velas de preço (Coinbase, reserva Kraken) em 15m, 1h e 1d.
2. Coleta funding rate e open interest de OKX, Bybit, Deribit e Hyperliquid.
3. Grava tudo em CSV no ramo [`dados`](../../tree/dados) e publica o `signal.json`.

Na primeira execução, ele também baixa o histórico longo de preço (desde 2015) e de funding.

**signal.json:** https://raw.githubusercontent.com/joaovpag/sinal-do-satoshi/dados/signal.json

Na fundação, o sinal é sempre `SEGURA` nível 1 ("em teste"), porque nada foi calibrado ainda.

## Rodar no computador

```bash
DATA_DIR=dados python -m src.testar_fontes     # testa as fontes
DATA_DIR=dados python -m src.coletar           # uma coleta
python -m unittest discover -s tests -t .      # testes sem internet
```

Só usa a biblioteca padrão do Python (3.11+).
