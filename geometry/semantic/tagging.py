"""
Growvity Semantic Tagging
Injects semantic metadata into geometry objects
"""
from typing import Dict, Any
from datetime import datetime, timezone


def assign_metadata(geometry_data: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject semantic properties into geometry data.
    
    This creates a semantically enriched object that contains both
    the geometry and its associated metadata.
    
    Args:
        geometry_data: Raw geometry data (meshes, curves, etc.)
        properties: Semantic properties to attach
    
    Returns:
        Enriched geometry data with metadata
    """
    return {
        'geometry': geometry_data,
        'metadata': properties,
        'semantic_version': '1.0',
        'schema': 'growvity-urban-v1',
        'tagged_at': datetime.now(timezone.utc).isoformat()
    }


def extract_metadata(enriched_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from an enriched geometry object.
    
    Args:
        enriched_data: Enriched geometry data with metadata
    
    Returns:
        Metadata dictionary
    """
    return enriched_data.get('metadata', {})


def validate_semantic_object(data: Dict[str, Any]) -> bool:
    """
    Validate that an object has proper semantic structure.
    
    Args:
        data: Object to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['geometry', 'metadata', 'semantic_version']
    return all(key in data for key in required_keys)


class SemanticObject:
    """
    A semantically enriched geometry object.
    Provides methods for property manipulation.
    """
    
    def __init__(self, geometry_data: Dict[str, Any]):
        """Initialize with raw geometry data"""
        self.geometry = geometry_data
        self.metadata = {}
        self.semantic_version = '1.0'
        self.schema = 'growvity-urban-v1'
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a semantic property"""
        self.metadata[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a semantic property"""
        return self.metadata.get(key, default)
    
    def has_property(self, key: str) -> bool:
        """Check if property exists"""
        return key in self.metadata
    
    def remove_property(self, key: str) -> bool:
        """Remove a property"""
        if key in self.metadata:
            del self.metadata[key]
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'geometry': self.geometry,
            'metadata': self.metadata,
            'semantic_version': self.semantic_version,
            'schema': self.schema,
            'tagged_at': datetime.now(timezone.utc).isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticObject':
        """Create from dictionary representation"""
        obj = cls(data.get('geometry', {}))
        obj.metadata = data.get('metadata', {})
        obj.semantic_version = data.get('semantic_version', '1.0')
        obj.schema = data.get('schema', 'growvity-urban-v1')
        return obj


# Urban-specific semantic types
URBAN_TYPES = {
    'residential': {
        'color': '#4A90D9',
        'category': 'living',
        'icon': 'home'
    },
    'commercial': {
        'color': '#E67E22',
        'category': 'business',
        'icon': 'briefcase'
    },
    'retail': {
        'color': '#9B59B6',
        'category': 'shopping',
        'icon': 'shopping-cart'
    },
    'office': {
        'color': '#2ECC71',
        'category': 'work',
        'icon': 'building'
    },
    'amenity': {
        'color': '#F1C40F',
        'category': 'service',
        'icon': 'users'
    }
}


def get_type_color(use_type: str) -> str:
    """Get the display color for a use type"""
    return URBAN_TYPES.get(use_type, {}).get('color', '#4A90D9')


def get_type_category(use_type: str) -> str:
    """Get the category for a use type"""
    return URBAN_TYPES.get(use_type, {}).get('category', 'unknown')
