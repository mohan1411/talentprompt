'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle, FileArchive, AlertCircle } from 'lucide-react';
import JSZip from 'jszip';
import { resumeApi } from '@/lib/api/client';
import { ApiError } from '@/lib/api/client';

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [uploadResults, setUploadResults] = useState<{
    file: File;
    status: 'success' | 'error' | 'processing';
    message?: string;
  }[]>([]);
  const [processingZip, setProcessingZip] = useState(false);
  const [jobPosition, setJobPosition] = useState('');
  const router = useRouter();
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const extractZipFiles = async (zipFile: File): Promise<File[]> => {
    const zip = new JSZip();
    const extractedFiles: File[] = [];
    
    try {
      const zipContent = await zip.loadAsync(zipFile);
      
      for (const [path, zipEntry] of Object.entries(zipContent.files)) {
        if (!zipEntry.dir && /\.(pdf|docx?|txt)$/i.test(path)) {
          const blob = await zipEntry.async('blob');
          const fileName = path.split('/').pop() || path;
          
          // Determine file type based on extension
          let mimeType = 'application/octet-stream';
          if (fileName.endsWith('.pdf')) mimeType = 'application/pdf';
          else if (fileName.endsWith('.docx')) mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          else if (fileName.endsWith('.doc')) mimeType = 'application/msword';
          else if (fileName.endsWith('.txt')) mimeType = 'text/plain';
          
          const file = new File([blob], fileName, {
            type: mimeType,
            lastModified: zipEntry.date ? zipEntry.date.getTime() : Date.now()
          });
          
          // Debug log
          console.log(`Extracted file: ${fileName}, size: ${file.size} bytes (blob size: ${blob.size} bytes)`);
          
          extractedFiles.push(file);
        }
      }
    } catch (error) {
      console.error('Error extracting ZIP:', error);
    }
    
    return extractedFiles;
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const regularFiles: File[] = [];
    const zipFiles: File[] = [];
    
    acceptedFiles.forEach(file => {
      if (file.type === 'application/zip' || file.name.endsWith('.zip')) {
        zipFiles.push(file);
      } else {
        regularFiles.push(file);
      }
    });
    
    // Add regular files immediately
    if (regularFiles.length > 0) {
      setFiles((prevFiles) => [...prevFiles, ...regularFiles]);
    }
    
    // Process ZIP files
    if (zipFiles.length > 0) {
      setProcessingZip(true);
      for (const zipFile of zipFiles) {
        console.log(`Processing ZIP file: ${zipFile.name}, size: ${formatFileSize(zipFile.size)}`);
        const extracted = await extractZipFiles(zipFile);
        console.log(`Extracted ${extracted.length} files from ${zipFile.name}`);
        setFiles((prevFiles) => [...prevFiles, ...extracted]);
      }
      setProcessingZip(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'application/zip': ['.zip'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB for ZIP files
  });

  const removeFile = (index: number) => {
    setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadResults([]);
    setUploadProgress({});

    const results = [];
    const CONCURRENT_UPLOADS = 5; // Limit concurrent uploads

    // Process files in batches to avoid overwhelming the backend
    for (let i = 0; i < files.length; i += CONCURRENT_UPLOADS) {
      const batch = files.slice(i, i + CONCURRENT_UPLOADS);
      
      // Process batch concurrently
      const batchPromises = batch.map(async (file, batchIndex) => {
        const fileIndex = i + batchIndex;
        const fileKey = `${file.name}-${fileIndex}`;
        
        // Update progress
        setUploadProgress(prev => ({ ...prev, [fileKey]: 0 }));
        
        // Show processing status
        setUploadResults(prev => {
          const newResults = [...prev];
          if (!newResults.find(r => r.file === file)) {
            newResults.push({
              file,
              status: 'processing' as const,
              message: 'Uploading...'
            });
          }
          return newResults;
        });
        
        try {
          // Simulate progress (in real app, use XMLHttpRequest or fetch with progress)
          setUploadProgress(prev => ({ ...prev, [fileKey]: 50 }));
          
          await resumeApi.upload(file, jobPosition || undefined);
          
          setUploadProgress(prev => ({ ...prev, [fileKey]: 100 }));
          
          // Update the specific result
          setUploadResults(prev => 
            prev.map(r => r.file === file ? { ...r, status: 'success' as const, message: undefined } : r)
          );
          
          return {
            file,
            status: 'success' as const,
          };
        } catch (error) {
          let message = 'Upload failed';
          if (error instanceof ApiError) {
            message = error.detail;
          }
          
          // Update the specific result
          setUploadResults(prev => 
            prev.map(r => r.file === file ? { ...r, status: 'error' as const, message } : r)
          );
          
          return {
            file,
            status: 'error' as const,
            message,
          };
        }
      });
      
      // Wait for current batch to complete before starting next batch
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      // Small delay between batches to avoid overwhelming the server
      if (i + CONCURRENT_UPLOADS < files.length) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    setUploading(false);

    // Clear successful files
    const successfulFiles = results
      .filter((r) => r.status === 'success')
      .map((r) => r.file);
    setFiles((prevFiles) =>
      prevFiles.filter((f) => !successfulFiles.includes(f))
    );

    // If all uploads were successful, redirect after a short delay
    if (results.every((r) => r.status === 'success') && results.length > 0) {
      setTimeout(() => {
        router.push('/dashboard/resumes');
      }, 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Upload Resumes
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Upload resume files to add them to your searchable database
        </p>
      </div>

      {/* Job Position Field */}
      <div className="card p-6 mb-6">
        <div className="mb-4">
          <label htmlFor="jobPosition" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Job Position (Optional)
          </label>
          <input
            type="text"
            id="jobPosition"
            value={jobPosition}
            onChange={(e) => setJobPosition(e.target.value)}
            placeholder="e.g., Senior Software Engineer, Product Manager"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Tag all uploaded resumes with this job position for easier organization
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`card p-8 border-2 border-dashed cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-center">
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag and drop resume files here, or click to select'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Supported formats: PDF, DOCX, DOC, TXT, ZIP (Max 50MB)
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            💡 Tip: Upload ZIP files containing multiple resumes for bulk import
          </p>
        </div>
      </div>

      {/* Processing ZIP notification */}
      {processingZip && (
        <div className="mt-4 card p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-center">
            <FileArchive className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-3 animate-pulse" />
            <p className="text-sm text-blue-800 dark:text-blue-300">
              Extracting files from ZIP archive...
            </p>
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Files to upload ({files.length})
            </h3>
            {files.length > 10 && (
              <span className="text-sm text-orange-600 dark:text-orange-400 flex items-center">
                <AlertCircle className="h-4 w-4 mr-1" />
                Large batch - uploads may take a while
              </span>
            )}
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {files.map((file, index) => {
              const fileKey = `${file.name}-${index}`;
              const progress = uploadProgress[fileKey];
              const isUploading = progress !== undefined;
              
              return (
                <div
                  key={fileKey}
                  className="card p-4 flex items-center justify-between relative overflow-hidden"
                >
                  {isUploading && (
                    <div
                      className="absolute inset-0 bg-blue-100 dark:bg-blue-900/20 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  )}
                  <div className="flex items-center relative z-10">
                    <FileText className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)}
                        {isUploading && ` - ${progress}%`}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    disabled={isUploading}
                    className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50 relative z-10"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              );
            })}
          </div>

          <div className="mt-4 flex items-center gap-4">
            <button
              onClick={handleUpload}
              disabled={uploading || processingZip}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? `Uploading ${files.length} files...` : `Upload ${files.length} file(s)`}
            </button>
            {files.length > 0 && !uploading && (
              <button
                onClick={() => setFiles([])}
                className="btn-secondary"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      )}

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Upload Results
          </h3>
          <div className="space-y-2">
            {uploadResults.map((result, index) => (
              <div
                key={`result-${index}`}
                className={`card p-4 flex items-center justify-between ${
                  result.status === 'success'
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                    : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}
              >
                <div className="flex items-center">
                  {result.status === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                  ) : (
                    <X className="h-5 w-5 text-red-600 mr-3" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {result.file.name}
                    </p>
                    {result.message && (
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {result.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}