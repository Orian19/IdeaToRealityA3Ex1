"use client";

import React, { useState, useEffect } from 'react';

export default function Home() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('');
  const [tripType, setTripType] = useState('');
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

    const response = await fetch('http://127.0.0.1:8001/user_preferences/', {
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
          <h1 className={`text-3xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Enter Trip Preferences</h1>
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
              <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Results:</h2>
              <pre>{JSON.stringify(results, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}