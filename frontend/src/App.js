// frontend/src/App.js

import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // We will add styles here
import MapDisplay from './MapDisplay';
import Logbook from './Logbook';

function App() {
  // Form input state
  const [currentLocation, setCurrentLocation] = useState('-122.4194,37.7749'); // Default: San Francisco (Lng, Lat)
  const [pickupLocation, setPickupLocation] = useState('-118.2437,34.0522'); // Default: Los Angeles
  const [dropoffLocation, setDropoffLocation] =useState('-74.0060,40.7128'); // Default: New York
  const [currentCycleUsed, setCurrentCycleUsed] = useState('20');

  // API response state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiResponse, setApiResponse] = useState(null);

  // frontend/src/App.js

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setApiResponse(null);

    try {
      // THIS IS THE API CALL to our Django backend
      const response = await axios.post('https://spotter-assessment-yd5m.onrender.com', {
        currentLocation,
        pickupLocation,
        dropoffLocation,
        currentCycleUsed: parseFloat(currentCycleUsed),
      });
      
      setApiResponse(response.data);

    } catch (err) {
      console.error("Full API Error:", err); // Log the whole error
      
      let errorMessage = "An unknown error occurred"; // Default message

      if (err.response) {
        // We got a response from the server, but it was an error
        const data = err.response.data;
        console.log("Server Error Data:", data);

        if (data.details) {
          // This is for Mapbox errors or 500 errors
          errorMessage = JSON.stringify(data.details);
        } else if (data.error) {
          // This is for our custom 400 errors
          errorMessage = data.error;
        } else {
          // If the response is something else
          errorMessage = JSON.stringify(data);
        }
      } else if (err.request) {
        // The request was made but no response was received
        // This is often a CORS or network error.
        errorMessage = "Could not connect to the backend server. Is it running?";
      } else {
        // Something else happened in setting up the request
        errorMessage = err.message;
      }
      
      setError(`Failed to calculate trip: ${errorMessage}`);
      
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Spotter ELD Log Simulator</h1>
      </header>
      
      <main>
        <div className="form-container">
          <h2>Enter Trip Details</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Current Location (Lng,Lat)</label>
              <input
                type="text"
                value={currentLocation}
                onChange={(e) => setCurrentLocation(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Pickup Location (Lng,Lat)</label>
              <input
                type="text"
                value={pickupLocation}
                onChange={(e) => setPickupLocation(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Dropoff Location (Lng,Lat)</label>
              <input
                type="text"
                value={dropoffLocation}
                onChange={(e) => setDropoffLocation(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Current Cycle Used (Hrs)</label>
              <input
                type="number"
                value={currentCycleUsed}
                onChange={(e) => setCurrentCycleUsed(e.target.value)}
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Calculating...' : 'Calculate Trip'}
            </button>
          </form>
        </div>

        {error && <div className="error-box">{error}</div>}

        {apiResponse && (
          <div className="results-container">
            <h2>Trip Results</h2>
            <div className="map-and-instructions">
              <MapDisplay mapData={apiResponse.map_data} />
              <div className="instructions">
                <h3>Route Instructions</h3>
                <ol>
                  {apiResponse.map_data.instructions.map((inst, i) => (
                    <li key={i}>{inst}</li>
                  ))}
                </ol>
              </div>
            </div>

            <div className="logbook-container">
              <h3>Generated Driver Logs</h3>
              {apiResponse.trip_summary.daily_logs.map((dayLog, i) => (
                <Logbook 
                  key={i} 
                  dayNumber={i + 1} 
                  events={dayLog} 
                  tripSummary={apiResponse.trip_summary}
                />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;