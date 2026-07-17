# Dados — testbed TrainTicket

Os dados **não são redistribuídos aqui** (o repositório *upstream* não declara
licença). Este diretório é preenchido automaticamente por `scripts/bootstrap.sh`;
os arquivos descompactados **não são versionados** (só este README).

## O que são

Os *traces* do *testbed* TrainTicket **já vetorizados** (STVs), como liberados
pelos autores. O artefato **não** inclui o código que constrói os STVs a partir de
*traces* brutos — apenas os vetores prontos e o dicionário de caminhos de chamada.

| arquivo | conteúdo | contagem |
|---|---|---|
| `train`         | *traces* normais de treino | 100.000 |
| `test_normal`   | *traces* normais de teste  | 30.355 |
| `test_abnormal` | *traces* anômalos de teste | 5.079 |

Formato de cada linha: `UUID:v1,v2,…,v889`, em que cada `vi` é o tempo de resposta
(ms) da dimensão `i` do STV e `0` indica caminho ausente (ver a seção "Dados" do
artigo). O dicionário `idx.pkl` mapeia índice de dimensão → caminho de chamada
(`chamador#chamado#endpoint`, encadeado desde a raiz).

## Fonte

Repositório oficial do artefato:
<https://github.com/NetManAIOps/TraceAnomaly> — pasta `train_ticket/`
(`train.zip`, `test_normal.zip`, `test_abnormal.zip`, `idx.pkl`).

Artigo: Liu et al., *Unsupervised Detection of Microservice Trace Anomalies…*,
ISSRE 2020, DOI [10.1109/ISSRE5003.2020.00014](https://doi.org/10.1109/ISSRE5003.2020.00014).

## Como obter

**Automático (recomendado):**

```bash
scripts/bootstrap.sh    # clona o upstream e descompacta os zips neste diretório
```

**Manual:**

```bash
git clone https://github.com/NetManAIOps/TraceAnomaly.git
cd TraceAnomaly/train_ticket
unzip -o train.zip test_normal.zip test_abnormal.zip -d <repo>/data/
```

Após obter, `data/` deve conter `train`, `test_normal` e `test_abnormal`.
