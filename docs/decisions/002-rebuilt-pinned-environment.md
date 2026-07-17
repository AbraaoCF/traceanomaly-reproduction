# 002 — Ambiente reconstruído e fixado (TF 1.15) em vez da imagem publicada

- **Data:** 2026-06-01
- **Status:** aceito

## Contexto

O repositório oferece uma imagem Docker (`silence1990/docker_for_traceanomaly`)
como caminho de reprodução. Ao inspecioná-la (verificado em 2026-06-01), o
ambiente Python 3.5 contém um conjunto de pacotes **internamente inconsistente**:
`tensorflow 1.12.0` + `tensorflow-gpu 1.8.0` + `tensorflow-estimator 2.1.0`
(pacote do TF 2.x) + `numpy 1.18.1`. Como resultado, `import tensorflow` falha
com `ImportError: cannot import name 'abs'`. O `README` ainda afirma "Python 3.6
/ TensorFlow 1.5", que não corresponde à imagem. Ou seja: o artefato publicado
**não roda como distribuído**.

## Decisão

Reconstruir um ambiente fixado a partir da imagem oficial
`tensorflow/tensorflow:1.15.0-py3` (Python 3.6, último TF 1.x), instalando as
duas dependências de git que o código exige (`zhusuan`, `tfsnippet@v0.2.0-alpha1`)
e as demais com versões pinadas. Em particular, `PyYAML==5.4.1` (o código usa
`yaml.load` sem `Loader`, incompatível com PyYAML 6.x). Ver `docker/Dockerfile`.

## Consequências

- A reprodução roda ponta a ponta (treino + detecção + CSV de scores),
  verificado em CPU: ~33 s por época, conjunto de teste com contagens idênticas
  às do artigo (30.355 normais, 5.079 anômalos).
- O ambiente difere do "original" (TF 1.15 em vez do 1.5 do `requirements.txt`).
  Isso é uma **ameaça à validade de construção** e deve ser declarado: estamos
  reproduzindo o *método e o código*, sob um ambiente restaurado, não a imagem
  binária exata dos autores (que está quebrada).
- Sem GPU, o treino completo é mais lento, porém viável (rede pequena).
