# Odoo 19 Community Edition Setup Guide for Windows 11

This guide provides step-by-step instructions to set up an Odoo 19 Community Edition development environment natively on Windows 11. It covers installing prerequisites, cloning the source code, setting up a virtual environment, configuring PostgreSQL, and starting the server.

---

## 1. Prevent Windows from Sleeping (Optional but Recommended)
Large downloads like the Odoo repository can fail if Windows goes to sleep and turns off the network adapter.
1. Open **Settings** > **System** > **Power & battery**.
2. Expand the **Screen and sleep** section.
3. Set the "When plugged in, put my device to sleep after" option to **Never**.

---

## 2. Install System Dependencies
We will use the Windows Package Manager (`winget`) to install the required system dependencies. Open PowerShell as Administrator and run the following commands:

```powershell
# Install Git
winget install Git.Git

# Install Python 3.12
winget install Python.Python.3.12

# Install PostgreSQL 17
winget install PostgreSQL.PostgreSQL.17

# Install wkhtmltopdf (Required for generating PDF reports)
winget install wkhtmltopdf
```

> [!IMPORTANT]
> During the PostgreSQL installation, a setup wizard will appear. When prompted, set the superuser password to **`postgres`** (or remember your custom password as you will need it in Step 5).

Close and reopen PowerShell to ensure all new installed programs are available in your system's `PATH`.

Verify the installations:
```powershell
git --version
python --version
postgres --version
wkhtmltopdf --version
```

---

## 3. Clone the Odoo 19 Repository
Navigate to your desired workspace folder (e.g., `C:\Users\YourUser\Documents\Odoo19DevEnv`) and clone the repository.

```powershell
mkdir C:\Users\YourUser\Documents\Odoo19DevEnv
cd C:\Users\YourUser\Documents\Odoo19DevEnv

# Clone the 19.0 branch (shallow clone to save time and disk space)
git clone https://github.com/odoo/odoo.git -b 19.0 --depth 1 odoo
```

---

## 4. Set Up the Python Virtual Environment
It is highly recommended to isolate Odoo's Python dependencies in a virtual environment.

```powershell
# Create the virtual environment named 'venv'
python -m venv venv

# Upgrade pip and setuptools, then install Odoo requirements
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\venv\Scripts\python.exe -m pip install -r .\odoo\requirements.txt
```

---

## 5. Configure PostgreSQL
Odoo needs a dedicated PostgreSQL user to manage its databases.

1. Set the default PostgreSQL superuser password in your environment (use the password you set during installation).
2. Use `psql` to create a new superuser named `odoo` with the password `odoo`.

```powershell
# Replace 'postgres' with your actual password if you chose a different one
$env:PGPASSWORD='postgres'
psql -U postgres -c "CREATE USER odoo WITH PASSWORD 'odoo' SUPERUSER;"
```

---

## 6. Create the Odoo Configuration File
You can generate the `odoo.conf` file automatically in your root directory by running the following PowerShell command:

```powershell
# Ensure you are in the directory which you created in Step 3 e.g., `C:\Users\YourUser\Documents\Odoo19DevEnv`
@"
[options]
; Master password for database operations:
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = $((Get-Location).Path)\odoo\addons
"@ | Out-File -FilePath .\odoo.conf -Encoding utf8
```

---

## 7. Start the Odoo Server
With everything configured, you can now start the Odoo server using the Python executable inside your virtual environment, passing it the path to `odoo-bin` and your `odoo.conf` file.

```powershell
.\venv\Scripts\python.exe .\odoo\odoo-bin -c odoo.conf
```

The server will initialize. Open your web browser and navigate to:
**[http://localhost:8069](http://localhost:8069)**

You should see the Odoo database creation screen. Congratulations! Your development environment is ready.
