# Sinal do Satoshi — Documento Base (v0.1)

> Uso pessoal, fechado e não comercial. Tudo roda em ferramentas gratuitas.
> Criado em 25/10/2026. Este documento é a fonte da verdade do projeto: decisões novas entram aqui antes de virar código.

---

## 1. Objetivo

Um sistema que diz **COMPRA, SEGURA ou VENDE** Bitcoin, em **vários horizontes de tempo**, com um **nível de confiança de 1 a 5** em cada sinal, e que mostra o porquê.

Prioridade número 1: **proteger contra quedas**. O erro mais caro do sistema é dizer "compra" ou "segura" logo antes de uma queda forte. Perder parte de uma alta é um erro aceitável; tomar uma queda cheia não é.

### Princípio de honestidade
Nenhum cruzamento de dados torna o mercado previsível com certeza. O sistema não "acha" que tem certeza: ele **mede a própria taxa de acerto histórica** e só exibe nível 5 quando aquele tipo de sinal, naquele tipo de mercado, acertou muito no passado e continua acertando no presente. A confiança é um número testado, não uma opinião.

---

## 2. Decisões já tomadas

| Tema | Decisão |
|---|---|
| Horizontes | Vários: curto, médio e longo (ver seção 3) |
| Definição de acerto | Foco em evitar quedas (ver seção 5) |
| Frequência | Recalcula a cada 15 minutos |
| Infraestrutura | Nuvem gratuita, repositório público no GitHub (minutos ilimitados; senhas nos Secrets) |
| Dados | Todas as famílias: técnico + derivativos, on-chain, macro + ETFs, sentimento + notícias |
| Confiança | 5 níveis, cada um com cor |
| Widget iPhone | Preço + sinal (mínimo e limpo) |
| Moeda | Dólar (USD) |
| Dados em conflito | SEGURA por padrão (conservador) |
| Alertas | Push gratuito no iPhone quando o sinal mudar (regra na seção 13) |
| Placar | Taxa de acerto sempre visível na tela |
| Notícias | Lidas e classificadas por IA com plano gratuito |

---

## 3. Horizontes

| Horizonte | Janela | O que mais pesa |
|---|---|---|
| Curto | próximas 24h | Técnico, derivativos (funding, liquidações), notícias |
| Médio | próximos 7 dias | Técnico, derivativos, fluxo de ETFs, sentimento |
| Longo | próximos 30–90 dias | On-chain, macro, ciclo |

Cada horizonte tem seu próprio sinal e sua própria confiança. É normal o curto dizer "vende" e o longo dizer "compra".

---

## 4. Níveis de confiança (5 níveis)

A confiança vem da **probabilidade calibrada**: quantas vezes, no histórico testado, um sinal com aquela força acertou.

| Nível | Nome | Acerto histórico | Cor (proposta) |
|---|---|---|---|
| 5 | Tem certeza | ≥ 80% | Verde-escuro / vermelho-escuro (conforme compra/vende) |
| 4 | Acha forte | 70–80% | Verde / vermelho |
| 3 | Acha | 60–70% | Amarelo |
| 2 | Talvez | 50–60% | Laranja-claro |
| 1 | Talvez nem aconteça | < 50% | Cinza → sinal vira **SEGURA** |

Regras:
- Nível 1 nunca gera compra ou venda.
- Se uma família de dados estiver fora do ar, a confiança máxima cai (ex.: sem dados on-chain, longo prazo limitado a nível 3).
- Faixas de % são provisórias; serão ajustadas depois do primeiro backtest.

---

## 5. Como medir acerto (foco em quedas)

Métrica principal: **queda evitada**.
- Um "VENDE" acerta se o preço cair pelo menos X% dentro do horizonte.
- Um "COMPRA" erra gravemente se o preço cair X% ou mais dentro do horizonte.
- Um "SEGURA" é neutro, mas conta como erro se uma queda forte acontecer e o sistema não avisou.

Valores iniciais de X (a validar):
- Curto: 3%
- Médio: 7%
- Longo: 15%

Métricas secundárias: precisão de cada sinal, drawdown máximo de uma estratégia que segue os sinais, comparação com "comprar e segurar".

---

## 6. Dados (candidatos gratuitos — a validar)

> Planos gratuitos mudam com frequência. Cada fonte será testada antes de entrar no sistema, e toda família terá uma fonte reserva.

| Família | Exemplos de dado | Fontes candidatas |
|---|---|---|
| Preço e volume | OHLCV em 15m, 1h, 1d | Coinbase, Kraken, OKX (APIs públicas) |
| Derivativos | Funding rate, open interest, liquidações, long/short | OKX, Deribit, Hyperliquid (testadas ✅). Bybit bloqueada nos EUA ❌ |
| On-chain | Fluxo para exchanges, MVRV, endereços ativos, hashrate, taxas | CoinMetrics Community, mempool.space, blockchain.com |
| Macro | DXY, juros dos EUA, S&P 500, Nasdaq, ouro | FRED (API gratuita), Yahoo Finance |
| ETFs | Fluxo diário dos ETFs de BTC | Páginas públicas de fluxo (coleta diária) |
| Sentimento | Fear & Greed, volume de buscas | alternative.me, Google Trends |
| Notícias | Manchetes cripto e macro | RSS de portais + IA gratuita para classificar |

Atenção: Binance e Bybit bloqueiam servidores nos EUA, onde roda o GitHub Actions (confirmado: Iowa). Por isso as fontes são outras corretoras.

---

## 7. Como o sinal é calculado

### Fase A — Placar por família (versão 1)
1. Cada família de dados gera uma nota de -100 (muito vendedor) a +100 (muito comprador) para cada horizonte.
2. As notas são combinadas com pesos diferentes por horizonte (seção 3).
3. **Regra de consenso**: compra ou venda só sai se a maioria das famílias concordar. Sem consenso → SEGURA.
4. **Detector de regime**: o sistema identifica se o mercado está em tendência de alta, tendência de baixa, lateral ou em alta volatilidade, e ajusta os pesos para cada regime.
5. **Freio de quedas**: sinais de risco (funding muito alto, alavancagem extrema, entrada forte de BTC em exchanges, macro piorando) podem rebaixar uma compra para segura, mesmo com o resto positivo.

### Fase B — Modelo treinado (versão 2)
- Um modelo de aprendizado de máquina (ex.: gradient boosting) aprende com anos de histórico quais combinações antecederam quedas e altas.
- Treino em **walk-forward**: o modelo sempre aprende só com o passado e é testado no período seguinte, imitando o uso real.
- A saída é **calibrada** para virar probabilidade real, que define o nível de 1 a 5.
- O placar da Fase A continua como "segundo opinião": se os dois discordam, SEGURA.

### Explicação do sinal
Cada sinal vem com os 3 motivos que mais pesaram (ex.: "funding alto", "saída de BTC das exchanges", "dólar caindo").

---

## 8. Validação e placar

- **Backtest** com anos de histórico, sem usar informação do futuro, antes de qualquer sinal ir para a tela.
- **Registro ao vivo desde o dia 1**: todo sinal emitido é salvo com horário, preço e nível, e é conferido automaticamente quando o horizonte vence.
- **Placar visível**: ex. "Nível 5 acertou 81% (últimos 90 dias, 42 sinais)". Se o placar ao vivo piorar muito em relação ao backtest, o sistema rebaixa a confiança sozinho.

---

## 9. Arquitetura (tudo gratuito)

```
[Agendador a cada 15 min]
        ↓
[Coleta: preço, derivativos, on-chain, macro, ETFs, sentimento, notícias]
        ↓
[Cálculo: notas por família → regime → consenso → nível de confiança]
        ↓
[Saída: signal.json + histórico]
        ↓                ↓                 ↓
   [Site low poly]  [Widget iPhone]   [Push no celular se mudou]
```

| Peça | Ferramenta proposta |
|---|---|
| Linguagem | Python |
| Execução a cada 15 min | GitHub Actions (com um agendador externo gratuito como reforço, porque o agendamento do GitHub pode atrasar) |
| Histórico | Arquivos CSV no ramo `dados` do próprio repositório |
| Site | GitHub Pages (gratuito em repositório público) |
| Widget iPhone | App Scriptable (gratuito), lendo o signal.json |
| Push | ntfy (app gratuito no iPhone) |
| IA para notícias | Plano gratuito de um modelo de IA, com limite de chamadas respeitado |

Dados que mudam devagar (macro, on-chain, ETFs) são atualizados 1x por dia ou por hora; preço e derivativos, a cada 15 minutos. Isso mantém tudo dentro dos limites gratuitos.

---

## 10. Formato do signal.json (rascunho)

```json
{
  "atualizado_em": "2026-10-25T13:15:00Z",
  "preco_usd": 0,
  "regime": "lateral",
  "sinais": {
    "curto":  { "acao": "SEGURA", "nivel": 2, "motivos": ["..."] },
    "medio":  { "acao": "COMPRA", "nivel": 4, "motivos": ["..."] },
    "longo":  { "acao": "COMPRA", "nivel": 3, "motivos": ["..."] }
  },
  "placar": { "nivel_5": 0.81, "nivel_4": 0.73, "janela_dias": 90 },
  "fontes_fora_do_ar": []
}
```

---

## 11. Riscos conhecidos

- **Excesso de ajuste ao passado**: muitos dados aumentam o risco de o modelo "decorar" o histórico. Defesa: walk-forward, poucos parâmetros, placar ao vivo.
- **Fontes gratuitas instáveis**: APIs mudam ou saem do ar. Defesa: fonte reserva por família e queda automática de confiança.
- **Eventos imprevisíveis** (hacks, decisões políticas repentinas): nenhum dado antecipa. Defesa: o foco em quedas e o padrão SEGURA reduzem o estrago.
- **Limites dos planos gratuitos** com recálculo a cada 15 min. Defesa: frequências diferentes por tipo de dado.

---

## 12. Roteiro

1. **Fundação** — repositório, coleta de preço e derivativos, signal.json simples.
2. **Dados completos** — on-chain, macro, ETFs, sentimento, notícias com IA.
3. **Placar por família** (Fase A) + backtest.
4. **Saídas** — site lendo o JSON, widget no iPhone, push.
5. **Registro ao vivo** e placar na tela.
6. **Modelo treinado** (Fase B) + calibração.
7. **Ajuste contínuo** com base no placar ao vivo.

---

## 13. Pendências e quando serão resolvidas

| Pendência | Problema | Quando resolve |
|---|---|---|
| Valores de queda X% (3% / 7% / 15%) | Muito baixo vira ruído; muito alto deixa poucos exemplos para aprender | Backtest (etapa 3) |
| Cores dos 5 níveis | Tons parecidos ficam ilegíveis no widget; precisa funcionar em modo claro e escuro | Junto com o visual low poly (etapa 4) |
| Fontes gratuitas (primária + reserva) | Planos mudam sem aviso; limites de chamada com recálculo a cada 15 min | Fundação e dados completos (etapas 1–2) |
| Modelo de IA para notícias | Limite diário de chamadas, erro de tom, atraso em relação ao preço; sistema deve funcionar sem ela | Dados completos (etapa 2) |

### Decidido: regra do push
- Mudança para **VENDE**: avisa sempre, em qualquer nível (foco em quedas).
- Mudança para **COMPRA**: avisa só nos níveis 4 e 5.
- Mudança para **SEGURA**: avisa se vier de uma COMPRA ou VENDE de nível 4–5.

---

*Versão base v0.1 fechada em 25/10/2026. Próxima etapa: Fundação (seção 12, item 1).*
