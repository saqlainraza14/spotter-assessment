// frontend/src/MapDisplay.js

import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const MapDisplay = ({ mapData }) => {
  // IMPORTANT: Mapbox returns [lng, lat], Leaflet needs [lat, lng]
  // We must swap the coordinates from the GeoJSON
  const polyline = mapData.route_geometry.coordinates.map(coord => [coord[1], coord[0]]);
  
  // Get marker positions (also need swapping)
  const parseCoords = (coordString) => {
    const [lng, lat] = coordString.split(',');
    return [parseFloat(lat), parseFloat(lng)];
  }
  
  const startPos = parseCoords(mapData.stops[0]);
  const pickupPos = parseCoords(mapData.stops[1]);
  const dropoffPos = parseCoords(mapData.stops[2]);

  return (
    <MapContainer center={startPos} zoom={5} style={{ height: '500px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      
      {/* Markers for stops */}
      <Marker position={startPos}>
        <Popup>Current Location</Popup>
      </Marker>
      <Marker position={pickupPos}>
        <Popup>Pickup Location</Popup>
      </Marker>
      <Marker position={dropoffPos}>
        <Popup>Dropoff Location</Popup>
      </Marker>
      
      {/* The route line */}
      <Polyline positions={polyline} color="blue" />
    </MapContainer>
  );
};

export default MapDisplay;