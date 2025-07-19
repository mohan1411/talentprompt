import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { Loader2, Copy, Mail, Sparkles, User, Briefcase, Code } from "lucide-react";
import { outreachApi, OutreachMessageRequest, OutreachMessage } from '@/lib/api/outreach';

interface OutreachModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidate: {
    id: string;
    name: string;
    title: string;
    skills?: string[];
    experience?: number;
  };
}

export function OutreachModal({ isOpen, onClose, candidate }: OutreachModalProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [messages, setMessages] = useState<{
    casual?: OutreachMessage;
    professional?: OutreachMessage;
    technical?: OutreachMessage;
  }>({});
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [copiedStyle, setCopiedStyle] = useState<string | null>(null);
  const { toast } = useToast();

  const handleGenerate = async () => {
    if (!jobTitle) {
      toast({
        title: "Job title required",
        description: "Please enter the job title you're recruiting for",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    try {
      const request: OutreachMessageRequest = {
        resume_id: candidate.id,
        job_title: jobTitle,
        company_name: companyName || undefined,
        custom_instructions: customInstructions || undefined,
      };

      const response = await outreachApi.generateMessages(request);
      
      if (response.success) {
        setMessages(response.messages);
        toast({
          title: "Messages generated!",
          description: "Three personalized messages have been created",
        });
      }
    } catch (error) {
      toast({
        title: "Generation failed",
        description: "Failed to generate messages. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async (message: OutreachMessage, style: string) => {
    try {
      const fullMessage = `Subject: ${message.subject}\n\n${message.body}`;
      await navigator.clipboard.writeText(fullMessage);
      setCopiedStyle(style);
      toast({
        title: "Copied to clipboard!",
        description: `${style} message copied successfully`,
      });
      
      // Track the copy action
      // await outreachApi.trackPerformance({
      //   message_id: 'generated-message-id', // You'd get this from the API
      //   event: 'sent',
      // });
      
      setTimeout(() => setCopiedStyle(null), 2000);
    } catch (error) {
      toast({
        title: "Copy failed",
        description: "Failed to copy message to clipboard",
        variant: "destructive",
      });
    }
  };

  const getStyleIcon = (style: string) => {
    switch (style) {
      case 'casual':
        return <User className="h-4 w-4" />;
      case 'professional':
        return <Briefcase className="h-4 w-4" />;
      case 'technical':
        return <Code className="h-4 w-4" />;
      default:
        return <Mail className="h-4 w-4" />;
    }
  };

  const getQualityBadgeVariant = (score: number): "default" | "secondary" | "outline" => {
    if (score >= 0.8) return "default";
    if (score >= 0.6) return "secondary";
    return "outline";
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Generate Outreach Messages
          </DialogTitle>
          <DialogDescription>
            Create personalized outreach messages for {candidate.name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Input Form */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="job-title">Job Title *</Label>
                <Input
                  id="job-title"
                  placeholder="e.g., Senior Software Engineer"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company-name">Company Name</Label>
                <Input
                  id="company-name"
                  placeholder="e.g., TechCorp Inc."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="instructions">Custom Instructions</Label>
              <Textarea
                id="instructions"
                placeholder="e.g., Emphasize remote work, equity package, or specific technologies..."
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                rows={3}
              />
            </div>

            <Button 
              onClick={handleGenerate} 
              disabled={isGenerating || !jobTitle}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Messages...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Messages
                </>
              )}
            </Button>
          </div>

          {/* Generated Messages */}
          {Object.keys(messages).length > 0 && (
            <Tabs defaultValue="casual" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="casual" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Casual
                </TabsTrigger>
                <TabsTrigger value="professional" className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4" />
                  Professional
                </TabsTrigger>
                <TabsTrigger value="technical" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Technical
                </TabsTrigger>
              </TabsList>

              {(['casual', 'professional', 'technical'] as const).map((style) => {
                const message = messages[style];
                if (!message) return null;

                return (
                  <TabsContent key={style} value={style}>
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center gap-2">
                            {getStyleIcon(style)}
                            {style.charAt(0).toUpperCase() + style.slice(1)} Style
                          </CardTitle>
                          <div className="flex items-center gap-2">
                            <Badge variant={getQualityBadgeVariant(message.quality_score)}>
                              Quality: {(message.quality_score * 100).toFixed(0)}%
                            </Badge>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(message, style)}
                            >
                              {copiedStyle === style ? (
                                <>Copied!</>
                              ) : (
                                <>
                                  <Copy className="mr-2 h-4 w-4" />
                                  Copy
                                </>
                              )}
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <Label className="text-sm text-muted-foreground">Subject</Label>
                          <p className="font-medium mt-1">{message.subject}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-muted-foreground">Message</Label>
                          <div className="mt-1 whitespace-pre-wrap bg-muted p-4 rounded-md">
                            {message.body}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>
                );
              })}
            </Tabs>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}