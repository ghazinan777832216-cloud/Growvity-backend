import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
# Add project root for 'graph' module - removed as graph is now in backend
# sys.path.append(str(BASE_DIR.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings.settings')
django.setup()

from django_app.services.graph_service import GraphService
from graph.neo4j_models import Project, create_sample_project

def test_connection():
    print("Testing Neo4j connection...")
    try:
        # 1. Check if we can reach the DB
        projects = list(Project.nodes.all())
        print(f"Connection successful. Found {len(projects)} projects.")
        
        # 2. If no projects, create a sample one
        if len(projects) == 0:
            print("No projects found. Creating sample project...")
            project = create_sample_project()
            print(f"Created sample project: {project.name} (uid: {project.uid})")
            projects = [project]
            
        # 3. Test serialization
        print("Testing serialization...")
        for p in projects:
            p_dict = p.to_dict()
            print(f"Project dict: {p_dict.get('name')} - {p_dict.get('uid')}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
