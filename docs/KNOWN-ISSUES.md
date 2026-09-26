# Moudir.ai Known Issues & Limitations

What the current release does not do yet, roughly in order of importance.

## Accounts & access

- **No password reset or email.** There's no email sending, so a manager who forgets their
  password must be given a new account by the owner, and an owner who forgets theirs needs an
  operator to reset it in the database. Adding a mail provider (and email verification on
  sign-up) is the next step.
- **Managers are added with a temporary password** that the owner shares with them, rather than
  by email invitation.
- **No two-factor authentication or SSO.**
- **Two roles only.** Owners manage manager accounts; every manager sees every employee in the
  organization. There are no per-team permissions.
- **Organizations can't be renamed or deleted from the dashboard.**

## Scaling & operations

- **Sign-in rate limiting is in memory, per backend process.** With `WEB_CONCURRENCY=2` the
  effective limit is up to twice the configured value, and it resets on restart. For several
  servers, add a shared limiter (e.g. at the proxy, or Redis).
- **Reports are computed on request** from raw events. That's fine for teams of tens to low
  hundreds of employees; larger organizations will want pre-aggregated daily scores.
- **No data retention policy.** Activity is kept until the employee (or organization) is
  deleted. Decide on a retention period for your customers' jurisdictions and add a scheduled
  purge.

## Scoring

- **Heuristic signals.** Scores and "productive hours" are rule-based estimates from event
  counts (see [SCORING.md](SCORING.md)). They don't see meetings, calls or offline work, and
  aren't timesheets or performance ratings.
- **UTC day boundaries.** Days, weeks and months are bucketed in UTC. Teams far from UTC, or
  shifts that cross midnight UTC, will see activity split across two days. Per-organization
  time zones are not supported yet.
- **The configured schedule, minimum productive hours and maximum idle minutes are stored but
  not yet used in the score.**

## Desktop agent

- **Windows only.** Active-window and idle tracking use Win32 APIs; the macOS fallback only
  exists for development.
- **Not packaged.** The agent runs as a Python script; there's no installer, auto-start service
  or auto-update yet.
