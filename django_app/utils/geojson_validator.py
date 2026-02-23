"""
GeoJSON Validation Utilities for Backend
Validates GeoJSON geometry before processing with Rhino Compute
"""
from typing import Dict, List, Tuple, Any


def validate_geojson(geojson: Any) -> Tuple[bool, List[str]]:
    """
    Validate GeoJSON geometry structure
    
    Args:
        geojson: GeoJSON object to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Basic type check
    if not isinstance(geojson, dict):
        errors.append("GeoJSON must be a dictionary/object")
        return (False, errors)
    
    # Type field validation
    if 'type' not in geojson:
        errors.append("Missing 'type' field")
        return (False, errors)
    
    geojson_type = geojson.get('type')
    valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                   'MultiLineString', 'MultiPolygon', 'GeometryCollection',
                   'Feature', 'FeatureCollection']
    
    if geojson_type not in valid_types:
        errors.append(f"Invalid GeoJSON type: {geojson_type}")
        return (False, errors)
    
    # Validate based on type
    if geojson_type == 'FeatureCollection':
        _validate_feature_collection(geojson, errors)
    elif geojson_type == 'Feature':
        _validate_feature(geojson, errors)
    else:
        _validate_geometry(geojson, errors)
    
    return (len(errors) == 0, errors)


def _validate_feature_collection(fc: Dict, errors: List[str]) -> None:
    """Validate FeatureCollection structure"""
    if 'features' not in fc:
        errors.append("FeatureCollection missing 'features' array")
        return
    
    if not isinstance(fc['features'], list):
        errors.append("'features' must be an array")
        return
    
    if len(fc['features']) == 0:
        errors.append("FeatureCollection has no features")
    
    for i, feature in enumerate(fc['features']):
        if not isinstance(feature, dict):
            errors.append(f"Feature at index {i} is not an object")
            continue
        
        if feature.get('type') != 'Feature':
            errors.append(f"Feature at index {i} has invalid type")
        else:
            _validate_feature(feature, errors, f"Feature {i}")


def _validate_feature(feature: Dict, errors: List[str], prefix: str = "Feature") -> None:
    """Validate Feature structure"""
    if 'geometry' not in feature:
        errors.append(f"{prefix}: Missing 'geometry' field")
        return
    
    geometry = feature['geometry']
    if geometry is None:
        errors.append(f"{prefix}: Geometry is null")
        return
    
    _validate_geometry(geometry, errors, prefix)


def _validate_geometry(geometry: Dict, errors: List[str], prefix: str = "Geometry") -> None:
    """Validate Geometry object"""
    if 'type' not in geometry:
        errors.append(f"{prefix}: Missing 'type' field")
        return
    
    if 'coordinates' not in geometry:
        errors.append(f"{prefix}: Missing 'coordinates' field")
        return
    
    coords = geometry['coordinates']
    if not isinstance(coords, list):
        errors.append(f"{prefix}: 'coordinates' must be an array")
        return
    
    geom_type = geometry['type']
    
    # Validate coordinates based on geometry type
    if geom_type == 'Point':
        _validate_position(coords, errors, prefix)
    elif geom_type == 'LineString':
        _validate_linestring_coords(coords, errors, prefix)
    elif geom_type == 'Polygon':
        _validate_polygon_coords(coords, errors, prefix)
    elif geom_type == 'MultiPoint':
        for i, pos in enumerate(coords):
            _validate_position(pos, errors, f"{prefix} Point {i}")
    elif geom_type == 'MultiLineString':
        for i, line in enumerate(coords):
            _validate_linestring_coords(line, errors, f"{prefix} LineString {i}")
    elif geom_type == 'MultiPolygon':
        for i, poly in enumerate(coords):
            _validate_polygon_coords(poly, errors, f"{prefix} Polygon {i}")


def _validate_position(pos: List, errors: List[str], prefix: str) -> None:
    """Validate a single position [lon, lat]"""
    if not isinstance(pos, list) or len(pos) < 2:
        errors.append(f"{prefix}: Position must be [longitude, latitude]")
        return
    
    lon, lat = pos[0], pos[1]
    
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        errors.append(f"{prefix}: Coordinates must be numbers")
        return
    
    if lon < -180 or lon > 180:
        errors.append(f"{prefix}: Longitude {lon} out of range [-180, 180]")
    
    if lat < -90 or lat > 90:
        errors.append(f"{prefix}: Latitude {lat} out of range [-90, 90]")


def _validate_linestring_coords(coords: List, errors: List[str], prefix: str) -> None:
    """Validate LineString coordinates"""
    if not isinstance(coords, list) or len(coords) < 2:
        errors.append(f"{prefix}: LineString must have at least 2 positions")
        return
    
    for i, pos in enumerate(coords):
        _validate_position(pos, errors, f"{prefix} position {i}")


def _validate_polygon_coords(coords: List, errors: List[str], prefix: str) -> None:
    """Validate Polygon coordinates"""
    if not isinstance(coords, list) or len(coords) == 0:
        errors.append(f"{prefix}: Polygon must have at least one ring")
        return
    
    for ring_idx, ring in enumerate(coords):
        ring_prefix = f"{prefix} ring {ring_idx}"
        
        if not isinstance(ring, list) or len(ring) < 4:
            errors.append(f"{ring_prefix}: Ring must have at least 4 positions")
            continue
        
        # Check closure
        first = ring[0]
        last = ring[-1]
        if not isinstance(first, list) or not isinstance(last, list):
            errors.append(f"{ring_prefix}: Invalid ring positions")
            continue
        
        if len(first) >= 2 and len(last) >= 2:
            if first[0] != last[0] or first[1] != last[1]:
                errors.append(f"{ring_prefix}: Ring not closed (first != last)")
        
        # Validate all positions
        for i, pos in enumerate(ring):
            _validate_position(pos, errors, f"{ring_prefix} position {i}")


def validate_geometry_for_grasshopper(geometry: Any) -> Tuple[bool, List[str]]:
    """
    Specific validation for geometries going to Grasshopper
    More strict requirements for building footprints
    
    Args:
        geometry: GeoJSON geometry object
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    # First run standard validation
    is_valid, errors = validate_geojson(geometry)
    
    if not is_valid:
        return (False, errors)
    
    # Additional Grasshopper-specific validations
    geom_type = geometry.get('type')
    
    # For building footprints, we expect Polygon or FeatureCollection with Polygons
    if geom_type == 'FeatureCollection':
        features = geometry.get('features', [])
        for i, feature in enumerate(features):
            feat_geom = feature.get('geometry', {})
            if feat_geom.get('type') not in ['Polygon', 'MultiPolygon']:
                errors.append(f"Feature {i}: Expected Polygon geometry for building footprint")
    
    elif geom_type == 'Feature':
        feat_geom = geometry.get('geometry', {})
        if feat_geom.get('type') not in ['Polygon', 'MultiPolygon']:
            errors.append("Expected Polygon geometry for building footprint")
    
    elif geom_type not in ['Polygon', 'MultiPolygon']:
        errors.append(f"Expected Polygon or MultiPolygon, got {geom_type}")
    
    return (len(errors) == 0, errors)
