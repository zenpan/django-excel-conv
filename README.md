# django-excel-conv

Django application for converting uploaded LexisNexis "Public Records Results
List" court Excel workbooks into a mail-merge-friendly spreadsheet for the
Doyaga Law Firm letter workflow. Production: <https://excel.doyagalawfirm.com>.

Each debtor record is flattened into seven columns — `name`, `ADDRESS_1`,
`City`, `State`, `Zip`, `Creditor`, `Judgment` (the judgment dollar amount,
e.g. `$10,329.00`). Both the New York / New Jersey **and** Florida
exports are supported; they share the `Public Records Results List` layout
delimited by `No.` and `Permissible Use:` markers (the Florida export keeps its
data behind an empty active `Sheet1`, which the converter handles). Converted
and source files are downloaded through a login-required view.

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Runtime

- Python 3.12+
- Django 6.0.x
- SQLite for current production, local development, and tests
- PostgreSQL-ready via production environment variables

## Local Setup

```bash
uv venv --python 3.12
uv pip sync requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Tests

```bash
.venv/bin/python -Wall manage.py test
```

The test suite covers the core conversion path (NY/NJ and Florida layouts),
public pages, authenticated upload and downloads, login protection for job
actions, graceful handling of unparseable files, and Django 6 logout behavior.

CI (`.github/workflows/ci.yml`) runs `manage.py check` and the full test suite
on Python 3.12 for every push and pull request.

## Django 6 Upgrade Notes

The app intentionally jumps from Django 4.2 to Django 6.0 because it is
low-traffic and easier to bug-fix directly than to stage through an LTS-only
upgrade. Keep production on Python 3.12 or newer before deploying this branch.

Live deployment to `excel.doyagalawfirm.com` completed on 2026-05-04. The app
now runs Django 6.0.4 on Python 3.12 with `django_excel.prod_settings`, Caddy
TLS termination, and the existing SQLite database as the source of truth.

`zp.portal` uses a read-only GitHub deploy key titled
`zp.portal django-excel-conv deploy key`. The on-host `origin` URL intentionally
uses the SSH host alias `github.com-django-excel-conv` so Git uses that
repo-scoped key:

```text
git@github.com-django-excel-conv:zenpan/django-excel-conv.git
```

The current upgrade also fixes two compatibility/security-adjacent issues:

- job status rendering now treats `ConvJob.success` as a boolean instead of
  comparing it to string literals in the template;
- convert and delete actions now require login, matching upload and job listing
  access.

For production, run with `DJANGO_SETTINGS_MODULE=django_excel.prod_settings`.
The production settings default to Caddy/TLS, the current SQLite database, and
`/var/www/excel.doyagalawfirm.com/static`, while allowing the deploy environment
to override hosts, CSRF origins, database settings, and static root. Do not
switch `DJANGO_DB_ENGINE` to PostgreSQL until the existing SQLite data has been
intentionally migrated.
