# AGENTS.md

Homelab service definitions for [linktools-cntr](https://github.com/linktools-toolkit/linktools/tree/master/linktools-cntr), using Docker / Docker Compose.
`CLAUDE.md` links here; maintain this file only. Keep `.linktools.json` requirements accurate (currently `linktools-cntr >=0.10.0`).

## Layout

- Each numbered service directory contains `container.py`, usually with `compose.yml` and optional Dockerfile/scripts. Numbers only group services.
- Categories: `2xx-homelab`, `3xx-proxy`, `4xx-mobile`, `5xx-ai`, `6xx-coder`, `7xx-builder`, `8xx-base`.
- `8xx-base` provides shared homelab, AI and developer configuration. Built-ins such as nginx, Authelia and Flare live upstream.
- VS Code and CloudCLI are in `5xx-ai`. Multica integrates with VS Code; CloudCLI remains standalone.

## Commands

```sh
ct-cntr add <name>
ct-cntr list
ct-cntr status <name> --json
ct-cntr config list <name>
ct-cntr config set KEY=VALUE
ct-cntr up <name> --dry-run --json
ct-cntr up <name> --pull
ct-cntr restart <name>
ct-cntr down <name>
ct-cntr compose <name> --check
ct-cntr doctor --runtime --check
ct-cntr exec <name> <subcommand>
```

`add/remove` change installation selection; lifecycle commands change runtime state.
`list` reads persisted state; `status` queries Docker. Configuration is project-wide: `config set/edit` take no container name.
`config validate` checks values; `compose --check` validates the native model and loads the whole installed project.

## Container Authoring

- Define `Container(BaseContainer)` with `dependencies`, cached `fields` and reusable `integrations`. Follow nearby services rather than duplicating framework internals.
- Public base classes, `Integrations` and `OperationContext` come from `linktools.cntr`; `Nginx`, `Flare`, `Authelia`, `endpoint` and URL helpers come from `linktools.cntr.ext`.
- Use `fields/extra_fields/config/register_fields`. Configuration helpers come from `linktools.core`; use `ConfigRef` for keys and resolve lazy values through `config.resolve`.
- `ConfigLazy` runs on every resolution and must be read-only. Persistent secrets use cached providers and `ConfigField(secret=True)`; password prompts also need `password=True`.
- Use framework path/service-name helpers and public `runtime` process factories. Path providers return paths without creating directories or changing ownership.
- Service `compose.yml` and Dockerfiles are Jinja templates. Use `APP_PATH`/`APP_DATA_PATH` for persistent data, `SOURCE_PATH` for repository files, and `$$` for Compose shell-variable escaping.
- `mkdir/chown/chmod` filters register deferred start hooks. Use `chown(docker_user)`; ownership/mode changes are nonrecursive by default.
- Omit `image` to enable Dockerfile auto-build injection; explicit `image` plus `build` is valid. Leave build identity to the framework; arbitrary `COPY` contents are not recursively fingerprinted.
- For archive builds, use `SourceContainer` and `get_docker_context_path()`; see `4xx-mobile/410-ws-scrcpy`. Keep source preparation deferred and use `context.refresh_services` for refresh decisions.

## Lifecycle

- Named `up/restart` initialize and refresh explicit targets only; `--pull` does not widen the selection. Select required outside dependencies/shared owners explicitly. Omitting names operates on the full installed project.
- Declare native Compose dependencies for service ordering. Startup conditions become `service_started`; the framework does not wait for health/job completion. Clients need their own retries.
- Keep declarations, getters, rendering and `on_init` free of writes/downloads/runtime operations. `on_init` registers hooks; `on_prepare` must be repeatable. Dry-run/status/doctor/config do not run preparation.
- Initialize persistent inputs in `on_starting` or deferred `BEFORE_START` hooks. Use `prepare_files({"config.json": text})` for immutable generated inputs and mount its returned path directly; validate with `on_check` and `context.file_path` before service replacement.
- Do not overwrite active generations, rotate persistent secrets during rendering, or create custom deployment/readiness/rollback orchestration. `add_stop_hook` runs after stopping; failures after application do not trigger rollback.
- Related running consumers may receive changed generated files only when their other model matches the applied snapshot; they reuse running images. Stopped consumers and pending unrelated changes require explicit selection.

## Integrations and Nginx

- Use `endpoint(self, domain=..., proxy=..., extensions=[...])`. It returns declarations; nested lists/tuples share framework normalization. Keep cached declarations reusable, without mapping keys, IDs or exhausted generators.
- Declare navigation with `Flare`, access rules/callbacks with `Authelia`. These declarations do not create startup dependencies. Endpoint `Flare.public()` inherits its site's URL; direct-port links keep explicit URLs.
- Keep URLs lazy. URL helpers take one path argument and keyword-only queries; plain strings are literals. Reference original sites through `ResolvedSite.find`; multiple sites need an explicit reference.
- OIDC callbacks must resolve to complete URLs; endpoint `{base_url}` templates are supported, path-only callbacks are not completed. Preserve exact slash/query behavior and keep callbacks independent of nginx auth.
- Custom nginx templates render once with `local/` or `nginx/` namespaces. Use shared header/authorization macros and `$original_*` variables. The framework includes `nginx/params.conf` at server scope; do not duplicate it.
- Preserve URI prefixes, captures, queries and intentional auth bypasses. Docker-hostname upstreams need variable targets for isolated validation; fnOS intentionally retains static LAN-IP targets.

Detailed contracts: [integrations](https://github.com/linktools-toolkit/linktools/blob/master/linktools-cntr/docs/integrations.md) and [lifecycle](https://github.com/linktools-toolkit/linktools/blob/master/linktools-cntr/docs/lifecycle.md).
Check current public exports and implementation when examples disagree; do not add compatibility shims.

## Published Images

- `.github/docker/` uses `# INCLUDE` fragments expanded by `.github/docker/scripts/render-dockerfile.sh`, separately from service Jinja rendering. Update workflow path filters when shared inputs change.
- `PREINSTALLED_BASE` defaults to `/opt/preinstalled`; `PREINSTALLED_PATH` is an executable search path. Shared npm tools use `${PREINSTALLED_BASE}/npm`, VS Code user tools use `/workspace/.node_modules`.
- Reuse code-server's bundled Node at `/usr/lib/code-server/lib/node`. Its `/entrypoint.d` scripts must launch long-running add-ons in the background.

## Verification

Use checks appropriate to the change; do not deploy the full project just to validate one service.

```sh
python - <<'PY'
from pathlib import Path
for path in Path(".").glob("[0-9]xx-*/**/*.py"):
    compile(path.read_bytes(), str(path), "exec")
PY
python -m json.tool .linktools.json > /dev/null
```

These checks cover syntax only. For image changes, render fragments and check shell syntax before building; deployment changes need targeted dry-run/doctor/native validation.
This repo has no `tests/` suite or source-check CI. Framework regressions belong upstream and use `manage.py`; do not recreate tests that merely mirror definitions.
