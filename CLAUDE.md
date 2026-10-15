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
- **`integrations`** (cached_property) — a reusable, optionally nested tuple/list annotated `Integrations`, containing `Nginx`, `Flare`, and `Authelia` declarations directly. Import these declarations, `endpoint`, and URL helpers from `linktools.cntr.ext`; root `linktools.cntr` supplies `BaseContainer`, `SourceContainer`, `Integrations`, and `OperationContext`. Each declaration identifies its consumer. Use `endpoint(self, domain=..., extensions=[...])` for sites; its plain tuple contains one `Nginx` declaration followed by its leaf extensions. An endpoint tuple or `Flare.links(...)` group can be an array element without `*`. The common integration normalizer recursively preserves declaration order; consumers do not implement separate flattening. Keep values lazy; no key/value declaration dictionaries, consumer-keyed mappings, or directly imported declaration implementation types
- **Custom subcommands** — methods decorated with `@subcommand(...)` and `@subcommand_argument(...)` become CLI subcommands under `exec <container>`

### `compose.yml` as Jinja2 Templates

The `compose.yml` in each folder is a **Jinja2 template**, not plain Docker Compose YAML. The framework renders it before passing to docker compose. Template variables include all `configs` keys plus framework-provided globals like `APP_PATH`, `DOCKER_UID`, `DOCKER_GID`, `DOCKER_USER`, and `containers["<name>"]` object access. Comments starting with `#` can contain Jinja2 control flow (e.g. `# {% if PORT > 0 %}`).

### Applying Configuration Changes

A targeted `ct-cntr up <container-name>` compares the selected services with their last successfully applied configuration. It includes required providers and running declared integration consumers; real Compose restart and namespace dependencies can also require actions outside the requested containers. These collateral changes are warned about before execution. Unrelated services are not applied merely because their current configuration differs.

Ordinary container authors declare `configs`, `dependencies`, and `integrations`; the framework handles configuration comparison and ordered application. Keep runtime dependencies explicit, including dependencies implied by cross-container template values, and declare nginx sites and independent Flare links in `integrations`. Native Compose profiles determine active full-project services; disabled running services retain their existing configuration unless a real dependency requires rebinding.

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
`endpoint(self, domain=..., proxy=...)`. Integrations contain declaration objects,
never site-key dictionaries. `Nginx.site(server_name=..., ...)` is also a direct
leaf declaration, with no author-supplied identity or navigation fields.

`load_nginx_url(self)` lazily reads the sole declared nginx site, including when
that site is disabled. It is ambiguous when the producer declares multiple sites,
even if only one is currently enabled. To select among multiple sites, retain an
endpoint in a `cached_property`, include that same tuple in `integrations`, and
pass it as `load_nginx_url(self, self.proxy_endpoint)`. An original declared
`Nginx` object is also accepted. References use object identity, so never recreate
an equivalent declaration or use a string key. The helper never registers a proxy
or changes ACL/OIDC state. For a single-site subpage, use
`load_nginx_url(self, None, "ui", queries=...)`. In general templates, use
`urls.load_nginx_url(container, ...)`.
Common site fields:

| Field | Description |
|-------|-------------|
| `server_name` | Lazy hostname; an empty value disables the site |
| `proxy` | Explicit upstream URL, such as `"http://my-service:8080"` |
| `template` | Custom native nginx template from `self.get_source_path(...)` |
| `template_vars` | Business template values and shared nginx server defaults |
| `https`, `waf`, `auth` | `None` inherits, `False` disables, `True` requires the global capability |
| `auth_bypass`, `waf_bypass` | Path regexes bypassing the selected protection |
| `auth_headers` | Lazy credentials injected only after successful authentication |
| `public_url` | Explicit public URL for a regex/nonliteral hostname |
| `default_server` | Explicit default-server policy; `server_name="_"` alone is insufficient |

Declare callbacks explicitly with `Authelia.oidc(redirect_uris=(lazy_absolute_url,...))`.
This contributes only callbacks to the existing shared Authelia OIDC client. It
never creates another client or credentials. There is no `enabled` argument:
OIDC declarations are independent of endpoint `auth` and `NGINX_AUTH_ENABLE`.
Empty URLs are omitted, and nonempty URLs retain their exact trailing slash/query.
GitLab and LiteLLM declare relative callback URLs in their endpoint extensions;
Proxmox uses `"{url}"` for the exact public base URL without adding a slash, and
keeps its configured local URL unchanged.
Disabling a public site omits only its empty derived URL; an explicit nonempty
absolute callback remains declared.
For the common web-site pattern, use the pure `endpoint` function. It returns
a plain tuple beginning with `Nginx.site(...)`, followed by the flattened
explicit `extensions`. It does not create navigation, callbacks, services,
clients, or lifecycle work automatically. `domain` maps to `server_name`; the
remaining site arguments are flat native fields: `proxy`, `template`, `https`,
`waf`, `waf_bypass`, `auth`, `auth_bypass`, `auth_headers`, `public_url`,
`cert_domains`, `template_vars`, and `default_server`. Capability defaults remain
`None` (inherit). There is no positional site key, navigation metadata, path,
direct-port, or OIDC option on `endpoint`.

Declare access-control rules with `Authelia.access(policy="one_factor", ...)`
in `extensions`. The endpoint binds the rule to its actual site automatically;
native rule fields such as `subject`, `resources`, and `methods` remain explicit.
For a standalone rule, pass the original declared site object as `site=...`.
Its domain comes from that site. `Nginx.site` does not accept `auth_rule`.

This repository uses `endpoint` for all 31 nginx sites, including custom nginx
templates, authentication headers, Xray's lazy template variables, VSCode's regex
proxy, and the six homelab sites. VSCode declares both sites in `integrations` and
keeps one lazy business `proxy_url` for the Compose `VSCODE_PROXY_URI` setting.
Its regex proxy site has no public navigation or OIDC reference, so it does not
need an explicit `public_url`. Homelab declares all six endpoints together;
Proxmox's callback declaration is inside its endpoint's extensions list.

Use `Flare.links(*links, name=..., icon=..., desc=...)` to share omitted metadata
across a public application and its private/direct-port bookmarks. It returns a
tuple of independent declarations that can sit directly in `extensions`, including
nested lists, without `*`. Per-link metadata overrides the group; blank descriptions retain
the normal fallback to the link name. For example, `Flare.public()` inherits the
site URL only when included in an endpoint's extensions, while
`Flare.container(url=load_port_url(self, "MY_PORT", https=False))` keeps its
explicit direct URL. Omitted public URLs inherit; explicitly supplied `None`,
empty strings, and custom URLs are preserved. Outside an endpoint, public links
need an explicit URL. Empty/None URLs disable links.

Navigation paths remain explicit: use `Flare.public(url="/ui")` inside endpoint
extensions, or `Flare.public(url=load_nginx_url(self, None, "ui"))` outside them
for a single-site producer. Declare OIDC separately with
`Authelia.oidc(redirect_uris=("/sso/callback",))` inside the endpoint.
A navigation path never changes a callback or the independent Authelia issuer.
GitLab and LiteLLM render their OIDC client settings whenever the installed
Authelia provider has a concrete HTTPS public URL, including when nginx auth is
off; missing or HTTP-only providers do not produce client settings. Each app's
read-only `oidc_provider` is shared by its template and runtime requirements, so a
targeted app start includes the available Authelia service even when nginx auth
is off. Unrelated selections do not request that provider.

Direct-port links and external bookmarks can also remain standalone Flare
declarations. `Flare.bookmark(name, icon, url, category="private"/"container"/"other")`
uses a standard group; `Flare.category(name, desc, order=...)` declares a custom
group. A category is callable as `(name, icon, desc, url)` or with omitted metadata
inside `Flare.links`. Flare consumes links in producer/declaration order within
each category. When migrating attached links, retain their order relative to that
producer's standalone links. Navigation never creates a runtime dependency.

### Lifecycle and Source Inputs

`on_starting(context: OperationContext)` prepares inputs; `on_check(context)`
validates them before services are replaced; `on_started(context)` runs afterward.
`on_prepare()` is available after installed config registration and before execution
selection; it must support repeated entries. Read-only planning/config commands do
not call it. Generate selected operation inputs in `on_starting(context)` instead.
Do not start another service from a hook or overwrite active generated config during preparation.

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
from linktools.cntr.ext import Nginx, Flare, endpoint, load_port_url
from linktools.core import ConfigField, ConfigRef, PromptProvider
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
        return endpoint(
            self,
            domain=ConfigRef("MY_DOMAIN"),
            proxy="http://my-service:8080",
            auth=None,
            extensions=[
                Flare.links(
                    Flare.public(),
                    Flare.container(url=load_port_url(self, "MY_PORT", https=False)),
                    name="My Service", icon="link", desc="服务描述",
                ),
            ],
        )
```

The second argument to `Flare.public`/`Flare.bookmark` is a [Material Design Icons](https://pictogrammers.com/library/mdi/) icon name in camelCase (e.g. `"link"`, `"microsoftVisualStudioCode"`).

Key config helpers:
- `ConfigRef("MY_DOMAIN")` — an unbound reference to an existing configuration key, resolved in the consumer-selected `Config`
- `ConfigFormat("*.{domain}", domain=ConfigRef("MY_DOMAIN"))` — resolve explicit arguments, then apply one `str.format`
- `ConfigLazy(lambda config: ...)` — a read-only computation receiving the selected `Config`; it runs on each resolution and must not create persistent secrets
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

Create a `nginx.conf` and reference it from `endpoint` in `container.py`.
Navigation stays explicit in `extensions`:

```python
endpoint(
    self,
    domain=ConfigRef("MY_DOMAIN"),
    template=self.get_source_path("nginx.conf"),
    extensions=[Flare.public("My Service", "link", "服务描述")],
),
```

Additional sites also use `endpoint` and can be declared together:

```python
@cached_property
def integrations(self) -> Integrations:
    return [
        endpoint(self, domain=ConfigRef("APP_DOMAIN"), proxy="http://app:8080"),
        endpoint(self, domain=ConfigRef("PROXY_DOMAIN"),
                 template=self.get_source_path("proxy.conf")),
    ]
```

VSCode keeps both declarations in `integrations`. Its lazy `proxy_url` supplies
the Compose `VSCODE_PROXY_URI` independently; it returns empty when nginx,
wildcard routing or the domain is unavailable.
Only retain an endpoint object in a cached property when another declaration
actually needs to reference that original object.

Use ordinary extension lists or generators. The endpoint binds only extension
URL fields: Flare links and Authelia redirect URIs. Relative URLs follow standard
URL resolution against the site's public URL, so `"/callback"` selects that path
at the origin and `"/"` retains the trailing root slash. A leading `"{url}"`
placeholder selects the exact public base, preserving its existing trailing
slash and query; `"{url}"` alone never adds a slash. Absolute URLs are unchanged.
Explicit empty/None link URLs stay disabled, and empty callback URLs are omitted.
When the site has no public URL, derived relative URLs are empty; independent
absolute URLs remain available. Other declaration fields are not interpolated.

Keep URL values lazy when they contain configuration. Mihomo uses
`load_nginx_url` for fragment-based public navigation and `load_port_url` for
its direct container URL. Both take nested configuration query values and resolve
them before URL encoding, only after the site or port is enabled. The public
setup port uses `ConfigLazy` to select the port for the resolved site's protocol;
the hostname and secret use `ConfigRef`. The URL
helpers cache their successful result for the declaration's command-local lifetime.
OIDC URLs remain independent of endpoint and global auth settings.

An omitted URL in `Flare.public()` inside either endpoint inherits that endpoint's
site; it does not select the producer's first or only enabled site.
Custom nginx templates receive `site`, `container`, `nginx`, `config`, and `template_vars`, plus `route_auth` when the framework groups a shared hostname. Import shared macros with `{% from "nginx/headers.j2" import proxy_headers with context %}` and emit `{{ proxy_headers() }}` in each proxy location. Also import/call `route_authorization()` in protected proxy locations so a shared hostname uses each route's policy; retain explicit `auth_request off` in intentional bypass locations. Use `grpc_headers` for gRPC and pass business-specific header overrides into the macro. The framework includes `nginx/params.conf` once at each business server and WAF origin server. It supplies shared request-body, buffering, cache, and timeout defaults through `template_vars`; custom locations inherit them. Do not include it again inside a business template or location. Keep genuinely different path-specific overrides, protocol settings, and header macros in their locations. Framework authentication is applied by the generated server; do not include removed native snippets or duplicate its headers.

### Migrating custom nginx defaults

Upgrade the paired framework and these templates together. External/custom templates
that include `nginx/params.conf` must remove those includes: the framework now emits
it at server scope. Remove same-value buffering/timeout duplicates, but preserve
intentional location overrides. All business locations now inherit shared streaming
defaults, including locations that previously omitted the snippet; this intentionally
changes their former nginx buffering and timeout defaults. Header macros and explicit
HTTP/gRPC protocol settings remain location-specific. The unused FastCGI temporary-file
setting is removed from these HTTP proxy templates. Set a site limit with, for example,
`template_vars={"client_max_body_size": "10m"}`; this applies across WAF hops without
changing SafeLine or application-specific limits.


Use explicit `local/` or `nginx/` Jinja namespaces. Business templates render once into self-contained site blocks in `sites/generated.conf`, and literal data is not evaluated as another template. Use `$original_scheme`, `$original_host`, and the other `$original_*` request variables, never removed `$cntr_*` names. Docker upstreams must use a variable target so isolated validation does not require running services. When replacing a static URI suffix, preserve its prefix/capture/query behavior explicitly. Set backend variables and WebDAV Destination before a `rewrite ... break`, which stops subsequent rewrite directives. fnOS intentionally retains static `proxy_pass` URLs: its defaults are numeric LAN IPs, and native nginx must preserve configured URI prefixes, query strings, and percent encoding. Changing those targets to hostnames is subject to the same isolated DNS validation constraints; it does not enable networked validation.

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

These declarations require the unbound configuration-value API from the matching
`linktools` `feat/core-config-values-180` source branch. The declared minimum is
still the in-development `linktools-cntr` 0.10.0; use a matching source checkout
rather than an older installation with the same version. Ordinary installations
require a supporting framework release before adopting these declarations.

This repository has no pull-request source-check CI or retained tests directory.
Framework regression checks belong to `linktools-cntr`; validate changed homelab
definitions locally against the matching framework checkout. The following
standard-library checks parse Python and repository metadata without creating
bytecode files:

```sh
python - <<'PYTHON'
from pathlib import Path
for path in Path(".").glob("[0-9]xx-*/**/*.py"):
    compile(path.read_bytes(), str(path), "exec")
PYTHON
python -m json.tool .linktools.json > /dev/null
```

These checks do not import the definitions or validate framework compatibility,
rendered templates, navigation, OIDC callbacks, lifecycle behavior, or CLI output.
Native service validation and live deployment require separate verification.
