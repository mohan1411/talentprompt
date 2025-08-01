'use client';

import { useEffect, useState, useMemo, memo, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { FixedSizeGrid as Grid, areEqual } from 'react-window';
import { 
  FileText, 
  Search, 
  Calendar, 
  MapPin, 
  Briefcase,
  Eye,
  Trash2,
  Download,
  CheckCircle,
  Clock,
  XCircle,
  Users,
  Linkedin,
  Mail,
  RefreshCw,
  Filter,
  Grid3X3,
  List,
  MoreVertical,
  Plus,
  ChevronDown,
  User,
  Sparkles,
  TrendingUp,
  AlertCircle,
  Upload,
  Command
} from 'lucide-react';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';
import { OutreachModal } from '@/components/outreach/OutreachModal';
import { RequestUpdateModal } from '@/components/submission/RequestUpdateModal';
import { format, formatDistanceToNow, isAfter, subDays } from 'date-fns';
import styles from './ResumesPage.module.css';

type ViewMode = 'grid' | 'list' | 'compact';
type SortOption = 'recent' | 'name' | 'experience' | 'views';
type FilterStatus = 'all' | 'processed' | 'pending' | 'failed';

export default function ResumesPage() {
  const router = useRouter();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedResumes, setSelectedResumes] = useState<Set<string>>(new Set());
  const [showBulkPositionModal, setShowBulkPositionModal] = useState(false);
  const [bulkJobPosition, setBulkJobPosition] = useState('');
  const [showOutreachModal, setShowOutreachModal] = useState(false);
  const [outreachCandidate, setOutreachCandidate] = useState<Resume | null>(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateCandidate, setUpdateCandidate] = useState<Resume | null>(null);
  
  // New state for modern UX
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('recent');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [hoveredResumeId, setHoveredResumeId] = useState<string | null>(null);

  useEffect(() => {
    fetchResumes();
  }, []);

  // Polling for async updates
  useEffect(() => {
    // Check if any resumes need updates
    const needsPolling = resumes.some(r => 
      r.parse_status === 'pending' || r.parse_status === 'processing'
    );

    if (!needsPolling) return;

    // Poll every 5 seconds for updates
    const interval = setInterval(async () => {
      try {
        const updatedData = await resumeApi.getMyResumes(0, 1000);
        
        // Check for status changes
        updatedData.forEach(newResume => {
          const oldResume = resumes.find(r => r.id === newResume.id);
          if (oldResume && oldResume.parse_status !== newResume.parse_status) {
            console.log(`Resume ${newResume.id} status changed: ${oldResume.parse_status} → ${newResume.parse_status}`);
            
            // Show notification for completed resumes
            if (newResume.parse_status === 'completed' && oldResume.parse_status === 'processing') {
              // You can add toast notification here
              console.log(`✓ Resume for ${newResume.first_name} ${newResume.last_name} parsed successfully`);
            }
          }
        });
        
        setResumes(updatedData);
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [resumes]);

  const fetchResumes = async () => {
    try {
      setIsLoading(true);
      const data = await resumeApi.getMyResumes(0, 1000);
      setResumes(data);
    } catch (error) {
      console.error('Failed to fetch resumes:', error);
      setResumes([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter and sort resumes
  const filteredAndSortedResumes = useMemo(() => {
    let filtered = [...resumes];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(resume => 
        `${resume.first_name} ${resume.last_name}`.toLowerCase().includes(query) ||
        resume.email?.toLowerCase().includes(query) ||
        resume.current_title?.toLowerCase().includes(query) ||
        resume.skills?.some(skill => skill.toLowerCase().includes(query))
      );
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(resume => {
        if (filterStatus === 'processed') return resume.parse_status === 'completed';
        if (filterStatus === 'pending') return resume.parse_status === 'pending';
        if (filterStatus === 'failed') return resume.parse_status === 'failed';
        return true;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'name':
          return `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`);
        case 'experience':
          return (b.years_experience || 0) - (a.years_experience || 0);
        case 'views':
          return (b.view_count || 0) - (a.view_count || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [resumes, searchQuery, filterStatus, sortBy]);

  // Group resumes by time period
  const groupedResumes = useMemo(() => {
    const groups: { [key: string]: Resume[] } = {
      'Today': [],
      'This Week': [],
      'This Month': [],
      'Older': []
    };

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const thisWeek = subDays(today, 7);
    const thisMonth = subDays(today, 30);

    filteredAndSortedResumes.forEach(resume => {
      const createdAt = new Date(resume.created_at);
      if (createdAt >= today) {
        groups['Today'].push(resume);
      } else if (createdAt >= thisWeek) {
        groups['This Week'].push(resume);
      } else if (createdAt >= thisMonth) {
        groups['This Month'].push(resume);
      } else {
        groups['Older'].push(resume);
      }
    });

    // Remove empty groups
    Object.keys(groups).forEach(key => {
      if (groups[key].length === 0) delete groups[key];
    });

    return groups;
  }, [filteredAndSortedResumes]);

  const handleDelete = async (resumeId: string) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await resumeApi.deleteResume(resumeId);
      setResumes(resumes.filter(r => r.id !== resumeId));
    } catch (error) {
      console.error('Failed to delete resume:', error);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedResumes.size === 0) return;
    if (!confirm(`Delete ${selectedResumes.size} resume(s)?`)) return;

    try {
      await resumeApi.bulkDelete(Array.from(selectedResumes));
      setResumes(resumes.filter(r => !selectedResumes.has(r.id)));
      setSelectedResumes(new Set());
    } catch (error) {
      console.error('Failed to bulk delete resumes:', error);
    }
  };

  const toggleResumeSelection = useCallback((resumeId: string) => {
    setSelectedResumes(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(resumeId)) {
        newSelection.delete(resumeId);
      } else {
        newSelection.add(resumeId);
      }
      return newSelection;
    });
  }, []);

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'pending': return 'bg-yellow-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  // Calculate grid dimensions based on viewport
  const gridContainerRef = useRef<HTMLDivElement>(null);
  // Initialize with reasonable defaults based on window size
  const getInitialColumns = () => {
    if (typeof window === 'undefined') return 3;
    const width = window.innerWidth;
    return width < 640 ? 1 : width < 1024 ? 2 : 3;
  };
  const [gridDimensions, setGridDimensions] = useState({ 
    width: typeof window !== 'undefined' ? window.innerWidth - 100 : 1200, 
    height: 600, 
    columns: getInitialColumns() 
  });
  const [isGridReady, setIsGridReady] = useState(false);

  useEffect(() => {
    const updateDimensions = () => {
      if (gridContainerRef.current) {
        const width = gridContainerRef.current.offsetWidth || gridContainerRef.current.clientWidth;
        const containerRect = gridContainerRef.current.getBoundingClientRect();
        const height = Math.max(600, window.innerHeight - containerRect.top - 100);
        const columns = width < 640 ? 1 : width < 1024 ? 2 : 3;
        
        // Only update if we have valid dimensions
        if (width > 0) {
          setGridDimensions({ width, height, columns });
          setIsGridReady(true);
        } else {
          // Fallback: use window dimensions if container dimensions not available
          const fallbackWidth = window.innerWidth - 100;
          if (fallbackWidth > 0) {
            const fallbackColumns = fallbackWidth < 640 ? 1 : fallbackWidth < 1024 ? 2 : 3;
            setGridDimensions({ width: fallbackWidth, height, columns: fallbackColumns });
            setIsGridReady(true);
          }
        }
      }
    };

    // Try multiple times to ensure dimensions are available
    updateDimensions(); // Try immediately
    
    // Try again after small delays
    const timeout1 = setTimeout(updateDimensions, 50);
    const timeout2 = setTimeout(updateDimensions, 150);
    const timeout3 = setTimeout(updateDimensions, 300);
    const timeout4 = setTimeout(updateDimensions, 500);
    
    // Force grid ready after 1 second as last resort
    const forceReady = setTimeout(() => {
      if (!isGridReady) {
        const fallbackWidth = window.innerWidth - 100;
        const fallbackColumns = fallbackWidth < 640 ? 1 : fallbackWidth < 1024 ? 2 : 3;
        setGridDimensions({ 
          width: fallbackWidth, 
          height: 600, 
          columns: fallbackColumns 
        });
        setIsGridReady(true);
      }
    }, 1000);
    
    // Set up resize observer for more reliable dimension updates
    const resizeObserver = new ResizeObserver(updateDimensions);
    if (gridContainerRef.current) {
      resizeObserver.observe(gridContainerRef.current);
    }

    // Also listen to window resize as fallback
    window.addEventListener('resize', updateDimensions);
    
    // Force update on load event
    window.addEventListener('load', updateDimensions);
    
    return () => {
      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);
      clearTimeout(timeout4);
      clearTimeout(forceReady);
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateDimensions);
      window.removeEventListener('load', updateDimensions);
    };
  }, [isGridReady]);

  const ResumeCard = memo(({ resume }: { resume: Resume }) => {
    const [showActions, setShowActions] = useState(false);
    const isNew = new Date(resume.created_at) > subDays(new Date(), 7);
    const hasUpdate = resume.updated_at && new Date(resume.updated_at).getTime() !== new Date(resume.created_at).getTime();

    return (
      <div
        className="group relative bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-shadow duration-200 overflow-hidden p-6 h-full"
        onMouseEnter={() => setHoveredResumeId(resume.id)}
        onMouseLeave={() => setHoveredResumeId(null)}
      >
        {/* Selection Checkbox */}
        <div className="absolute top-4 left-4 z-10">
          <input
            type="checkbox"
            checked={selectedResumes.has(resume.id)}
            onChange={() => toggleResumeSelection(resume.id)}
            className="h-4 w-4 text-primary rounded border-gray-300 focus:ring-primary"
          />
        </div>

        {/* Status Indicator */}
        <div className={`absolute top-0 right-0 w-2 h-full ${getStatusColor(resume.parse_status)}`} />

        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              {/* Avatar */}
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-semibold">
                {getInitials(resume.first_name, resume.last_name)}
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  {resume.first_name} {resume.last_name}
                  {isNew && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      NEW
                    </span>
                  )}
                </h3>
                {resume.current_title && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {resume.current_title}
                  </p>
                )}
                {/* Parse Status Badge */}
                {resume.parse_status && (
                  <div className="mt-1 flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      resume.parse_status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                      resume.parse_status === 'processing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                      resume.parse_status === 'pending' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                      resume.parse_status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
                    }`}>
                      {resume.parse_status === 'completed' ? '✓ Parsed' :
                       resume.parse_status === 'processing' ? (
                         <span className="flex items-center gap-1">
                           <span className="animate-pulse">●</span> Processing
                         </span>
                       ) :
                       resume.parse_status === 'pending' ? 'Pending' :
                       resume.parse_status === 'failed' ? 'Failed' :
                       resume.parse_status}
                    </span>
                    {resume.parse_status === 'failed' && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            await resumeApi.retryParsing(resume.id);
                            // Update local state to show processing
                            setResumes(prev => prev.map(r => 
                              r.id === resume.id ? { ...r, parse_status: 'processing' } : r
                            ));
                          } catch (error) {
                            console.error('Failed to retry parsing:', error);
                          }
                        }}
                        className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Actions Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowActions(!showActions)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <MoreVertical className="h-4 w-4 text-gray-500" />
              </button>
              
              {showActions && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg z-20 py-1">
                  <button
                    onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Eye className="h-4 w-4" /> View Details
                  </button>
                  <button
                    onClick={() => router.push(`/dashboard/search/similar/${resume.id}?name=${encodeURIComponent(`${resume.first_name} ${resume.last_name}`)}`)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Users className="h-4 w-4" /> Find Similar
                  </button>
                  <button
                    onClick={() => {
                      setUpdateCandidate(resume);
                      setShowUpdateModal(true);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" /> Request Update
                  </button>
                  <button
                    onClick={() => {
                      setOutreachCandidate(resume);
                      setShowOutreachModal(true);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Mail className="h-4 w-4" /> Generate Outreach
                  </button>
                  <hr className="my-1 border-gray-200 dark:border-gray-700" />
                  <button
                    onClick={() => handleDelete(resume.id)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" /> Delete
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Key Info */}
          <div className="space-y-2 mb-4">
            {resume.location && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <MapPin className="h-4 w-4 mr-2" />
                {resume.location}
              </div>
            )}
            {resume.years_experience !== null && (
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <Briefcase className="h-4 w-4 mr-2" />
                {resume.years_experience} years experience
              </div>
            )}
            {hasUpdate && (
              <div className="flex items-center text-sm text-blue-600 dark:text-blue-400">
                <RefreshCw className="h-4 w-4 mr-2" />
                Updated {formatDistanceToNow(new Date(resume.updated_at!), { addSuffix: true })}
              </div>
            )}
          </div>

          {/* Skills */}
          {resume.skills && resume.skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {resume.skills.slice(0, 4).map((skill, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary dark:bg-primary/20"
                >
                  {skill}
                </span>
              ))}
              {resume.skills.length > 4 && (
                <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                  +{resume.skills.length - 4} more
                </span>
              )}
            </div>
          )}

          {/* Footer Stats */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                {resume.view_count || 0} views
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {format(new Date(resume.created_at), 'MMM d')}
              </span>
            </div>
            
            {/* Primary Action */}
            <button
              onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
              className="px-3 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary/90 transition-colors"
            >
              View Profile
            </button>
          </div>
        </div>
      </div>
    );
  });
  
  ResumeCard.displayName = 'ResumeCard';

  // Virtual grid cell renderer
  const VirtualResumeCard = memo(({ columnIndex, rowIndex, style, data }: {
    columnIndex: number;
    rowIndex: number;
    style: React.CSSProperties;
    data: { resumes: Resume[]; columns: number; selectedResumes: Set<string>; toggleResumeSelection: (id: string) => void; router: any; setUpdateCandidate: any; setShowUpdateModal: any; setOutreachCandidate: any; setShowOutreachModal: any; handleDelete: any; };
  }) => {
    const [showActions, setShowActions] = useState(false);
    
    const { resumes, columns, selectedResumes, toggleResumeSelection, router, setUpdateCandidate, setShowUpdateModal, setOutreachCandidate, setShowOutreachModal, handleDelete } = data;
    const index = rowIndex * columns + columnIndex;
    const resume = resumes[index];

    if (!resume) return null;

    const isNew = new Date(resume.created_at) > subDays(new Date(), 7);
    const hasUpdate = resume.updated_at && new Date(resume.updated_at).getTime() !== new Date(resume.created_at).getTime();

    // Helper functions inside component
    const getInitials = (firstName: string, lastName: string) => {
      return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
    };

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'completed': return 'bg-green-500';
        case 'processing': return 'bg-blue-500';
        case 'pending': return 'bg-yellow-500';
        case 'failed': return 'bg-red-500';
        default: return 'bg-gray-500';
      }
    };

    return (
      <div style={{ ...style, padding: '8px' }}>
        <div
          className={`group relative bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg overflow-hidden h-full ${styles.resumeCard}`}
          data-index={index % 9}
        >
          {/* Selection Checkbox */}
          <div className="absolute top-4 left-4 z-10">
            <input
              type="checkbox"
              checked={selectedResumes.has(resume.id)}
              onChange={() => toggleResumeSelection(resume.id)}
              className="h-4 w-4 text-primary rounded border-gray-300 focus:ring-primary"
            />
          </div>

          {/* Status Indicator */}
          <div className={`absolute top-0 right-0 w-2 h-full ${getStatusColor(resume.parse_status)}`} />

          <div className="p-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                {/* Avatar */}
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-semibold">
                  {getInitials(resume.first_name, resume.last_name)}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    {resume.first_name} {resume.last_name}
                    {isNew && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                        NEW
                      </span>
                    )}
                  </h3>
                  {resume.current_title && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {resume.current_title}
                    </p>
                  )}
                </div>
              </div>

              {/* Actions Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowActions(!showActions)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <MoreVertical className="h-4 w-4 text-gray-500" />
                </button>
                
                {showActions && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg z-20 py-1">
                    <button
                      onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <Eye className="h-4 w-4" /> View Details
                    </button>
                    <button
                      onClick={() => router.push(`/dashboard/search/similar/${resume.id}?name=${encodeURIComponent(`${resume.first_name} ${resume.last_name}`)}`)}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <Users className="h-4 w-4" /> Find Similar
                    </button>
                    <button
                      onClick={() => {
                        setUpdateCandidate(resume);
                        setShowUpdateModal(true);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <RefreshCw className="h-4 w-4" /> Request Update
                    </button>
                    <button
                      onClick={() => {
                        setOutreachCandidate(resume);
                        setShowOutreachModal(true);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <Mail className="h-4 w-4" /> Generate Outreach
                    </button>
                    <hr className="my-1 border-gray-200 dark:border-gray-700" />
                    <button
                      onClick={() => handleDelete(resume.id)}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center gap-2"
                    >
                      <Trash2 className="h-4 w-4" /> Delete
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Key Info */}
            <div className="space-y-2 mb-4">
              {resume.location && (
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <MapPin className="h-4 w-4 mr-2" />
                  {resume.location}
                </div>
              )}
              {resume.years_experience !== null && (
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Briefcase className="h-4 w-4 mr-2" />
                  {resume.years_experience} years experience
                </div>
              )}
              {hasUpdate && (
                <div className="flex items-center text-sm text-blue-600 dark:text-blue-400">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Updated {formatDistanceToNow(new Date(resume.updated_at!), { addSuffix: true })}
                </div>
              )}
            </div>

            {/* Skills */}
            {resume.skills && resume.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {resume.skills.slice(0, 4).map((skill, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary dark:bg-primary/20"
                  >
                    {skill}
                  </span>
                ))}
                {resume.skills.length > 4 && (
                  <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                    +{resume.skills.length - 4} more
                  </span>
                )}
              </div>
            )}

            {/* Footer Stats */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  {resume.view_count || 0} views
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {format(new Date(resume.created_at), 'MMM d')}
                </span>
              </div>
              
              {/* Primary Action */}
              <button
                onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
                className={`px-3 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary/90 ${styles.actionButton}`}
              >
                View Profile
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }, areEqual);

  VirtualResumeCard.displayName = 'VirtualResumeCard';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              My Resumes
              <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                ({filteredAndSortedResumes.length})
              </span>
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage your talent pipeline with AI-powered insights
            </p>
          </div>
        </div>

        {/* Search and Filters Bar */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, email, title, or skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              )}
            </div>

            {/* Filter & Sort Controls */}
            <div className="flex items-center gap-2">
              {/* Status Filter */}
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
              >
                <option value="all">All Status</option>
                <option value="processed">Processed</option>
                <option value="pending">Pending</option>
                <option value="failed">Failed</option>
              </select>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
              >
                <option value="recent">Most Recent</option>
                <option value="name">Name (A-Z)</option>
                <option value="experience">Most Experience</option>
                <option value="views">Most Viewed</option>
              </select>

              {/* View Toggle */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}`}
                  title="Grid view"
                >
                  <Grid3X3 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded ${viewMode === 'list' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}`}
                  title="List view"
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Active Filters Summary */}
          {(searchQuery || filterStatus !== 'all') && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-gray-500">Active filters:</span>
              {searchQuery && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary/10 text-primary">
                  Search: "{searchQuery}"
                  <button onClick={() => setSearchQuery('')} className="ml-1">
                    <XCircle className="h-3 w-3" />
                  </button>
                </span>
              )}
              {filterStatus !== 'all' && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary/10 text-primary">
                  Status: {filterStatus}
                  <button onClick={() => setFilterStatus('all')} className="ml-1">
                    <XCircle className="h-3 w-3" />
                  </button>
                </span>
              )}
            </div>
          )}
        </div>

        {/* Bulk Actions Bar */}
        <AnimatePresence>
          {selectedResumes.size > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-4 bg-primary/10 dark:bg-primary/20 rounded-lg p-4 flex items-center justify-between"
            >
              <span className="text-sm font-medium">
                {selectedResumes.size} resume{selectedResumes.size > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowBulkPositionModal(true)}
                  className="px-3 py-1.5 bg-white dark:bg-gray-800 text-sm rounded-lg hover:shadow-md transition-shadow"
                >
                  Update Position
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                >
                  Delete Selected
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : filteredAndSortedResumes.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16 px-4"
        >
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {searchQuery || filterStatus !== 'all' ? 'No resumes found' : 'Start building your talent pipeline'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {searchQuery || filterStatus !== 'all' 
                ? 'Try adjusting your filters or search terms'
                : 'Upload resumes or import from LinkedIn to get started'}
            </p>
            {!(searchQuery || filterStatus !== 'all') && (
              <div className="space-y-2">
                <Link
                  href="/dashboard/upload"
                  className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Resume
                </Link>
                <Link
                  href="/dashboard/bulk-upload"
                  className="inline-flex items-center justify-center w-full px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                >
                  <Linkedin className="h-5 w-5 mr-2" />
                  Import from LinkedIn
                </Link>
              </div>
            )}
          </div>
        </motion.div>
      ) : viewMode === 'grid' ? (
        // Virtual Grid View
        <div ref={gridContainerRef} className="min-h-[600px] w-full" style={{ height: 'calc(100vh - 300px)' }}>
          {!isGridReady || gridDimensions.width === 0 ? (
            // Loading skeleton while grid initializes
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`h-12 w-12 rounded-full bg-gray-200 dark:bg-gray-700 ${styles.skeleton}`} />
                      <div>
                        <div className={`h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2 ${styles.skeleton}`} />
                        <div className={`h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded ${styles.skeleton}`} />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className={`h-3 w-full bg-gray-200 dark:bg-gray-700 rounded ${styles.skeleton}`} />
                    <div className={`h-3 w-3/4 bg-gray-200 dark:bg-gray-700 rounded ${styles.skeleton}`} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Grid
              columnCount={gridDimensions.columns}
              columnWidth={Math.max(300, (gridDimensions.width - 32) / gridDimensions.columns)}
              height={gridDimensions.height}
              rowCount={Math.ceil(filteredAndSortedResumes.length / gridDimensions.columns)}
              rowHeight={320}
              width={gridDimensions.width || window.innerWidth - 100}
              itemData={{
                resumes: filteredAndSortedResumes,
                columns: gridDimensions.columns,
                selectedResumes,
                toggleResumeSelection,
                router,
                setUpdateCandidate,
                setShowUpdateModal,
                setOutreachCandidate,
                setShowOutreachModal,
                handleDelete
              }}
            >
              {VirtualResumeCard}
            </Grid>
          )}
        </div>
      ) : (
        // List View
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedResumes.size === filteredAndSortedResumes.length && filteredAndSortedResumes.length > 0}
                    onChange={() => {
                      if (selectedResumes.size === filteredAndSortedResumes.length) {
                        setSelectedResumes(new Set());
                      } else {
                        setSelectedResumes(new Set(filteredAndSortedResumes.map(r => r.id)));
                      }
                    }}
                    className="h-4 w-4 text-primary rounded border-gray-300"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Candidate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Experience
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Skills
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Added
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSortedResumes.map((resume) => (
                <tr key={resume.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedResumes.has(resume.id)}
                      onChange={() => toggleResumeSelection(resume.id)}
                      className="h-4 w-4 text-primary rounded border-gray-300"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-semibold text-sm">
                          {getInitials(resume.first_name, resume.last_name)}
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {resume.first_name} {resume.last_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {resume.current_title || resume.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {resume.years_experience || 0} years
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {resume.skills?.slice(0, 3).map((skill, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                        >
                          {skill}
                        </span>
                      ))}
                      {resume.skills && resume.skills.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{resume.skills.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      resume.parse_status === 'completed' ? 'bg-green-100 text-green-800' :
                      resume.parse_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {resume.parse_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(resume.created_at), 'MMM d, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
                      className="text-primary hover:text-primary/80"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Floating Action Button */}
      <Link
        href="/dashboard/upload"
        className="fixed bottom-6 right-6 bg-primary text-white rounded-full p-4 shadow-lg hover:shadow-xl hover:scale-110 transition-all"
      >
        <Plus className="h-6 w-6" />
      </Link>

      {/* Polling Indicator */}
      {resumes.some(r => r.parse_status === 'pending' || r.parse_status === 'processing') && (
        <div className="fixed bottom-20 right-6 flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 px-4 py-2 rounded-lg shadow-lg">
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="text-sm">Checking for updates...</span>
        </div>
      )}

      {/* Keyboard Shortcut Hint */}
      <div className="fixed bottom-6 left-6 text-sm text-gray-500 dark:text-gray-400 bg-white/90 dark:bg-gray-800/90 backdrop-blur px-3 py-2 rounded-lg shadow-sm">
        Press <kbd className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">⌘K</kbd> for quick actions
      </div>

      {/* Modals */}
      {showBulkPositionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md shadow-xl"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Update Job Position
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Update the job position for {selectedResumes.size} selected resume(s)
            </p>
            <input
              type="text"
              value={bulkJobPosition}
              onChange={(e) => setBulkJobPosition(e.target.value)}
              placeholder="e.g., Senior Software Engineer"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowBulkPositionModal(false);
                  setBulkJobPosition('');
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (bulkJobPosition.trim()) {
                    await resumeApi.bulkUpdatePosition(Array.from(selectedResumes), bulkJobPosition);
                    await fetchResumes();
                    setSelectedResumes(new Set());
                    setShowBulkPositionModal(false);
                    setBulkJobPosition('');
                  }
                }}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
                disabled={!bulkJobPosition.trim()}
              >
                Update Position
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Outreach Modal */}
      {showOutreachModal && outreachCandidate && (
        <OutreachModal
          isOpen={showOutreachModal}
          onClose={() => {
            setShowOutreachModal(false);
            setOutreachCandidate(null);
          }}
          candidate={{
            id: outreachCandidate.id,
            name: `${outreachCandidate.first_name} ${outreachCandidate.last_name}`,
            title: outreachCandidate.current_title || '',
            skills: outreachCandidate.skills,
            experience: outreachCandidate.years_experience || undefined
          }}
        />
      )}

      {/* Request Update Modal */}
      {showUpdateModal && updateCandidate && (
        <RequestUpdateModal
          isOpen={showUpdateModal}
          onClose={() => {
            setShowUpdateModal(false);
            setUpdateCandidate(null);
          }}
          candidate={{
            id: updateCandidate.id,
            name: `${updateCandidate.first_name} ${updateCandidate.last_name}`,
            email: updateCandidate.email,
            title: updateCandidate.current_title
          }}
          onSuccess={() => {
            // Optionally refresh or show success message
          }}
        />
      )}
    </div>
  );
}