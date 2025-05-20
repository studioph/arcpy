ARG PYTHON_VERSION=3.11
ARG PDM_VERSION=2.24.1

FROM localhost/pdm:${PYTHON_VERSION}-${PDM_VERSION}


RUN \
    sed -i -e's/ main/ main contrib non-free non-free-firmware/g' /etc/apt/sources.list.d/debian.sources \
    && apt update \
    && apt install -y \
    libunrar5