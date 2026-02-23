"""
Growvity GLB Encoder
Utilities for Base64 GLB encoding/decoding

GLB is the binary container format for glTF 3D models.
All geometry in Growvity is transferred as Base64-encoded GLB strings.
"""
import base64
import json
import struct
from typing import Dict, Any, Optional


def encode_glb(binary_data: bytes) -> str:
    """
    Encode binary data to Base64 string.
    
    Args:
        binary_data: Raw binary data (GLB format)
    
    Returns:
        Base64-encoded string
    """
    return base64.b64encode(binary_data).decode('utf-8')


def decode_glb(base64_string: str) -> bytes:
    """
    Decode Base64 string to binary data.
    
    Args:
        base64_string: Base64-encoded string
    
    Returns:
        Raw binary data (GLB format)
    """
    return base64.b64decode(base64_string)


def is_valid_glb(data: bytes) -> bool:
    """
    Check if binary data is valid GLB format.
    GLB files start with magic number 0x46546C67 ('glTF')
    
    Args:
        data: Binary data to check
    
    Returns:
        True if valid GLB format
    """
    if len(data) < 12:
        return False
    
    magic = struct.unpack('<I', data[:4])[0]
    return magic == 0x46546C67


def create_simple_glb(geometry_json: Dict[str, Any]) -> bytes:
    """
    Create a simple GLB container from geometry JSON.
    This is a simplified implementation for development.
    
    For production, use pygltflib or similar library.
    
    Args:
        geometry_json: Geometry data as dictionary
    
    Returns:
        GLB binary data
    """
    # Convert to JSON string
    json_str = json.dumps(geometry_json, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    
    # Pad to 4-byte alignment
    padding = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b' ' * padding
    
    # GLB Header (12 bytes)
    magic = 0x46546C67  # 'glTF'
    version = 2
    total_length = 12 + 8 + len(json_bytes)
    
    header = struct.pack('<III', magic, version, total_length)
    
    # JSON Chunk Header (8 bytes)
    chunk_length = len(json_bytes)
    chunk_type = 0x4E4F534A  # 'JSON'
    chunk_header = struct.pack('<II', chunk_length, chunk_type)
    
    return header + chunk_header + json_bytes


def extract_json_from_glb(glb_data: bytes) -> Optional[Dict[str, Any]]:
    """
    Extract JSON chunk from GLB data.
    
    Args:
        glb_data: GLB binary data
    
    Returns:
        Parsed JSON dictionary or None if invalid
    """
    if not is_valid_glb(glb_data):
        return None
    
    # Read header
    magic, version, total_length = struct.unpack('<III', glb_data[:12])
    
    # Read first chunk (should be JSON)
    chunk_length, chunk_type = struct.unpack('<II', glb_data[12:20])
    
    if chunk_type != 0x4E4F534A:  # Not JSON
        return None
    
    json_data = glb_data[20:20 + chunk_length]
    
    try:
        return json.loads(json_data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def geometry_to_base64_glb(geometry_data: Dict[str, Any]) -> str:
    """
    Convert geometry data to Base64-encoded GLB string.
    This is the main function used for API responses.
    
    Args:
        geometry_data: Geometry data dictionary
    
    Returns:
        Base64-encoded GLB string
    """
    glb_binary = create_simple_glb(geometry_data)
    return encode_glb(glb_binary)


def base64_glb_to_geometry(base64_string: str) -> Optional[Dict[str, Any]]:
    """
    Convert Base64-encoded GLB string back to geometry data.
    
    Args:
        base64_string: Base64-encoded GLB string
    
    Returns:
        Geometry data dictionary or None if invalid
    """
    try:
        glb_binary = decode_glb(base64_string)
        return extract_json_from_glb(glb_binary)
    except Exception:
        return None


# For development: mock GLB creation for simple shapes
def create_box_glb(width: float, depth: float, height: float) -> bytes:
    """
    Create a simple box geometry as GLB.
    
    Args:
        width: Box width
        depth: Box depth
        height: Box height
    
    Returns:
        GLB binary data
    """
    geometry = {
        'asset': {'version': '2.0', 'generator': 'Growvity'},
        'scene': 0,
        'scenes': [{'nodes': [0]}],
        'nodes': [{'mesh': 0}],
        'meshes': [{
            'primitives': [{
                'attributes': {'POSITION': 0},
                'mode': 4  # TRIANGLES
            }]
        }],
        'metadata': {
            'type': 'box',
            'dimensions': {
                'width': width,
                'depth': depth,
                'height': height
            }
        }
    }
    
    return create_simple_glb(geometry)
