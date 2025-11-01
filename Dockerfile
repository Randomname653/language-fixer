FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

# Install gosu for lightweight user switching and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        mkvtoolnix \
        ffmpeg \
        gosu \
        tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python packages
RUN python3 -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir requests flask && \
    chmod -R 755 /opt/venv && \
    chown -R 568:568 /opt/venv

# Ensure virtual environment is activated in all subsequent commands
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

WORKDIR /app

COPY --chown=568:568 language_fixer.py .
COPY --chown=568:568 web/ ./web/
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Expose web UI port
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
