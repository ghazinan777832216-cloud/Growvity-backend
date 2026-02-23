"""
WSGI config for Growvity project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings.settings')

application = get_wsgi_application()
