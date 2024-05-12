"use client";

import React, { useState, useEffect } from 'react';

export default function Home() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('');
  const [tripType, setTripType] = useState('');

  const [selectedTripIndex, setSelectedTripIndex] = useState(null);
  const [travelPlan, setTravelPlan] = useState('');
  const [travelImages, setTravelImages] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [darkMode, setDarkMode] = useState(false);

  const handleButtonClick = () => {
    setDarkMode(prevDarkMode => !prevDarkMode);
  };

  useEffect(() => {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDarkMode);
    document.body.classList.toggle('dark', isDarkMode);
  }, []);

  useEffect(() => {
    localStorage.setItem('darkMode', darkMode.toString());
    document.body.classList.toggle('dark', darkMode);
  }, [darkMode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const response = await fetch('http://127.0.0.1:8001/travel_options/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        start_date: startDate,
        end_date: endDate,
        budget: budget,
        trip_type: tripType
      }),
    });

    if (response.ok) {
      const data = await response.json();
      setResults([data]); // Assuming data returned is an object
    } else {
      console.error("Failed to fetch data");
      setResults([]);
    }

    setIsLoading(false);
  };

  const handleSubmitTripSelection = async (event) => {
    event.preventDefault();
    if (selectedTripIndex === null) {
      alert('Please select a destination.');
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8001/travel_plans/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trip_selection_idx: selectedTripIndex })
      });
      if (response.ok) {
        const data = await response.json();
        setTravelPlan(data[0]);  // Assume the backend sends back a plain string
        setTravelImages(data[1]);  // Assume the backend sends back a plain string
      } else {
        console.error("Failed to generate travel plan");
      }
    } catch (error) {
      console.error("Error generating travel plan:", error);
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <main className={`flex min-h-screen items-center justify-center ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-black'}`}>
      <div className="flex w-full max-w-4xl">
        <button 
          className={`fixed top-5 right-5 p-2 rounded font-semibold transition-colors duration-300 ease-in-out 
                      ${darkMode ? 'bg-gray-800 text-gray-200 border border-gray-700 hover:bg-gray-700' : 'bg-blue-500 text-white hover:bg-blue-400'}`}
          onClick={handleButtonClick}>
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>

        {/* Main Content Area */}
        <div className="flex-grow p-4">
          <h1 className={`text-5xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>AI Trip Planner</h1>
          <h2 className={`text-2xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Enter Trip Preferences</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              type="date"
              placeholder="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className={`w-full rounded-md border p-2 text-lg ${darkMode ? 'bg-gray-800 border-gray-600 text-gray-300' : 'border-gray-300 text-gray-900'}`}
            />
            <input
              type="date"
              placeholder="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className={`w-full rounded-md border p-2 text-lg ${darkMode ? 'bg-gray-800 border-gray-600 text-gray-300' : 'border-gray-300 text-gray-900'}`}
            />
            <input
              type="number"
              placeholder="Budget in $"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className={`w-full rounded-md border p-2 text-lg ${darkMode ? 'bg-gray-800 border-gray-600 text-gray-300' : 'border-gray-300 text-gray-900'}`}
            />
            <select
              value={tripType}
              onChange={(e) => setTripType(e.target.value)}
              className={`w-full rounded-md border p-2 text-lg ${darkMode ? 'bg-gray-800 border-gray-600 text-gray-300' : 'border-gray-300 text-gray-900'}`}
            >
              <option value="">Select Trip Type</option>
              <option value="city">City</option>
              <option value="beach">Beach</option>
              <option value="ski">Ski</option>
            </select>
            <button type="submit" className={`w-full rounded-md py-2 px-4 text-lg text-white ${darkMode ? 'bg-gray-600 hover:bg-gray-700' : 'bg-blue-500 hover:bg-blue-600'}`}>
              Submit Preferences
            </button>
          </form>
          {isLoading ? (
              <p className="text-lg font-semibold">Loading...</p>
            ) : (
              <div className="mt-4">
                <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Travel Results:</h2>
                {results.length > 0 ? (
                  <form onSubmit={handleSubmitTripSelection}>
                    {results[0].map((option, index) => (
                      <div key={index} className={`mb-4 p-4 rounded shadow ${darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}`}>
                        <div>
                          <input type="radio" id={`trip-${index}`} name="tripSelection" value={index}
                            onChange={() => setSelectedTripIndex(index)} checked={selectedTripIndex === index} />
                          <label htmlFor={`trip-${index}`} className="text-lg font-bold mb-2">Destination: {option.destination}</label>
                        </div>
                        <div>
                        <h4 className="font-bold" style={{ color: 'blue' }}>Flights:</h4>
                          <h5 className="font-bold" style={{ color: 'red' }}>Outbound:</h5>
                          {option.flight[0]?.[option.destination]?.flights?.map((flight, flightIdx) => (
                            <div key={flightIdx} className="mb-2">
                              <p><strong>Departure:</strong> {flight.departure_airport.name} ({flight.departure_airport.time})</p>
                              <p><strong>Arrival:</strong> {flight.arrival_airport.name} ({flight.arrival_airport.time})</p>
                              <p><strong>Airline:</strong> {flight.airline} <img src={flight.airline_logo} alt="Airline logo" style={{verticalAlign: 'middle', height: '20px'}}/></p>
                            </div>
                          ))}
                          <h5 className="font-bold" style={{ color: 'green' }}>Inbound:</h5>
                          {option.flight[1]?.[option.destination]?.flights?.map((flight, flightIdx) => (
                            <div key={flightIdx} className="mb-2">
                              <p><strong>Departure:</strong> {flight.departure_airport.name} ({flight.departure_airport.time})</p>
                              <p><strong>Arrival:</strong> {flight.arrival_airport.name} ({flight.arrival_airport.time})</p>
                              <p><strong>Airline:</strong> {flight.airline} <img src={flight.airline_logo} alt="Airline logo" style={{verticalAlign: 'middle', height: '20px'}}/></p>
                            </div>
                          ))}
                        </div>
                        <div>
                          <h4 className="font-semibold">Hotel:</h4>
                          <p><strong>Name:</strong> {option.hotel?.[option.destination]?.name}</p>
                          <p><strong>Check-in:</strong> {option.hotel?.[option.destination]?.check_in_time}, <strong>Check-out:</strong> {option.hotel?.[option.destination]?.check_out_time}</p>
                          <p><strong>Rate per night:</strong> {option.hotel?.[option.destination]?.rate_per_night?.lowest}</p>
                        </div>
                        <div>
                          <h4 className="font-semibold">Total Cost:</h4>
                          <p>${option.total_cost}</p>
                        </div>
                      </div>
                    ))}
                    <button type="submit" className={`rounded-md py-2 px-4 text-lg text-white ${darkMode ? 'bg-gray-600 hover:bg-gray-700' : 'bg-blue-500 hover:bg-blue-600'}`}>
                      Generate Travel Plan
                    </button>
                  </form>
                ) : (
                  <p>No results found yet.</p>
                )}
                {/* Display the travel plan if available */}
                {travelPlan && (
                  <div className="travel-plan mt-4">
                    <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Your Travel Plan:</h2>
                    <p className={`p-4 ${darkMode ? 'bg-gray-700 text-white' : 'bg-white text-black'}`} style={{ whiteSpace: 'pre-wrap' }}>{travelPlan}</p>
                  </div>
                )}
                {/* Display the travel plan if available */}
                {travelImages && travelImages.length > 0 && (
                  <div className="travel-plan mt-4">
                    <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Your Travel Plan in Images:</h2>
                    <div className={`p-4 ${darkMode ? 'bg-gray-700 text-white' : 'bg-white text-black'}`}>
                      {travelImages.map((url, index) => (
                        <img key={index} src={url} alt={`Travel Plan Image ${index + 1}`} style={{ width: '100%', marginBottom: '10px' }} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

        </div>
      </div>
    </main>
  );
}
