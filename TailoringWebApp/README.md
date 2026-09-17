# Custom Blouse Tailoring & Order Management Web Application

A working implementation of the BRS: customer + admin portals, versioned
measurements, blouse designs, orders with a controlled status workflow,
trial images with an email-gated notification, payments, delivery
scheduling, reports, and an audit trail.

It runs out of the box on **SQLite** (zero setup) and is structured so it
can be pointed at **MS SQL Server** for production, per the BRS, by
changing configuration only - no application code changes.

## 1. Quick start (local demo)

```bash
cd TailoringWebApp
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000

- **Customer site**: register with any 10-digit mobile number starting 6-9.
- **Admin portal**: http://localhost:5000/admin/login
  - Default demo login: `admin` / `admin123` — **change this immediately** if
    you deploy this anywhere real (see Security notes below).

A SQLite database file is created automatically at
`database/tailoring.db`, along with a default admin user, sample designs,
and default website settings, so the app is usable immediately.

> **Note:** `config.py`'s built-in default for `DB_ENGINE` currently points
> at `mssql` (with a specific local SQL Server instance name as the
> default `MSSQL_SERVER`), not `sqlite`. To get the zero-setup SQLite
> demo described above, explicitly set `DB_ENGINE=sqlite` (e.g. in a
> `.env` file next to `run.py`) before starting the app - see Section 8
> for the full local-SQL-Server path if you'd rather use `mssql` directly.

## 2. Project layout

```
TailoringWebApp/
├── run.py                  # entry point
├── config.py                # all configuration (no hard-coded paths)
├── requirements.txt
├── app/
│   ├── __init__.py          # app factory, blueprint registration, seeding
│   ├── db.py                 # DB abstraction (sqlite / mssql via pyodbc)
│   ├── utils.py               # validation, image storage, email, audit log
│   ├── auth.py                 # customer + admin authentication
│   ├── public.py                # public website (home/designs/gallery/track)
│   ├── customer.py                # customer portal (measurements, orders)
│   └── admin.py                     # admin portal (orders, trial, reports...)
├── templates/                # Jinja2 templates (public / customer / admin)
├── static/css/style.css        # styling
├── uploads/Images/               # BRS Section 3 folder structure
│   ├── BlouseDesign/ Gallery/ CustomerReference/ Trial/ Order/ Logo/ Brand/ HomePage/
├── database/
│   ├── schema_sqlite.sql        # dev/demo schema
│   └── schema_mssql.sql          # PRODUCTION schema (BRS Section 2/28)
└── logs/
```

## 3. Switching to MS SQL Server (production, per BRS Section 2)

1. Create the database and run the production schema once:
   ```
   sqlcmd -S <server> -d TailoringDB -i database/schema_mssql.sql
   ```
2. Install the ODBC driver dependency:
   ```
   pip install pyodbc
   ```
3. Set environment variables (e.g. in IIS's application settings, or a
   `.env` loaded before `run.py`):
   ```
   DB_ENGINE=mssql
   MSSQL_SERVER=your-server
   MSSQL_DATABASE=TailoringDB
   MSSQL_USERNAME=...
   MSSQL_PASSWORD=...
   MSSQL_DRIVER=ODBC Driver 17 for SQL Server
   ```
No code changes are required — `app/db.py` reads `DB_ENGINE` and switches
connections; every query already uses the `?` placeholder style that both
SQLite and pyodbc understand.

> **Note:** `database/schema_mssql.sql` is the maintained production
> schema; `database/MSSQL.sql` is an older SSMS-generated snapshot of the
> same schema and shouldn't be run separately - treat `schema_mssql.sql`
> as the source of truth. Both engines implement the same 12 tables
> (`admin_users`, `customers`, `measurements`, `designs`, `gallery`,
> `orders`, `order_status_history`, `payments`, `order_images`,
> `email_logs`, `website_settings`, `audit_logs`) - there are no separate
> `MeasurementDetails`/`DesignImages`/`OrderItems`/`PaymentTransactions`
> tables as the BRS's "recommended" table list (Section 28) names, since
> those fields are folded directly into the tables above (one line item
> - a blouse - per order).

## 4. Deploying to IIS (Windows Server)

This is a standard Flask (WSGI) app. On Windows/IIS the common approaches are:

- **HttpPlatformHandler** (simplest): install the IIS HttpPlatformHandler
  module, then point IIS at `python run.py` (or better, a production WSGI
  server like `waitress`: `pip install waitress` and run
  `waitress-serve --port=5000 run:app`), with IIS reverse-proxying to it.
- **wfastcgi**: `pip install wfastcgi`, then configure a FastCGI handler in
  `web.config` pointing at `run.app`.

Either way:
- Set `FLASK_ENV=production` and a strong random `SECRET_KEY`.
- Serve `/static` and `/uploads` via IIS directly for better performance
  once you outgrow Flask's built-in static serving.
- Put the `uploads/` folder on persistent storage (not the IIS temp path).

## 5. Email (BRS Section 21)

`EMAIL_BACKEND` config controls how the "Send Trial Message" button behaves:

- `console` (default): logs the email instead of sending it - safe for
  local development, and every send attempt is still recorded in the
  `email_logs` table.
- `smtp`: sends via `smtplib` using `SMTP_HOST` / `SMTP_PORT` /
  `SMTP_USERNAME` / `SMTP_PASSWORD` (e.g. an app password for Gmail SMTP).
  Includes automatic retry (3 attempts) and an IPv4-only DNS workaround
  for Windows machines where dual-stack lookups fail.
- `gmail_api`: placeholder in `app/utils.py::send_trial_email` - wire up
  OAuth2 + the Gmail API here if you need the full API integration instead
  of SMTP.

The "Send Trial Message" button is disabled in the UI, and the backend
route also refuses, until a trial image has actually been uploaded for
that order (BR-011). When sent, the trial email now attaches the trial
image itself - it's automatically downscaled/re-compressed to JPEG first
(via Pillow, if installed; falls back to the original file otherwise) so
a large phone photo doesn't stall the send. Both the trial email and all
status-change emails are queued onto a background thread so the admin's
request returns immediately instead of blocking on the SMTP round-trip.

### Automatic status-change emails (beyond the trial invite)

Admin > Settings has an **Email Triggers** section where specific order
statuses (e.g. `ORDER_RECEIVED`) can be opted in to send the customer an
automatic email whenever an order reaches that status - both when a
customer places a new order and when admin updates an order's status.
This is configuration only (stored in `website_settings.email_trigger_statuses`
as a comma-separated list) - no code change is needed to enable/disable a
status. See `app/utils.py::send_status_email` / `get_enabled_status_email_triggers`
and `app/admin.py::settings`.

## 6. Key business rules implemented

| Rule | Where |
|---|---|
| Mobile number unique & mandatory | `app/auth.py` registration |
| Measurements are versioned, orders snapshot a version | `app/customer.py`, `orders.measurement_id` |
| Order numbers are unique, generated as `ORD<YYYYMMDD><seq>`, never reused | `app/utils.py::generate_order_number` |
| Pending amount = Total − Received, auto-calculated | `app/customer.py` (order creation), `app/admin.py::add_payment` |
| Payment cannot exceed order amount, duplicate reference blocked | `app/admin.py::add_payment` |
| Only admin can change order status; every change is logged | `app/admin.py::update_status` + `order_status_history` |
| Trial email gated on a trial image existing | `app/admin.py::send_trial_notification` |
| Customers can only view their own orders | `app/customer.py::order_detail` (filters by customer_id) |
| Historical design price/measurements don't change retroactively | orders store `total_amount` + `measurement_id` snapshot at creation time |
| Images never keep their original filename; stored with metadata in SQL | `app/utils.py::save_image`, `order_images` / `designs.image_path` / `gallery.image_path` |
| Admin actions audited | `app/utils.py::write_audit_log`, `audit_logs` table, `/admin/audit-logs` |
| Delivery date can't be before order date; daily capacity limit | `app/customer.py::new_order` |
| Admin account lockout after repeated failed logins | `app/auth.py::admin_login` |
| Admin can create a customer and take their first measurement together in one step (walk-in flow) | `app/admin.py::quick_measurement` |
| Order-status emails (order received, etc.) fire automatically only for statuses the admin has enabled | `app/utils.py::send_status_email`, `app/admin.py::settings` |
| Customers can upload their own reference image against an order | `app/customer.py::upload_reference_image` |
| Admin can permanently delete an order (and its images/payments/history) - separate from Cancel | `app/admin.py::delete_order` |
| Individual trial images can be removed by admin | `app/admin.py::delete_trial_image` |

## 7. What's intentionally simplified for this build

The BRS describes a large, multi-phase production system. This build
implements the full end-to-end workflow (registration → measurement →
design → order → payment → cutting/stitching/trial → email → delivery →
admin dashboard/reports/audit) using **Flask + SQLite/MSSQL + server-side
sessions**, without the following, which can be layered on without
restructuring the app:

- OTP / 2FA verification (hooks exist at registration & admin login)
- Real payment gateway integration - customer only *selects* a payment
  mode when ordering (no live gateway, no customer-side upload of a
  payment reference/UTR); admin manually records the actual payment
  (amount/mode/reference/status) afterwards on the order detail screen
- WhatsApp/SMS notifications (BRS Section 36.2/36.3 - future enhancement)
- Monthly Orders / Customer-wise Orders / a standalone Payment Report
  and CSV/PDF export of reports - `app/admin.py::reports` currently
  covers Orders by Status, Design-wise Orders & Revenue, Daily Revenue
  (last 14 days) and Pending Payments; the queries are isolated there if
  you want to extend them or add `openpyxl`/`reportlab` export
- "Edit" / change the design or measurement snapshot of an *existing*
  order - intentionally unsupported, since it would break the
  never-changes-retroactively guarantee (BR-006/013/014); only status,
  payment, trial, delivery date, cancel and (hard) delete are available
  per order
- A consolidated payment/trial history view on the customer record -
  each is viewed per-order from `Admin > Customers > <customer> > Orders`
- A dedicated "Services" section and a "Customer Reviews" section on the
  public home page (it currently has Hero/About Us, Featured Designs,
  Customisation Gallery and a "How It Works" summary)
- HTTPS termination (handled by IIS/reverse proxy in production, not the
  Python app itself)

## 8. Using a local SQL Server (SSMS) instead of SQLite

If you have SQL Server installed locally and manage it through SSMS
(rather than Azure SQL), here's the exact path to get this app writing
to it instead of the SQLite file:

1. **Create the database** in SSMS: right-click **Databases** → **New
   Database** → name it `TailoringDB` → OK.
2. **Run the schema**: open `database/schema_mssql.sql` in SSMS (make
   sure `TailoringDB` is the selected database in the toolbar dropdown),
   and execute it (F5). This creates all the tables.
3. **Find your ODBC driver name** - open PowerShell and run:
   ```powershell
   Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
   ```
   Use the exact name that appears (commonly `ODBC Driver 17 for SQL
   Server` or `ODBC Driver 18 for SQL Server`). If none appear, download
   and install "ODBC Driver 18 for SQL Server" from Microsoft first.
4. **Install pyodbc**: `pip install pyodbc` (already in `requirements.txt`).
5. **Configure the app**: copy `.env.example` to `.env` in the project
   root and fill it in - at minimum `DB_ENGINE=mssql`, `MSSQL_SERVER`
   (check the "Server name" SSMS shows when you connect - often
   `localhost`, `localhost\SQLEXPRESS`, or `.\SQLEXPRESS`), and
   `MSSQL_DRIVER` from step 3. Leave `MSSQL_USERNAME`/`MSSQL_PASSWORD`
   blank to connect with Windows Authentication (the default for a local
   instance you access via your own Windows login in SSMS).
6. **Restart the app**: stop `python run.py` if it's running (Ctrl+C)
   and start it again - environment variables are only read once, at
   startup, so editing `.env` while the app is already running has no
   effect until you restart it.

**How to confirm it worked**: after restarting, use the app (register a
customer, place an order, etc.), then refresh the tables in SSMS
(right-click `TailoringDB` → Refresh, or re-run
`SELECT * FROM customers`) - your data should appear there. No new file
should appear in `database/` after this point; if `database/tailoring.db`
still gets touched, the app is still on SQLite - double check `.env` is
in the same folder as `run.py` and that you fully restarted the process.

**Important**: `web.config` (used only when deployed under IIS) and
`.env` (used only for local `python run.py` runs) are two separate,
independent places to set these values - editing one does not affect
the other. Make sure you're editing the one that matches how you're
actually running the app right now.

## 10. Installable as a mobile app (PWA)

The site is a Progressive Web App: it has a web manifest
(`/manifest.webmanifest`, generated dynamically from your brand name in
Admin > Settings) and a service worker (`/sw.js`) that caches static
assets for a faster, app-like feel.

- **Android (Chrome)**: visiting the site shows an "Install app" /
  "Add to Home Screen" prompt automatically (or via the browser menu).
  It installs with its own icon and opens without browser chrome.
- **iOS (Safari)**: Safari doesn't show an automatic install banner -
  users tap **Share → Add to Home Screen** instead. The `apple-touch-icon`
  and related meta tags in the templates make this look like a proper app
  icon/splash rather than a bookmark.
- **Desktop (Chrome/Edge)**: an install icon appears in the address bar.

This requires **HTTPS** in production (service workers are blocked on
plain HTTP except on `localhost`) - see Part C of
`docs/AZURE_IIS_DEPLOYMENT.md` for getting a free certificate via
win-acme once your domain is pointed at the server.

The app icon is generated at `static/icons/` (192/512/512-maskable/
apple-touch-icon) with a placeholder "ET" monogram - replace those PNGs
with your real logo whenever you have one; no code changes needed.

## 11. Security notes before going live

- Change the default admin password immediately (`admin`/`admin123`).
- Set a strong random `SECRET_KEY` via environment variable.
- Run behind HTTPS (terminate TLS at IIS or a reverse proxy).
- Review `MAX_CONTENT_LENGTH` / `ALLOWED_IMAGE_EXTENSIONS` in `config.py`
  for your needs.
- **`config.py` currently has real-looking defaults committed in source**
  for `SMTP_USERNAME`/`SMTP_PASSWORD`/`EMAIL_FROM` and a specific
  `MSSQL_SERVER` machine name. Move these to environment variables/`.env`
  (which are `.gitignore`d) instead of hard-coded defaults, and rotate
  (regenerate) that Gmail app password since it has been sitting in a
  plain source file.
- **`config.py`'s `MAX_LOGIN_ATTEMPTS` setting is currently unused.**
  Admin lockout is implemented with its own hard-coded `MAX_ATTEMPTS = 5`
  / `LOCKOUT_MINUTES = 15` constants in `app/auth.py`, not wired to this
  config value - update `app/auth.py` directly (or wire it to the config
  setting) if you need this configurable.
