FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ripgrep ffmpeg gcc python3-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY . /opt/kermit
WORKDIR /opt/kermit
RUN pip install --no-cache-dir -e .

ENV HERMES_HOME=/opt/data
VOLUME ["/opt/data", "/opt/shared"]
ENTRYPOINT ["python", "-m", "main"]
CMD ["gateway", "run"]
