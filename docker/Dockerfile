# Rebuilt, pinned environment for reproducing TraceAnomaly (ISSRE'20).
# The authors' published image (silence1990/docker_for_traceanomaly) no longer
# imports TensorFlow: its Python env mixes tensorflow 1.12 + tensorflow-gpu 1.8
# + tensorflow-estimator 2.1 + numpy 1.18, which is internally inconsistent.
# We rebuild from the official TF 1.15 CPU image (the last TF1, Python 3.6).
FROM tensorflow/tensorflow:1.15.0-py3

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# numpy must stay <1.17 for TF 1.15's compiled ops; install it first.
RUN pip install --no-cache-dir "numpy==1.16.4"

# Two dependencies the code needs that exist only on git.
# NOTE (reproducibility caveat): zhusuan is pulled from master (it resolved to
# 0.4.0 at our build time). Upstream master can drift; this is the one dependency
# not pinned to an immutable ref. tfsnippet is pinned to the v0.2.0-alpha1 tag and
# installed with --no-deps so it cannot downgrade TensorFlow 1.15.
RUN pip install --no-cache-dir git+https://github.com/thu-ml/zhusuan.git
RUN pip install --no-cache-dir --no-deps \
    git+https://github.com/haowen-xu/tfsnippet.git@v0.2.0-alpha1

# Remaining runtime + evaluation deps, fully pinned (single source of truth).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /code
