import subprocess
import os
import sys
import platform
import os.path  # For path checks

# Detect the platform and set paths accordingly
os_type = platform.system()
if os_type == 'Windows':
    venv_python = '.venv\\Scripts\\python.exe'
else:  # macOS, Linux, WSL
    venv_python = '.venv/bin/python'

# Function to run shell commands and check for errors with better logging and feedback
def run_command(command, check=True):
    print(f"Running command: {command}")  # Show the command being run
    try:
        result = subprocess.run(command, shell=False, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Print stdout
        stdout_content = result.stdout.decode().strip()
        if stdout_content:
            print(f"stdout: {stdout_content}")
        
        # Print stderr
        stderr_content = result.stderr.decode().strip()
        if stderr_content:
            print(f"stderr: {stderr_content}")
        
        if result.returncode == 0 and check:
            print("Command completed successfully.")  # Indicate success
        elif result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}.")
            sys.exit(1)
        return result
    except FileNotFoundError:
        print(f"Error: The command or file was not found. Ensure UV is installed and paths are correct.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

# Step 1: Check for existing UV project and run uv init
print("Initializing UV project...")
if os.path.exists("pyproject.toml"):
    print("Warning: pyproject.toml already exists. Skipping uv init.")
else:
    run_command(["uv", "init"])

# Step 2: Create the virtual environment using UV
print("Creating virtual environment...")
run_command(["uv", "venv", ".venv"])

# Pre-check: Ensure the virtual environment was created
if not os.path.exists(venv_python):
    print(f"Error: Virtual environment Python executable not found at {venv_python}. Please check creation.")
    sys.exit(1)

# Step 3: Add Django using UV
print("Adding Django to the project using UV...")
run_command(["uv", "add", "django"])

# Step 4: Create the Django project using uv run
print("Creating Django project using uv run...")
run_command(["uv", "run", "django-admin", "startproject", "xtremeadmin"])  # Updated command

# Step 5: Change into the project directory
os.chdir("xtremeadmin")

# Step 6: Create the Django app using uv run
print("Creating Django app using uv run...")
run_command(["uv", "run", "manage.py", "startapp", "xtreme_admin"])  # Updated command

# Step 7: Modify settings.py to add the app to INSTALLED_APPS
settings_path = "xtremeadmin/settings.py"
with open(settings_path, "r") as f:
    lines = f.readlines()

with open(settings_path, "w") as f:
    in_installed_apps = False
    for line in lines:
        if line.strip().startswith("INSTALLED_APPS = ["):
            in_installed_apps = True
            f.write(line)
        elif in_installed_apps and line.strip() == "]":
            f.write("    'xtreme_admin',\n")  # Add the app
            f.write(line)
            in_installed_apps = False
        else:
            f.write(line)

# Step 8: Modify views.py in the app
views_path = "xtreme_admin/views.py"
with open(views_path, "w") as f:
    f.write("""
from django.shortcuts import render

def welcome(request):
    return render(request, 'welcome.html')
    """)

# Step 9: Create urls.py in the app
app_urls_path = "xtreme_admin/urls.py"
with open(app_urls_path, "w") as f:
    f.write("""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
]
    """)

# Step 10: Modify the project's urls.py to include the app's URLs (UPDATED FOR FIX)
project_urls_path = "xtremeadmin/urls.py"
with open(project_urls_path, "r") as f:
    lines = f.readlines()

# Improved check and insertion for 'from django.urls import include'
if not any("include" in line and line.strip().startswith("from django.urls import") for line in lines):  # More precise check
    import_indices = [i for i, line in enumerate(lines) if line.strip().startswith(("from", "import"))]
    if import_indices:
        insert_index = import_indices[-1] + 1  # Insert after the last import line
    else:
        insert_index = 0  # Insert at the beginning if no imports
    lines.insert(insert_index, "from django.urls import include\n")  # Insert the import line

# Now, build a new set of lines with the correct modification
new_lines = []
in_urlpatterns = False
for line in lines:
    if in_urlpatterns and line.strip().rstrip(',').endswith("]"):
        new_lines.append("    path('', include('xtreme_admin.urls')),\n")  # Add inside the list
    new_lines.append(line)  # Add the original line
    if line.strip().startswith("urlpatterns = ["):
        in_urlpatterns = True
    elif in_urlpatterns and line.strip().endswith("],"):
        in_urlpatterns = False

with open(project_urls_path, "w") as f:
    f.writelines(new_lines)

# Step 11: Create the template file
template_dir = "xtreme_admin/templates"
os.makedirs(template_dir, exist_ok=True)
welcome_template_path = os.path.join(template_dir, "welcome.html")
with open(welcome_template_path, "w") as f:
    f.write("""
<h1>Welcome to Xtreme Admin</h1>
    """)

# Step 12: Add `fastcore`
print("Adding fastcore for Fast Tag support...")
run_command(["uv", "pip", "install", "fastcore"])

# Step 13: Add `fastlite`
print("Adding fastlite for Mini Data Spec support...")
run_command(["uv", "pip", "install", "fastlite"])

print("Setup complete! You can now run the server with:")
print(f"uv run xtremedjango/manage.py runserver")
