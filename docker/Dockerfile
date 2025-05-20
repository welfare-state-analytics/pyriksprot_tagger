FROM nvidia/cuda:11.6.2-base-ubuntu20.04

LABEL MAINTAINER=Roger Mähler <roger dot mahler at umu dot se>

ENV SHELL=/bin/bash
ENV DEBIAN_FRONTEND=noninteractive

USER root

RUN apt update \
    && apt upgrade -y
RUN apt install -y --no-install-recommends git \
        build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev curl \
        libncursesw5-dev libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID="201"
ARG APP_GID="2001"
ARG APP_USER="pyriksprot"

RUN addgroup --gid $APP_GID "${APP_USER}"
RUN adduser ${APP_USER} --uid ${APP_UID} --gid ${APP_GID} --disabled-password --gecos '' --shell /bin/bash

RUN mkdir /data && chown ${APP_USER}.${APP_USER} /data

#  && adduser -a -G sudo ${APP_USER} \
#  && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER $APP_USER

ENV HOME=/home/$APP_USER

WORKDIR ${HOME}

ARG PYTHON_VERSION="3.11"
ENV PYENV_ROOT=${HOME}/.pyenv
ENV PATH=${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:$PATH

RUN curl https://pyenv.run | bash
RUN pyenv update \
    && pyenv install ${PYTHON_VERSION} \
    && pyenv global ${PYTHON_VERSION}

WORKDIR ${HOME}/work

ARG PACKAGE_VERSION=2023.3.1

RUN set -ex

RUN python -m venv .venv \
    && . .venv/bin/activate \
    && python -m pip install pip --upgrade

ENV PATH="${HOME}/work/.venv/bin:/usr/local/bin:$PATH"

RUN pip install pyyaml mkl mkl-include setuptools cmake cffi typing

    # && pip install --no-cache-dir \
    #     torch==1.13.1 \
    #     torchvision==0.14.1 \
    #     torchaudio==0.13.1 \
    #     torchviz==0.0.2 \
    #  --extra-index-url https://download.pytorch.org/whl/cu116

RUN pip install pyriksprot_tagger==${PACKAGE_VERSION}

ENV STANZA_DATADIR="/data/sparv/models/stanza"


# sudo apt update && sudo apt upgrade -y
# # Run the container with the current and home directories mounted.
# docker run -it --rm --network host \
#     --mount "type=bind,src=$(pwd),dst=/repo" \
#     --mount "type=bind,src=$HOME,dst=$homedst" \
#     --mount "type=bind,src=/etc/passwd,dst=/etc/passwd" \
#     "${passopt[@]}" "$SQITCH_IMAGE" "$@"
# # +---------------------------------------------------------------------------------------+

# Check compatibility here:
# https://pytorch.org/get-started/locally/
# Installation via conda leads to errors installing cudatoolkit=11.1
# RUN pip install --no-cache-dir torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1  && \
#     torchviz==0.0.2 --extra-index-url https://download.pytorch.org/whl/cu116

# reinstall nvcc with cuda-nvcc to install ptax
# USER $NB_UID
# RUN conda install -c nvidia cuda-nvcc -y && \
#     conda clean --all -f -y && \
