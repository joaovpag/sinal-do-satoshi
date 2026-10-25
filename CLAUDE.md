# Sinal do Satoshi — instruções para o Claude

Projeto pessoal do João. Fale com ele em português do Brasil, em linguagem simples (ele sabe seguir instruções, mas não é programador).

## Leia antes de mudar algo
- `docs/sinal-do-satoshi.md` — documento base, fonte da verdade. Decisões novas entram aqui antes de virar código.
- `docs/fundacao.md` — etapa atual e roteiro.

## Regras do projeto
- Tudo gratuito. Repositório público; segredos só em GitHub Secrets.
- Prioridade é **evitar quedas**. Na dúvida ou com dados em conflito, o sinal é SEGURA.
- Nunca exibir confiança que não foi medida em backtest. Até a etapa 3, o sinal é SEGURA nível 1.
- Nunca inventar dado nem repetir dado antigo como novo. Fonte que falha vai para `falhas.csv` e `fontes_fora_do_ar`.
- Só biblioteca padrão do Python, a menos que haja motivo forte.
- A Binance bloqueia servidores dos EUA (onde roda o GitHub Actions). Não usar como fonte.

## Estrutura
- `src/coletar.py` roda a cada 15 min; `src/baixar_historico.py` roda uma vez; `src/testar_fontes.py` roda a cada push.
- Dados ficam no ramo `dados` (CSV por mês/ano). O código fica no `main`.
- Testes: `python -m unittest discover -s tests -t .` (sem internet).
