# placement-prep-analyser

## Install Github Desktop / Github cli
# Clone repo into local in terminal / command prompt. Before cloning install github desktop / github cli
1. git clone https://github.com/ksrctcse/placement-prep-analyser.git from cli or git desktop
Install python3 
  # If windows download python3 from the python website and set the PATH accordingly
  # If mac use brew install python3
Install Postgres
  # 🐘 Install PostgreSQL on Windows
🔽 1. Download PostgreSQL
Go to the official site: PostgreSQL
Download the Windows installer (by EnterpriseDB)
⚙️ 2. Run the Installer

During setup:

You’ll be asked to configure:
Installation Directory → keep default
Components → ensure:
✅ PostgreSQL Server
✅ pgAdmin (GUI tool)
Password → set a password for user postgres ⚠️ remember this
Port → default is 5432 (keep it unless conflict)
🧪 3. Verify Installation

After installation:

Option A: Using Command Prompt
psql -U postgres

Enter your password → you should see:

postgres=#


**Then run the below migration for the first time. ** 
cd backend
python run_migrations.py up

## Commands to run BE,FE & migrations
