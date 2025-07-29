import React, { useState, useRef } from 'react';
import axios from 'axios';

const LicensePlateScanner = ({ setIsLoading, setScanResults, setError }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.match('image.*')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    } else {
      setError("Please drop an image file");
    }
  };

  const uploadImage = async () => {
    if (!selectedFile) {
        setError("Please select an image first");
        return;
    }

    setIsLoading(true);
    setScanResults(null);

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
        const API_URL = import.meta.env.VITE_API_URL;

        const response = await axios.post(`${API_URL}/api/recognize-plate`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        console.log("✅ Backend Response:", response.data); // DEBUGGING
        setIsLoading(false);
        setScanResults(response.data);
    } catch (error) {
        setIsLoading(false);
        setError("Error processing the image. Please try again.");
        console.error("❌ Error uploading image:", error); // DEBUGGING
    }
};


  const resetSelection = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setScanResults(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-semibold mb-4 text-black">Upload License Plate Image</h2>
      
      <div 
        className={`border-2 border-dashed rounded-lg p-6 text-center ${selectedFile ? 'border-green-400' : 'border-gray-300 hover:border-blue-400'}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {previewUrl ? (
          <div className="mb-4">
            <img 
              src={previewUrl} 
              alt="License plate preview" 
              className="max-h-64 mx-auto rounded-md"
            />
          </div>
        ) : (
          <div className="py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p className="mt-1 text-sm text-gray-600">
              Drag and drop an image here, or click to select
            </p>
          </div>
        )}
        
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          ref={fileInputRef}
          id="file-upload"
        />
        
        <div className="mt-4 flex flex-wrap justify-center gap-3">
          <label 
            htmlFor="file-upload" 
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer"
          >
            Select Image
          </label>
          
          {selectedFile && (
            <>
              <button 
                onClick={uploadImage} 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Scan License Plate
              </button>
              
              <button 
                onClick={resetSelection} 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Reset
              </button>
            </>
          )}
        </div>
      </div>
      
      <div className="mt-4">
        <h3 className="font-medium text-gray-900">Instructions:</h3>
        <ul className="mt-2 list-disc pl-5 text-sm text-gray-600">
          <li>Upload a clear image of a vehicle license plate</li>
          <li>Make sure the plate is visible and not obscured</li>
          <li>The system works best with front-facing, well-lit images</li>
          <li>Supported formats: JPG, PNG, JPEG</li>
        </ul>
      </div>
    </div>
  );
};

export default LicensePlateScanner;