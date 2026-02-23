"""
Growvity API Views - Simplified
RESTful endpoints for Building operations only
"""
import sys
import os

# Add graph module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import BuildingSerializer, BuildingListSerializer
from ..services.graph_service import GraphService


class ApiRootView(APIView):
    """API Root with links to endpoints"""
    
    def get(self, request):
        return Response({
            'message': 'Welcome to Growvity API - Simplified',
            'status': 'Running',
            'endpoints': {
                'buildings': request.build_absolute_uri('buildings/'),
                'admin': request.build_absolute_uri('/admin/')
            }
        })


class BuildingListView(APIView):
    """List all buildings or create a new building"""
    
    def get(self, request):
        """Get all buildings"""
        buildings = GraphService.list_buildings()
        serializer = BuildingListSerializer(buildings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new building with Rhino Compute geometry"""
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            try:
                building = GraphService.create_building(serializer.validated_data)
                return Response(
                    BuildingSerializer(building).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': f'Building creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BuildingDetailView(APIView):
    """Retrieve, update or delete a building"""
    
    def get(self, request, uid):
        """Get building by UID"""
        building = GraphService.get_building(uid)
        if not building:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(BuildingSerializer(building).data)
    
    def put(self, request, uid):
        """Update building (full update)"""
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            building = GraphService.update_building(uid, serializer.validated_data)
            if not building:
                return Response(
                    {'error': 'Building not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(BuildingSerializer(building).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, uid):
        """Update building (partial update)"""
        building = GraphService.get_building(uid)
        if not building:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BuildingSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            building = GraphService.update_building(uid, serializer.validated_data)
            return Response(BuildingSerializer(building).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, uid):
        """Delete building"""
        success = GraphService.delete_building(uid)
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Building not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class BuildingRecomputeView(APIView):
    """Force recompute building geometry"""
    
    def post(self, request, uid):
        """Trigger geometry recomputation"""
        try:
            building = GraphService.recompute_building(uid)
            if not building:
                return Response(
                    {'error': 'Building not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(BuildingSerializer(building).data)
        except Exception as e:
            return Response(
                {'error': f'Recompute failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectListView(APIView):
    """List projects (Synthetic)"""
    
    def get(self, request):
        return Response([{
            'uid': 'proj-001',
            'name': 'Growvity Project',
            'type': 'project'
        }])


class ProjectTreeView(APIView):
    """Get full project tree"""
    
    def get(self, request, uid):
        tree = GraphService.get_project_tree(uid)
        if not tree:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(tree)

