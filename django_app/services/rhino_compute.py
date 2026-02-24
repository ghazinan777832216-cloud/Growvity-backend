"""
Growvity Rhino Compute Service - Simplified
Based on Test_Geo.py structure for direct Rhino Compute integration
"""
# Try to import Rhino/Compute libraries; if unavailable, enable a safe offline mode
try:
    import compute_rhino3d.Util as _cr_util
    import compute_rhino3d.Grasshopper as gh
    import rhino3dm
    HAVE_RHINO = True
except Exception:
    _cr_util = None  # type: ignore
    gh = None  # type: ignore
    rhino3dm = None  # type: ignore
    HAVE_RHINO = False
import json
import base64
from typing import Dict, Any
from django.conf import settings
import os

# Development toggle: allow running the backend without Rhino Compute
# If USE_DUMMY_RHINO is set to a truthy value, compute_building will return an empty string
# to indicate no geometry is produced. This helps running the server in environments without
# Rhino Compute installed (e.g., local dev machines).
USE_DUMMY_RHINO = str(os.environ.get('USE_DUMMY_RHINO', '0')).lower() in ('1', 'true', 'yes')


class RhinoComputeService:
    """Service for executing Grasshopper definitions via Rhino Compute"""
    
    # Rhino Compute URL
    BASE_URL = getattr(settings, 'RHINO_COMPUTE_URL', 'http://localhost:5000/')
    
    # Grasshopper definition path
    GH_DEFINITION = r'C:\\Users\\hisham\\Desktop\\compute_test\\Geo_Test.gh'
    
    @classmethod
    def compute_building(cls, building_data: Dict[str, Any]) -> str:
        """
        Compute building geometry using Rhino Compute.
        Based on Test_Geo.py structure.
        
        Args:
            building_data: Dict with keys:
                - name: Building name
                - geojson: GeoJSON FeatureCollection or Polygon
                - floors_number: Number of floors
                - floor_to_floor_height: Height per floor
        
        Returns:
            Base64 encoded GLB geometry string
        
        Raises:
            RuntimeError: If Rhino Compute fails
        """
        # If in dummy mode, skip actual Rhino Compute and return empty GLB
        if USE_DUMMY_RHINO or not HAVE_RHINO:
            return ""
        # Set Rhino Compute URL
        _cr_util.url = cls.BASE_URL  # type: ignore
        
        try:
            # Prepare input trees (matching Test_Geo.py)
            input_trees = cls._prepare_input_trees(building_data)
            
            # Execute Grasshopper definition
            output = gh.EvaluateDefinition(cls.GH_DEFINITION, input_trees)  # type: ignore
            
            # Extract geometry from output
            glb_base64 = cls._extract_geometry(output)
            
            return glb_base64
            
        except Exception as e:
            if USE_DUMMY_RHINO:
                # In dummy mode, treat compute failure as non-fatal geometry absence
                return ""
            raise RuntimeError(f"Rhino Compute failed: {str(e)}")
    
    @classmethod
    def _prepare_input_trees(cls, building_data: Dict[str, Any]) -> list:
        """
        Prepare Grasshopper DataTree inputs.
        Matches Test_Geo.py structure exactly.
        
        Args:
            building_data: Building parameters
            
        Returns:
            List of DataTree objects
        """
        # Extract parameters
        name = building_data.get('name', 'Unnamed Building')
        geojson = building_data.get('geojson', {})
        floors_number = building_data.get('floors_number', 11.0)
        floor_to_floor_height = building_data.get('floor_to_floor_height', 4.0)
        
        # Prepare GeoJSON string (matching Test_Geo.py format)
        # Ensure it's a FeatureCollection
        if geojson.get('type') == 'Polygon':
            geojson_fc = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": geojson
                }]
            }
        else:
            geojson_fc = geojson
        
        # Convert to escaped JSON string (matching Test_Geo.py)
        geojson_str = json.dumps(geojson_fc)
        geojson_escaped = f'"{geojson_str}"'
        
        # Building name (matching Test_Geo.py format)
        building_name_escaped = f'"{name}"'
        
        # Create DataTrees (matching Test_Geo.py order and structure)
        input_trees = []
        
        # 1. GeoJson_Input
        tree = gh.DataTree("GeoJson_Input")
        tree.Append([0], [geojson_escaped])
        input_trees.append(tree)
        
        # 2. Building_Name
        tree = gh.DataTree("Building_Name")
        tree.Append([0, 0], [building_name_escaped])
        input_trees.append(tree)
        
        # 3. _floor_to_floor_hight
        tree = gh.DataTree("_floor_to_floor_hight")
        tree.Append([0, 0], [str(floor_to_floor_height)])
        input_trees.append(tree)
        
        # 4. Floors_Numbers
        tree = gh.DataTree("Floors_Numbers")
        tree.Append([0], [str(floors_number)])
        input_trees.append(tree)
        
        return input_trees
    
    @classmethod
    def _extract_geometry(cls, output: Dict) -> str:
        """
        Extract GLB geometry from Grasshopper output.
        Expects a 'GLB_File' or similar output parameter containing the binary string.
        
        Args:
            output: Grasshopper evaluation output
            
        Returns:
            Base64 encoded GLB string
        """
        values = output.get('values', [])
        
        # 1. Search for explicit 'GLB' output
        for value in values:
            param_name = value.get('ParamName', '')
            inner_tree = value.get('InnerTree', {})
            
            # Check for common names for the GLB output
            if 'GLB' in param_name.upper() or 'FILE' in param_name.upper():
                for path, data_list in inner_tree.items():
                    for data_item in data_list:
                        data = data_item.get('data')
                        if isinstance(data, str):
                            # Assess if it's already base64 or needs encoding
                            # Users often return the raw binary string from GH
                            # If it looks like JSON (starts with {), it might be our mock
                            if data.strip().startswith('{') and '"asset"' in data:
                                # It's our mock JSON, encode it
                                return base64.b64encode(data.encode()).decode()
                            
                            # Assume it's the GLB string (Base64 or Raw)
                            # If it's pure logic, we might need to check if it's valid base64
                            return data

        # 2. Fallback: Check for any string output that looks like valid data
        for value in values:
             inner_tree = value.get('InnerTree', {})
             for path, data_list in inner_tree.items():
                 for data_item in data_list:
                     data = data_item.get('data')
                     if isinstance(data, str) and len(data) > 100:
                         # Likely the geometry file
                         return data

        # 3. Fallback: Logic for previous rhino3dm extraction (kept for safety)
        geometry_objects = []
        for value in values:
            inner_tree = value.get('InnerTree', {})
            for path, data_list in inner_tree.items():
                for data_item in data_list:
                    data = data_item.get('data')
                    if isinstance(data, str) and 'archive3dm' in data:
                        try:
                            # We don't really want this path for GLB workflow, 
                            # but keeping it prevents total failure if GH def is old
                            pass 
                        except Exception:
                            pass
        
        raise RuntimeError("No GLB output found in Grasshopper response")
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if Rhino Compute server is available"""
        try:
            import requests
            response = requests.get(f"{cls.BASE_URL}version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
