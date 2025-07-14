'use client';

import { useState } from 'react';

export default function TestFolderPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>('');

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError('');
    console.log('Event:', e);
    console.log('Files:', e.target.files);
    
    if (e.target.files) {
      const fileList = Array.from(e.target.files);
      console.log('File list:', fileList);
      
      fileList.forEach((file: any) => {
        console.log({
          name: file.name,
          size: file.size,
          type: file.type,
          webkitRelativePath: file.webkitRelativePath,
          path: file.path,
        });
      });
      
      setFiles(fileList);
    } else {
      setError('No files selected');
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Folder Selection Test</h1>
      
      <div className="space-y-4">
        <div>
          <label className="block mb-2">Select Folder (webkitdirectory):</label>
          <input
            type="file"
            // @ts-ignore
            webkitdirectory=""
            multiple
            onChange={handleFolderSelect}
            className="border p-2"
          />
        </div>

        <div>
          <label className="block mb-2">Select Files (regular):</label>
          <input
            type="file"
            multiple
            onChange={handleFolderSelect}
            className="border p-2"
          />
        </div>

        {error && (
          <div className="text-red-500">Error: {error}</div>
        )}

        {files.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-2">Selected Files ({files.length}):</h2>
            <ul className="space-y-1">
              {files.map((file: any, index) => (
                <li key={index} className="text-sm">
                  {file.webkitRelativePath || file.name} - {(file.size / 1024).toFixed(2)} KB
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}