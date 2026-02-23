"""
Growvity Graph Service - Simplified
Simple CRUD operations for Building nodes
"""
from typing import Dict, List, Optional
from graph.neo4j_models import Building
from .rhino_compute import RhinoComputeService
from datetime import datetime


class GraphService:
    """Service layer for Neo4j Building operations"""
    
    @classmethod
    def create_building(cls, data: Dict) -> Dict:
        """
        Create a new building and compute its geometry.
        
        Args:
            data: Dict with name, geojson, floors_number, floor_to_floor_height
            
        Returns:
            Building dictionary with computed geometry
        """
        # Create building node
        building = Building(
            name=data['name'],
            geojson=data['geojson'],
            floors_number=data.get('floors_number', 11.0),
            floor_to_floor_height=data.get('floor_to_floor_height', 4.0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        ).save()
        
        # Compute geometry using Rhino Compute
        try:
            glb_base64 = RhinoComputeService.compute_building({
                'name': building.name,
                'geojson': building.geojson,
                'floors_number': building.floors_number,
                'floor_to_floor_height': building.floor_to_floor_height
            })
            
            # Update building with computed geometry
            building.update_geometry(glb_base64)
            
        except Exception as e:
            print(f"Warning: Geometry computation failed: {e}")
            # Building is still saved, just without geometry
        
        return building.to_dict()
    
    @classmethod
    def get_building(cls, uid: str) -> Optional[Dict]:
        """
        Get a building by UID.
        
        Args:
            uid: Building UID
            
        Returns:
            Building dictionary or None if not found
        """
        try:
            building = Building.nodes.get(uid=uid)
            return building.to_dict()
        except Building.DoesNotExist:
            return None
    
    @classmethod
    def list_buildings(cls) -> List[Dict]:
        """
        List all buildings.
        
        Returns:
            List of building dictionaries
        """
        buildings = Building.nodes.all()
        return [b.to_dict() for b in buildings]
    
    @classmethod
    def update_building(cls, uid: str, data: Dict) -> Optional[Dict]:
        """
        Update a building and recompute geometry if parameters changed.
        
        Args:
            uid: Building UID
            data: Updated fields
            
        Returns:
            Updated building dictionary or None if not found
        """
        try:
            building = Building.nodes.get(uid=uid)
            
            # Track if geometry-affecting fields changed
            needs_recompute = False
            
            if 'name' in data:
                building.name = data['name']
            
            if 'geojson' in data:
                building.geojson = data['geojson']
                needs_recompute = True
            
            if 'floors_number' in data:
                building.floors_number = data['floors_number']
                needs_recompute = True
            
            if 'floor_to_floor_height' in data:
                building.floor_to_floor_height = data['floor_to_floor_height']
                needs_recompute = True
            
            building.updated_at = datetime.now()
            building.save()
            
            # Recompute if needed
            if needs_recompute:
                try:
                    glb_base64 = RhinoComputeService.compute_building({
                        'name': building.name,
                        'geojson': building.geojson,
                        'floors_number': building.floors_number,
                        'floor_to_floor_height': building.floor_to_floor_height
                    })
                    building.update_geometry(glb_base64)
                except Exception as e:
                    print(f"Warning: Geometry recomputation failed: {e}")
            
            return building.to_dict()
            
        except Building.DoesNotExist:
            return None
    
    @classmethod
    def delete_building(cls, uid: str) -> bool:
        """
        Delete a building.
        
        Args:
            uid: Building UID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            building = Building.nodes.get(uid=uid)
            building.delete()
            return True
        except Building.DoesNotExist:
            return False
    
    @classmethod
    def recompute_building(cls, uid: str) -> Optional[Dict]:
        """
        Force recompute building geometry.
        
        Args:
            uid: Building UID
            
        Returns:
            Updated building dictionary or None if not found
        """
        try:
            building = Building.nodes.get(uid=uid)
            
            glb_base64 = RhinoComputeService.compute_building({
                'name': building.name,
                'geojson': building.geojson,
                'floors_number': building.floors_number,
                'floor_to_floor_height': building.floor_to_floor_height
            })
            
            building.update_geometry(glb_base64)
            return building.to_dict()
            
        except Building.DoesNotExist:
            return None
        except Exception as e:
            raise RuntimeError(f"Recompute failed: {str(e)}")

    @classmethod
    def get_project_tree(cls, project_uid: str) -> Optional[Dict]:
        """
        Construct a synthetic project tree containing all buildings.
        Adapts the flat Building model to the hierarchical Frontend expectation.
        """
        # We only support one default project for now
        if project_uid != 'proj-001':
            return None
            
        buildings = cls.list_buildings()
        
        # Construct tree
        return {
            'uid': 'proj-001',
            'name': 'Growvity Project',
            'type': 'project',
            'overrides': {},
            'effective_properties': {},
            'children': [
                {
                    'uid': 'site-001',
                    'name': 'Default Site',
                    'type': 'site',
                    'overrides': {},
                    'effective_properties': {},
                    'children': buildings  # All buildings go here
                }
            ]
        }

