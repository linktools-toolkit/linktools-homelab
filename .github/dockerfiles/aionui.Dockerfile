FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm sudo \
    && rm -rf /var/lib/apt/lists/*

# INCLUDE install-agent-cli.dockerfile
# INCLUDE install-chrome.dockerfile
# INCLUDE install-preinstalled.dockerfile

WORKDIR /app
COPY dist/ ./
RUN chmod +x aionui-web

ENV NODE_ENV=production
ENV AIONUI_PORT=3000
ENV AIONUI_HOST=0.0.0.0
ENV AIONUI_ALLOW_REMOTE=true
ENV AIONUI_DATA_DIR=/data

EXPOSE 3000

CMD ["/app/aionui-web"]
