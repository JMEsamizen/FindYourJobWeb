# FindYourJobWeb

Find a job that's the perfect match for you.

FindYourJob is a Django job-search portal for discovering vacancies, matching them to a user profile, saving jobs, analyzing vacancy requirements, and building a CV. The site also links users directly to the FindYourJob Telegram bot at https://t.me/FYDJ_bot.

## Bot-to-web feature map

| Existing bot behavior | Web equivalent |
| --- | --- |
| `parser.Vacancy` fields (`title`, `text`, `date`, `channel`, `url`) | `jobs.Vacancy` PostgreSQL model and `fetch_vacancies` command |
| `profile.py` profile preferences and language | Registration, Profile, and Settings pages backed by `jobs.Profile` |
| `vacancy_filter.py` keyword/category filtering | Normal Django `Q` filters plus `jobs.services` matching functions |
| `matching.py` role, level, format, location, language scoring | Deterministic `matches_profile` and `recommended_vacancies` service functions |
| Bot vacancy callbacks and seen records | Job detail page plus `ViewedJob` history |
| Saved/selected vacancy behavior | Saved Jobs page and `SavedJob` model |
| `ai_analysis.py` fallback and limited analysis | Detail-page analysis with required skills, match score, and fallback result |
| Bot learning/usage limits | First-free CV generation counter and PDF export |
| Telegram language choice | Profile language and Settings language selection: Uzbek, Russian, English |

## Local setup

1. Install Python 3.11+ and PostgreSQL 14+.
2. Create a PostgreSQL database and user:

```sql
CREATE USER findyourjob;
CREATE DATABASE findyourjob OWNER findyourjob;
ALTER USER findyourjob PASSWORD '<set-this-on-the-server>';
```

3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and set the values for your machine. Never commit `.env`.

Required environment variables:

```dotenv
SECRET_KEY=replace-with-a-long-random-value
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
```

`OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are optional. Without an AI key, local matching and CV fallback behavior remains available. The web project does not contain the Telegram bot process; configure the bot's own `BOT_TOKEN` in its separate service environment and never place it in this repository.

5. Install GNU gettext and compile the Russian and Uzbek catalogs (`msgfmt` must be on PATH):

```powershell
python manage.py compilemessages
```

6. Apply migrations and create an admin account:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

7. Import current public Telegram vacancy posts. Each imported record keeps the original Telegram post URL, source name, and Telegram `data-post` identifier for deduplication:

```powershell
python manage.py import_jobs
# or choose channels explicitly
python manage.py import_jobs kasbim_uz job_react ayti_jobs smmprtashkent
```

`fetch_vacancies` remains an alias for the same importer. A source failure is logged and reported while other configured sources continue. The site currently has no HH.uz API/feed integration; do not add HH links by search text or generated vacancy IDs. Add HH only after an authorized API/feed integration is available.

8. For an initial local dataset, create 120 varied, idempotent records:

```powershell
python manage.py seed_jobs
```

9. Start the development server:

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

The Telegram importer is the production ingestion path. `seed_jobs` creates only `is_demo=True` records without source URLs and those records are excluded from the production catalog.

## Project structure

- `config/` - Django settings, URL routing, and WSGI entry point.
- `jobs/` - models, views, forms, services, migrations, tests, and management commands.
- `templates/` - shared layout and page templates.
- `static/` - CSS and JavaScript assets.
- `locale/` - Russian and Uzbek translation catalogs.
- `requirements.txt` - Python runtime dependencies.

## AI configuration

AI is intentionally optional and limited to CV generation and vacancy analysis. The project works without an API key using local deterministic matching, skill extraction, and a profile-based CV fallback. When configured, `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are used by the OpenRouter adapter. Do not put secrets in source control.

## Telegram bot

The website button opens the existing bot username `@FYDJ_bot`. Run the bot from its own bot source/project using its documented command and a server-side `BOT_TOKEN`; this Django repository only imports public Telegram vacancy posts with `fetch_vacancies`.

## VPS deployment

Use PostgreSQL, set `DEBUG=False`, provide a strong `SECRET_KEY`, configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` with HTTPS origins, and run:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

Put Nginx in front of Gunicorn, terminate TLS with the VPS provider or Certbot, and schedule `python manage.py import_jobs` with cron or a systemd timer (for example every 15 minutes). Keep `.env` outside version control and back up PostgreSQL regularly.

For the bot, create a separate systemd service using the bot project's virtual environment and environment file. Run database migrations and `collectstatic` during each deployment, and verify the site with `python manage.py check --deploy` before exposing it publicly.
