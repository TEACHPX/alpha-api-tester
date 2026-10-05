# Vercel + PostgreSQL Deployment

PULSE API X uses PostgreSQL for persistent data on Vercel. SQLite is not used in the Vercel deployment because serverless function filesystems are not suitable for persistent application data.

## 1. Create a PostgreSQL database

Create a database with a PostgreSQL provider such as Neon or Supabase and copy its connection string.

## 2. Import the repository into Vercel

Import `TEACHPX/Api-Tester` from GitHub and deploy it as a Python project.

## 3. Add the environment variable

In Vercel → Project → Settings → Environment Variables, add:

`DATABASE_URL` = your PostgreSQL connection string.

Use `sslmode=require` when your provider requires SSL.

## 4. Redeploy

After adding the variable, redeploy the project. The app creates its three tables automatically on first local initialization; for Vercel, run the following once from a trusted environment using the same `DATABASE_URL`:

```bash
python -c "from app import init_db; init_db()"
```

The API also exposes `/api/health` to verify the database connection.

## Notes

- Never commit `.env` or real database credentials.
- Do not put database passwords in frontend JavaScript.
- `DATABASE_URL` must be stored in Vercel Environment Variables.
