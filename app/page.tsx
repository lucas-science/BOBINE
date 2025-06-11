"use client";
import { Upload } from 'lucide-react';
import React, { useState } from 'react';

interface FileUploadProps {
  title: string;
  description: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ title, description }) => {
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files ? event.target.files[0] : null;
    setFile(selectedFile);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files ? event.dataTransfer.files[0] : null;
    setFile(droppedFile);
  };

  if (title === "Chromeleon") {
    return (
      <div
        className="bg-white space-y-4 p-4 rounded-lg shadow-md"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <h2 className="text-lg font-semibold mb-2">{title}</h2>

        <div className='bg-filezone border-gray-300 p-4 rounded-lg flex flex-col items-center justify-center'>
          <label className="cursor-pointer flex flex-col justify-center items-center">
            <p className="text-gray-600 mb-4">{description}</p>
            <label className='bg-primary p-2 rounded-lg cursor-pointer'>
              <Upload />
            </label>
            <input type="file" onChange={handleFileChange} className="hidden" />
            <p>Drag and drop or click to upload</p>
          </label>
          {file && <p className="mt-2">Selected File: {file.name}</p>}
        </div>

        <div className='bg-filezone border-gray-300 p-4 rounded-lg flex flex-col items-center justify-center'>
          <label className="cursor-pointer flex flex-col justify-center items-center">
            <p className="text-gray-600 mb-4">{description}</p>
            <label className='bg-primary p-2 rounded-lg cursor-pointer'>
              <Upload />
            </label>
            <input type="file" onChange={handleFileChange} className="hidden" />
            <p>Drag and drop or click to upload</p>
          </label>
          {file && <p className="mt-2">Selected File: {file.name}</p>}
        </div>
      </div>
    );
  }

  return (
    <div
      className="bg-white p-4 h-fit rounded-lg shadow-md"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <h2 className="text-lg font-semibold mb-2">{title}</h2>
      <div className='bg-filezone border-gray-300 p-4 rounded-lg flex flex-col items-center justify-center'>
        <label className="cursor-pointer flex flex-col justify-center items-center">
          <p className="text-gray-600 mb-4">{description}</p>
          <label className='bg-primary p-2 rounded-lg cursor-pointer'>
            <Upload />
          </label>
          <input type="file" onChange={handleFileChange} className="hidden" />
          <p>Drag and drop or click to upload</p>
        </label>
        {file && <p className="mt-2">Selected File: {file.name}</p>}
      </div>
    </div>
  );
};

const UploadPage = () => {
  return (
    <div className="p-4">
      <div className="grid grid-cols-2 gap-4">
        <FileUpload
          title="Chromeleon"
          description="Fichiers Online"
        />
        <FileUpload
          title="Pignat"
          description="Drag and drop or click to upload"
        />
      </div>
    </div>
  );
};

export default UploadPage;
