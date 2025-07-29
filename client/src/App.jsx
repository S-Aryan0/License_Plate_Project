import React, { useState } from 'react';
import LicensePlateScanner from './components/LicensePlateScanner';
import ScanResults from './components/ScanResults';


function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [error, setError] = useState(null);

  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 md:p-8">
      <div className="max-w-3xl mx-auto">
        <header className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-gray-900">License Plate Recognition System</h1>
          <p className="mt-2 text-gray-600">Upload and analyze vehicle license plates</p>
        </header>

        <LicensePlateScanner 
          setIsLoading={setIsLoading} 
          setScanResults={setScanResults} 
          setError={setError} 
        />
        
        {isLoading && (
          <div className="mt-6 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600"></div>
            <p className="mt-2 text-gray-700">Processing image...</p>
          </div>
        )}
        
        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-red-800">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}
        
        {!isLoading && scanResults && (
          <ScanResults results={scanResults} />
        )}
      </div>
    </div>
  );
}

export default App;