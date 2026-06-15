# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-06-15

### Added
- A footer on every page showing the copyright notice (© ZenPan Technology
  Solutions) and the running app version. The version is single-sourced from
  `django_excel.__version__` and exposed to templates via the
  `django_excel.context_processors.app_meta` context processor ([#8]).

## [1.2.0] - 2026-06-15

### Added
- New **Judgment** column (column G) in the converted sheet: the judgment
  dollar amount parsed from the source "Filing" column, formatted as
  `$10,329.00`. Blank when the source row has no amount ([#7]).

## [1.1.0] - 2026-06-15

Stabilization release following the 1.0.0 Django 6 migration. Resolves the
"Excel file not working / letters blocked" issue reported by Doyaga
(Zammad #77799).

### Fixed
- `/convert/<id>` returned **HTTP 500** for missing jobs and for files that
  failed to parse. Jobs are now fetched with `get_object_or_404` (404), and the
  conversion is guarded so a bad file surfaces an on-screen error instead of a
  server error ([#2]).
- Conversion **timed out the gunicorn worker on large files** — the workbook was
  re-saved on every row (O(n²)). It is now saved once after processing
  (~1,500 rows: ~35s → ~0.4s) ([#2]).
- **Florida exports failed to convert.** Their `Public Records Results List`
  data sits behind an empty active `Sheet1`; the converter now selects the sheet
  that contains the records instead of `workbook.active` ([#4]).
- **Converted files could not be downloaded** in production — with `DEBUG=False`,
  `/media` was not served. Files are now streamed through a login-required
  download view, so debtor PII is no longer exposed via public `/media/` URLs
  ([#5]).

### Added
- Continuous integration (GitHub Actions): `manage.py check` and the test suite
  run on Python 3.12 for every push and pull request ([#3]).
- Regression tests for missing-job 404s, unparseable-file handling, the Florida
  multi-sheet layout, and authenticated downloads.

## [1.0.0] - 2026-05-04

Modernization release (migrated `excel.doyagalawfirm.com`; URL unchanged).

### Changed
- Upgraded to Python 3.12 / Django 6.0.4 / Gunicorn 25.3.0.
- Migrated the public edge from nginx to Caddy on the managed host.
- Made `prod_settings` environment-driven (`DEBUG`, `SECRET_KEY`,
  `ALLOWED_HOSTS`, CSRF origins, database, static root); enabled secure cookies
  and HSTS.

### Added
- Initial automated test suite and `requirements.in` / `requirements.txt`.

### Fixed
- Job-status column treated `ConvJob.success` as a boolean instead of comparing
  it to string literals.
- `convert` and `delete` actions now require login (matching upload and jobs).

[1.3.0]: https://github.com/zenpan/django-excel-conv/releases/tag/v1.3.0
[1.2.0]: https://github.com/zenpan/django-excel-conv/releases/tag/v1.2.0
[1.1.0]: https://github.com/zenpan/django-excel-conv/releases/tag/v1.1.0
[1.0.0]: https://github.com/zenpan/django-excel-conv/releases/tag/v1.0.0
[#8]: https://github.com/zenpan/django-excel-conv/pull/8
[#7]: https://github.com/zenpan/django-excel-conv/pull/7
[#2]: https://github.com/zenpan/django-excel-conv/pull/2
[#3]: https://github.com/zenpan/django-excel-conv/pull/3
[#4]: https://github.com/zenpan/django-excel-conv/pull/4
[#5]: https://github.com/zenpan/django-excel-conv/pull/5
