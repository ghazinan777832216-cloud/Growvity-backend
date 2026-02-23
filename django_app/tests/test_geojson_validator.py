"""
Unit tests for GeoJSON Validator
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from geojson_validator import (
    validate_geojson,
    validate_geometry_for_grasshopper,
    _validate_position
)


def test_valid_polygon():
    """Test validation of a valid polygon"""
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [ [
            [28.43, 13.03],
            [27.17, 12.91],
            [27.43, 11.74],
            [28.74, 11.89],
            [28.43, 13.03]  # Closed
        ] ]
    }
    
    is_valid, errors = validate_geojson(valid_polygon)
    assert is_valid, f"Expected valid, got errors: {errors}"
    assert len(errors) == 0
    print("✓ Valid polygon test passed")


def test_unclosed_polygon():
    """Test validation catches unclosed polygon"""
    unclosed_polygon = {
        "type": "Polygon",
        "coordinates": [ [
            [28.43, 13.03],
            [27.17, 12.91],
            [27.43, 11.74],
            [28.74, 11.89]
            # Missing closing point
        ] ]
    }
    
    is_valid, errors = validate_geojson(unclosed_polygon)
    assert not is_valid, "Expected invalid for unclosed polygon"
    assert any('not closed' in err.lower() for err in errors)
    print("✓ Unclosed polygon test passed")


def test_invalid_coordinates():
    """Test validation catches coordinates out of range"""
    invalid_coords = {
        "type": "Point",
        "coordinates": [200, 100]  # Invalid lon/lat
    }
    
    is_valid, errors = validate_geojson(invalid_coords)
    assert not is_valid, "Expected invalid for out of range coordinates"
    assert len(errors) > 0
    print("✓ Invalid coordinates test passed")


def test_valid_feature_collection():
    """Test validation of FeatureCollection"""
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Test Building"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [ [
                    [28.43, 13.03],
                    [27.17, 12.91],
                    [27.43, 11.74],
                    [28.74, 11.89],
                    [28.43, 13.03]
                ] ]
            }
        }]
    }
    
    is_valid, errors = validate_geojson(feature_collection)
    assert is_valid, f"Expected valid, got errors: {errors}"
    print("✓ Valid FeatureCollection test passed")


def test_grasshopper_validation():
    """Test Grasshopper-specific validation"""
    # Valid for Grasshopper (Polygon)
    valid_for_gh = {
        "type": "Polygon",
        "coordinates": [ [
            [28.43, 13.03],
            [27.17, 12.91],
            [27.43, 11.74],
            [28.74, 11.89],
            [28.43, 13.03]
        ] ]
    }
    
    is_valid, errors = validate_geometry_for_grasshopper(valid_for_gh)
    assert is_valid, f"Expected valid for Grasshopper, got errors: {errors}"
    print("✓ Grasshopper validation test passed")
    
    # Invalid for Grasshopper (Point not accepted for buildings)
    invalid_for_gh = {
        "type": "Point",
        "coordinates": [28.43, 13.03]
    }
    
    is_valid, errors = validate_geometry_for_grasshopper(invalid_for_gh)
    assert not is_valid, "Expected invalid for Grasshopper (Point not for buildings)"
    print("✓ Grasshopper rejection test passed")


def test_missing_type():
    """Test validation catches missing type field"""
    no_type = {
        "coordinates": [[28.43, 13.03]]
    }
    
    is_valid, errors = validate_geojson(no_type)
    assert not is_valid
    assert any('type' in err.lower() for err in errors)
    print("✓ Missing type test passed")


def run_all_tests():
    """Run all validation tests"""
    print("\n🧪 Running GeoJSON Validation Tests\n")
    
    tests = [
        test_valid_polygon,
        test_unclosed_polygon,
        test_invalid_coordinates,
        test_valid_feature_collection,
        test_grasshopper_validation,
        test_missing_type
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print(f"{'='*50}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
