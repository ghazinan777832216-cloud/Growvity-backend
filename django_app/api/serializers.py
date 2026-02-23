"""
Growvity API Serializers - Simplified
Matches the simplified Building model
"""
from rest_framework import serializers


class BuildingSerializer(serializers.Serializer):
    """Serializer for simplified Building model"""
    
    # Read-only fields
    uid = serializers.CharField(read_only=True)
    glb_geometry = serializers.CharField(read_only=True, allow_null=True)
    computed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Required fields
    name = serializers.CharField(max_length=255, required=True)
    geojson = serializers.JSONField(required=True)
    
    # Optional fields with defaults
    floors_number = serializers.FloatField(default=11.0, min_value=1, max_value=200)
    floor_to_floor_height = serializers.FloatField(default=4.0, min_value=2.5, max_value=10.0)
    
    def validate_geojson(self, value):
        """Validate GeoJSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("GeoJSON must be a dictionary")
        
        # Accept both FeatureCollection and direct Polygon
        if value.get('type') == 'FeatureCollection':
            features = value.get('features', [])
            if not features:
                raise serializers.ValidationError("FeatureCollection must have at least one feature")
            
            # Validate first feature has geometry
            if not features[0].get('geometry'):
                raise serializers.ValidationError("Feature must have geometry")
                
        elif value.get('type') == 'Polygon':
            # Direct polygon is ok
            if not value.get('coordinates'):
                raise serializers.ValidationError("Polygon must have coordinates")
        else:
            raise serializers.ValidationError("GeoJSON must be FeatureCollection or Polygon")
        
        return value


class BuildingListSerializer(serializers.Serializer):
    """Serializer for listing buildings (without heavy GLB data)"""
    uid = serializers.CharField()
    name = serializers.CharField()
    floors_number = serializers.FloatField()
    floor_to_floor_height = serializers.FloatField()
    computed_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()