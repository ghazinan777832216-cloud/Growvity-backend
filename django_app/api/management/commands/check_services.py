
from django.core.management.base import BaseCommand
from django.conf import settings
from neomodel import db
import requests
import sys

class Command(BaseCommand):
    help = 'Check connections to external services (Neo4j, Rhino Compute)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking connections...")
        
        # Check Neo4j
        neo_url = getattr(settings, 'NEO4J_BOLT_URL', 'Unknown')
        self.stdout.write(f"Neo4j URL: {neo_url}")
        try:
            db.set_connection(neo_url)
            results, _ = db.cypher_query("MATCH (n) RETURN count(n) LIMIT 1")
            self.stdout.write(self.style.SUCCESS(f"✅ Neo4j Connected. Node count check: {results}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Neo4j Failed: {str(e)}"))
            self.stdout.write(self.style.WARNING("  -> Ensure Neo4j is running and credentials in settings.py or environment variables are correct."))

        # Check Rhino Compute
        rhino_url = getattr(settings, 'RHINO_COMPUTE_URL', 'http://host.docker.internal:5000')
        self.stdout.write(f"Rhino Compute URL: {rhino_url}")
        try:
            # Rhino Compute usually has a health check or just root
            resp = requests.get(rhino_url + '/healthcheck', timeout=2)
            if resp.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✅ Rhino Compute Reachable (/healthcheck)"))
            else:
                 # Fallback check root
                resp = requests.get(rhino_url, timeout=2)
                if resp.status_code < 500:
                    self.stdout.write(self.style.SUCCESS("✅ Rhino Compute Reachable (Root)"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Rhino Compute Error: {resp.status_code}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Rhino Compute Failed: {str(e)}"))
            self.stdout.write(self.style.WARNING("  -> Ensure Rhino.Compute.exe is running."))

