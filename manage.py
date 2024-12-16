#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import ctypes

# Add the path to your geos_c.dll
geos_path = r'C:\Program Files\GEOS\build\bin\Debug'
os.environ['PATH'] = geos_path + ';' + os.environ['PATH']

# Load the DLL
ctypes.WinDLL(os.path.join(geos_path, 'geos_c.dll'))

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_security_app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
