'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone, FileWithPath } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle,
  Folder,
  RefreshCw,
  Pause,
  Play,
  BarChart,
  Clock,
  Zap
} from 'lucide-react';
import { resumeApi } from '@/lib/api/client';

// Extend HTMLInputElement interface for webkitdirectory
declare module 'react' {
  interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    webkitdirectory?: string;
  }
}

interface UploadFile {
  id: string;
  file: File;
  path: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
  resumeId?: string;
  duplicate?: boolean;
}

interface UploadStats {
  total: number;
  pending: number;
  uploading: number;
  processing: number;
  completed: number;
  failed: number;
}

const CONCURRENT_UPLOADS = 5;
const SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt'];

export default function BulkUploadCenterPage() {
  const router = useRouter();
  const [files, setFiles] = useState<Map<string, UploadFile>>(new Map());
  const [isUploading, setIsUploading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState('');
  const [includeSubfolders, setIncludeSubfolders] = useState(true);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const uploadQueueRef = useRef<string[]>([]);
  const activeUploadsRef = useRef<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const isUploadingRef = useRef(false);
  const isPausedRef = useRef(false);

  // Calculate stats
  const getStats = (): UploadStats => {
    const fileArray = Array.from(files.values());
    return {
      total: fileArray.length,
      pending: fileArray.filter(f => f.status === 'pending').length,
      uploading: fileArray.filter(f => f.status === 'uploading').length,
      processing: fileArray.filter(f => f.status === 'processing').length,
      completed: fileArray.filter(f => f.status === 'completed').length,
      failed: fileArray.filter(f => f.status === 'failed').length,
    };
  };

  const stats = getStats();

  // Process dropped items recursively
  const processDroppedItems = async (items: DataTransferItemList): Promise<FileWithPath[]> => {
    const files: FileWithPath[] = [];
    const promises: Promise<void>[] = [];

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        if (entry) {
          promises.push(
            processEntry(entry, files).catch(err => {
              console.error('Error processing entry:', err);
            })
          );
        }
      }
    }

    await Promise.all(promises);
    return files;
  };

  // Process file system entry (file or directory)
  const processEntry = async (entry: FileSystemEntry, files: FileWithPath[], path = ''): Promise<void> => {
    if (entry.isFile) {
      const fileEntry = entry as FileSystemFileEntry;
      const file = await new Promise<FileWithPath>((resolve, reject) => {
        fileEntry.file((file) => {
          // Create a new object with the path property
          const fileWithPath = Object.assign(file, {
            path: path + file.name
          }) as FileWithPath;
          resolve(fileWithPath);
        }, reject);
      });

      // Check if file is supported format
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (SUPPORTED_FORMATS.includes(ext)) {
        files.push(file);
      }
    } else if (entry.isDirectory) {
      const dirEntry = entry as FileSystemDirectoryEntry;
      const reader = dirEntry.createReader();
      
      // Read all entries (may need multiple calls for large directories)
      const readAllEntries = async (): Promise<FileSystemEntry[]> => {
        const allEntries: FileSystemEntry[] = [];
        let entries: FileSystemEntry[];
        
        do {
          entries = await new Promise<FileSystemEntry[]>((resolve) => {
            reader.readEntries((entries) => resolve(entries));
          });
          allEntries.push(...entries);
        } while (entries.length > 0);
        
        return allEntries;
      };
      
      const entries = await readAllEntries();
      const promises: Promise<void>[] = [];
      
      for (const childEntry of entries) {
        if (includeSubfolders || childEntry.isFile) {
          promises.push(processEntry(childEntry, files, path + dirEntry.name + '/'));
        }
      }
      
      await Promise.all(promises);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[], fileRejections: any, event: any) => {
    console.log('Drop event:', { acceptedFiles, event });
    
    // Handle folder drops
    if (event?.dataTransfer?.items && event.dataTransfer.items.length > 0) {
      console.log('Processing dropped items...');
      const droppedFiles = await processDroppedItems(event.dataTransfer.items);
      console.log('Dropped files:', droppedFiles);
      
      // Add files to upload queue
      const newFiles = new Map(files);
      droppedFiles.forEach(file => {
        const id = `${file.name}-${file.size}-${Date.now()}`;
        newFiles.set(id, {
          id,
          file,
          path: file.path || file.name,
          status: 'pending',
          progress: 0,
        });
        uploadQueueRef.current.push(id);
      });
      setFiles(newFiles);
    } else if (acceptedFiles && acceptedFiles.length > 0) {
      console.log('Processing accepted files...');
      // Handle regular file drops
      const newFiles = new Map(files);
      acceptedFiles.forEach(file => {
        const id = `${file.name}-${file.size}-${Date.now()}`;
        newFiles.set(id, {
          id,
          file,
          path: file.name,
          status: 'pending',
          progress: 0,
        });
        uploadQueueRef.current.push(id);
      });
      setFiles(newFiles);
    }
  }, [files, includeSubfolders, processDroppedItems]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: true,
    noClick: true, // We'll handle click ourselves for folder selection
    useFsAccessApi: false, // Disable FileSystem Access API to ensure compatibility
  });

  // Process upload queue
  const processQueue = async () => {
    if (isPausedRef.current || !isUploadingRef.current) return;

    while (activeUploadsRef.current.size < CONCURRENT_UPLOADS && uploadQueueRef.current.length > 0) {
      if (isPausedRef.current || !isUploadingRef.current) break;
      
      const fileId = uploadQueueRef.current.shift();
      if (!fileId) break;

      const uploadFileData = files.get(fileId);
      if (!uploadFileData || uploadFileData.status !== 'pending') continue;

      activeUploadsRef.current.add(fileId);
      uploadSingleFile(fileId);
    }
  };

  // Upload single file
  const uploadSingleFile = async (fileId: string) => {
    const uploadFile = files.get(fileId);
    if (!uploadFile) return;

    try {
      // Update status to uploading
      setFiles(prev => {
        const updated = new Map(prev);
        const file = updated.get(fileId);
        if (file) file.status = 'uploading';
        return updated;
      });

      // Upload file
      const response = await resumeApi.upload(uploadFile.file, selectedPosition);

      // Update status to processing
      setFiles(prev => {
        const updated = new Map(prev);
        const file = updated.get(fileId);
        if (file) {
          file.status = 'processing';
          file.resumeId = response.id;
        }
        return updated;
      });

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Update status to completed
      setFiles(prev => {
        const updated = new Map(prev);
        const file = updated.get(fileId);
        if (file) {
          file.status = 'completed';
          file.progress = 100;
        }
        return updated;
      });

    } catch (error: any) {
      // Update status to failed
      setFiles(prev => {
        const updated = new Map(prev);
        const file = updated.get(fileId);
        if (file) {
          file.status = 'failed';
          file.error = error.message || 'Upload failed';
        }
        return updated;
      });
    } finally {
      activeUploadsRef.current.delete(fileId);
      processQueue();
    }
  };

  // Start upload process
  const startUpload = async () => {
    setIsUploading(true);
    setIsPaused(false);
    isUploadingRef.current = true;
    isPausedRef.current = false;
    
    // Start processing the queue
    processQueue();
  };

  // Pause/Resume upload
  const togglePause = () => {
    const newPausedState = !isPaused;
    setIsPaused(newPausedState);
    isPausedRef.current = newPausedState;
    
    // If we're resuming (unpause), process the queue
    if (!newPausedState && isUploading) {
      processQueue();
    }
  };

  // Retry failed uploads
  const retryFailed = () => {
    const failedFiles = Array.from(files.values()).filter(f => f.status === 'failed');
    failedFiles.forEach(file => {
      file.status = 'pending';
      file.error = undefined;
      uploadQueueRef.current.push(file.id);
    });
    setFiles(new Map(files));
    if (isUploadingRef.current && !isPausedRef.current) {
      processQueue();
    }
  };

  // Clear completed files
  const clearCompleted = () => {
    const newFiles = new Map(files);
    Array.from(files.values())
      .filter(f => f.status === 'completed')
      .forEach(f => newFiles.delete(f.id));
    setFiles(newFiles);
  };

  // Get progress percentage
  const getProgress = () => {
    if (stats.total === 0) return 0;
    return Math.round(((stats.completed + stats.failed) / stats.total) * 100);
  };

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const newFiles = new Map(files);
    
    selectedFiles.forEach(file => {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (SUPPORTED_FORMATS.includes(ext)) {
        const id = `${file.name}-${file.size}-${Date.now()}`;
        newFiles.set(id, {
          id,
          file,
          path: file.name,
          status: 'pending',
          progress: 0,
        });
        uploadQueueRef.current.push(id);
      }
    });
    
    setFiles(newFiles);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Handle folder input change
  const handleFolderInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('Folder input change:', e.target.files);
    const selectedFiles = Array.from(e.target.files || []);
    const newFiles = new Map(files);
    
    let processedCount = 0;
    selectedFiles.forEach(file => {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (SUPPORTED_FORMATS.includes(ext)) {
        // @ts-ignore - webkitRelativePath is not in the type definitions
        const relativePath = file.webkitRelativePath || file.name;
        console.log('Processing file:', { name: file.name, path: relativePath });
        const id = `${file.name}-${file.size}-${Date.now()}-${processedCount++}`;
        newFiles.set(id, {
          id,
          file,
          path: relativePath,
          status: 'pending',
          progress: 0,
        });
        uploadQueueRef.current.push(id);
      }
    });
    
    console.log('Total files processed:', processedCount);
    setFiles(newFiles);
    if (folderInputRef.current) folderInputRef.current.value = '';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <Zap className="h-8 w-8 text-primary" />
          Bulk Upload Center
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Upload hundreds of resumes at once with our powerful bulk processing system
        </p>
      </div>

      {/* Upload Configuration */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Upload Settings
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Job Position (Optional)
            </label>
            <input
              type="text"
              value={selectedPosition}
              onChange={(e) => setSelectedPosition(e.target.value)}
              placeholder="e.g., Software Engineer"
              className="input"
              disabled={isUploading}
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeSubfolders}
                onChange={(e) => setIncludeSubfolders(e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                disabled={isUploading}
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Include subfolders
              </span>
            </label>
          </div>

          <div className="flex items-end">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={skipDuplicates}
                onChange={(e) => setSkipDuplicates(e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                disabled={isUploading}
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Skip duplicates
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* Drop Zone */}
      {files.size === 0 && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center
            transition-colors duration-200
            ${isDragActive 
              ? 'border-primary bg-primary/5' 
              : 'border-gray-300 dark:border-gray-600 hover:border-primary'
            }
          `}
        >
          <input {...getInputProps()} />
          <Folder className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Drop folders or files here
          </p>
          <div className="flex items-center justify-center gap-4 mt-4">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
            >
              Select Files
            </button>
            <button
              type="button"
              onClick={() => folderInputRef.current?.click()}
              className="btn-secondary"
            >
              Select Folder
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-4">
            Supports PDF, DOCX, DOC, TXT files
          </p>
          
          {/* Hidden file inputs */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
          <input
            ref={folderInputRef}
            type="file"
            webkitdirectory=""
            multiple
            onChange={handleFolderInputChange}
            style={{ display: 'none' }}
          />
        </div>
      )}

      {/* Upload Stats Dashboard */}
      {files.size > 0 && (
        <div className="space-y-6">
          {/* Progress Overview */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Upload Progress
              </h3>
              <div className="flex items-center gap-2">
                {!isUploading ? (
                  <button
                    onClick={startUpload}
                    className="btn-primary flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    Start Upload
                  </button>
                ) : (
                  <button
                    onClick={togglePause}
                    className="btn-secondary flex items-center gap-2"
                  >
                    {isPaused ? (
                      <>
                        <Play className="h-4 w-4" />
                        Resume
                      </>
                    ) : (
                      <>
                        <Pause className="h-4 w-4" />
                        Pause
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                <span>Overall Progress</span>
                <span>{getProgress()}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-primary h-3 rounded-full transition-all duration-300"
                  style={{ width: `${getProgress()}%` }}
                />
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-500">
                  {stats.pending}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Pending</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.uploading}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Uploading</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {stats.processing}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Processing</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {stats.completed}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {stats.failed}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Failed</div>
              </div>
            </div>
          </div>

          {/* File List */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Files ({files.size})
              </h3>
              <div className="flex items-center gap-2">
                {stats.failed > 0 && (
                  <button
                    onClick={retryFailed}
                    className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Retry Failed
                  </button>
                )}
                {stats.completed > 0 && (
                  <button
                    onClick={clearCompleted}
                    className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Clear Completed
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {Array.from(files.values()).map(file => (
                <div 
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <FileText className="h-5 w-5 text-gray-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {file.path}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(file.file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {file.status === 'pending' && (
                      <span className="text-xs text-gray-500">Waiting...</span>
                    )}
                    {file.status === 'uploading' && (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        <span className="text-xs text-blue-600">Uploading...</span>
                      </div>
                    )}
                    {file.status === 'processing' && (
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-yellow-600 animate-pulse" />
                        <span className="text-xs text-yellow-600">Processing...</span>
                      </div>
                    )}
                    {file.status === 'completed' && (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    )}
                    {file.status === 'failed' && (
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <span className="text-xs text-red-600">{file.error}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add more files */}
          <div
            {...getRootProps()}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-primary transition-colors"
          >
            <input {...getInputProps()} />
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Drop more files here
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary text-sm"
              >
                Add Files
              </button>
              <button
                type="button"
                onClick={() => folderInputRef.current?.click()}
                className="btn-secondary text-sm"
              >
                Add Folder
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}