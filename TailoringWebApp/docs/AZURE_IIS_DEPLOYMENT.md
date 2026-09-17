# Deploying to Azure: Windows Server + IIS + Azure SQL Database

This follows the original BRS architecture exactly: IIS on Windows Server,
MS SQL Server (as Azure SQL Database, the managed version of SQL Server)
as the database.

Total time: roughly 1-2 hours the first time.

---

## Part A - Create the database (Azure SQL Database)

1. In the [Azure Portal](https://portal.azure.com), click **Create a resource** → **SQL Database**.
2. Fill in:
   - **Resource group**: create a new one, e.g. `tailoring-rg`
   - **Database name**: `TailoringDB`
   - **Server**: click "Create new" → give it a name (becomes
     `yourserver.database.windows.net`) → set an admin username/password
     (write these down) → choose a region close to your users.
   - **Compute + storage**: pick the cheapest tier to start (Basic / 5 DTU,
     or "Serverless" on the vCore model) - you can scale up later.
3. Under **Networking**, allow "Azure services and resources to access this
   server", and add your own IP so you can connect from your machine to
   run the schema script.
4. Once created, open the database's **Query editor** in the portal (or
   connect with [Azure Data Studio](https://azure.microsoft.com/products/data-studio) /
   SQL Server Management Studio using the server name + admin login), and
   run the contents of `database/schema_mssql.sql` from this project.

You now have a live SQL Server database with all the required tables.

---

## Part B - Create the web server (Windows Server VM + IIS)

1. In the Azure Portal: **Create a resource** → **Virtual Machine**.
   - **Image**: Windows Server 2022 Datacenter (Azure Edition is fine)
   - **Size**: B2s is enough to start (2 vCPU / 4GB RAM)
   - **Resource group**: same as above (`tailoring-rg`)
   - Set an admin username/password for RDP login.
   - Under **Networking**, allow inbound ports: **3389** (RDP, for setup),
     **80** (HTTP), **443** (HTTPS).
2. Once it's running, connect via RDP (Azure Portal → VM → **Connect** →
   download the `.rdp` file → open it, log in with your admin credentials).

### On the VM, install the pieces:

3. **Enable IIS**: Server Manager → Add Roles and Features → check
   "Web Server (IIS)" → finish the wizard.
4. **Install HttpPlatformHandler**: download and run the installer from
   Microsoft: search "IIS HttpPlatformHandler download" (it's a small
   `.msi`). This lets IIS manage a Python process.
5. **Install Python**: download the Windows installer from
   [python.org](https://www.python.org/downloads/windows/) (3.11 or 3.12),
   run it, and check "Add python.exe to PATH".
6. **Install the SQL Server ODBC driver**: download "ODBC Driver 18 for
   SQL Server" from Microsoft and install it.

### Deploy the app files:

7. Copy this whole `TailoringWebApp` folder onto the server, e.g. to
   `C:\inetpub\wwwroot\TailoringWebApp`. (Easiest ways: `git clone` your
   repo on the VM, or upload the zip via RDP clipboard/file transfer and
   extract it there.)
8. Open a Command Prompt on the VM in that folder and run:
   ```
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```
9. Edit `web.config` (already included in this project) and fill in:
   - The real path to `python.exe` inside `venv\Scripts\` if different
     from the default shown.
   - `SECRET_KEY` - generate one with
     `python -c "import secrets; print(secrets.token_hex(32))"`.
   - `MSSQL_SERVER`, `MSSQL_DATABASE`, `MSSQL_USERNAME`, `MSSQL_PASSWORD`
     from Part A.
   - Email settings if you want real emails sent (otherwise leave
     `EMAIL_BACKEND=console`, which just logs instead of sending).

### Create the IIS site:

10. Open **IIS Manager** → right-click **Sites** → **Add Website**:
    - **Site name**: TailoringWebApp
    - **Physical path**: `C:\inetpub\wwwroot\TailoringWebApp`
    - **Binding**: Type `http`, port `80` (add `https`/443 later once you
      have a certificate).
11. Click the site → **OK**. IIS will read `web.config` and start the
    Python process behind the scenes the first time a request comes in.
12. Test by browsing to `http://<vm-public-ip>` from your own computer.
    You should see the tailoring home page. Try `/admin/login` too.

If it doesn't load, check `logs\stdout.log` inside the app folder on the
VM - `web.config` is configured to log the Python process's output there.

---

## Part C - Domain name + HTTPS

1. **Point your domain at the VM**: in your domain registrar's DNS
   settings, add an **A record** pointing to the VM's public IP address
   (find it in the Azure Portal on the VM's overview page). Optionally
   use **Azure DNS** instead if you want to manage it inside Azure.
2. **Get a free TLS certificate**: the simplest option on a VM is
   [win-acme](https://www.win-acme.com/) (a free Let's Encrypt client for
   Windows/IIS) - download it, run it on the VM, point it at your site in
   IIS, and it automatically creates the certificate, binds it to port
   443, and sets up auto-renewal.
3. Once that's done, your site is live at `https://yourdomain.com`.

---

## Part D - Ongoing operations

- **Updating the app**: stop the site in IIS Manager (or just overwrite
  files - HttpPlatformHandler restarts the Python process on the next
  request after a recycle), redeploy your updated files, restart the site.
- **Backups**: Azure SQL Database has automatic backups built in
  (Point-in-Time Restore) - no extra setup needed, but check the
  retention period matches what BRS Section 37 expects for your business.
  Also back up the `uploads/Images/` folder separately (e.g. to Azure
  Blob Storage or a scheduled copy job) since that's where trial/order
  photos live.
- **Scaling**: if traffic grows, resize the VM (Azure Portal → VM → Size)
  or scale the Azure SQL Database tier up - no code changes needed either
  way.
- **Change the default admin password** (`admin` / `admin123`) the moment
  the site is reachable publicly - log in and there's currently no
  in-app password-change screen, so update it directly via a SQL query
  against `admin_users.password_hash` using a hash generated with:
  ```
  python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-new-password'))"
  ```

---

## Alternative: skip the VM, use Azure App Service (less BRS-literal, less setup)

If at any point managing your own VM/IIS feels like more than you want,
**Azure App Service (Windows plan) with Python** can run this same app
directly - no IIS install, no VM patching - while still using the same
Azure SQL Database from Part A. It's not literally "IIS on a server you
manage," but it is Microsoft's standard, fully-managed way to host a
Python web app on Windows infrastructure with SQL Server. Ask if you'd
like the steps for that instead.
