
# Havalastaria: Your New Kingdom

A property listing website built with Django. Browse houses, apartments and condos, book tours, and chat with agents. Agents manage their own listings from a dashboard, and a superuser manages agents and user accounts.

## Features

- **Browse and search** listings by title or location, filter by bedrooms, and sort by price
- **Listing pages** with photos, price, size, year built and agent contact details
- **Agent tools:** create, edit and unlist your own listings (agents can only change their own)
- **Tour requests and chat:** a logged-in user books a tour, the listing's agent is notified, and both can follow up in a built-in chat with accept or decline
- **Dashboard** with listing totals, portfolio value, average price, recent listings and charts
- **User management (superuser only):** create agent accounts, promote or demote users, enable or disable accounts
- **Design:** light and dark themes, responsive layout, animated logo and loading screen
- **Ready for Vercel:** PostgreSQL through `DATABASE_URL` and S3-compatible storage for uploaded photos

## Tech stack

- Python and Django
- SQLite locally, PostgreSQL in production (Neon)
- Pillow for image handling
- `django-storages` for production file storage
- Hosted on Vercel

## Project layout

```
havalastaria/
└── property_site/          <- the Django project (contains manage.py)
    ├── manage.py
    ├── requirements.txt
    ├── property_site/      <- settings, urls, wsgi
    └── listings/           <- the app: models, views, forms, templates
```

When deploying to Vercel, set the project's **Root Directory** to `property_site`.

## Run it locally

Requires Python 3.12 or newer.

```powershell
git clone https://github.com/GreatDalmon/havalastaria.git
cd havalastaria/property_site

python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Locally the project uses SQLite and stores uploaded photos in the `media/` folder.

## Roles

| Role | Can do |
|------|--------|
| Visitor | Browse and search listings |
| Member | Book tours and chat with agents |
| Agent | Create, edit and delete their own listings; reply to tour requests |
| Superuser | Everything above, plus add agents and manage user accounts |

Only a superuser can create agents (Dashboard, then Users and agents).

## Deploying

The project reads these environment variables in production:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Required on Vercel. Generate a long random value |
| `DATABASE_URL` | PostgreSQL connection string (set automatically by the Neon integration) |
| `AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | S3-compatible bucket for listing photos |
| `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN` | Optional, depending on the storage provider |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_ORIGINS` | Needed for a custom domain, comma-separated (origins include `https://`) |

After the first deployment, create the tables once from your own machine by setting `DATABASE_URL` to the production database and running `python manage.py migrate` and `python manage.py createsuperuser`.

Never commit `db.sqlite3`, the `media/` folder, `venv/` or any `.env` file. The included `.gitignore` covers these.

## Status

Active development. Ideas for later: saved listings, email notifications for new tour requests, and richer photo galleries.
