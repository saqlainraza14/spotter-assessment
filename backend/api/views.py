# backend/api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import json
import traceback # <-- ADD THIS IMPORT

# Import our HOS logic
from .hos_simulator import HOSSimulator

def parse_coordinates(coord_string):
    """Helper function to parse 'lng,lat' string into [lng, lat] list."""
    try:
        lng, lat = map(float, coord_string.split(','))
        return [lng, lat]
    except Exception as e:
        raise ValueError(f"Invalid coordinate format: {coord_string}")

class TripCalculatorView(APIView):
    """
    API endpoint to calculate a trip, its route, and its HOS logs.
    This version uses OpenRouteService.
    """
    
    def post(self, request, *args, **kwargs):
        # ---!! START FIX: Add robust try...except block !!---
        try:
            # 1. Get the 4 inputs from the React frontend
            data = request.data
            current_location_str = data.get('currentLocation')
            pickup_location_str = data.get('pickupLocation')
            dropoff_location_str = data.get('dropoffLocation')
            cycle_used_hours = float(data.get('currentCycleUsed', 0))

            if not all([current_location_str, pickup_location_str, dropoff_location_str]):
                return Response(
                    {"error": "Missing location inputs"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Call OpenRouteService API
            ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImEyMjUzNzMwMjBlMjQ4MmRiZTk1MmIxZjc0OWIwNzBlIiwiaCI6Im11cm11cjY0In0="
            
            try:
                coordinates_list = [
                    parse_coordinates(current_location_str),
                    parse_coordinates(pickup_location_str),
                    parse_coordinates(dropoff_location_str)
                ]
            except ValueError as e:
                 return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
            headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
            body = {"coordinates": coordinates_list, "instructions": "true"}

            ors_response = requests.post(url, headers=headers, json=body)
            
            if ors_response.status_code != 200:
                # Try to parse error details, but have a fallback
                try:
                    details = ors_response.json()
                except:
                    details = ors_response.text # Fallback if error is not JSON
                return Response(
                    {"error": "Could not get route from OpenRouteService", "details": details},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ors_data = ors_response.json()
            
            # 3. Parse the ORS response
            if not ors_data.get('features'):
                 return Response(
                    {"error": "No route found for the given coordinates."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            route = ors_data['features'][0]
            summary = route['properties']['summary']
            
            trip_duration_seconds = summary['duration']
            trip_distance_meters = summary['distance']
            
            trip_drive_minutes = trip_duration_seconds / 60
            trip_total_miles = trip_distance_meters / 1609.34
            
            route_geometry = route['geometry']
            route_instructions = []
            for segment in route['properties']['segments']:
                for step in segment['steps']:
                    route_instructions.append(step['instruction'])

            # 4. Run the HOS Simulator
            sim = HOSSimulator(cycle_used_hours=cycle_used_hours)
            
            trip_summary = sim.simulate_trip(
                total_drive_minutes=trip_drive_minutes,
                total_miles=trip_total_miles
            )

            # 5. Return the complete package
            return Response({
                "trip_summary": trip_summary,
                "map_data": {
                    "route_geometry": route_geometry,
                    "instructions": route_instructions,
                    "stops": [current_location_str, pickup_location_str, dropoff_location_str]
                }
            }, status=status.HTTP_200_OK)

        except AttributeError as e:
            # Catch the specific error you mentioned
            return Response(
                {
                    "error": "An AttributeError occurred on the server.",
                    "details": str(e),
                    "traceback": traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVICE_ERROR
            )
        except Exception as e:
            # Catch all other errors
            return Response(
                {
                    "error": "An unexpected error occurred",
                    "details": str(e),
                    "traceback": traceback.format_exc() # Get exact line number
                },
                status=status.HTTP_500_INTERNAL_SERVICE_ERROR
            )
        # ---!! END FIX !!---