# CLAUDE.md

## What This Repo Is

A collection of homelab service definitions managed by the [`linktools-cntr`](https://github.com/linktools-toolkit/linktools/tree/master/linktools-cntr) framework. Each subdirectory under a category folder (e.g. `2xx-homelab/230-nextcloud/`) represents one deployable container unit. The numbering is cosmetic grouping only.

## Key Commands

All container management goes through `ct-cntr`:

```bash
# List all known containers (across all added repos)
ct-cntr list

# Deploy one or more containers (starts docker compose)
ct-cntr up <container-name>
ct-cntr up --build <container-name>   # rebuild image first

# Stop containers
ct-cntr down <container-name>

# View/edit configuration values
ct-cntr config list <container-name>
ct-cntr config set <container-name> KEY=VALUE
ct-cntr config edit <container-name> --editor vim

# Run container-specific subcommands (defined in container.py)
ct-cntr exec <container-name> <subcommand> [args]
# e.g.: ct-cntr exec coder install-modules
# e.g.: ct-cntr exec safeline reset-admin
```

## Architecture

### Container Definition Pattern

Every service folder contains at minimum a `container.py` that defines a `Container(BaseContainer)` class. This class declares:

- **`dependencies`** — other container names that must be deployed first (e.g. `["nginx", "coder"]`)
- **`configs`** (cached_property) — a dict of config keys with defaults, using `Config.Alias`, `Config.Lazy`, `Config.Prompt`, `Config.Property` helpers from `linktools.core`
- **`exposes`** (cached_property) — list of `ExposeLink` objects produced by `self.expose_public(...)`, `self.expose_private(...)`, `self.expose_container(...)` — each wires up an nginx reverse-proxy entry and/or a direct port
- **Custom subcommands** — methods decorated with `@subcommand(...)` and `@subcommand_argument(...)` become CLI subcommands under `exec <container>`

### `compose.yml` as Jinja2 Templates

The `compose.yml` in each folder is a **Jinja2 template**, not plain Docker Compose YAML. The framework renders it before passing to docker compose. Template variables include all `configs` keys plus framework-provided globals like `APP_PATH`, `DOCKER_UID`, `DOCKER_GID`, `DOCKER_USER`, and `containers["<name>"]` object access. Comments starting with `#` can contain Jinja2 control flow (e.g. `# {% if PORT > 0 %}`).

### `Dockerfile` as Jinja2 Templates

Dockerfiles also use Jinja2. They can `{% include "Dockerfile_ADD_SUDO_USER" %}` and similar shared snippets provided by the framework.

### Base Container Types

- **`BaseContainer`** — standard container, most services use this
- **`SourceContainer`** — for containers built from a downloaded source archive (e.g. `620-cloudcli` fetches a zip from GitHub)

### Base Infrastructure (8xx-base)

The `8xx-base/` containers are shared infrastructure depended upon by many services:
- `860-coder` — shared developer environment config (git identity, home dir, project path, npm registry)

The `linktools-cntr` built-in containers (nginx, authelia, lldap, flare, portainer, safeline) are bundled inside the `linktools` package itself, not in this repo.

### Nginx Integration

Containers declare their public domain via `self.get_nginx_domain()` in configs. The `load_nginx_url(...)` call in `exposes` registers a hook that writes the nginx proxy config at deploy time.

`load_nginx_url` key parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `proxy_url` | `str` | Upstream URL (default: inferred from service name) |
| `proxy_conf` | `Path` | Path to a custom nginx `nginx.conf` snippet |
| `auth_enable` | `bool` | Enable Authelia SSO protection (default: `False`) |
| `auth_extra` | `dict` | Fine-grained SSO options (see below) |

`auth_extra` sub-keys:

| Key | Example | Description |
|-----|---------|-------------|
| `acl_bypass` | `["\\.(css\|js)$"]` | URL patterns that skip Authelia auth (regex list) |
| `auth_headers` | `{"Authorization": "Basic ..."}` | Headers injected into proxied requests after auth |
| `oidc_redirect_uris` | `["{base_url}/callback"]` | Extra OIDC redirect URIs registered with Authelia; `{base_url}` is replaced with the service's public URL |

## Creating a New Container

### Step 1: Create the folder

Pick the appropriate category prefix and choose an unused number:

```
2xx-homelab/2NN-my-service/
```

### Step 2: Write `container.py`

Minimal template (copy and adapt):

```python
from typing import Iterable
from linktools.cntr import BaseContainer, ExposeLink
from linktools.core import Config
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            MY_TAG="latest",
            MY_DOMAIN=self.get_nginx_domain(),
            MY_PORT=Config.Alias(type=int, default=0),
            MY_PASSWORD=Config.Prompt(cached=True),
        )

    @cached_property
    def exposes(self) -> Iterable[ExposeLink]:
        return [
            self.expose_public("My Service", "icon-name", "服务描述", self.load_nginx_url(
                "MY_DOMAIN",
                auth_enable=True,
            )),
            self.expose_container("My Service", "icon-name", "服务描述", self.load_port_url(
                "MY_PORT", https=False,
            )),
        ]
```

The second argument to `expose_public`/`expose_container` is a [Material Design Icons](https://pictogrammers.com/library/mdi/) icon name in camelCase (e.g. `"link"`, `"microsoftVisualStudioCode"`).

Key `Config` helpers:
- `Config.Alias(type=int, default=0)` — typed alias with a default value
- `Config.Lazy(lambda cfg: ...)` — computed at render time from other config values
- `Config.Prompt(cached=True)` — interactive prompt, value stored after first entry

### Step 3: Write `compose.yml`

This is a Jinja2 template rendered by the framework before docker compose sees it:

```yaml
services:
  my-service:
    image: vendor/image:{{ MY_TAG }}
#   {% if MY_PORT > 0 %}
    ports:
      - '{{ MY_PORT }}:8080'
#   {% endif %}
    environment:
      - MY_PASSWORD={{ MY_PASSWORD }}
    volumes:
      - "{{ (APP_PATH/'data') | mkdir | chown }}:/app/data"
    networks:
      - nginx

networks:
  nginx:
```

Available Jinja2 globals: all `configs` keys, `APP_PATH` (pathlib.Path), `SOURCE_PATH` (pathlib.Path), `DOCKER_UID`, `DOCKER_GID`, `DOCKER_USER`, `containers["name"]`.

- `APP_PATH` — runtime data directory (writable, persisted)
- `SOURCE_PATH` — container source directory (read-only; use for mounting scripts/configs baked into the repo)

The `| mkdir | chown` filters create the host directory and set ownership automatically.

Use `$$` in compose templates to produce a literal `$` in the rendered output (needed when embedding shell variable syntax inside `entrypoint` or `command` YAML blocks).

### Step 4 (optional): Add a custom nginx config

Create a `nginx.conf` and reference it in `container.py`:

```python
self.load_nginx_url("MY_DOMAIN", proxy_conf=self.get_source_path("nginx.conf"))
```

### Step 5 (optional): Add a custom `Dockerfile`

Dockerfiles are also Jinja2 templates. Use `SourceContainer` as base class when you need to download and build from an upstream archive (see `6xx-coder/620-cloudcli` for an example).

**Auto-build injection**: when a `Dockerfile` is present in the container folder, the framework automatically injects `build.context` and `build.dockerfile` into the service definition — no manual `build:` block needed in `compose.yml`. **This injection is skipped if the service already has an `image:` field** — the framework treats an existing `image:` as a pre-built image to pull, not a local build target. To use a Dockerfile, omit `image:` from `compose.yml` entirely (or comment it out).

**nginx-style entrypoint pattern**: for containers that need ordered initialization scripts, adopt the `/docker-entrypoint.d/` convention:

1. Write `scripts/entrypoint.sh` that iterates `/docker-entrypoint.d/` (sorted with `find | sort -V`), checks the exec bit, and sources `.envsh` / runs `.sh` files before `exec "$@"`.
2. In `Dockerfile`: `COPY scripts/entrypoint.sh /docker-entrypoint.sh` + `RUN chmod +x /docker-entrypoint.sh` + `ENTRYPOINT ["/docker-entrypoint.sh"]`.
3. In `compose.yml`: mount individual scripts read-only via `SOURCE_PATH`:

```yaml
volumes:
  - '{{ SOURCE_PATH/"scripts/00-init.sh" }}:/docker-entrypoint.d/00-init.sh:ro'
```

This keeps script logic in the repo (version-controlled, hot-swappable without rebuild) while the entrypoint dispatcher lives in the image.

## Category Map

| Prefix | Domain |
|--------|--------|
| `2xx-homelab` | NAS, media, cloud storage, download managers |
| `3xx-proxy` | VPN, proxy, subscription converters, FRP |
| `4xx-mobile` | Android-in-cloud (Redroid, scrcpy) |
| `6xx-coder` | Dev environments (VS Code, CloudCLI, GitLab, PyPI) |
| `7xx-builder` | Image/firmware builders (OpenWrt, Redroid) |
| `8xx-base` | Shared infrastructure volumes and config |
