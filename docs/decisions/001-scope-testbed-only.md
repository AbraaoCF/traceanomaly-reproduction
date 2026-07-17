# 001 — Escopo: reprodução restrita ao testbed TrainTicket

- **Data:** 2026-06-01
- **Status:** aceito

## Contexto

O artigo TraceAnomaly (ISSRE'20) avalia o método em dois cenários: (a) um
*testbed* TrainTicket com 41 microsserviços, e (b) quatro grandes serviços
online de produção da "company S" (um banco digital), com 61 a 344
microsserviços. O repositório público disponibiliza **apenas** o código e os
dados do testbed (`train.zip`, `test_normal.zip`, `test_abnormal.zip`). Os dados
de produção são proprietários e nunca foram liberados. O repositório também não
inclui os 7 baselines comparados nem o código de localização de causa-raiz.

## Decisão

A reprodução cobre **somente** a linha do TraceAnomaly na avaliação de testbed
(Tabela II do artigo: precisão/recall agregados ≈ 0,98/0,97). Ficam
explicitamente **fora de escopo**: os serviços de produção da company S, a
comparação com os baselines, e a localização de causa-raiz.

## Consequências

- A reprodução é honesta e executável com artefatos públicos.
- Não é possível reproduzir a quebra por tipo de anomalia (tempo de resposta vs.
  caminho), porque o conjunto de teste liberado traz um rótulo único (0/1).
- A delimitação precisa ser declarada no artigo (Escopo e Ameaças à Validade)
  para não prometer mais do que se entrega.
