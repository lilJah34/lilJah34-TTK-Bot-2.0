#!/usr/bin/env python3
"""
TTK Bot 2.0 - Location Service
Advanced Flask-based location tracking service for driver management
"""

from flask import Flask, request, jsonify
import json
import datetime
import pytz
from typing import Dict, List, Tuple, Optional
import logging
import threading
from dataclasses import dataclass
from shapely.geometry import Point, Polygon
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@dataclass
class LocationUpdate:
    """Data class for location updates"""
    driver_id: str
    latitude: float
    longitude: float
    timestamp: datetime.datetime
    region: Optional[str] = None
    
@dataclass
class DeliveryRegion:
    """Data class for delivery regions with polygon boundaries"""
    name: str
    polygon: Polygon
    is_active: bool = True

class LocationService:
    """Advanced location tracking service with region detection"""
    
    def __init__(self):
        self.driver_locations: Dict[str, LocationUpdate] = {}
        self.delivery_regions: Dict[str, DeliveryRegion] = {}
        self.region_transition_callbacks = []
        self.location_lock = threading.Lock()
        
        # Initialize delivery regions
        self._initialize_regions()
    
    def _initialize_regions(self):
        """Initialize delivery region polygons"""
        # Define delivery regions with coordinate boundaries (Philadelphia & Jersey regions)
        regions_data = {
            "philly_north": {
                "coordinates": [
                    [-75.2000, 39.9800],  # Southwest
                    [-75.1200, 39.9800],  # Southeast  
                    [-75.1200, 40.0200],  # Northeast
                    [-75.2000, 40.0200],  # Northwest
                ]
            },
            "philly_south": {
                "coordinates": [
                    [-75.2200, 39.9200],
                    [-75.1400, 39.9200],
                    [-75.1400, 39.9800],
                    [-75.2200, 39.9800],
                ]
            },
            "philly_west": {
                "coordinates": [
                    [-75.2800, 39.9400],
                    [-75.2000, 39.9400],
                    [-75.2000, 40.0000],
                    [-75.2800, 40.0000],
                ]
            },
            "philly_northeast": {
                "coordinates": [
                    [-75.1200, 40.0200],
                    [-75.0400, 40.0200],
                    [-75.0400, 40.0800],
                    [-75.1200, 40.0800],
                ]
            },
            "jersey_camden": {
                "coordinates": [
                    [-75.1400, 39.8800],
                    [-75.0200, 39.8800],
                    [-75.0200, 39.9600],
                    [-75.1400, 39.9600],
                ]
            },
            "jersey_gloucester": {
                "coordinates": [
                    [-75.2000, 39.7800],
                    [-75.0800, 39.7800],
                    [-75.0800, 39.8800],
                    [-75.2000, 39.8800],
                ]
            },
            "jersey_burlington": {
                "coordinates": [
                    [-74.9800, 39.8000],
                    [-74.7000, 39.8000],
                    [-74.7000, 40.1000],
                    [-74.9800, 40.1000],
                ]
            },
            "delaware_county": {
                "coordinates": [
                    [-75.4000, 39.8200],
                    [-75.2200, 39.8200],
                    [-75.2200, 39.9800],
                    [-75.4000, 39.9800],
                ]
            },
            "montgomery_county": {
                "coordinates": [
                    [-75.4800, 40.0000],
                    [-75.2000, 40.0000],
                    [-75.2000, 40.2000],
                    [-75.4800, 40.2000],
                ]
            },
            "chester_county": {
                "coordinates": [
                    [-75.8000, 39.8000],
                    [-75.4000, 39.8000],
                    [-75.4000, 40.1000],
                    [-75.8000, 40.1000],
                ]
            }
        }
        
        for region_name, data in regions_data.items():
            polygon = Polygon(data["coordinates"])
            self.delivery_regions[region_name] = DeliveryRegion(
                name=region_name,
                polygon=polygon,
                is_active=True
            )
        
        logger.info(f"Initialized {len(self.delivery_regions)} delivery regions")
    
    def add_region_transition_callback(self, callback):
        """Add callback for region transitions"""
        self.region_transition_callbacks.append(callback)
    
    def _detect_region(self, latitude: float, longitude: float) -> Optional[str]:
        """Detect which delivery region contains the given coordinates"""
        point = Point(longitude, latitude)
        
        for region_name, region in self.delivery_regions.items():
            if region.is_active and region.polygon.contains(point):
                return region_name
        
        return None
    
    def _check_region_transition(self, driver_id: str, new_location: LocationUpdate):
        """Check if driver has transitioned between regions"""
        if driver_id not in self.driver_locations:
            return  # First location update
        
        old_location = self.driver_locations[driver_id]
        old_region = old_location.region
        new_region = new_location.region
        
        if old_region != new_region:
            logger.info(f"Driver {driver_id} transitioned from {old_region} to {new_region}")
            
            # Notify callbacks about region transition
            for callback in self.region_transition_callbacks:
                try:
                    callback(driver_id, old_region, new_region, new_location)
                except Exception as e:
                    logger.error(f"Error in region transition callback: {e}")
    
    def update_location(self, driver_id: str, latitude: float, longitude: float, 
                       timestamp: Optional[datetime.datetime] = None) -> Dict:
        """Update driver location and detect region"""
        if timestamp is None:
            timestamp = datetime.datetime.now(pytz.UTC)
        
        # Detect current region
        region = self._detect_region(latitude, longitude)
        
        # Create location update
        location_update = LocationUpdate(
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            region=region
        )
        
        with self.location_lock:
            # Check for region transitions
            self._check_region_transition(driver_id, location_update)
            
            # Store the location
            self.driver_locations[driver_id] = location_update
        
        logger.info(f"Updated location for driver {driver_id}: {region}")
        
        return {
            "status": "success",
            "driver_id": driver_id,
            "region": region,
            "timestamp": timestamp.isoformat(),
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
    
    def get_current_region(self, driver_id: str) -> Dict:
        """Get the current region for a driver"""
        with self.location_lock:
            if driver_id not in self.driver_locations:
                return {
                    "status": "not_found",
                    "driver_id": driver_id,
                    "message": "No location data available"
                }
            
            location = self.driver_locations[driver_id]
            return {
                "status": "success",
                "driver_id": driver_id,
                "region": location.region,
                "timestamp": location.timestamp.isoformat(),
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
            }
    
    def get_all_drivers(self) -> Dict:
        """Get all driver locations and regions"""
        with self.location_lock:
            drivers_data = {}
            for driver_id, location in self.driver_locations.items():
                drivers_data[driver_id] = {
                    "region": location.region,
                    "timestamp": location.timestamp.isoformat(),
                    "coordinates": {
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    }
                }
            
            return {
                "status": "success",
                "drivers": drivers_data,
                "total_drivers": len(drivers_data)
            }
    
    def get_drivers_in_region(self, region_name: str) -> Dict:
        """Get all drivers currently in a specific region"""
        with self.location_lock:
            drivers_in_region = []
            for driver_id, location in self.driver_locations.items():
                if location.region == region_name:
                    drivers_in_region.append({
                        "driver_id": driver_id,
                        "timestamp": location.timestamp.isoformat(),
                        "coordinates": {
                            "latitude": location.latitude,
                            "longitude": location.longitude
                        }
                    })
            
            return {
                "status": "success",
                "region": region_name,
                "drivers": drivers_in_region,
                "count": len(drivers_in_region)
            }

# Global location service instance
location_service = LocationService()

# Flask API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TTK Bot Location Service",
        "timestamp": datetime.datetime.now(pytz.UTC).isoformat(),
        "active_regions": len(location_service.delivery_regions),
        "tracked_drivers": len(location_service.driver_locations)
    })

@app.route('/location-update', methods=['POST'])
def location_update():
    """
    POST /location-update
    Update driver location with GPS coordinates and timestamp
    
    Body: {
        "driver_id": "string",
        "latitude": float,
        "longitude": float,
        "timestamp": "ISO format string (optional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ["driver_id", "latitude", "longitude"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        driver_id = data["driver_id"]
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        
        # Parse timestamp if provided
        timestamp = None
        if "timestamp" in data:
            try:
                timestamp = datetime.datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Invalid timestamp format"
                }), 400
        
        # Update location
        result = location_service.update_location(driver_id, latitude, longitude, timestamp)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid coordinate values: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in location update: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/current-region/<driver_id>', methods=['GET'])
def get_current_region(driver_id: str):
    """
    GET /current-region/<driver_id>
    Get the last known region for a specific driver
    """
    try:
        result = location_service.get_current_region(driver_id)
        
        if result["status"] == "not_found":
            return jsonify(result), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting current region: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/drivers', methods=['GET'])
def get_all_drivers():
    """
    GET /drivers
    Get all driver locations and regions
    """
    try:
        result = location_service.get_all_drivers()
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting all drivers: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/region/<region_name>/drivers', methods=['GET'])
def get_drivers_in_region(region_name: str):
    """
    GET /region/<region_name>/drivers
    Get all drivers currently in a specific region
    """
    try:
        result = location_service.get_drivers_in_region(region_name)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting drivers in region: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/regions', methods=['GET'])
def get_regions():
    """
    GET /regions
    Get all available delivery regions
    """
    try:
        regions_info = {}
        for region_name, region in location_service.delivery_regions.items():
            regions_info[region_name] = {
                "name": region.name,
                "is_active": region.is_active,
                "boundary_points": len(region.polygon.exterior.coords)
            }
        
        return jsonify({
            "status": "success",
            "regions": regions_info,
            "total_regions": len(regions_info)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting regions: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

def run_location_service(host='0.0.0.0', port=5001, debug=False):
    """Run the Flask location service"""
    logger.info(f"Starting TTK Bot Location Service on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    run_location_service(debug=True)
