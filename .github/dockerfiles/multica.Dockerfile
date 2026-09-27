FROM ghcr.io/linktools-toolkit/code-server:latest

USER root

ARG MULTICA_VERSION=latest
ARG TARGETARCH

RUN set -eux; \
    tag="${MULTICA_VERSION}"; \
    if [ "$tag" = "latest" ]; then \
        tag="$(curl -fsSL https://api.github.com/repos/multica-ai/multica/releases/latest | jq -r .tag_name)"; \
    fi; \
    version="${tag#v}"; \
    curl -fsSL "https://github.com/multica-ai/multica/releases/download/${tag}/multica-cli-${version}-linux-${TARGETARCH}.tar.gz" \
        -o /tmp/multica-cli.tar.gz; \
    tar -xzf /tmp/multica-cli.tar.gz -C /tmp multica; \
    install -m 0755 /tmp/multica /usr/local/bin/multica; \
    rm -f /tmp/multica /tmp/multica-cli.tar.gz

COPY .github/scripts/multica-entrypoint.sh /usr/local/bin/multica-entrypoint
RUN chmod 0755 /usr/local/bin/multica-entrypoint

ENTRYPOINT ["/usr/local/bin/multica-entrypoint"]
CMD ["daemon", "start", "--foreground"]
