"""
Growvity Neo4j Graph Models
Hierarchical urban node structure with override-based inheritance

Hierarchy:
    Project → Site → Building → Zone
   
Each node supports:
    - Local overrides (properties set directly on the node)
    - Inherited properties (resolved recursively from parent nodes)
"""
from neomodel import (
    StructuredNode, StringProperty, JSONProperty, UniqueIdProperty,
    RelationshipTo, RelationshipFrom, ZeroOrMore, ZeroOrOne, DateTimeProperty
)
from datetime import datetime
from typing import Optional, Any
import hashlib
import json


class BaseUrbanNode(StructuredNode):
    """
    Abstract base class for all urban planning nodes.
    Provides common properties and inheritance resolution.
    """
    __abstract_node__ = True
    
    # Unique identifier
    uid = UniqueIdProperty()
    
    # Node name (required)
    name = StringProperty(required=True, index=True)
    
    # Local overrides - properties that override inherited values
    # Stored as JSON: {"num_floors": 15, "floor_height": 3.2}
    overrides = JSONProperty(default=dict)
    
    def resolve_property(self, key: str, default: Any = None) -> Any:
        """
        Resolve a single property through the inheritance chain.
        
        Priority:
            1. Local override
            2. Parent's resolved value
            3. Default value
        
        Args:
            key: Property name to resolve
            default: Default value if not found anywhere
        
        Returns:
            Resolved property value
        """
        # Check local overrides first
        if self.overrides and key in self.overrides:
            return self.overrides[key]
        
        # Check parent
        parent = self.get_parent()
        if parent:
            return parent.resolve_property(key, default)
        
        return default
    
    def get_parent(self) -> Optional['BaseUrbanNode']:
        """
        Get the parent node. Override in child classes.
        
        Returns:
            Parent node or None if at root
        """
        return None
    
    def get_effective_properties(self) -> dict:
        """
        Get all effective properties (resolved through inheritance).
        
        Returns:
            Dictionary of all resolved properties
        """
        # Property keys to resolve
        keys = [
            'num_floors', 'floor_height', 'setback',
            'use_type', 'gfa_ratio', 'color'
        ]
        
        # Defaults
        defaults = {
            'num_floors': 10,
            'floor_height': 3.5,
            'setback': 5.0,
            'use_type': 'residential',
            'gfa_ratio': 0.8,
            'color': '#4A90D9'
        }
        
        return {
            key: self.resolve_property(key, defaults.get(key))
            for key in keys
        }
    
    def set_override(self, key: str, value: Any) -> None:
        """Set a local override value"""
        if self.overrides is None:
            self.overrides = {}
        self.overrides[key] = value
        self.save()
    
    def clear_override(self, key: str) -> bool:
        """Remove a local override (inherit from parent)"""
        if self.overrides and key in self.overrides:
            del self.overrides[key]
            self.save()
            return True
        return False
    
    def to_dict(self, include_children: bool = False) -> dict:
        """Convert node to dictionary"""
        return {
            'uid': self.uid,
            'name': self.name,
            'type': self.__class__.__name__.lower(),
            'overrides': self.overrides or {},
            'effective_properties': self.get_effective_properties()
        }


class Project(BaseUrbanNode):
    """
    Top-level project node.
    Contains multiple sites and provides default parameters.
    """
    # Relationships
    sites = RelationshipTo('Site', 'HAS_SITE', cardinality=ZeroOrMore)
    
    # Project-specific properties
    description = StringProperty(default='')
    
    def get_parent(self) -> Optional[BaseUrbanNode]:
        """Projects have no parent"""
        return None
    
    def to_dict(self, include_children: bool = False) -> dict:
        data = super().to_dict()
        data['description'] = self.description
        
        if include_children:
            data['children'] = [
                site.to_dict(include_children=True)
                for site in self.sites.all()
            ]
        
        return data


class Site(BaseUrbanNode):
    """
    Site node within a project.
    Represents a land parcel that can contain buildings.
    """
    # Relationships
    project = RelationshipFrom('Project', 'HAS_SITE', cardinality=ZeroOrOne)
    buildings = RelationshipTo('Building', 'HAS_BUILDING', cardinality=ZeroOrMore)
    
    # Site-specific properties
    boundary_geojson = JSONProperty(default=None)  # GeoJSON polygon boundary
    
    def get_parent(self) -> Optional[BaseUrbanNode]:
        """Get parent project"""
        projects = self.project.all()
        return projects[0] if projects else None
    
    def to_dict(self, include_children: bool = False) -> dict:
        data = super().to_dict()
        data['boundary_geojson'] = self.boundary_geojson
        data['geometry'] = self.boundary_geojson
        
        if include_children:
            data['children'] = [
                building.to_dict(include_children=True)
                for building in self.buildings.all()
            ]
        
        return data


class Building(BaseUrbanNode):
    """
    Building node within a site.
    Contains parametric building data and zones.
    """
    # Relationships
    site = RelationshipFrom('Site', 'HAS_BUILDING', cardinality=ZeroOrOne)
    zones = RelationshipTo('Zone', 'HAS_ZONE', cardinality=ZeroOrMore)
    
    # Building-specific properties
    footprint_geojson = JSONProperty(default=None)  # GeoJSON polygon footprint
    
    # Cache fields
    cached_geometry = StringProperty(default=None)     # GLTF binary string
    cache_key = StringProperty(default=None)           # Hash of parameters
    cache_timestamp = DateTimeProperty(default=None)   # When cached
    cache_lod = StringProperty(default='medium')       # LOD level cached
    
    def get_cache_key(self, lod: str = 'medium') -> str:
        """
        Generate cache key from effective properties.
        Cache key includes geometry and all parameters that affect compute.
        
        Args:
            lod: Level of detail (affects cache key)
        
        Returns:
            SHA256 hash of relevant properties
        """
        props = self.get_effective_properties()
        
        # Include all parameters that affect geometry generation
        key_data = {
            'geometry': self.footprint_geojson,
            'num_floors': props.get('num_floors'),
            'floor_height': props.get('floor_height'),
            'setback': props.get('setback'),
            'lod': lod
        }
        
        # Create stable JSON string
        json_str = json.dumps(key_data, sort_keys=True)
        
        # Return SHA256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def is_cache_valid(self, lod: str = 'medium') -> bool:
        """
        Check if cached geometry is still valid.
        
        Args:
            lod: Level of detail to check
        
        Returns:
            True if cache exists and parameters haven't changed
        """
        if not self.cached_geometry or not self.cache_key:
            return False
        
        # Check if LOD matches
        if self.cache_lod != lod:
            return False
        
        # Check if parameters have changed
        current_key = self.get_cache_key(lod)
        return current_key == self.cache_key
    
    def invalidate_cache(self) -> None:
        """Clear cached geometry"""
        self.cached_geometry = None
        self.cache_key = None
        self.cache_timestamp = None
        self.cache_lod = None
        self.save()
    
    def get_parent(self) -> Optional[BaseUrbanNode]:
        """Get parent site"""
        sites = self.site.all()
        return sites[0] if sites else None
    
    def get_total_height(self) -> float:
        """Calculate total building height"""
        num_floors = self.resolve_property('num_floors', 10)
        floor_height = self.resolve_property('floor_height', 3.5)
        return num_floors * floor_height
    
    def to_dict(self, include_children: bool = False) -> dict:
        data = super().to_dict()
        data['footprint_geojson'] = self.footprint_geojson
        data['geometry'] = self.footprint_geojson
        data['total_height'] = self.get_total_height()
        
        # Include cache metadata
        data['cache_status'] = {
            'cached': self.cached_geometry is not None,
            'cache_timestamp': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            'cache_lod': self.cache_lod
        }
        
        if include_children:
            data['children'] = [
                zone.to_dict(include_children=True)
                for zone in self.zones.all()
            ]
        
        return data


class Zone(BaseUrbanNode):
    """
    Zone node within a building.
    Represents a functional area (residential, commercial, etc.)
    """
    # Relationships
    building = RelationshipFrom('Building', 'HAS_ZONE', cardinality=ZeroOrOne)
    
    # Zone-specific properties
    floor_range_start = StringProperty(default='1')  # Start floor
    floor_range_end = StringProperty(default='1')    # End floor
    
    def get_parent(self) -> Optional[BaseUrbanNode]:
        """Get parent building"""
        buildings = self.building.all()
        return buildings[0] if buildings else None
    
    def to_dict(self, include_children: bool = False) -> dict:
        data = super().to_dict()
        data['floor_range'] = {
            'start': self.floor_range_start,
            'end': self.floor_range_end
        }
        return data


# ==================== UTILITY FUNCTIONS ====================

def create_sample_project() -> Project:
    """Create a sample project with hierarchy for testing"""
    # Create project
    project = Project(
        name='Sample Urban Development',
        description='A mixed-use urban development project',
        overrides={
            'floor_height': 3.5,
            'setback': 5.0
        }
    ).save()
    
    # Create site
    site = Site(
        name='Main Site',
        boundary_geojson={
            'type': 'Polygon',
            'coordinates': [[[0, 0], [100, 0], [100, 80], [0, 80], [0, 0]]]
        }
    ).save()
    project.sites.connect(site)
    
    # Create buildings
    building_a = Building(
        name='Tower A',
        overrides={
            'num_floors': 25,
            'use_type': 'residential'
        }
    ).save()
    site.buildings.connect(building_a)
    
    building_b = Building(
        name='Building B',
        overrides={
            'num_floors': 8,
            'use_type': 'commercial'
        }
    ).save()
    site.buildings.connect(building_b)
    
    # Create zones
    zone_residential = Zone(
        name='Residential Zone',
        floor_range_start='5',
        floor_range_end='25',
        overrides={'use_type': 'residential'}
    ).save()
    building_a.zones.connect(zone_residential)
    
    zone_podium = Zone(
        name='Podium Retail',
        floor_range_start='1',
        floor_range_end='4',
        overrides={'use_type': 'retail'}
    ).save()
    building_a.zones.connect(zone_podium)
    
    return project
