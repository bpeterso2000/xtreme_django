# Developer Documentation: Django Project Setup Script

## Overview

This Python script automates the setup of a Django project using UV (a fast Python package installer and resolver). It creates a virtual environment, installs Django, sets up a project structure, and configures a basic welcome page.

## Prerequisites

- **Python 3.7+** installed on your system
- **UV** package manager installed ([Installation Guide](https://github.com/astral-sh/uv))
- Operating System: Windows, macOS, Linux, or WSL

## Features

- Cross-platform compatibility (Windows, macOS, Linux, WSL)
- Automated virtual environment creation
- Django project and app initialization
- Basic template and view configuration
- Comprehensive error handling and logging

## Script Components

### 1. Platform Detection

```python
os_type = platform.system()
if os_type == 'Windows':
    venv_python = '.venv\\Scripts\\python.exe'
else:
    venv_python = '.venv/bin/python'
```

Automatically detects the operating system and sets appropriate paths for the virtual environment Python executable.

### 2. Command Execution Function

```python
def run_command(command, check=True)
```

A utility function that:
- Executes shell commands safely
- Provides detailed logging (stdout/stderr)
- Handles errors gracefully
- Exits on failure when `check=True`

**Parameters:**
- `command` (list): Command and arguments to execute
- `check` (bool): Whether to exit on non-zero return codes

**Returns:**
- `subprocess.CompletedProcess` object

### 3. Project Structure Created

```
.venv/                  # Virtual environment
pyproject.toml          # UV project configuration
xtremeadmin/           # Django project directory
├── manage.py
├── xtremeadmin/       # Project settings directory
│   ├── __init__.py
│   ├── settings.py    # Modified to include app
│   ├── urls.py        # Modified to include app URLs
│   └── wsgi.py
└── xtreme_admin/      # Django app directory
    ├── __init__.py
    ├── views.py       # Custom welcome view
    ├── urls.py        # App URL configuration
    └── templates/
        └── welcome.html  # Welcome page template
```

## Workflow Steps

1. **UV Project Initialization**
   - Checks for existing `pyproject.toml`
   - Runs `uv init` if not present

2. **Virtual Environment Creation**
   - Creates `.venv` directory using `uv venv`
   - Verifies environment creation

3. **Django Installation**
   - Adds Django to project dependencies via `uv add django`

4. **Django Project Creation**
   - Creates project named `xtremeadmin`
   - Uses `uv run` to execute Django commands

5. **Django App Creation**
   - Creates app named `xtreme_admin`
   - Maintains Python naming conventions

6. **Configuration Updates**
   - Adds app to `INSTALLED_APPS` in settings.py
   - Creates welcome view in views.py
   - Sets up URL routing
   - Creates HTML template

## Usage

### Basic Usage

```bash
python setup_script.py
```

### Post-Setup

After successful execution, run the development server:

```bash
cd xtremeadmin
uv run manage.py runserver
```

Access the application at `http://localhost:8000/`

## Error Handling

The script includes comprehensive error handling for:

- **Missing UV Installation**: Exits with clear error message
- **File Not Found**: Handles missing executables or paths
- **Command Failures**: Logs stderr and exit codes
- **Virtual Environment Issues**: Verifies venv creation before proceeding

## Customization

### Modifying Project/App Names

To change the project or app names, update these variables:

```python
# Line 44: Project name
run_command(["uv", "run", "django-admin", "startproject", "your_project_name"])

# Line 50: App name
run_command(["uv", "run", "manage.py", "startapp", "your_app_name"])
```

Remember to update all references throughout the script.

### Adding Additional Dependencies

Add more packages after Django installation:

```python
run_command(["uv", "add", "package_name"])
```

## Troubleshooting

### Common Issues

1. **UV Not Found**
   - Ensure UV is installed: `pip install uv`
   - Verify UV is in PATH: `uv --version`

2. **Permission Errors**
   - On Unix systems, ensure script has execute permissions
   - Run with appropriate user privileges

3. **Existing Project Files**
   - Script skips `uv init` if `pyproject.toml` exists
   - Clean directory for fresh installation

4. **Virtual Environment Issues**
   - Check `.venv` directory permissions
   - Ensure no conflicting Python installations

### Debug Mode

For verbose output, the script already includes detailed logging. To add more debugging:

```python
# Add before run_command calls
print(f"DEBUG: Current directory: {os.getcwd()}")
print(f"DEBUG: Files present: {os.listdir('.')}")
```

## Security Considerations

- Script uses `shell=False` in subprocess calls for security
- No user input is directly passed to shell commands
- File operations use safe path joining methods

## Limitations

- Assumes UV is installed and accessible in PATH
- Creates opinionated project structure
- Basic template without styling
- No database migrations run automatically

## Future Enhancements

Potential improvements for the script:

1. Add command-line arguments for project/app names
2. Include database migration commands
3. Add option for different Django project templates
4. Include CSS/JavaScript framework setup
5. Add Docker configuration generation

## Contributing

When modifying this script:

1. Maintain cross-platform compatibility
2. Add error handling for new commands
3. Update documentation for changes
4. Test on multiple operating systems
5. Follow Python PEP 8 style guidelines

## License

This script is provided as-is for educational and development purposes.
