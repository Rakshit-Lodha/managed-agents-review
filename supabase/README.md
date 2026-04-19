# Supabase setup

Create a Supabase project named `getrivue`, then run the SQL in:

```text
supabase/migrations/20260417000000_create_users.sql
```

The migration creates `public.users`, enables row-level security, and mirrors basic Google profile details from `auth.users`:

- `id`
- `email`
- `full_name`
- `avatar_url`
- `provider`
- `created_at`
- `updated_at`
- `last_sign_in_at`

Enable Google as an auth provider in the Supabase dashboard and add this redirect URL:

```text
http://localhost:3003/auth/callback
```

For local frontend auth, copy `frontend/.env.example` to `frontend/.env.local` and fill in:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```
