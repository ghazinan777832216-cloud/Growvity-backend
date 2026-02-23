
import os
import django
import sys

# Add graph module to path
sys.path.insert(0, os.path.join(os.getcwd()))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings.settings')
django.setup()

from graph.neo4j_models import Project, create_sample_project
from neomodel import db

def populate():
    try:
        # Check if any projects exist
        projects = Project.nodes.all()
        if not projects:
            print("No projects found. Creating sample project...")
            project = create_sample_project()
            print(f"Sample project created: {project.name} ({project.uid})")
        else:
            print(f"Found {len(projects)} existing projects.")
            for p in projects:
                print(f" - {p.name} ({p.uid})")
    except Exception as e:
        print(f"Error connecting to Neo4j or populating data: {e}")

if __name__ == "__main__":
    populate()
