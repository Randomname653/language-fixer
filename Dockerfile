FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        mkvtoolnix \
        ffmpeg \
        sudo \
        tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir requests

WORKDIR /app

COPY language_fixer.py .

RUN chown appuser:appuser language_fixer.py

CMD ["python3", "/app/language_fixer.py"]
