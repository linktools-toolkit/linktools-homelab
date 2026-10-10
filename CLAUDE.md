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
ct-cntr up --pull <container-name>    # refresh images/source inputs

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
- **`configs`** (cached_property) — a dict of config keys with defaults, using `ConfigField`, `LazyProvider`, and `PromptProvider` helpers from `linktools.core`
- **`integrations`** (cached_property) — a reusable flat tuple/list annotated `Integrations`. Import `Nginx`, `Flare`, `Authelia`, and URL helpers from `linktools.cntr.ext`; root `linktools.cntr` supplies `BaseContainer`, `SourceContainer`, `Integrations`, and `OperationContext`. Each declaration identifies its consumer. Sites use `Nginx.site(..., local_id="web")`; links use `Flare.public(...)`, `Flare.bookmark(...)`, or callable `Flare.category(...)` groups. Keep values lazy and preserve declaration order; no consumer-keyed mappings or directly imported declaration implementation types
- **Custom subcommands** — methods decorated with `@subcommand(...)` and `@subcommand_argument(...)` become CLI subcommands under `exec <container>`

### `compose.yml` as Jinja2 Templates

The `compose.yml` in each folder is a **Jinja2 template**, not plain Docker Compose YAML. The framework renders it before passing to docker compose. Template variables include all `configs` keys plus framework-provided globals like `APP_PATH`, `DOCKER_UID`, `DOCKER_GID`, `DOCKER_USER`, and `containers["<name>"]` object access. Comments starting with `#` can contain Jinja2 control flow (e.g. `# {% if PORT > 0 %}`).

### Applying Configuration Changes

A targeted `ct-cntr up <container-name>` compares the selected services with their last successfully applied configuration. It includes required providers and running declared integration consumers; real Compose restart and namespace dependencies can also require actions outside the requested containers. These collateral changes are warned about before execution. Unrelated services are not applied merely because their current configuration differs.

Ordinary container authors declare `configs`, `dependencies`, and `integrations`; the framework handles configuration comparison and ordered application. Keep runtime dependencies explicit, including dependencies implied by cross-container template values, and declare each nginx site or Flare link under its consumer. Native Compose profiles determine active full-project services; disabled running services retain their existing configuration unless a real dependency requires rebinding.

### `Dockerfile` as Jinja2 Templates

Dockerfiles also use Jinja2. They can `{% include "Dockerfile_ADD_SUDO_USER" %}` and similar shared snippets provided by the framework.

### Base Container Types

- **`BaseContainer`** — standard container, most services use this
- **`SourceContainer`** — for containers built from a downloaded source archive (e.g. `620-cloudcli` fetches a zip from GitHub)

### Base Infrastructure (8xx-base)

The `8xx-base/` containers are shared infrastructure depended upon by many services:
- `860-coder` — shared developer environment config (git identity, home dir, project path, npm registry)

The `linktools-cntr` built-in containers (nginx, authelia, lldap, flare, portainer, safeline) are bundled inside the `linktools` package itself, not in this repo.

### Nginx and Authelia Integration

Declare domain defaults with `Nginx.domain(self, name=None)` and proxy sites with
`Nginx.site(server_name=..., local_id="web", ...)`. Site IDs are unique within
each producer and remain stable across commands. `load_nginx_url(self, "web", *path,
queries=...)` lazily reads that resolved site; it never registers a proxy or changes
ACL/OIDC state. In general templates, use `urls.load_nginx_url(container, ...)`.

Common site fields:

| Field | Description |
|-------|-------------|
| `server_name` | Lazy hostname; an empty value disables the site |
| `proxy` | Explicit upstream URL, such as `"http://my-service:8080"` |
| `template` | Custom native nginx template from `self.get_source_path(...)` |
| `https`, `waf`, `auth` | `None` inherits, `False` disables, `True` requires the global capability |
| `auth_bypass`, `waf_bypass` | Path regexes bypassing the selected protection |
| `auth_headers` | Lazy credentials injected only after successful authentication |
| `auth_rule` | Optional native Authelia access-control rule |
| `url` | Explicit public URL for a regex/nonliteral hostname |
| `default` | Explicit default-server policy; `server_name="_"` alone is insufficient |
| `expose` | Attached `Flare.public(...)` link; omitted URL inherits the site URL |

Declare callbacks separately with `Authelia.oidc(redirect_uris=(lazy_absolute_url,...),
enabled=lazy_switch)`. This contributes only callbacks to the existing shared
Authelia OIDC client. It never creates another client or credentials. Empty URLs
are omitted, disabled declarations do not resolve their URLs, and nonempty URLs
retain their exact trailing slash/query. GitLab and LiteLLM use `load_nginx_url`;
Proxmox keeps its exact public and configured local callback URLs.

Direct-port links and external bookmarks are standalone Flare declarations.
`Flare.bookmark(name, icon, url, category="private"/"container"/"other")` uses a
standard group; `Flare.category(name, desc, order=...)` declares a custom group.
A category is callable as `(name, icon, desc, url)`, preserving existing link
metadata. An explicit empty/None link URL disables that link. Flare consumes
attached site links first, then standalone links, preserving container/declaration
order within each category. Navigation never creates a runtime dependency.

### Lifecycle and Source Inputs

`on_starting(context: OperationContext)` prepares inputs; `on_check(context)`
validates them before services are replaced; `on_started(context)` runs afterward.
Do not use the removed `on_prepare` loading callback, start another service from a
hook, or overwrite active generated config during preparation.

Use `context.write_files(self, {"config.json": rendered_text})` once per operation.
Compose mounts the logical `APP_PATH/"generated/current/config.json"`; the
framework substitutes the immutable prepared file before checks/application.
Read it in `on_check` with `context.file_path(self, "config.json")`.
`context.project_containers` is the complete installed project selection;
`context.target_containers` identifies the operation targets. `context.prepared_dirs`
maps container names to their immutable prepared directories. Persistent
credentials and runtime data remain separate from these generated inputs.

`SourceContainer` registers its own source-preparation hook. Keep that hook; don't
download source during declaration or planning. Build inputs live in retained
content-addressed snapshots behind `get_docker_context_path()`. `--pull` requests a
source refresh through `context.refresh_services`; inspecting `context.actions`
for a `pull` action no longer expresses that policy.

Multica registers no loading-time preparation. VSCode registers a lazy
`AFTER_COMPOSE_RENDER` callback in `on_init`; installed Multica contributes its
environment/mounts then registers its existing persistent-secret preparation on
VSCode's `BEFORE_START` hook. Rendering itself does not write the PAT or data.

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
from linktools.cntr import BaseContainer, Integrations
from linktools.cntr.ext import Nginx, Flare, load_port_url
from linktools.core import ConfigField, PromptProvider
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> Iterable[str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            MY_TAG="latest",
            MY_DOMAIN=Nginx.domain(self),
            MY_PORT=ConfigField(cast=int, default=0),
            MY_PASSWORD=ConfigField(provider=PromptProvider(cached=True)),
        )

    @cached_property
    def integrations(self) -> Integrations:
        return (
            Nginx.site(
                local_id="web",
                server_name=self.get_config_later("MY_DOMAIN"),
                proxy="http://my-service:8080",
                auth=None,
                expose=Flare.public("My Service", "link", "服务描述"),
            ),
            Flare.bookmark(
                "My Service", "link", load_port_url(self, "MY_PORT", https=False),
                category="container",
            ),
        )
```

The second argument to `Flare.public`/`Flare.bookmark` is a [Material Design Icons](https://pictogrammers.com/library/mdi/) icon name in camelCase (e.g. `"link"`, `"microsoftVisualStudioCode"`).

Key config helpers:
- `ConfigField(cast=int, default=0)` — typed field with a default value
- `ConfigField(provider=LazyProvider(lambda cfg: ...))` — computed when resolved from other config values
- `ConfigField(provider=PromptProvider(cached=True))` — interactive prompt, value stored after first entry

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

Available Jinja2 globals: all `configs` keys, `APP_PATH` (pathlib.Path), `SOURCE_PATH` (pathlib.Path), `DOCKER_UID`, `DOCKER_GID`, `DOCKER_USER`, `container` (the owning container), `containers["name"]`, and `urls` (the module containing lazy URL functions).

- `APP_PATH` — runtime data directory (writable, persisted)
- `SOURCE_PATH` — container source directory (read-only; use for mounting scripts/configs baked into the repo)

The `| mkdir | chown` filters create the host directory and set ownership automatically.

Use `$$` in compose templates to produce a literal `$` in the rendered output (needed when embedding shell variable syntax inside `entrypoint` or `command` YAML blocks).

### Step 4 (optional): Add a custom nginx config

Create a `nginx.conf` and reference it in the site declaration in `container.py`:

```python
Nginx.site(
    local_id="web",
    server_name=self.get_config_later("MY_DOMAIN"),
    template=self.get_source_path("nginx.conf"),
),
```

Custom nginx templates receive `site`, `container`, `nginx`, `config`, and `vars`, plus `route_auth` when the framework groups a shared hostname. Import shared macros with `{% from "nginx/headers.j2" import proxy_headers with context %}` and emit `{{ proxy_headers() }}` in each proxy location. Also import/call `route_authorization()` in protected proxy locations so a shared hostname uses each route's policy; retain explicit `auth_request off` in intentional bypass locations. Use `grpc_headers` for gRPC and pass business-specific header overrides into the macro. Common streaming limits are available through `{% include "nginx/params.conf" %}`. Framework authentication is applied by the generated server; do not include removed native snippets or duplicate its headers.

Use explicit `local/` or `nginx/` Jinja namespaces. Business templates render once into self-contained `sites/<id>.conf` files, and literal data is not evaluated as another template. Use `$original_scheme`, `$original_host`, and the other `$original_*` request variables, never removed `$cntr_*` names. Docker upstreams must use a variable target so isolated validation does not require running services. When replacing a static URI suffix, preserve its prefix/capture/query behavior explicitly. Set backend variables and WebDAV Destination before a `rewrite ... break`, which stops subsequent rewrite directives. fnOS intentionally retains static `proxy_pass` URLs: its defaults are numeric LAN IPs, and native nginx must preserve configured URI prefixes, query strings, and percent encoding. Changing those targets to hostnames is subject to the same isolated DNS validation constraints; it does not enable networked validation.

### Step 5 (optional): Add a custom `Dockerfile`

Dockerfiles are also Jinja2 templates. Use `SourceContainer` as base class when you need to download and build from an upstream archive (see `4xx-mobile/410-ws-scrcpy` for an example).

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


## Source Verification

This branch follows the matching `linktools` `refactor/cntr-integrations` branch.
The declared minimum is still the in-development `linktools-cntr` 0.10.0; use a
matching source checkout rather than an older installation with the same version.

The `Check source syntax` workflow compiles the Python definitions on Python
3.10, 3.12, and 3.14 and parses `.linktools.json` using only the standard library:

```sh
python -m compileall -q [0-9]xx-*
python -m json.tool .linktools.json > /dev/null
```

These checks do not import the definitions or validate framework compatibility,
rendered templates, navigation, OIDC callbacks, lifecycle behavior, or CLI output.
Native service validation and live deployment require separate verification.
