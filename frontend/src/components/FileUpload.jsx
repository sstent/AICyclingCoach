import React, { useState } from 'react';
import { toast } from 'react-toastify';

const FileUpload = ({ onUpload, acceptedTypes = ['.gpx'] }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleFileInput = (e) => {
    handleFiles(e.target.files);
  };

  const handleFiles = (newFiles) => {
    const validFiles = Array.from(newFiles).map(file => {
      const fileExt = file.name.split('.').pop().toLowerCase();
      
      // Validate file type
      if (!acceptedTypes.includes(`.${fileExt}`)) {
        return { file, error: 'Invalid file type', progress: 0 };
      }

      // Validate file size
      if (file.size > 10 * 1024 * 1024) {
        return { file, error: 'File too large', progress: 0 };
      }

      return { file, progress: 0, error: null };
    });

    setFiles(prev => [...prev, ...validFiles]);
    uploadFiles(validFiles.filter(f => !f.error));
  };

  const uploadFiles = async (filesToUpload) => {
    for (const fileObj of filesToUpload) {
      try {
        const formData = new FormData();
        formData.append('files', fileObj.file);

        const response = await fetch('/api/routes/upload', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) throw new Error('Upload failed');
        
        setFiles(prev => prev.map(f =>
          f.file === fileObj.file ? { ...f, progress: 100 } : f
        ));
        
        toast.success(`${fileObj.file.name} uploaded successfully`);
        
        if (onUpload) onUpload(fileObj.file);

      } catch (err) {
        setFiles(prev => prev.map(f =>
          f.file === fileObj.file ? { ...f, error: err.message } : f
        ));
        toast.error(`${fileObj.file.name} upload failed: ${err.message}`);
      }
    }
  };

  const parseGPXMetadata = (content) => {
    try {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(content, "text/xml");
      return {
        name: xmlDoc.getElementsByTagName('name')[0]?.textContent || 'Unnamed Route',
        distance: xmlDoc.getElementsByTagName('distance')[0]?.textContent || 'N/A',
        elevation: xmlDoc.getElementsByTagName('ele')[0]?.textContent || 'N/A'
      };
    } catch {
      return null;
    }
  };

  const removeFile = (fileName) => {
    setFiles(prev => prev.filter(f => f.file.name !== fileName));
  };

  return (
    <div className="space-y-4">
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          className="hidden"
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          multiple
        />
        <div className="flex flex-col items-center justify-center">
          <svg className="h-10 w-10 text-gray-400 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="mt-2 text-sm text-gray-600">
            <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {acceptedTypes.join(', ')} files, max 10MB each
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((fileObj, index) => (
            <div key={index} className="p-4 border rounded-lg bg-white">
              <div className="flex items-center justify-between mb-2">
                <div className="truncate">
                  <span className="font-medium">{fileObj.file.name}</span>
                  {fileObj.error && (
                    <span className="text-red-500 text-sm ml-2">- {fileObj.error}</span>
                  )}
                </div>
                <button
                  onClick={() => removeFile(fileObj.file.name)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              {!fileObj.error && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${fileObj.progress}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;