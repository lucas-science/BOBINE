"use client";
import React, { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState<File | null>(null);
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    setFile(file);
  };

  const handleValidation = () => {
    if (file) {
      localStorage.setItem('uploadedFile', file.name);
    }
  };

  return (
    <div className='bg-blue-300 p-6 rounded-lg'>
      <h1>Upload Your File</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleValidation}>Validate File</button>
    </div>
  );
};

export default FileUpload;
