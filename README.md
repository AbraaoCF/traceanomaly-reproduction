# Reprodução: TraceAnomaly (ISSRE'20)

<!-- DOI (Zenodo): após o 1º release com o Zenodo ligado, substitua XXXXXXX e descomente:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
-->

Kit de reprodução do experimento de **detecção não supervisionada de anomalias em
*traces* de microsserviços** do artigo:

> P. Liu, H. Xu, Q. Ouyang, R. Jiao, Z. Chen, S. Zhang, J. Yang, L. Mo, J. Zeng,
> W. Xue, D. Pei. *Unsupervised Detection of Microservice Trace Anomalies through
> Service-Level Deep Bayesian Networks.* ISSRE 2020, pp. 48–58.
> DOI: [10.1109/ISSRE5003.2020.00014](https://doi.org/10.1109/ISSRE5003.2020.00014).
> Artefato original: <https://github.com/NetManAIOps/TraceAnomaly>.

Repositório: <https://github.com/AbraaoCF/traceanomaly-reproduction>

Estudo de **reprodução** (mesmo código, mesmos dados liberados), restrito ao
*testbed* TrainTicket. **Fora de escopo** (por imposição do artefato): os serviços
de produção proprietários ("empresa S"), os *baselines* e a localização de
causa-raiz — ver [`docs/decisions/001-scope-testbed-only.md`](docs/decisions/001-scope-testbed-only.md).

## Questões de pesquisa

- **RQ1** — Reexecutando o artefato público sobre o dataset TrainTicket liberado, o
  desempenho de detecção (precisão/recall agregados) é comparável ao reportado no
  artigo (≈ 0,98/0,97)?
- **RQ2** — A etapa de decisão que separa *traces* normais de anômalos — descrita no
  artigo como um KDE sobre as log-verossimilhanças dos *traces* normais seguido de um
  teste de p-valor (α = 0,001) — **não está presente no código liberado**. As
  informações disponíveis bastam para reimplementá-la, e o desempenho reportado se
  sustenta sob essa etapa reimplementada?

## Pré-requisitos

- **Docker** (testado com 28.x). Toda a stack legada (Python 3.6 / TensorFlow 1.15 /
  `zhusuan` / `tfsnippet`) vive dentro de uma imagem fixada — **nada é instalado no
  host**. Sem GPU (validado em CPU).
- `git`, `unzip`, `bash`.
- Recursos: ~4 GB de disco (imagem + dados); uma execução completa leva **~1 h em
  CPU** (com o padrão `MAX_EPOCH=100`).

## Como reproduzir

```bash
# 1. Clona o artefato upstream, descompacta os dados do testbed e constrói a
#    imagem Docker fixada (idempotente).
scripts/bootstrap.sh

# 2. Treina nos traces normais, pontua o teste, reconstrói as métricas (RQ1) e
#    aplica a etapa de decisão KDE + p-valor (RQ2).
scripts/run-experiment.sh
```

Saída em `results/`:
- `rnvp_testbed.csv` — um *score* por *trace* de teste (`id,label,score`), 35.434
  linhas (30.355 normais + 5.079 anômalos);
- `vrnvp_testbed.csv` — *scores* de validação (normais) que ajustam o KDE;
- `pr_curve.png` — curva precisão–recall com os pontos de operação;
- no stdout: AUPRC e o ponto de **melhor F1** (curva de referência, RQ1) e
  precisão/recall/F1 sob a **regra KDE + p-valor** a α=0,001 (RQ2).

Compare com as saídas de referência em
[`reference-results/`](reference-results/AGGREGATE.md).

## Determinismo e resultado esperado

O código *upstream* **não fixa *seed***. Os resultados **não são bit-idênticos**
entre execuções — em especial o *recall* no ponto de decisão varia bastante. O
critério de reprodução é **cair na faixa** observada em 5 execuções nossas:

| Métrica | faixa esperada (5 execuções) |
|---|---|
| AUPRC | 0,95 – 0,99 |
| melhor-F1 | 0,92 – 0,95 |
| KDE+p precisão (α=0,001) | 0,99 – 1,00 |
| KDE+p **recall** (α=0,001) | **0,13 – 0,60** |

Detalhe por execução e agregado em [`reference-results/AGGREGATE.md`](reference-results/AGGREGATE.md).

> **Por que reconstruímos métricas e decisão?** O código publicado emite apenas os
> *anomaly scores* por *trace* — não calcula precisão/recall nem inclui a etapa de
> decisão (KDE + p-valor) que o artigo descreve. `src/evaluate.py` reconstrói as
> métricas a partir dos *scores* + rótulos e reimplementa a etapa de decisão.

## Estrutura

```
src/                 evaluate.py (métricas RQ1 + regra KDE+p-valor RQ2)
                     plot_pr.py  (figura da curva PR anotada)
scripts/             bootstrap.sh (setup idempotente) + run-experiment.sh
docker/              Dockerfile (ambiente fixado; consome requirements.txt)
requirements.txt     deps PyPI fixadas (versões exatas resolvidas)
data/                dados NÃO redistribuídos — data/README.md diz como obtê-los
reference-results/   nossas saídas das 5 execuções: scores brutos (rnvp_/vrnvp_*.csv)
                     + métricas (eval_r*.txt) + agregado (AGGREGATE.md) + figura
results/             saídas de execuções novas (geradas por run-experiment; não versionado)
docs/decisions/      ADRs (escopo; ambiente reconstruído)
```

## Notas de reprodutibilidade

- **Ambiente fixado (não o publicado).** A imagem Docker dos autores **não importa o
  TensorFlow** (pacotes conflitantes). Reconstruímos um ambiente equivalente a partir
  da imagem oficial TF 1.15 — ver
  [`docs/decisions/002-rebuilt-pinned-environment.md`](docs/decisions/002-rebuilt-pinned-environment.md).
  Deps PyPI fixadas em `requirements.txt`; `zhusuan` é instalado do *master* (resolveu
  para 0.4.0) — a única dependência não presa a um *ref* imutável.
- **Dados menores.** O conjunto de treino liberado (~100 mil *traces*) é menor que os
  ~380 mil do artigo; o rótulo de teste é apenas binário (sem o tipo da anomalia).
- **Sem *seed*** → variância real entre execuções (ver faixas acima).

## Licença

Código sob licença **MIT** (ver [`LICENSE`](LICENSE)). Os dados do *testbed* e o
método pertencem aos autores do artigo original (ver artefato *upstream*).
