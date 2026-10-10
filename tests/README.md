# Offline cntr contract checks

Use matching `refactor/cntr-integrations` checkouts of this repository and
`linktools-toolkit/linktools`. These tests exercise the actual extension factories,
shared declaration snapshot, built-in nginx/Flare/Authelia consumers, operation
file staging, and retained source-build hooks. No old editable installation or
removed compatibility facades are required. The cross-repository CI job logs both
exact commit SHAs before installation, and accepts a `linktools_ref` override for
reproducing a particular paired revision.

In a fresh virtual environment, install the matching local source packages:

```sh
(cd ../linktools && python -m pip install -r requirements.txt && \
  python manage.py install 'linktools[cli,git]' linktools-cntr --editable --quiet)
python -m pip install pytest
PYTHONPATH=../linktools/linktools/src:../linktools/linktools-cntr/src \
  LINKTOOLS_PATH="$(mktemp -d)" python -m pytest -q tests
```

The test harness verifies `.linktools.json` requirements before loading homelab
containers. All configuration, tokens, addresses and runtime files used by tests
are synthetic. File preparation uses temporary directories; process creation is
mocked. Tests do not run Docker, download sources, contact a provider/CA, read
home configuration, or write live deployment files.

Coverage includes the frozen 65-entry navigation fixture and its ordering,
31 proxy declarations, all 12 business templates, authentication/WAF combinations,
exact OIDC callback slash/query behavior, generated-config immutable mounts,
Multica's lazy VSCode composition, source hook preservation, and refresh selection.
Native `nginx -t`, Docker image/native-service checks and live deployment remain
separate validation; a passing offline run does not claim they were performed.
