'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  Send, 
  Calendar, 
  Users, 
  CheckCircle,
  Clock,
  Eye,
  Mail,
  Plus,
  AlertCircle,
  X
} from 'lucide-react';
import { submissionApi } from '@/lib/api/client';
import { RequestUpdateModal } from '@/components/submission/RequestUpdateModal';

interface Campaign {
  id: string;
  name: string;
  created_at: string;
  total_invitations: number;
  completed_submissions: number;
  pending_submissions: number;
  expired_submissions: number;
  submissions?: Submission[];
}

interface Submission {
  id: string;
  token: string;
  submission_type: 'update' | 'new';
  status: 'pending' | 'completed' | 'expired';
  candidate_name: string;
  candidate_email: string;
  created_at: string;
  expires_at: string;
  submitted_at?: string;
  candidate_id?: string;
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null);
  const [campaignDetails, setCampaignDetails] = useState<Campaign | null>(null);
  const [showNewRequestModal, setShowNewRequestModal] = useState(false);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await submissionApi.getCampaigns();
      setCampaigns(data);
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCampaignDetails = async (campaignId: string) => {
    try {
      const data = await submissionApi.getCampaignDetails(campaignId);
      setCampaignDetails(data);
    } catch (error) {
      console.error('Failed to fetch campaign details:', error);
    }
  };

  const handleViewCampaign = (campaignId: string) => {
    setSelectedCampaign(campaignId);
    fetchCampaignDetails(campaignId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50';
      case 'expired':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'expired':
        return <X className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Submission Campaigns
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Track and manage candidate submission requests
            </p>
          </div>
          <button
            onClick={() => setShowNewRequestModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>New Request</span>
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Campaigns</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {campaigns.length}
                </p>
              </div>
              <Mail className="h-8 w-8 text-gray-400" />
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Invitations</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {campaigns.reduce((acc, c) => acc + c.total_invitations, 0)}
                </p>
              </div>
              <Send className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {campaigns.reduce((acc, c) => acc + c.completed_submissions, 0)}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Response Rate</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {campaigns.length > 0 
                    ? Math.round((campaigns.reduce((acc, c) => acc + c.completed_submissions, 0) / 
                        campaigns.reduce((acc, c) => acc + c.total_invitations, 0)) * 100)
                    : 0}%
                </p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Mail className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            No campaigns yet
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Start by sending update requests to candidates.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map((campaign) => (
            <div
              key={campaign.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    {campaign.name}
                  </h3>
                  <div className="mt-1 flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Calendar className="h-4 w-4 mr-1" />
                    Created {new Date(campaign.created_at).toLocaleDateString()}
                  </div>
                  
                  <div className="mt-4 grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Sent</p>
                      <p className="text-lg font-medium text-gray-900 dark:text-white">
                        {campaign.total_invitations}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Completed</p>
                      <p className="text-lg font-medium text-green-600">
                        {campaign.completed_submissions}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                      <p className="text-lg font-medium text-yellow-600">
                        {campaign.pending_submissions}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Expired</p>
                      <p className="text-lg font-medium text-red-600">
                        {campaign.expired_submissions}
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${(campaign.completed_submissions / campaign.total_invitations) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleViewCampaign(campaign.id)}
                  className="ml-4 flex items-center space-x-2 px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md transition-colors"
                >
                  <Eye className="h-4 w-4" />
                  <span>View Details</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Campaign Details Modal */}
      {selectedCampaign && campaignDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {campaignDetails.name}
                </h2>
                <button
                  onClick={() => {
                    setSelectedCampaign(null);
                    setCampaignDetails(null);
                  }}
                  className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              <div className="space-y-4">
                {campaignDetails.submissions?.map((submission) => (
                  <div
                    key={submission.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {submission.candidate_name}
                        </h4>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(submission.status)}`}>
                          {getStatusIcon(submission.status)}
                          <span className="ml-1">{submission.status}</span>
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {submission.candidate_email}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>Sent: {new Date(submission.created_at).toLocaleDateString()}</span>
                        <span>Expires: {new Date(submission.expires_at).toLocaleDateString()}</span>
                        {submission.submitted_at && (
                          <span className="text-green-600">
                            Submitted: {new Date(submission.submitted_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>

                    {submission.status === 'pending' && (
                      <div className="flex items-center space-x-2">
                        <button
                          className="text-sm text-blue-600 hover:text-blue-700"
                          onClick={() => {
                            // Copy link to clipboard
                            const submissionUrl = `${window.location.origin}/submit/${submission.token}`;
                            navigator.clipboard.writeText(submissionUrl);
                            alert('Submission link copied to clipboard!');
                          }}
                        >
                          Copy Link
                        </button>
                        <button
                          className="text-sm text-orange-600 hover:text-orange-700"
                          onClick={() => {
                            // TODO: Implement resend functionality
                            alert('Resend functionality coming soon!');
                          }}
                        >
                          Resend
                        </button>
                      </div>
                    )}

                    {submission.status === 'completed' && submission.candidate_id && (
                      <Link
                        href={`/dashboard/resumes/${submission.candidate_id}`}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        View Profile
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Request Modal */}
      {showNewRequestModal && (
        <RequestUpdateModal
          isOpen={showNewRequestModal}
          onClose={() => setShowNewRequestModal(false)}
          candidate={{
            id: '',
            name: '',
            email: '',
            title: ''
          }}
          onSuccess={() => {
            setShowNewRequestModal(false);
            fetchCampaigns();
          }}
        />
      )}
    </div>
  );
}