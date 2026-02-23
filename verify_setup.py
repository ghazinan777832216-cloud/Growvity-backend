
import os
import sys
import requests
from neomodel import config, db

# Setup Django standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings.settings')
import django
django.setup()

from django.conf import settings

output_file = 'setup_status.txt'

def check_neo4j():
    try:
        db.set_connection(settings.NEO4J_BOLT_URL)
        # Try a simple query
        db.cypher_query("MATCH (n) RETURN count(n) LIMIT 1")
        return "Neo4j: Connected"
    except Exception as e:
        return f"Neo4j: Failed ({str(e)})"

def check_rhino():
    url = settings.RHINO_COMPUTE_URL + '/healthcheck' 
    # Rhino compute usually has /healthcheck or just /
    try:
        # Just check base URL or version
        response = requests.get(settings.RHINO_COMPUTE_URL, timeout=2)
        if response.status_code < 500:
            return "Rhino Compute: Reachable"
        return f"Rhino Compute: Error {response.status_code}"
    except Exception as e:
        return f"Rhino Compute: Failed ({str(e)})"

with open(output_file, 'w') as f:
    f.write(check_neo4j() + '\n')
    f.write(check_rhino() + '\n')

print("Verification complete. Check setup_status.txt")
