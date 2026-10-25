# Sinal do Satoshi — Plano da Fundação (Etapa 1)

> Criado em 25/10/2026. Referência: `sinal-do-satoshi.md`, seção 12, item 1.

---

## 1. Objetivo

Deixar o "esqueleto" rodando sozinho na nuvem a cada 15 minutos:
- coletar o preço e os dados de derivativos;
- gravar tudo num histórico;
- publicar um `signal.json` simples.

Ainda **não** há sinal de verdade nesta etapa. O sinal só aparece depois do backtest (etapa 3). Até lá, o `signal.json` mostra **SEGURA, nível 1, "em teste"**, para não criar uma confiança que ainda não foi medida.

### Por que começar já
Dados de derivativos (funding, open interest) costumam ter **pouco histórico disponível de graça**. Cada dia gravado agora é um dia a mais para o backtest e para o placar.

---

## 2. Decisões desta etapa

| Tema | Decisão |
|---|---|
| Repositório | **Público** no GitHub: minutos do GitHub Actions ilimitados e grátis. Chaves e senhas ficam nos *Secrets*, que não aparecem para ninguém |
| Site | GitHub Pages (grátis em repositório público; substitui o Cloudflare Pages) |
| Histórico | Arquivos CSV num ramo separado chamado `dados`, para o código principal não ficar poluído com um commit a cada 15 min |
| Linguagem | Python |
| Divisão de trabalho | Claude escreve o código e os passos; você cria as contas, cola os arquivos e confere |

---

## 3. O que entra e o que fica de fora

**Entra:**
- Preço e volume do BTC em velas de 15 min (fonte primária + reserva).
- Funding rate e open interest do BTC (fonte primária + reserva).
- Download do histórico longo de preço (anos de velas diárias e de 1h) para o backtest.
- `signal.json` com preço, dados coletados, horário e status das fontes.
- Registro de falhas: qual fonte caiu e quando.

**Fica para depois:**
- On-chain, macro, ETFs, sentimento, notícias → etapa 2.
- Cálculo do sinal e níveis → etapa 3.
- Site low poly, widget e push → etapa 4.

---

## 4. Fontes (a testar no passo 3 do roteiro)

| Dado | Primária | Reserva | Observação |
|---|---|---|---|
| Preço e volume 15m | Coinbase (API pública) | Kraken (API pública) | Sem necessidade de chave |
| Funding rate + open interest | **Todas**: OKX, Bybit, Deribit, Hyperliquid | — | Uma linha por fonte (ver abaixo) |
| Histórico longo de preço | Coinbase | Kraken | 1d e 1h desde 2015; 15m dos últimos 2 anos |
| Histórico de funding | Todas as que responderem | — | Baixado uma vez na primeira execução |

Regra do preço: se a primária falhar, usa a reserva. Se as duas falharem, o campo fica vazio, a fonte vai para `fontes_fora_do_ar` e o histórico marca o buraco. **Nunca inventar ou repetir dado antigo como se fosse novo.**

Mudança na implementação: em derivativos, **coletamos todas as fontes em vez de primária/reserva**. Cada corretora tem seu próprio funding e open interest, então trocar de fonte no meio quebraria a série. Coletar todas custa quase nada e permite somar o open interest e tirar a média do funding. Deribit e Hyperliquid entraram porque a Bybit (e talvez a OKX) bloqueia servidores dos EUA. O funding é normalizado para "taxa equivalente a 8 horas".

O teste real das fontes roda no próprio GitHub Actions a cada push no `main` e grava o resultado em `relatorios/fontes.json` no ramo `dados`.

---

## 5. Estrutura do repositório

```
sinal-do-satoshi/                (ramo main)
├── docs/
│   ├── sinal-do-satoshi.md      documento base
│   └── fundacao.md              este plano
├── src/
│   ├── fontes.py                lógica de primária/reserva e repetição em caso de erro
│   ├── coletores/
│   │   ├── preco.py
│   │   └── derivativos.py
│   ├── historico.py             grava e lê os CSVs
│   ├── sinal.py                 monta o signal.json (provisório nesta etapa)
│   └── baixar_historico.py      download único do histórico longo
├── .github/workflows/
│   └── coleta.yml               roda a cada 15 min
├── requirements.txt
└── README.md

(ramo dados)
├── preco_15m/2026-10.csv        um arquivo por mês
├── derivativos/2026-10.csv
├── preco_1h/  preco_1d/         histórico longo
├── falhas.csv
└── signal.json
```

---

## 6. Como cada execução funciona

1. O GitHub dispara o workflow a cada 15 min.
2. Os coletores buscam preço e derivativos, com primária → reserva.
3. Os dados novos são adicionados ao CSV do mês, sem duplicar linhas já gravadas.
4. O `signal.json` é regenerado.
5. Um único commit vai para o ramo `dados`.
6. Uma trava impede que duas execuções rodem ao mesmo tempo e briguem pelo arquivo.

Se uma execução atrasar ou não acontecer, a próxima completa as velas que faltaram. Por isso o histórico se recupera sozinho.

---

## 7. Roteiro passo a passo

| # | Passo | Quem |
|---|---|---|
| 1 | Criar o repositório público `sinal-do-satoshi` no GitHub | Você |
| 2 | Conectar o repositório a esta conversa para eu escrever os arquivos direto nele (alternativa: eu te mando os arquivos e você sobe) | Você + Claude |
| 3 | Testar cada fonte da seção 4: responde? quanto histórico devolve? qual o limite de chamadas? | Claude |
| 4 | Escrever coletores, histórico e `signal.json` provisório | Claude |
| 5 | Rodar uma vez manualmente pelo GitHub e conferir os CSVs | Você confere |
| 6 | Ligar o agendamento de 15 min | Claude |
| 7 | Rodar o download do histórico longo | Claude |
| 8 | Ativar o GitHub Pages servindo o `signal.json` (ainda sem visual) | Você + Claude |
| 9 | Observar 7 dias e medir atrasos e falhas | Os dois |
| 10 | Se o agendamento do GitHub atrasar muito, adicionar o agendador externo gratuito como reforço | Claude |

---

## 8. Critério de "fundação pronta"

- 7 dias seguidos rodando sozinho.
- Pelo menos 95% das execuções de 15 min concluídas.
- Histórico de 15 min sem buracos (ou com buracos registrados em `falhas.csv`).
- Troca para a fonte reserva testada de propósito pelo menos uma vez.
- `signal.json` acessível por um link público, pronto para o widget ler.
- Histórico longo de preço baixado.

---

## 9. Riscos desta etapa

- **Atraso do agendamento do GitHub**: execuções podem atrasar em horários de pico. Defesa: a coleta completa as velas que faltaram; reforço externo no passo 10.
- **Repositório público parado**: o GitHub pode desligar agendamentos de repositórios públicos sem atividade por muito tempo. Verificar se os commits automáticos contam como atividade; se não contarem, criar uma rotina de "manter vivo".
- **APIs mudarem**: cada coletor valida o formato da resposta e registra falha em vez de gravar lixo.
- **Repositório crescendo**: 96 commits por dia no ramo `dados`. Os CSVs são pequenos, mas, se o ramo crescer demais, ele é compactado periodicamente.

---

## 10. Andamento

- [x] Passo 1–2: repositório `joaovpag/sinal-do-satoshi` criado e conectado (25/10/2026).
- [x] Passo 4: coletores, histórico e `signal.json` provisório escritos, com testes sem internet.
- [x] Passo 6–7: agendamento de 15 min e download do histórico longo já configurados no workflow.
- [ ] Passo 3: teste das fontes rodando no GitHub (automático no primeiro push).
- [ ] Passo 5: conferir os CSVs da primeira execução.
- [ ] Passo 8: GitHub Pages. Enquanto isso, o `signal.json` fica em
  `https://raw.githubusercontent.com/joaovpag/sinal-do-satoshi/dados/signal.json`.
- [ ] Passo 9–10: observar 7 dias.
