app/
  main.py
  api/
    dependencies/
      __init__.py
      auth.py           # Staff/owner auth, workspace scoping
      pagination.py
    routers/
      __init__.py
      workspaces.py
      staff.py
      contacts.py
      conversations.py
      messages.py
      bookings.py
      forms.py
      inventory.py
      automation.py
      alerts.py
      analytics.py
      health.py
  core/
    __init__.py
    config.py          # Pydantic v2 settings, env-based
    logging.py
    database.py        # SessionLocal, engine, async if needed
    security.py        # Password hashing, JWT for staff
    exceptions.py      # Custom exception types
    background.py      # BackgroundTasks helpers
  models/
    __init__.py
    mixins.py          # TimestampMixin, UUIDMixin, SoftDeleteMixin (optional)
    workspace.py
    user.py            # Staff + Owner roles
    contact.py
    conversation.py
    message.py
    booking.py
    form.py
    inventory.py
    automation.py
    event.py           # EventLog
    alert.py
  schemas/
    __init__.py
    workspace.py
    user.py
    contact.py
    conversation.py
    message.py
    booking.py
    form.py
    inventory.py
    automation.py
    event.py
    alert.py
    analytics.py
  services/
    __init__.py
    unit_of_work.py    # UoW / transactional boundary
    workspace_service.py
    user_service.py
    contact_service.py
    conversation_service.py
    booking_service.py
    form_service.py
    inventory_service.py
    automation_service.py
    analytics_service.py
    event_service.py   # central event recording + dispatch
    alert_service.py
  integrations/
    __init__.py
    email_resend.py    # Resend client wrapper
    sms_provider.py    # Abstraction for Twilio/other (future)
    ai_gemini.py       # AI service integration
  analytics/
    __init__.py
    aggregations.py    # DB-level aggregation helpers
  migrations/
    env.py
    versions/
  tests/
    __init__.py
    test_api/
    test_services/
    test_integrations/
  scripts/
    prestart.sh        # run migrations (for Render)
    seed_data.py



    On Render production, set CORS_ORIGINS and FRONTEND_URL so allow_origins is restricted to your real frontend domain.

    start command
    uvicorn app.main:app --host 0.0.0.0 --port 8000

    or 
    bash scripts/prestart.sh
 
    auto-run migrations before startup
    #!/usr/bin/env bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting app..."
uvicorn app.main:app --host 0.0.0.0 --port 8000


render environment
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>/<db>?sslmode=require


from Neon; convert postgres:// to postgresql+psycopg2://)
RESEND_API_KEY=...
GEMINI_API_KEY=...
JWT_SECRET_KEY=some-strong-random-string


optional

FRONTEND_URL=https://your-frontend.onrender.com
CORS_ORIGINS=https://your-frontend.onrender.com
LOG_LEVEL=INFO (if you add it to Settings)

Generating migrations
Locally, after model changes:
alembic revision --autogenerate -m "init schema"alembic upgrade head


Step-by-step deployment process on Render
Push code to GitHub (or GitLab/Bitbucket).
Create Neon Postgres:
Create a Neon project and database.
Copy the connection string.
Create Render Web Service:
New → Web Service → connect to your repo.
Set Build Command: pip install -r requirements.txt
Set Start Command: bash scripts/prestart.sh (or direct uvicorn if you run migrations manually).
Choose Environment: Python 3.12.
Set environment variables (Render → Environment):
APP_ENV=production
DEBUG=false
DATABASE_URL=<Neon URL converted to postgresql+psycopg2>
RESEND_API_KEY, GEMINI_API_KEY, JWT_SECRET_KEY, FRONTEND_URL, CORS_ORIGINS, etc.
Commit and push Alembic migrations if not already:
alembic revision --autogenerate -m "init schema"
alembic upgrade head (locally to verify).
Commit migrations/ & alembic.ini.
Deploy:
Render builds the image, installs dependencies.
scripts/prestart.sh runs alembic upgrade head.
uvicorn starts serving app.main:app.
Configure health check:
Set path to /api/v1/health in Render service settings.
Verify:
Hit /api/v1/health to confirm healthy.
Hit /api/v1/workspaces/onboard, /api/v1/public/{workspace_id}/booking-types, /api/v1/analytics/workspaces/{workspace_id}/overview, etc., from your frontend or Postman.
Monitor logs:
Use Render Logs to watch stdout.
Alerts and event logs are in DB; your analytics and alerts endpoints expose them to the dashboard.


frontend/
  app/
    layout.tsx
    globals.css

    (marketing)/
      page.tsx                 # landing

    (auth)/
      login/
        page.tsx
      onboarding/
        page.tsx               # workspace onboarding wizard

    (dashboard)/
      layout.tsx               # dashboard shell (sidebar/topbar)
      page.tsx                 # dashboard overview (cards + charts)
      inbox/
        page.tsx
      inventory/
        page.tsx
      bookings/
        page.tsx
      analytics/
        page.tsx
      settings/
        page.tsx

    public/
      [workspaceId]/
        layout.tsx             # public booking shell
        page.tsx               # booking type selection + slot picker

  components/
    layout/
      AppShell.tsx
      Sidebar.tsx
      Topbar.tsx
    ui/
      Card.tsx
      StatCard.tsx
      Button.tsx
      Badge.tsx
      Table.tsx
      Input.tsx
      Select.tsx
      Tabs.tsx
      Skeleton.tsx
      AlertBanner.tsx
      Tooltip.tsx
    dashboard/
      BookingList.tsx
      InventoryLowStockList.tsx
      UnansweredList.tsx
      AlertsList.tsx
      AiInsightCard.tsx
    inbox/
      ConversationList.tsx
      MessageThread.tsx
      ReplyBox.tsx
    booking/
      BookingTypeSelector.tsx
      DatePicker.tsx
      TimeSlotGrid.tsx
      BookingForm.tsx
    onboarding/
      WorkspaceOnboardingWizard.tsx

  lib/
    api/
      client.ts                # fetch wrapper
      auth.ts
      workspace.ts
      booking.ts
      inbox.ts
      inventory.ts
      analytics.ts
      ai.ts
    auth/
      session.ts               # read JWT from cookies, decode role
    types/
      workspace.ts
      booking.ts
      inbox.ts
      inventory.ts
      analytics.ts
      ai.ts

  public/
    favicon.ico
    logo.svg

  tailwind.config.ts
  postcss.config.mjs
  next.config.mjs
  tsconfig.json
  package.json
  .env.local.example


  For later: To recreate or reset the DB in the future, run from the project root:
python -m scripts.create_tables

To re-run the migration yourself from the project root:
python -m app.migrations.add_form_templates_booking_type_id
