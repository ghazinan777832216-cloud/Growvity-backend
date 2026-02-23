from django.apps import AppConfig
from django.conf import settings
from neomodel import config, db
import logging

logger = logging.getLogger(__name__)

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app.api'

    def ready(self):
        # Initialize Neo4j connection
        try:
            bolt_url = getattr(config, 'DATABASE_URL', getattr(settings, 'NEO4J_BOLT_URL', 'bolt://neo4j:password@localhost:7687'))
            logger.info(f"Initializing Neo4j connection to {bolt_url}")
            db.set_connection(bolt_url)
            # Verify connection
            db.cypher_query("MATCH (n) RETURN count(n) LIMIT 1")
            logger.info("Neo4j connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
