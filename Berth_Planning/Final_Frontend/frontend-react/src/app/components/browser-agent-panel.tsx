import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  X, Play, Square, RefreshCw, Monitor, Bot, Brain, 
  ChevronRight, ChevronDown, Eye, MousePointer, 
  Navigation, Type, Scroll, CheckCircle2, XCircle,
  Clock, AlertTriangle, Loader2, Maximize2, Minimize2,
  Globe, Camera, List, Database, Cpu, Search, Zap
} from 'lucide-react';

// Agent Types
interface AgentStep {
  step_number: number;
  action: string | null;
  action_details?: {
    selector?: string;
    value?: string;
    url?: string;
  };
  reasoning: string;
  success: boolean | null;
  error?: string;
  timestamp: string;
}

// Tool call interface for internal backend calls
interface ToolCall {
  tool_name: string;
  parameters: Record<string, unknown>;
  result: unknown;
  status: 'running' | 'success' | 'error';
  timestamp: string;
  execution_time?: number;
}

interface AgentStatus {
  available: boolean;
  running: boolean;
  current_task: string | null;
  state: string | null;
  steps_completed: number;
  errors: number;
  tools_available?: boolean;
  tool_count?: number;
  tool_calls_this_session?: number;
}

interface WebSocketMessage {
  type: 'connected' | 'step' | 'state' | 'screenshot' | 'stopped' | 'error' | 'status' | 'pong' | 'tool_call' | 'completed';
  task_id?: string;
  status?: AgentStatus;
  step_number?: number;
  action?: string;
  action_details?: {
    selector?: string;
    value?: string;
    url?: string;
  };
  reasoning?: string;
  success?: boolean;
  error?: string;
  state?: string;
  data?: string; // base64 screenshot
  timestamp?: string;
  // Tool call specific
  tool_name?: string;
  parameters?: Record<string, unknown>;
  result?: unknown;
  execution_time_ms?: number;
  // Completion specific
  final_summary?: string;
  summary?: string;
  model_used?: string;
  pages_visited?: string[];
  steps?: number;
  tool_calls_count?: number;
}

// Get icon for tool type
const ToolIcon = ({ tool }: { tool: string }) => {
  if (!tool) return <Zap className="w-4 h-4 text-gray-400" />;
  if (tool.startsWith('db_')) {
    return <Database className="w-4 h-4 text-blue-400" />;
  } else if (tool.startsWith('ml_')) {
    return <Cpu className="w-4 h-4 text-purple-400" />;
  } else if (tool.startsWith('rag_')) {
    return <Search className="w-4 h-4 text-green-400" />;
  } else if (tool.startsWith('manager_')) {
    return <Brain className="w-4 h-4 text-yellow-400" />;
  } else if (tool.startsWith('system_')) {
    return <Zap className="w-4 h-4 text-orange-400" />;
  }
  return <Bot className="w-4 h-4 text-gray-400" />;
};

// Action icon mapping
const ActionIcon = ({ action }: { action: string | null }) => {
  switch (action) {
    case 'NAVIGATE':
      return <Navigation className="w-4 h-4 text-blue-400" />;
    case 'CLICK':
      return <MousePointer className="w-4 h-4 text-green-400" />;
    case 'TYPE':
      return <Type className="w-4 h-4 text-purple-400" />;
    case 'SCROLL_DOWN':
    case 'SCROLL_UP':
      return <Scroll className="w-4 h-4 text-orange-400" />;
    case 'READ_PAGE':
      return <Eye className="w-4 h-4 text-cyan-400" />;
    case 'SCREENSHOT':
      return <Camera className="w-4 h-4 text-pink-400" />;
    case 'COMPLETE':
      return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    case 'FAIL':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'TOOL_CALL':
      return <Database className="w-4 h-4 text-blue-400" />;
    default:
      return <Bot className="w-4 h-4 text-gray-400" />;
  }
};

// State badge component
const StateBadge = ({ state }: { state: string | null }) => {
  const stateConfig: Record<string, { color: string; label: string }> = {
    idle: { color: 'bg-gray-500', label: 'Idle' },
    thinking: { color: 'bg-yellow-500 animate-pulse', label: 'Thinking...' },
    acting: { color: 'bg-blue-500 animate-pulse', label: 'Acting...' },
    observing: { color: 'bg-cyan-500', label: 'Observing' },
    waiting: { color: 'bg-orange-500', label: 'Waiting' },
    completed: { color: 'bg-green-500', label: 'Completed' },
    failed: { color: 'bg-red-500', label: 'Failed' },
    paused: { color: 'bg-gray-400', label: 'Paused' },
  };

  const config = stateConfig[state || 'idle'] || stateConfig.idle;

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${config.color}`}>
      {config.label}
    </span>
  );
};

export function BrowserAgentPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Agent state
  const [status, setStatus] = useState<AgentStatus>({
    available: false,
    running: false,
    current_task: null,
    state: 'idle',
    steps_completed: 0,
    errors: 0,
    tools_available: false,
    tool_count: 0,
    tool_calls_this_session: 0,
  });
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [currentScreenshot, setCurrentScreenshot] = useState<string | null>(null);
  const [finalSummary, setFinalSummary] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);
  const [taskInput, setTaskInput] = useState('');
  // Default to the SmartBerth prototype URL instead of external sites
  const [urlInput, setUrlInput] = useState(window.location.origin);
  const [isConnecting, setIsConnecting] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [showScreenshot, setShowScreenshot] = useState(true);
  const [showToolCalls, setShowToolCalls] = useState(true);
  const [controlMyBrowser, setControlMyBrowser] = useState(true); // CDP mode - control user's actual browser
  
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  const stepsContainerRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    setIsConnecting(true);
    
    // Use relative path - vite proxy will handle the routing
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/agent/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnecting(false);
      setWsConnected(true);
      console.log('Browser Agent WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      setIsConnecting(false);
      console.log('Browser Agent WebSocket disconnected');
      
      // Attempt reconnect after 3 seconds if panel is open
      if (isOpen) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error('Browser Agent WebSocket error:', error);
      setIsConnecting(false);
    };

    wsRef.current = ws;
  }, [isOpen]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        if (message.status) {
          setStatus(message.status);
        }
        break;
        
      case 'step':
        const newStep: AgentStep = {
          step_number: message.step_number || 0,
          action: message.action || null,
          action_details: message.action_details,
          reasoning: message.reasoning || '',
          success: message.success ?? null,
          error: message.error,
          timestamp: message.timestamp || new Date().toISOString(),
        };
        setSteps(prev => [...prev, newStep]);
        setStatus(prev => ({
          ...prev,
          steps_completed: message.step_number || prev.steps_completed,
          errors: message.success === false ? prev.errors + 1 : prev.errors,
        }));
        break;
        
      case 'state':
        setStatus(prev => ({
          ...prev,
          state: message.state || prev.state,
          running: !['idle', 'completed', 'failed'].includes(message.state || ''),
        }));
        break;
        
      case 'screenshot':
        if (message.data) {
          setCurrentScreenshot(message.data);
        }
        break;
        
      case 'stopped':
        setStatus(prev => ({
          ...prev,
          running: false,
          state: 'idle',
        }));
        break;
      
      case 'completed':
        // Task completed - show final summary
        setFinalSummary(message.final_summary || message.summary || 'Task completed successfully.');
        setModelUsed(message.model_used || null);
        // Capture final full-screen screenshot if available
        if (message.final_screenshot) {
          setCurrentScreenshot(message.final_screenshot);
          setShowScreenshot(true); // Auto-show the final screenshot
        }
        setStatus(prev => ({
          ...prev,
          running: false,
          state: 'completed',
          steps_completed: message.steps || prev.steps_completed,
        }));
        // Add completion step to timeline
        const completionStep: AgentStep = {
          step_number: steps.length + 1,
          action: 'COMPLETE',
          reasoning: message.final_summary || message.summary || 'Task completed',
          success: message.success ?? true,
          timestamp: message.timestamp || new Date().toISOString(),
        };
        setSteps(prev => [...prev, completionStep]);
        break;
        
      case 'error':
        console.error('Agent error:', message.error);
        setStatus(prev => ({
          ...prev,
          running: false,
          state: 'failed',
          errors: prev.errors + 1,
        }));
        break;
        
      case 'status':
        if (message.status) {
          setStatus(message.status);
        }
        break;
        
      case 'tool_call':
        // Handle internal tool calls (database, ML, RAG, etc.)
        const toolCallStatus = (message as { status?: string }).status;
        const newToolCall: ToolCall = {
          tool_name: message.tool_name || 'unknown',
          parameters: message.parameters || {},
          result: message.result,
          status: (toolCallStatus === 'success' || toolCallStatus === 'error' || toolCallStatus === 'running') 
            ? toolCallStatus 
            : (message.success ? 'success' : 'error'),
          timestamp: message.timestamp || new Date().toISOString(),
          execution_time: message.execution_time_ms,
        };
        setToolCalls(prev => [...prev, newToolCall]);
        setStatus(prev => ({
          ...prev,
          tool_calls_this_session: (prev.tool_calls_this_session || 0) + 1,
        }));
        
        // Generate summary for step
        const resultSummary = typeof message.result === 'string' 
          ? message.result.slice(0, 100) 
          : (message.result && typeof message.result === 'object' 
              ? (Array.isArray(message.result) ? `${message.result.length} items` : 'result')
              : 'done');
        
        // Also add as a step for timeline
        const toolStep: AgentStep = {
          step_number: steps.length + 1,
          action: 'TOOL_CALL',
          action_details: {
            selector: message.tool_name,
            value: JSON.stringify(message.parameters || {}),
          },
          reasoning: `Called ${message.tool_name}: ${resultSummary}`,
          success: newToolCall.status === 'success',
          timestamp: message.timestamp || new Date().toISOString(),
        };
        setSteps(prev => [...prev, toolStep]);
        break;
    }
  }, [steps.length]);

  // Auto-scroll steps container
  useEffect(() => {
    if (stepsContainerRef.current) {
      stepsContainerRef.current.scrollTop = stepsContainerRef.current.scrollHeight;
    }
  }, [steps]);

  // Connect WebSocket when panel opens
  useEffect(() => {
    if (isOpen && !wsRef.current) {
      connectWebSocket();
    }
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [isOpen, connectWebSocket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Start a new task
  const startTask = async () => {
    if (!taskInput.trim() || status.running) return;
    
    try {
      // Clear previous steps, tool calls, and summary
      setSteps([]);
      setToolCalls([]);
      setCurrentScreenshot(null);
      setFinalSummary(null);
      setModelUsed(null);
      
      // Enhance task with SmartBerth prototype context
      const enhancedTask = `You are navigating the SmartBerth Port Management Prototype at ${urlInput || window.location.origin}. 
The prototype has these main navigation tabs: Dashboard, Upcoming Vessels, Vessels Tracking, Berth Overview, Digital Twin, and Gantt Chart.
Your task: ${taskInput}
Navigate WITHIN this prototype to complete the task. You can visit MULTIPLE tabs/pages to gather information. Click on navigation tabs, explore the UI, and explain what you see.`;
      
      const response = await fetch('/agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: enhancedTask,
          start_url: controlMyBrowser ? '' : (urlInput || window.location.origin), // Don't navigate when controlling user's browser
          max_steps: 50,
          connect_to_chrome: controlMyBrowser, // Enable CDP mode to control user's actual browser
          cdp_endpoint: 'http://localhost:9222', // Default CDP endpoint
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        alert(`Failed to start task: ${error.detail || 'Unknown error'}`);
        return;
      }
      
      const result = await response.json();
      console.log('Task started:', result);
      
      setStatus(prev => ({
        ...prev,
        running: true,
        current_task: taskInput,
        state: 'thinking',
        steps_completed: 0,
        errors: 0,
      }));
      
    } catch (error) {
      console.error('Failed to start task:', error);
      alert('Failed to start task. Is the AI service running?');
    }
  };

  // Stop current task
  const stopTask = async () => {
    try {
      const response = await fetch('/agent/stop', { method: 'POST' });
      
      if (!response.ok) {
        const error = await response.json();
        console.error('Failed to stop task:', error);
      }
      
    } catch (error) {
      console.error('Failed to stop task:', error);
    }
  };

  // Fetch status
  const fetchStatus = async () => {
    try {
      const response = await fetch('/agent/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-24 right-6 z-50 p-4 bg-gradient-to-r from-purple-600 to-indigo-600 
                   text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 
                   transition-all duration-200 group"
        title="Browser Agent"
      >
        <Bot className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full 
                        border-2 border-white animate-pulse" />
      </button>
    );
  }

  // Minimized view
  if (isMinimized) {
    return (
      <div className="fixed bottom-24 right-6 z-50 bg-slate-800 rounded-lg shadow-xl p-3 
                     border border-slate-700 flex items-center gap-3">
        <Bot className="w-5 h-5 text-purple-400" />
        <span className="text-sm text-white font-medium">Browser Agent</span>
        <StateBadge state={status.state} />
        <button
          onClick={() => setIsMinimized(false)}
          className="p-1 hover:bg-slate-700 rounded"
          title="Expand panel"
        >
          <Maximize2 className="w-4 h-4 text-gray-400" />
        </button>
        <button
          onClick={() => setIsOpen(false)}
          className="p-1 hover:bg-slate-700 rounded"
          title="Close panel"
        >
          <X className="w-4 h-4 text-gray-400" />
        </button>
      </div>
    );
  }

  // Full panel
  return (
    <div 
      className={`fixed bottom-6 right-6 z-50 bg-slate-900 rounded-xl shadow-2xl 
                  border border-slate-700 flex flex-col transition-all duration-300
                  ${isExpanded ? 'w-[800px] h-[700px]' : 'w-[450px] h-[600px]'}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 
                     bg-gradient-to-r from-purple-900/50 to-indigo-900/50 rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Bot className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Browser Agent</h3>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
              {wsConnected ? 'Connected' : 'Disconnected'}
              {status.running && (
                <span className="ml-2">• Steps: {status.steps_completed}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? (
              <Minimize2 className="w-4 h-4 text-gray-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-400" />
            )}
          </button>
          <button
            onClick={() => setIsMinimized(true)}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            title="Minimize panel"
          >
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            title="Close panel"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 bg-slate-800/50 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <StateBadge state={status.state} />
          {status.current_task && (
            <span className="text-xs text-gray-400 truncate max-w-[200px]">
              {status.current_task}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>Errors: {status.errors}</span>
          <button
            onClick={fetchStatus}
            className="p-1 hover:bg-slate-700 rounded"
            title="Refresh status"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className={`flex-1 overflow-hidden flex ${isExpanded ? 'flex-row' : 'flex-col'}`}>
        {/* Steps Timeline / Tool Calls Panel */}
        <div className={`${isExpanded ? 'w-1/2 border-r border-slate-700' : 'flex-1'} 
                        overflow-hidden flex flex-col`}>
          {/* Tab Selector */}
          <div className="px-3 py-2 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowToolCalls(false)}
                className={`text-xs font-medium flex items-center gap-1 px-2 py-1 rounded transition-colors ${
                  !showToolCalls 
                    ? 'bg-purple-600/30 text-purple-300 border border-purple-500/50' 
                    : 'text-gray-400 hover:bg-slate-700'
                }`}
              >
                <List className="w-3 h-3" />
                Actions
                <span className="ml-1 text-xs opacity-70">({steps.length})</span>
              </button>
              <button
                onClick={() => setShowToolCalls(true)}
                className={`text-xs font-medium flex items-center gap-1 px-2 py-1 rounded transition-colors ${
                  showToolCalls 
                    ? 'bg-cyan-600/30 text-cyan-300 border border-cyan-500/50' 
                    : 'text-gray-400 hover:bg-slate-700'
                }`}
              >
                <Zap className="w-3 h-3" />
                Tools
                <span className="ml-1 text-xs opacity-70">({toolCalls.length})</span>
              </button>
            </div>
            {showToolCalls && toolCalls.length > 0 && (
              <span className="text-xs text-gray-500">
                {toolCalls.filter(t => t.status === 'success').length} succeeded
              </span>
            )}
          </div>
          
          {/* Conditional Content: Actions or Tools */}
          {!showToolCalls ? (
            // Actions Timeline
            <div 
              ref={stepsContainerRef}
              className="flex-1 overflow-y-auto p-3 space-y-2"
            >
              {steps.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Brain className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-sm">No actions yet</p>
                  <p className="text-xs">Start a task to see the agent in action</p>
                </div>
              ) : (
                steps.map((step, index) => (
                  <div 
                    key={index}
                    className={`p-3 rounded-lg border ${
                      step.success === false 
                        ? 'bg-red-900/20 border-red-800' 
                        : step.success === true
                          ? 'bg-green-900/20 border-green-800'
                          : 'bg-slate-800 border-slate-700'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="flex-shrink-0 mt-0.5">
                        <ActionIcon action={step.action} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono text-gray-500">
                            #{step.step_number}
                          </span>
                          <span className="text-sm font-medium text-white">
                            {step.action || 'Unknown'}
                          </span>
                          {step.success === true && (
                            <CheckCircle2 className="w-3 h-3 text-green-400" />
                          )}
                          {step.success === false && (
                            <XCircle className="w-3 h-3 text-red-400" />
                          )}
                        </div>
                        
                        {step.action_details && (
                          <div className="text-xs text-gray-400 mb-1 font-mono truncate">
                            {step.action_details.url && (
                              <span className="text-blue-400">{step.action_details.url}</span>
                            )}
                            {step.action_details.selector && (
                              <span className="text-purple-400">{step.action_details.selector}</span>
                            )}
                            {step.action_details.value && (
                              <span className="text-green-400">"{step.action_details.value}"</span>
                            )}
                          </div>
                        )}
                        
                        {step.reasoning && (
                          <p className="text-xs text-gray-400 line-clamp-2">
                            {step.reasoning}
                          </p>
                        )}
                        
                        {step.error && (
                          <p className="text-xs text-red-400 mt-1">
                            Error: {step.error}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {status.running && (
                <div className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                  <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                  <span className="text-sm text-gray-400">
                    {status.state === 'thinking' ? 'Deciding next action...' : 
                     status.state === 'acting' ? 'Executing action...' :
                     status.state === 'observing' ? 'Reading page...' : 'Processing...'}
                  </span>
                </div>
              )}
            </div>
          ) : (
            // Tool Calls View
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {toolCalls.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Zap className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-sm">No tool calls yet</p>
                  <p className="text-xs">Agent will use internal tools for complex queries</p>
                </div>
              ) : (
                toolCalls.map((tool, index) => (
                  <div 
                    key={index}
                    className={`p-3 rounded-lg border ${
                      tool.status === 'error' 
                        ? 'bg-red-900/20 border-red-800' 
                        : tool.status === 'success'
                          ? 'bg-cyan-900/20 border-cyan-800'
                          : 'bg-slate-800 border-slate-700'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="flex-shrink-0 mt-0.5">
                        <ToolIcon tool={tool.tool_name} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white font-mono">
                            {tool.tool_name}
                          </span>
                          {tool.status === 'success' && (
                            <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                          )}
                          {tool.status === 'error' && (
                            <XCircle className="w-3 h-3 text-red-400" />
                          )}
                          {tool.status === 'running' && (
                            <Loader2 className="w-3 h-3 text-yellow-400 animate-spin" />
                          )}
                          {tool.execution_time && (
                            <span className="text-xs text-gray-500">
                              {tool.execution_time}ms
                            </span>
                          )}
                        </div>
                        
                        {/* Tool Parameters */}
                        {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                          <div className="text-xs text-gray-400 mb-2 font-mono bg-slate-900/50 p-2 rounded">
                            {Object.entries(tool.parameters).slice(0, 3).map(([key, value]) => (
                              <div key={key} className="truncate">
                                <span className="text-purple-400">{key}</span>
                                <span className="text-gray-500">: </span>
                                <span className="text-green-400">
                                  {typeof value === 'string' ? `"${value}"` : JSON.stringify(value)}
                                </span>
                              </div>
                            ))}
                            {Object.keys(tool.parameters).length > 3 && (
                              <span className="text-gray-500">
                                +{Object.keys(tool.parameters).length - 3} more params
                              </span>
                            )}
                          </div>
                        )}
                        
                        {/* Tool Result Summary */}
                        {tool.result !== undefined && tool.result !== null && (
                          <div className="text-xs text-gray-400">
                            {tool.status === 'success' ? (
                              <span className="text-cyan-400">
                                {(() => {
                                  const r = tool.result;
                                  if (Array.isArray(r)) return `Returned ${r.length} items`;
                                  if (typeof r === 'object' && r !== null) {
                                    const obj = r as Record<string, unknown>;
                                    if (obj.summary) return String(obj.summary);
                                    return 'Success';
                                  }
                                  return String(r).substring(0, 100);
                                })()}
                              </span>
                            ) : (
                              <span className="text-red-400">
                                {(() => {
                                  const r = tool.result;
                                  if (typeof r === 'object' && r !== null) {
                                    const obj = r as Record<string, unknown>;
                                    if (obj.error) return String(obj.error);
                                  }
                                  return 'Execution failed';
                                })()}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Screenshot Preview (only in expanded mode) */}
        {isExpanded && (
          <div className="w-1/2 flex flex-col overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-700 flex items-center justify-between">
              <span className="text-xs font-medium text-gray-400 flex items-center gap-1">
                <Monitor className="w-3 h-3" />
                Live Preview
              </span>
              <button
                onClick={() => setShowScreenshot(!showScreenshot)}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                {showScreenshot ? 'Hide' : 'Show'}
              </button>
            </div>
            
            <div className="flex-1 overflow-hidden p-3">
              {currentScreenshot ? (
                <img
                  src={`data:image/png;base64,${currentScreenshot}`}
                  alt="Browser screenshot"
                  className="w-full h-full object-contain rounded-lg border border-slate-700"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-slate-800 rounded-lg border border-slate-700">
                  <div className="text-center text-gray-500">
                    <Camera className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No screenshot available</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Final Summary - Shown when task completes */}
      {finalSummary && status.state === 'completed' && (
        <div className="mx-4 mb-3 p-4 bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-700/50 rounded-xl">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 p-2 bg-green-500/20 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-green-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="text-sm font-semibold text-green-300">✨ Task Complete - Final Summary</h4>
                {modelUsed && (
                  <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                    {modelUsed.includes('qwen') ? '🚀 GPU Accelerated' : '☁️ Cloud'}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap mb-3">
                {finalSummary}
              </p>
              
              {/* Full-screen final screenshot */}
              {currentScreenshot && (
                <div className="mt-3 border border-green-700/30 rounded-lg overflow-hidden">
                  <div className="px-3 py-1.5 bg-green-900/30 border-b border-green-700/30 flex items-center gap-2">
                    <Monitor className="w-4 h-4 text-green-400" />
                    <span className="text-xs text-green-400 font-medium">Full Screen Capture - All Panels Expanded</span>
                  </div>
                  <img
                    src={`data:image/png;base64,${currentScreenshot}`}
                    alt="Final full-screen capture"
                    className="w-full h-auto rounded-b-lg cursor-zoom-in hover:opacity-90 transition-opacity"
                    onClick={() => {
                      // Open screenshot in new tab for full view
                      const newTab = window.open('');
                      if (newTab) {
                        newTab.document.write(`<img src="data:image/png;base64,${currentScreenshot}" style="max-width: 100%; height: auto;" />`);
                        newTab.document.title = 'SmartBerth - Browser Agent Screenshot';
                      }
                    }}
                  />
                </div>
              )}
              
              {modelUsed && (
                <p className="mt-2 text-xs text-gray-500">
                  Model: {modelUsed}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Task Input */}
      <div className="p-4 border-t border-slate-700 bg-slate-800/50">
        <div className="space-y-3">
          {/* Control Mode Toggle */}
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={controlMyBrowser}
                onChange={(e) => setControlMyBrowser(e.target.checked)}
                disabled={status.running}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-purple-500 
                          focus:ring-purple-500 focus:ring-offset-0 cursor-pointer"
              />
              <Monitor className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                Control my browser
              </span>
            </label>
            {controlMyBrowser && (
              <span className="text-xs text-yellow-500/80">
                ⚠️ Launch browser with --remote-debugging-port=9222
              </span>
            )}
          </div>
          
          {/* URL Input - Only show when NOT using CDP mode */}
          {!controlMyBrowser && (
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-gray-500 flex-shrink-0" />
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Starting URL (optional)"
                disabled={status.running}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 
                          text-sm text-white placeholder-gray-500 focus:outline-none 
                          focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
              />
            </div>
          )}
          
          {/* Task Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !status.running && startTask()}
              placeholder="Describe what you want the agent to do..."
              disabled={status.running}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 
                        text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                        focus:ring-purple-500 disabled:opacity-50"
            />
            
            {status.running ? (
              <button
                onClick={stopTask}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg 
                          font-medium transition-colors flex items-center gap-2"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            ) : (
              <button
                onClick={startTask}
                disabled={!taskInput.trim() || isConnecting}
                className="px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 
                          disabled:cursor-not-allowed text-white rounded-lg font-medium 
                          transition-colors flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Start
              </button>
            )}
          </div>
        </div>
        
        {/* Quick Tasks - SmartBerth Prototype Navigation */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500">Navigate prototype:</span>
          {[
            'Navigate to Vessels Tracking and show me all tracked vessels',
            'Go to Berth Overview and explain berth utilization',
            'Show me the Digital Twin view and explain what I see',
            'Navigate to Gantt chart and summarize schedules',
            'Click on Upcoming Vessels and explain delayed vessels',
          ].map((task, i) => (
            <button
              key={i}
              onClick={() => setTaskInput(task)}
              disabled={status.running}
              className="px-2 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-gray-400 
                        rounded border border-slate-700 transition-colors disabled:opacity-50"
            >
              {task.substring(0, 35)}...
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
