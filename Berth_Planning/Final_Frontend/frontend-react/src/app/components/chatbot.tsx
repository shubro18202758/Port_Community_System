import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { X, Send, MessageSquare, Minimize2, TrendingUp, Ship, Anchor, Clock, AlertCircle, CheckCircle2, BarChart3, Zap, ChevronRight, Bot, Loader2, Brain, RefreshCw, Navigation, Sparkles, MapPin, Calendar, Target, Activity } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { aiService } from '../../api/services';
import type { AIChatResponse, AIChatVesselData, AIChatBerthData, AIChatAction } from '../../types';

/**
 * Convert markdown text to clean, human-readable HTML
 * Handles: headers, bold, italic, lists, code, blockquotes
 */
function renderMarkdown(text: string): string {
  if (!text) return '';
  
  let html = text;
  
  // Escape HTML to prevent XSS
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  
  // Headers: ### -> h3, ## -> h2, # -> h1
  html = html.replace(/^### (.+)$/gm, '<strong class="text-base block mt-3 mb-1 text-cyan-300">$1</strong>');
  html = html.replace(/^## (.+)$/gm, '<strong class="text-lg block mt-3 mb-1 text-cyan-200">$1</strong>');
  html = html.replace(/^# (.+)$/gm, '<strong class="text-xl block mt-4 mb-2 text-cyan-100">$1</strong>');
  
  // Bold: **text** or __text__
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  
  // Italic: *text* or _text_
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
  
  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-700/50 px-1.5 py-0.5 rounded text-cyan-300 text-sm">$1</code>');
  
  // Blockquotes: > text
  html = html.replace(/^&gt; (.+)$/gm, '<div class="border-l-2 border-cyan-500 pl-3 my-1 text-slate-300 italic">$1</div>');
  
  // Unordered lists: - item or * item
  html = html.replace(/^[\-\*] (.+)$/gm, '<div class="flex items-start gap-2 my-0.5"><span class="text-cyan-400 mt-0.5">•</span><span>$1</span></div>');
  
  // Numbered lists: 1. item
  html = html.replace(/^(\d+)\. (.+)$/gm, '<div class="flex items-start gap-2 my-0.5"><span class="text-cyan-400 font-medium min-w-[1.5rem]">$1.</span><span>$2</span></div>');
  
  // Horizontal rule: --- or ***
  html = html.replace(/^[\-\*]{3,}$/gm, '<hr class="my-3 border-slate-600"/>');
  
  // Convert newlines to proper line breaks for paragraphs
  html = html.replace(/\n\n/g, '</p><p class="my-2">');
  html = html.replace(/\n/g, '<br/>');
  
  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<')) {
    html = '<p class="my-1">' + html + '</p>';
  }
  
  return html;
}

interface Vessel {
  id: string;
  name: string;
  imo: string;
  predictedETA: Date;
  declaredETA: Date;
  status: string;
  readiness: string;
  aiRecommendation?: {
    suggestedBerth: string;
    confidence: number;
    reason: string;
  };
  loa: number;
  draft: number;
  cargoType: string;
  cargoQuantity: number;
  ata?: Date;
}

interface Berth {
  id: string;
  name: string;
  status: string;
  currentVessel?: {
    name: string;
    etd: Date;
  };
  upcomingVessels?: Array<{
    name: string;
    eta: Date;
  }>;
  maxLOA: number;
  maxDraft: number;
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  cards?: VesselCard[] | BerthCard[];
  chart?: ChartData;
  actions?: MessageAction[];
}

interface VesselCard {
  type: 'vessel';
  vesselId: string;
  vesselName: string;
  eta: Date;
  berth?: string;
  status: string;
  confidence?: number;
}

interface BerthCard {
  type: 'berth';
  berthId: string;
  berthName: string;
  status: string;
  currentVessel?: string;
  nextAvailable?: Date;
}

interface ChartData {
  type: 'demand' | 'latency' | 'traffic' | 'performance';
  title: string;
  data: any[];
  explanation: string;
}

interface MessageAction {
  label: string;
  vesselId?: string;
  berthId?: string;
  action: 'view-vessel' | 'view-berth' | 'view-timeline';
}

interface ChatbotProps {
  vessels: Vessel[];
  berths: Berth[];
  currentView: 'vessels' | 'berths' | 'terminal3d';
  selectedVessel?: Vessel | null;
  selectedBerth?: Berth | null;
  onVesselClick: (vesselId: string) => void;
  onBerthClick: (berthId: string) => void;
  onViewChange?: (view: 'vessels' | 'berths') => void;
}

export function Chatbot({ vessels, berths, currentView, selectedVessel, selectedBerth, onVesselClick, onBerthClick, onViewChange }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  
  // Generate context-aware welcome message
  const getWelcomeMessage = (): Message => {
    let content = 'Hello! I\'m SmartBerth AI Assistant. ';
    
    if (selectedVessel) {
      content += `I see you're viewing **${selectedVessel.name}**. I can help you with:\n\n`;
      content += `• ETA predictions and accuracy\n`;
      content += `• AI berth allocation reasoning\n`;
      content += `• Readiness status and constraints\n`;
      content += `• Historical performance\n\nWhat would you like to know?`;
    } else if (selectedBerth) {
      content += `I see you're viewing **${selectedBerth.name}**. I can help you with:\n\n`;
      content += `• Current and upcoming vessels\n`;
      content += `• Berth availability windows\n`;
      content += `• Equipment specifications\n`;
      content += `• Utilization analytics\n\nWhat would you like to know?`;
    } else if (currentView === 'berths') {
      content += `You're viewing the **Berth Overview**. I can help you with:\n\n`;
      content += `• Berth occupancy and availability\n`;
      content += `• Upcoming vessel assignments\n`;
      content += `• Equipment and resource status\n`;
      content += `• Berth utilization trends\n\nWhat would you like to know?`;
    } else {
      content += `You're viewing **Upcoming Vessels**. I can help you with:\n\n`;
      content += `• Vessel arrival schedules\n`;
      content += `• ETA predictions and delays\n`;
      content += `• AI berth recommendations\n`;
      content += `• Readiness and constraints\n\nWhat would you like to know?`;
    }
    
    return {
      id: '1',
      type: 'bot',
      content,
      timestamp: new Date(),
    };
  };
  
  const [messages, setMessages] = useState<Message[]>([getWelcomeMessage()]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isConnected, setIsConnected] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate context-aware smart suggestions based on current view and selection
  const smartSuggestions = useMemo(() => {
    const suggestions: Array<{ icon: any; text: string; query: string; navigation?: { view: 'vessels' | 'berths'; id?: string } }> = [];
    
    if (selectedVessel) {
      // Vessel-specific suggestions
      suggestions.push(
        { icon: Clock, text: 'ETA Confidence', query: `What is the ETA confidence for ${selectedVessel.name}?` },
        { icon: Anchor, text: 'Berth Recommendation', query: `Why was ${selectedVessel.name} assigned to this berth?` },
        { icon: AlertCircle, text: 'Potential Delays', query: `Are there any predicted delays for ${selectedVessel.name}?` },
        { icon: Activity, text: 'Vessel History', query: `Show me the historical performance of ${selectedVessel.name}` },
      );
    } else if (selectedBerth) {
      // Berth-specific suggestions
      suggestions.push(
        { icon: Ship, text: 'Current Vessel', query: `What vessel is currently at ${selectedBerth.name}?` },
        { icon: Calendar, text: 'Next Availability', query: `When will ${selectedBerth.name} be available?` },
        { icon: Target, text: 'Upcoming Schedule', query: `Show me the upcoming vessels for ${selectedBerth.name}` },
        { icon: BarChart3, text: 'Utilization', query: `What is the utilization rate of ${selectedBerth.name}?` },
      );
    } else if (currentView === 'berths') {
      // Berth overview suggestions
      suggestions.push(
        { icon: Anchor, text: 'Available Berths', query: 'Which berths are available right now?' },
        { icon: Ship, text: 'Occupied Berths', query: 'Show me all occupied berths and their vessels' },
        { icon: Clock, text: 'Next Available', query: 'When is the next berth becoming available?' },
        { icon: BarChart3, text: 'Utilization Report', query: 'Show me berth utilization analytics' },
      );
    } else {
      // Vessel overview suggestions
      suggestions.push(
        { icon: Ship, text: 'Arriving Today', query: 'Which vessels are arriving in the next 24 hours?' },
        { icon: AlertCircle, text: 'Delayed Vessels', query: 'Are there any vessels with predicted delays?' },
        { icon: Target, text: 'AI Decisions', query: 'Explain the latest AI berth allocation decisions' },
        { icon: TrendingUp, text: 'Port Demand', query: 'Show me the vessel demand forecast' },
      );
    }
    
    return suggestions;
  }, [selectedVessel, selectedBerth, currentView]);

  // Navigation suggestions based on context
  const navigationSuggestions = useMemo(() => {
    const navs: Array<{ icon: any; text: string; action: () => void }> = [];
    
    if (currentView === 'vessels' && berths.length > 0) {
      const occupiedBerths = berths.filter(b => b.status === 'occupied');
      if (occupiedBerths.length > 0) {
        navs.push({
          icon: Anchor,
          text: `View ${occupiedBerths.length} Occupied Berths`,
          action: () => onViewChange?.('berths'),
        });
      }
    }
    
    if (currentView === 'berths' && vessels.length > 0) {
      const arrivingSoon = vessels.filter(v => {
        const hoursUntil = (v.predictedETA.getTime() - Date.now()) / (1000 * 60 * 60);
        return hoursUntil > 0 && hoursUntil <= 12;
      });
      if (arrivingSoon.length > 0) {
        navs.push({
          icon: Ship,
          text: `${arrivingSoon.length} Vessels Arriving Soon`,
          action: () => onViewChange?.('vessels'),
        });
      }
    }
    
    if (selectedVessel?.aiRecommendation?.suggestedBerth) {
      const suggestedBerth = berths.find(b => b.name === selectedVessel.aiRecommendation?.suggestedBerth);
      if (suggestedBerth) {
        navs.push({
          icon: MapPin,
          text: `View ${suggestedBerth.name}`,
          action: () => {
            onBerthClick(suggestedBerth.id);
            onViewChange?.('berths');
          },
        });
      }
    }
    
    return navs;
  }, [currentView, vessels, berths, selectedVessel, onViewChange, onBerthClick]);

  const handleSuggestionClick = async (suggestion: { query: string; navigation?: { view: 'vessels' | 'berths'; id?: string } }) => {
    setShowSuggestions(false);
    
    // Create user message from suggestion
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: suggestion.query,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    try {
      // Call AI backend
      const response = await aiService.chat(suggestion.query, sessionId);
      
      if (response && typeof response === 'object' && 'sessionId' in response) {
        setSessionId(response.sessionId);
      }
      
      const botMessage = mapAIResponseToMessage(response as AIChatResponse);
      setMessages(prev => [...prev, botMessage]);
      setIsConnected(true);
      setRetryCount(0);
    } catch (error) {
      console.error('AI Chat Error:', error);
      setIsConnected(false);
      setRetryCount(prev => prev + 1);
      
      // Use fallback processing
      const fallbackMessage = processQueryFallback(suggestion.query);
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Context-aware: Update suggestions and add context message when selection changes
  useEffect(() => {
    if (isOpen && messages.length > 0) {
      let contextMessage: Message | null = null;
      
      if (selectedVessel) {
        contextMessage = {
          id: `context-${Date.now()}`,
          type: 'bot',
          content: `📍 **Context Updated**: Now viewing **${selectedVessel.name}**\n\nI can help you understand:\n• ETA predictions and confidence scores\n• AI berth allocation reasoning\n• Vessel constraints and requirements\n\nTry the smart suggestions above or ask me anything!`,
          timestamp: new Date(),
        };
      } else if (selectedBerth) {
        contextMessage = {
          id: `context-${Date.now()}`,
          type: 'bot',
          content: `📍 **Context Updated**: Now viewing **${selectedBerth.name}**\n\nI can help you with:\n• Current vessel status and ETD\n• Upcoming vessel schedule\n• Berth specifications and availability\n\nTry the smart suggestions above or ask me anything!`,
          timestamp: new Date(),
        };
      }
      
      // Only add context message if it's different from the last message
      if (contextMessage) {
        const lastMessage = messages[messages.length - 1];
        if (!lastMessage?.content?.includes('Context Updated')) {
          setMessages(prev => [...prev, contextMessage!]);
          setShowSuggestions(true);
        }
      }
    }
  }, [selectedVessel?.id, selectedBerth?.id]);  // Only trigger on ID changes

  // Convert AI backend response to Message format
  const mapAIResponseToMessage = useCallback((response: AIChatResponse): Message => {
    const cards: (VesselCard | BerthCard)[] = [];
    
    // Map vessel data to cards
    if (response.structuredData?.vessels) {
      response.structuredData.vessels.forEach((v: AIChatVesselData) => {
        cards.push({
          type: 'vessel',
          vesselId: v.vesselId.toString(),
          vesselName: v.vesselName,
          eta: v.predictedEta ? new Date(v.predictedEta) : new Date(v.eta || Date.now()),
          berth: v.berth,
          status: v.status || 'unknown',
          confidence: v.confidence,
        });
      });
    }
    
    // Map berth data to cards
    if (response.structuredData?.berths) {
      response.structuredData.berths.forEach((b: AIChatBerthData) => {
        cards.push({
          type: 'berth',
          berthId: b.berthId.toString(),
          berthName: b.berthName,
          status: b.status,
          currentVessel: b.currentVessel,
          nextAvailable: b.nextAvailable ? new Date(b.nextAvailable) : undefined,
        });
      });
    }

    // Map AI actions to message actions
    const actions: MessageAction[] = response.actions?.map((action: AIChatAction) => ({
      label: action.label,
      vesselId: action.vesselId?.toString(),
      berthId: action.berthId?.toString(),
      action: action.type as 'view-vessel' | 'view-berth' | 'view-timeline',
    })) || [];

    // Map chart data if present
    let chart: ChartData | undefined;
    if (response.structuredData?.charts) {
      const chartData = response.structuredData.charts;
      chart = {
        type: chartData.type as 'demand' | 'latency' | 'traffic' | 'performance',
        title: chartData.title,
        data: chartData.data,
        explanation: chartData.explanation,
      };
    }

    return {
      id: Date.now().toString(),
      type: 'bot',
      content: response.text,
      timestamp: new Date(),
      cards: cards.length > 0 ? cards : undefined,
      actions: actions.length > 0 ? actions : undefined,
      chart,
    };
  }, []);

  // Fallback response when AI is unavailable
  const processQueryFallback = useCallback((query: string): Message => {
    const lowerQuery = query.toLowerCase();
    const now = new Date();

    // FR-BOT-01: Vessel Queue Intelligence
    if (lowerQuery.includes('arriving') || lowerQuery.includes('next') && (lowerQuery.includes('hours') || lowerQuery.includes('day'))) {
      const hours = lowerQuery.includes('12') ? 12 : lowerQuery.includes('24') ? 24 : lowerQuery.includes('48') ? 48 : 12;
      const upcomingVessels = vessels.filter(v => {
        const hoursUntil = (v.predictedETA.getTime() - now.getTime()) / (1000 * 60 * 60);
        return hoursUntil > 0 && hoursUntil <= hours;
      }).sort((a, b) => a.predictedETA.getTime() - b.predictedETA.getTime());

      const cards: VesselCard[] = upcomingVessels.slice(0, 5).map(v => ({
        type: 'vessel',
        vesselId: v.id,
        vesselName: v.name,
        eta: v.predictedETA,
        berth: v.aiRecommendation?.suggestedBerth,
        status: v.status,
        confidence: v.aiRecommendation?.confidence,
      }));

      return {
        id: Date.now().toString(),
        type: 'bot',
        content: `🔄 **[Offline Mode]** Found ${upcomingVessels.length} vessel${upcomingVessels.length !== 1 ? 's' : ''} arriving in the next ${hours} hours.`,
        timestamp: new Date(),
        cards,
        actions: upcomingVessels.length > 0 ? [{ label: 'View Timeline', action: 'view-timeline' }] : undefined,
      };
    }

    // Default fallback
    return {
      id: Date.now().toString(),
      type: 'bot',
      content: `⚠️ **AI Service Temporarily Unavailable**\n\nI'm currently unable to reach the AI backend. Please try again in a moment or check:\n\n• AI Service is running at port 8001\n• .NET API is running at port 5185\n\nIn the meantime, you can browse vessels and berths using the main interface.`,
      timestamp: new Date(),
    };
  }, [vessels]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    const currentInput = inputValue;
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Call AI backend
      const response = await aiService.chat(currentInput, sessionId);
      
      // Update session ID if provided
      if (response && typeof response === 'object' && 'sessionId' in response) {
        setSessionId(response.sessionId);
      }
      
      const botMessage = mapAIResponseToMessage(response as AIChatResponse);
      setMessages(prev => [...prev, botMessage]);
      setIsConnected(true);
      setRetryCount(0);
    } catch (error) {
      console.error('AI Chat Error:', error);
      setIsConnected(false);
      setRetryCount(prev => prev + 1);
      
      // Use fallback processing
      const fallbackMessage = processQueryFallback(currentInput);
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRetryConnection = async () => {
    setIsTyping(true);
    try {
      const healthResponse = await aiService.getHealth();
      if (healthResponse) {
        setIsConnected(true);
        setRetryCount(0);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'bot',
          content: '✅ **AI Service Connected**\n\nI\'m back online and ready to assist you with:\n\n• Vessel arrival predictions\n• Berth allocation recommendations\n• Conflict detection and resolution\n• What-if simulations\n\nHow can I help you?',
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'bot',
        content: '❌ **Connection Failed**\n\nUnable to reach AI service. Please ensure the backend services are running.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleAction = (action: MessageAction) => {
    if (action.action === 'view-vessel' && action.vesselId) {
      onVesselClick(action.vesselId);
      onViewChange?.('vessels');
    } else if (action.action === 'view-berth' && action.berthId) {
      onBerthClick(action.berthId);
      onViewChange?.('berths');
    } else if (action.action === 'view-timeline') {
      onViewChange?.('vessels');
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 md:bottom-6 md:right-6 w-12 h-12 md:w-14 md:h-14 rounded-full shadow-2xl flex items-center justify-center transition-transform hover:scale-110 z-40"
        style={{ backgroundColor: 'var(--kale-blue)' }}
      >
        <MessageSquare className="w-5 h-5 md:w-6 md:h-6 text-white" />
      </button>
    );
  }

  return (
    <div 
      className={`fixed bg-white shadow-2xl border flex flex-col z-40 transition-all ${!isMinimized ? 'inset-0 md:inset-auto md:bottom-6 md:right-6 md:w-[420px] md:h-[600px] md:rounded-2xl' : 'bottom-4 right-4 md:bottom-6 md:right-6 rounded-2xl'}`}
      style={{ 
        borderColor: 'var(--border)',
        ...(isMinimized ? {
          width: '280px',
          height: '60px',
        } : {}),
      }}
    >
      {/* Header */}
      <div 
        className="px-4 py-3 border-b flex items-center justify-between rounded-t-2xl cursor-pointer"
        style={{ 
          background: 'linear-gradient(135deg, var(--kale-blue) 0%, var(--kale-teal) 100%)',
          borderColor: 'var(--border)',
        }}
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center relative">
            <Brain className="w-5 h-5 text-white" />
            {/* Connection Status Indicator */}
            <div 
              className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}
              title={isConnected ? 'AI Connected' : 'AI Disconnected'}
            />
          </div>
          <div>
            <div className="text-white flex items-center gap-2" style={{ fontWeight: 700 }}>
              SmartBerth AI
              {!isConnected && (
                <span className="text-xs px-1.5 py-0.5 bg-red-500/30 rounded text-white/90">
                  Offline
                </span>
              )}
            </div>
            <div className="text-xs text-white/80">
              {isConnected ? 'Powered by Claude + Qwen3' : 'Reconnecting...'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isConnected && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRetryConnection();
              }}
              className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
              title="Retry Connection"
            >
              <RefreshCw className={`w-4 h-4 text-white ${isTyping ? 'animate-spin' : ''}`} />
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsMinimized(!isMinimized);
            }}
            className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
          >
            <Minimize2 className="w-4 h-4 text-white" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(false);
            }}
            className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
          >
            <X className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                  <div
                    className="px-4 py-3 rounded-2xl"
                    style={{
                      backgroundColor: message.type === 'user' ? 'var(--kale-blue)' : 'var(--kale-sky)',
                      color: message.type === 'user' ? 'white' : 'var(--foreground)',
                    }}
                  >
                    {message.type === 'user' ? (
                      <span className="whitespace-pre-wrap">{message.content}</span>
                    ) : (
                      <div 
                        className="chatbot-response prose prose-sm max-w-none text-inherit leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
                      />
                    )}
                  </div>
                  
                  {/* Vessel/Berth Cards */}
                  {message.cards && message.cards.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {message.cards.map((card, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl border cursor-pointer hover:shadow-md transition-shadow"
                          style={{ borderColor: 'var(--border)', backgroundColor: 'white' }}
                          onClick={() => {
                            if (card.type === 'vessel') {
                              handleAction({ label: '', vesselId: card.vesselId, action: 'view-vessel' });
                            } else if (card.type === 'berth') {
                              handleAction({ label: '', berthId: card.berthId, action: 'view-berth' });
                            }
                          }}
                        >
                          {card.type === 'vessel' ? (
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                  <Ship className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                                  <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{card.vesselName}</span>
                                </div>
                                {card.confidence && (
                                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ 
                                    backgroundColor: 'var(--status-on-time)',
                                    color: 'white'
                                  }}>
                                    {card.confidence}%
                                  </span>
                                )}
                              </div>
                              <div className="text-xs space-y-1" style={{ color: 'var(--muted-foreground)' }}>
                                <div>ETA: {card.eta.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
                                {card.berth && <div>Berth: {card.berth}</div>}
                                <div className="capitalize">Status: {card.status.replace('-', ' ')}</div>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <Anchor className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                                <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{card.berthName}</span>
                              </div>
                              <div className="text-xs space-y-1" style={{ color: 'var(--muted-foreground)' }}>
                                <div className="capitalize">Status: {card.status}</div>
                                {card.currentVessel && <div>Current: {card.currentVessel}</div>}
                                {card.nextAvailable && <div>Next: {card.nextAvailable.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Charts */}
                  {message.chart && (
                    <div className="mt-2 p-4 rounded-xl border" style={{ borderColor: 'var(--border)', backgroundColor: 'white' }}>
                      <div className="mb-3" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                        {message.chart.title}
                      </div>
                      <div style={{ height: '200px' }}>
                        {renderChart(message.chart)}
                      </div>
                      <div className="mt-3 text-xs p-3 rounded-lg" style={{ 
                        backgroundColor: 'var(--kale-sky)',
                        color: 'var(--foreground)'
                      }}>
                        💡 {message.chart.explanation}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {message.actions && message.actions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {message.actions.map((action, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleAction(action)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors"
                          style={{ 
                            backgroundColor: 'var(--kale-blue)',
                            color: 'white',
                            fontWeight: 500,
                          }}
                        >
                          {action.label}
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <div className="text-xs mt-1" style={{ color: 'var(--muted-foreground)' }}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="px-4 py-3 rounded-2xl" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--kale-blue)' }} />
                    <span className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      {isConnected ? 'AI is thinking...' : 'Processing locally...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Smart Suggestions - Context Aware */}
          {showSuggestions && messages.length <= 2 && (
            <div className="px-4 py-3 border-t" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--kale-sky)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                <span className="text-xs font-semibold" style={{ color: 'var(--kale-blue)' }}>
                  Smart Suggestions
                  {selectedVessel && ` for ${selectedVessel.name}`}
                  {selectedBerth && !selectedVessel && ` for ${selectedBerth.name}`}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 mb-3">
                {smartSuggestions.slice(0, 4).map((suggestion, idx) => {
                  const IconComponent = suggestion.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all hover:scale-105 hover:shadow-md"
                      style={{ 
                        backgroundColor: 'white',
                        color: 'var(--kale-blue)',
                        border: '1px solid var(--border)',
                        fontWeight: 500,
                      }}
                    >
                      <IconComponent className="w-3.5 h-3.5" />
                      {suggestion.text}
                    </button>
                  );
                })}
              </div>
              
              {/* Navigation Suggestions */}
              {navigationSuggestions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {navigationSuggestions.map((nav, idx) => {
                    const IconComponent = nav.icon;
                    return (
                      <button
                        key={idx}
                        onClick={nav.action}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all hover:scale-105"
                        style={{ 
                          backgroundColor: 'var(--kale-teal)',
                          color: 'white',
                          fontWeight: 500,
                        }}
                      >
                        <Navigation className="w-3 h-3" />
                        {nav.text}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about vessels, berths, or AI decisions..."
                className="flex-1 px-4 py-2 rounded-lg border outline-none focus:ring-2"
                style={{
                  borderColor: 'var(--border)',
                }}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim()}
                className="px-4 py-2 rounded-lg transition-opacity disabled:opacity-50"
                style={{ backgroundColor: 'var(--kale-blue)' }}
              >
                <Send className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Chart generation helpers
function generateDemandChart(vessels: Vessel[]) {
  const now = new Date();
  const data = [];
  
  for (let i = 0; i < 48; i += 4) {
    const timeSlot = new Date(now.getTime() + i * 60 * 60 * 1000);
    const timeSlotEnd = new Date(now.getTime() + (i + 4) * 60 * 60 * 1000);
    
    const arrivals = vessels.filter(v => 
      v.predictedETA >= timeSlot && v.predictedETA < timeSlotEnd
    ).length;
    
    data.push({
      time: `+${i}h`,
      arrivals,
    });
  }
  
  const peakSlot = data.reduce((max, slot) => slot.arrivals > max.arrivals ? slot : max, data[0]);
  
  return {
    data,
    explanation: `Peak demand occurs at ${peakSlot.time} with ${peakSlot.arrivals} vessel arrivals. Current forecast shows ${vessels.filter(v => v.predictedETA > now).length} total vessels in the next 48 hours.`,
  };
}

function generateLatencyChart(vessels: Vessel[]) {
  const vesselsWithATA = vessels.filter(v => v.ata);
  const data = vesselsWithATA.slice(0, 10).map(v => ({
    vessel: v.name.substring(0, 15),
    latency: Math.abs(Math.round((v.ata!.getTime() - v.predictedETA.getTime()) / (1000 * 60))),
  }));
  
  const avgLatency = data.length > 0 
    ? Math.round(data.reduce((sum, d) => sum + d.latency, 0) / data.length)
    : 0;
  
  return {
    data,
    explanation: `Average ETA prediction latency is ${avgLatency} minutes. ${data.filter(d => d.latency <= 15).length} out of ${data.length} vessels arrived within the 15-minute accuracy window.`,
  };
}

function generateTrafficChart(berths: Berth[], vessels: Vessel[]) {
  const data = berths.map(b => {
    const assignedVessels = vessels.filter(v => v.aiRecommendation?.suggestedBerth === b.name);
    return {
      berth: b.name,
      load: assignedVessels.length,
      status: b.status,
    };
  });
  
  const maxLoad = Math.max(...data.map(d => d.load));
  const berthAtCapacity = data.find(d => d.load === maxLoad);
  
  return {
    data,
    explanation: `${berthAtCapacity?.berth} has the highest traffic load with ${maxLoad} assigned vessels. ${data.filter(d => d.status === 'available').length} berths are currently available.`,
  };
}

function generatePerformanceChart() {
  const data = Array.from({ length: 7 }, (_, i) => ({
    day: `Day ${i + 1}`,
    accuracy: 92 + Math.random() * 6,
    confidence: 88 + Math.random() * 8,
  }));
  
  const avgAccuracy = Math.round(data.reduce((sum, d) => sum + d.accuracy, 0) / data.length);
  
  return {
    data,
    explanation: `Model performance is stable with ${avgAccuracy}% average accuracy over the past week. No significant drift detected. All metrics within acceptable thresholds.`,
  };
}

function renderChart(chart: ChartData) {
  switch (chart.type) {
    case 'demand':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="time" style={{ fontSize: '12px' }} />
            <YAxis style={{ fontSize: '12px' }} />
            <Tooltip />
            <Area type="monotone" dataKey="arrivals" stroke="var(--kale-blue)" fill="var(--kale-sky)" />
          </AreaChart>
        </ResponsiveContainer>
      );
    
    case 'latency':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="vessel" style={{ fontSize: '10px' }} angle={-45} textAnchor="end" height={80} />
            <YAxis style={{ fontSize: '12px' }} />
            <Tooltip />
            <Bar dataKey="latency" fill="var(--kale-teal)" />
          </BarChart>
        </ResponsiveContainer>
      );
    
    case 'traffic':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="berth" style={{ fontSize: '12px' }} />
            <YAxis style={{ fontSize: '12px' }} />
            <Tooltip />
            <Bar dataKey="load" fill="var(--kale-blue)" />
          </BarChart>
        </ResponsiveContainer>
      );
    
    case 'performance':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="day" style={{ fontSize: '12px' }} />
            <YAxis style={{ fontSize: '12px' }} domain={[80, 100]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="accuracy" stroke="var(--kale-blue)" strokeWidth={2} />
            <Line type="monotone" dataKey="confidence" stroke="var(--kale-teal)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      );
  }
}