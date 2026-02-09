import api from './config';
import type {
  Vessel,
  Berth,
  Schedule,
  Port,
  Terminal,
  Resource,
  DashboardMetrics,
  BerthStatus,
  SuggestionResponse,
  ETAPrediction,
  AIServiceHealth,
  AIModelInfo,
  AIETAPrediction,
  AIBerthSuggestion,
  AIChatRequest,
  AIChatResponse,
  AIExplanationRequest,
  AIExplanationResponse,
  AISearchResult,
  AIConflict,
  AIWhatIfRequest,
  AIWhatIfResult,
  AIVesselArrivalProcessing,
  AIAlert,
  AIDashboardOverview,
} from '../types';

// ============================================
// Schedule Change Notification Types
// ============================================
interface ScheduleChangeEvent {
  event_type: 'berth_allocation' | 'eta_update' | 'arrival' | 'berthing' | 'departure';
  vessel_id: number;
  vessel_name?: string;
  berth_id?: number;
  berth_name?: string;
  previous_value?: string;
  new_value?: string;
  performed_by?: string;
  additional_context?: Record<string, unknown>;
}

interface NotificationResponse {
  success: boolean;
  notification_id: string;
  stakeholders_notified: string[];
  explanation: string;
  message: string;
}

// ============================================
// Notification Service Functions
// ============================================
const notifyScheduleChange = (event: ScheduleChangeEvent) =>
  api.post<NotificationResponse>('/ai/monitoring/notify/schedule-change', event);

const notifyBulkChanges = (events: ScheduleChangeEvent[]) =>
  api.post('/ai/monitoring/notify/bulk', events);

const getStakeholdersForVessel = (vesselId: number) =>
  api.get(`/ai/monitoring/stakeholders/${vesselId}`);

// Internal helper to send notification after successful operation
const sendNotification = async (event: ScheduleChangeEvent): Promise<void> => {
  try {
    await notifyScheduleChange(event);
    console.log(`[Notification] Sent ${event.event_type} notification for vessel ${event.vessel_id}`);
  } catch (error) {
    // Don't fail the main operation if notification fails
    console.warn(`[Notification] Failed to send ${event.event_type} notification:`, error);
  }
};

// Dashboard
export const getDashboardMetrics = (terminalId?: number) =>
  api.get<DashboardMetrics>('/dashboard/metrics', { params: terminalId ? { terminalId } : undefined });
export const getBerthStatus = (terminalId?: number) =>
  api.get<BerthStatus[]>('/dashboard/berth-status', { params: terminalId ? { terminalId } : undefined });
export const getAlerts = () => api.get('/dashboard/alerts');

// Vessels
export const getVessels = () => api.get<Vessel[]>('/vessels');

// Berths
export const getBerths = (terminalId?: number) =>
  api.get<Berth[]>('/berths', { params: terminalId ? { terminalId } : undefined });
export const createBerth = (berth: Partial<Berth>) => api.post<Berth>('/berths', berth);

// Schedules
export const getAllSchedules = () => api.get<Schedule[]>('/schedules');
export const getActiveSchedules = (terminalId?: number) =>
  api.get<Schedule[]>('/schedules/active', { params: terminalId ? { terminalId } : undefined });
export const getScheduleById = (id: number) => api.get<Schedule>(`/schedules/${id}`);
export const getScheduleByVesselId = (vesselId: number) => api.get<Schedule>(`/schedules/vessel/${vesselId}`);
export const getSchedulesByStatus = (status: string) => api.get<Schedule[]>(`/schedules/status/${status}`);
export const getSchedulesByBerth = (berthId: number) => api.get<Schedule[]>(`/schedules/berth/${berthId}`);
export const createSchedule = (schedule: Partial<Schedule>) => api.post<Schedule>('/schedules/allocate', schedule);
export const updateSchedule = (id: number, data: Partial<Schedule>) => api.put(`/schedules/${id}`, data);
export const updateScheduleETA = (id: number, newETA: string, newPredictedETA?: string) =>
  api.put(`/schedules/${id}/eta`, { newETA, newPredictedETA });
export const recordArrival = (id: number, ata: string) => api.put(`/schedules/${id}/arrival`, { ata });
export const recordBerthing = (id: number, atb: string) => api.put(`/schedules/${id}/berthing`, { atb });
export const recordDeparture = (id: number, atd: string) => api.put(`/schedules/${id}/departure`, { atd });
export const deleteSchedule = (id: number) => api.delete(`/schedules/${id}`);
export const clearAllSchedules = () => api.delete('/schedules/clear-all');

// Ports
export const getPorts = () => api.get<Port[]>('/ports');
export const createPort = (port: Partial<Port>) => api.post<Port>('/ports', port);

// Terminals
export const getTerminals = () => api.get<Terminal[]>('/terminals');
export const createTerminal = (terminal: Partial<Terminal>) => api.post<Terminal>('/terminals', terminal);

// AI Suggestions
export const getBerthSuggestions = (vesselId: number, preferredETA?: string) =>
  api.get<SuggestionResponse>(`/suggestions/berth/${vesselId}`, { params: { preferredETA } });

// Predictions
export const getAllActiveETAPredictions = () => api.get<ETAPrediction[]>('/predictions/eta/active');

// Resources
export const getResources = () => api.get<Resource[]>('/resources');
export const createResource = (resource: Partial<Resource>) => api.post<Resource>('/resources', resource);

// Service Objects (grouped for convenience)
export const dashboardService = {
  getMetrics: (terminalId?: number) => getDashboardMetrics(terminalId).then(res => res.data),
  getBerthStatus: (terminalId?: number) => getBerthStatus(terminalId).then(res => res.data),
  getAlerts: () => getAlerts().then(res => res.data),
};

export const vesselService = {
  getAll: () => getVessels().then(res => res.data),
};

export const berthService = {
  getAll: (terminalId?: number) => getBerths(terminalId).then(res => res.data),
  create: (berth: Partial<Berth>) => createBerth(berth).then(res => res.data),
};

export const scheduleService = {
  getAll: () => getAllSchedules().then(res => res.data),
  getActive: (terminalId?: number) => getActiveSchedules(terminalId).then(res => res.data),
  getById: (id: number) => getScheduleById(id).then(res => res.data),
  getByVesselId: (vesselId: number) => getScheduleByVesselId(vesselId).then(res => res.data),
  getByStatus: (status: string) => getSchedulesByStatus(status).then(res => res.data),
  getByBerth: (berthId: number) => getSchedulesByBerth(berthId).then(res => res.data),
  
  // Berth allocation with stakeholder notification
  allocate: async (schedule: Partial<Schedule>) => {
    const result = await createSchedule(schedule).then(res => res.data);
    // Notify stakeholders after successful allocation
    await sendNotification({
      event_type: 'berth_allocation',
      vessel_id: schedule.vesselId || result.vesselId,
      berth_id: schedule.berthId || result.berthId,
      performed_by: 'Port Operations'
    });
    return result;
  },
  
  update: (id: number, data: Partial<Schedule>) => updateSchedule(id, data).then(res => res.data),
  
  // ETA update with stakeholder notification
  updateETA: async (id: number, newETA: string, newPredictedETA?: string, vesselId?: number, previousETA?: string) => {
    const result = await updateScheduleETA(id, newETA, newPredictedETA).then(res => res.data);
    // Notify stakeholders about ETA change
    if (vesselId) {
      await sendNotification({
        event_type: 'eta_update',
        vessel_id: vesselId,
        previous_value: previousETA,
        new_value: newETA,
        performed_by: 'Planning System',
        additional_context: { scheduleId: id, predictedETA: newPredictedETA }
      });
    }
    return result;
  },
  
  // Arrival recording with stakeholder notification
  recordArrival: async (id: number, ata: string, vesselId?: number, vesselName?: string) => {
    const result = await recordArrival(id, ata).then(res => res.data);
    if (vesselId) {
      await sendNotification({
        event_type: 'arrival',
        vessel_id: vesselId,
        vessel_name: vesselName,
        new_value: ata,
        performed_by: 'Harbor Control'
      });
    }
    return result;
  },
  
  // Berthing recording with stakeholder notification
  recordBerthing: async (id: number, atb: string, vesselId?: number, vesselName?: string, berthId?: number, berthName?: string) => {
    const result = await recordBerthing(id, atb).then(res => res.data);
    if (vesselId) {
      await sendNotification({
        event_type: 'berthing',
        vessel_id: vesselId,
        vessel_name: vesselName,
        berth_id: berthId,
        berth_name: berthName,
        new_value: atb,
        performed_by: 'Berth Operations'
      });
    }
    return result;
  },
  
  // Departure recording with stakeholder notification
  recordDeparture: async (id: number, atd: string, vesselId?: number, vesselName?: string, berthId?: number, berthName?: string) => {
    const result = await recordDeparture(id, atd).then(res => res.data);
    if (vesselId) {
      await sendNotification({
        event_type: 'departure',
        vessel_id: vesselId,
        vessel_name: vesselName,
        berth_id: berthId,
        berth_name: berthName,
        new_value: atd,
        performed_by: 'Harbor Control'
      });
    }
    return result;
  },
  
  delete: (id: number) => deleteSchedule(id).then(res => res.data),
  clearAll: () => clearAllSchedules().then(res => res.data),
};

export const portService = {
  getAll: () => getPorts().then(res => res.data),
  create: (port: Partial<Port>) => createPort(port).then(res => res.data),
};

export const terminalService = {
  getAll: () => getTerminals().then(res => res.data),
  create: (terminal: Partial<Terminal>) => createTerminal(terminal).then(res => res.data),
};

export const suggestionService = {
  getBerthSuggestions: (vesselId: number, preferredETA?: string) =>
    getBerthSuggestions(vesselId, preferredETA).then(res => res.data),
};

export const predictionService = {
  getAllActiveETA: () => getAllActiveETAPredictions().then(res => res.data),
};

export const resourceService = {
  getAll: () => getResources().then(res => res.data),
  create: (resource: Partial<Resource>) => createResource(resource).then(res => res.data),
};

// ============================================
// AI Service API Calls
// ============================================

// AI Health & Status
export const getAIHealth = () => api.get<AIServiceHealth>('/ai/health');
export const getAIModelInfo = () => api.get<AIModelInfo>('/ai/model/info');
export const loadAIModel = () => api.post('/ai/model/load');

// AI ETA Predictions
export const getAIETAPrediction = (vesselId: number, scheduleId?: number) =>
  api.get<AIETAPrediction>(`/ai/predictions/eta/${vesselId}`, { params: { schedule_id: scheduleId } });
export const getAIETABatch = (vesselIds: number[]) =>
  api.get<AIETAPrediction[]>('/ai/predictions/eta/batch', { params: { vessel_ids: vesselIds.join(',') } });
export const getClaudeETAPrediction = (vesselId: number, includeRagContext = true) =>
  api.post('/ai/predictions/eta/claude', { vessel_id: vesselId, include_rag_context: includeRagContext });

// AI Berth Suggestions
export const getAIBerthSuggestions = (vesselId: number, preferredEta?: string, topN = 5) =>
  api.get<AIBerthSuggestion[]>(`/ai/suggestions/berth/${vesselId}`, { params: { preferred_eta: preferredEta, top_n: topN } });
export const getClaudeBerthOptimization = (vesselId: number, includeRagContext = true, timeHorizonHours = 48) =>
  api.post('/ai/suggestions/berth/claude', { vessel_id: vesselId, include_rag_context: includeRagContext, time_horizon_hours: timeHorizonHours });

// AI Chatbot
export const sendChatMessage = (message: string, sessionId?: string) =>
  api.post<AIChatResponse>('/ai/chat', { message, session_id: sessionId });
export const getChatHistory = () => api.get<{ history: Array<{ role: string; content: string; timestamp: string }> }>('/ai/chat/history');
export const clearChatHistory = () => api.post('/ai/chat/clear');

// AI RAG Knowledge Base
export const generateExplanation = (query: string, contextCategory?: string, additionalContext?: string) =>
  api.post<AIExplanationResponse>('/ai/rag/explain', { query, context_category: contextCategory, additional_context: additionalContext });
export const searchKnowledgeBase = (query: string, k = 5, category?: string) =>
  api.get<{ results: AISearchResult[] }>('/ai/rag/search', { params: { query, k, category } });
export const hybridSearch = (query: string, topK = 5, method = 'hybrid') =>
  api.post<{ results: AISearchResult[]; method: string; total_results: number }>('/ai/rag/hybrid-search', { query, top_k: topK, method });

// AI Conflict Detection
export const detectConflicts = (hours = 48) =>
  api.get<{ time_window_hours: number; conflicts_found: number; conflicts: AIConflict[] }>('/ai/conflicts', { params: { hours } });
export const resolveConflict = (conflictId: number, resolutionAction: string) =>
  api.post('/ai/conflicts/resolve', { conflict_id: conflictId, resolution_action: resolutionAction });
export const getClaudeConflictResolution = (timeStart?: string, timeEnd?: string, includeRagContext = true) =>
  api.post('/ai/conflicts/claude', { time_start: timeStart, time_end: timeEnd, include_rag_context: includeRagContext });

// AI Multi-Agent Processing
export const processVesselArrival = (vesselId: number) =>
  api.post<AIVesselArrivalProcessing>('/ai/agents/process-arrival', { vessel_id: vesselId });
export const optimizeScheduleWithAI = (algorithm = 'greedy', timeHorizonHours = 48) =>
  api.post('/ai/agents/optimize-schedule', { algorithm, time_horizon_hours: timeHorizonHours });

// AI What-If Simulation
export const runWhatIfSimulation = (request: AIWhatIfRequest) =>
  api.post<AIWhatIfResult>('/ai/simulation/what-if', request);
export const simulateDelayImpact = (vesselId: number, delayHours = 4) =>
  api.get<AIWhatIfResult>(`/ai/simulation/delay-impact/${vesselId}`, { params: { delayHours } });
export const simulateBerthClosure = (berthId: number, durationHours = 24) =>
  api.get<AIWhatIfResult>(`/ai/simulation/berth-closure/${berthId}`, { params: { durationHours } });
export const simulateCapacitySurge = (additionalVessels = 5) =>
  api.get<AIWhatIfResult>('/ai/simulation/capacity-surge', { params: { additionalVessels } });

// AI Dashboard & Analytics
export const getAIDashboardOverview = () => api.get<AIDashboardOverview>('/ai/dashboard/overview');
export const getAIBerthTimeline = (hours = 48) => api.get('/ai/dashboard/timeline', { params: { hours } });

// AI Alerts
export const getActiveAIAlerts = () => api.get<AIAlert[]>('/ai/alerts/active');

// AI Constraint Validation
export const validateConstraints = (vesselId: number, berthId: number, eta?: string) =>
  api.post('/ai/validate/constraints', { vesselId, berthId, eta });

// ============================================
// AI Service Objects (grouped for convenience)
// ============================================

export const aiService = {
  // Health & Status
  getHealth: () => getAIHealth().then(res => res.data),
  getModelInfo: () => getAIModelInfo().then(res => res.data),
  loadModel: () => loadAIModel().then(res => res.data),

  // ETA Predictions
  predictETA: (vesselId: number, scheduleId?: number) => getAIETAPrediction(vesselId, scheduleId).then(res => res.data),
  predictETABatch: (vesselIds: number[]) => getAIETABatch(vesselIds).then(res => res.data),
  getClaudeETA: (vesselId: number, includeRag = true) => getClaudeETAPrediction(vesselId, includeRag).then(res => res.data),

  // Berth Suggestions
  getBerthSuggestions: (vesselId: number, preferredEta?: string, topN = 5) =>
    getAIBerthSuggestions(vesselId, preferredEta, topN).then(res => res.data),
  getClaudeBerth: (vesselId: number, includeRag = true, hours = 48) =>
    getClaudeBerthOptimization(vesselId, includeRag, hours).then(res => res.data),

  // Chatbot
  chat: (message: string, sessionId?: string) => sendChatMessage(message, sessionId).then(res => res.data),
  getChatHistory: () => getChatHistory().then(res => res.data),
  clearChat: () => clearChatHistory().then(res => res.data),

  // RAG
  explain: (query: string, category?: string, context?: string) =>
    generateExplanation(query, category, context).then(res => res.data),
  search: (query: string, k = 5, category?: string) => searchKnowledgeBase(query, k, category).then(res => res.data),
  hybridSearch: (query: string, topK = 5, method = 'hybrid') => hybridSearch(query, topK, method).then(res => res.data),

  // Conflicts
  detectConflicts: (hours = 48) => detectConflicts(hours).then(res => res.data),
  resolveConflict: (conflictId: number, action: string) => resolveConflict(conflictId, action).then(res => res.data),
  getClaudeConflicts: (start?: string, end?: string, includeRag = true) =>
    getClaudeConflictResolution(start, end, includeRag).then(res => res.data),

  // Multi-Agent
  processArrival: (vesselId: number) => processVesselArrival(vesselId).then(res => res.data),
  optimizeSchedule: (algorithm = 'greedy', hours = 48) => optimizeScheduleWithAI(algorithm, hours).then(res => res.data),

  // Simulation
  whatIf: (request: AIWhatIfRequest) => runWhatIfSimulation(request).then(res => res.data),
  simulateDelay: (vesselId: number, hours = 4) => simulateDelayImpact(vesselId, hours).then(res => res.data),
  simulateClosure: (berthId: number, hours = 24) => simulateBerthClosure(berthId, hours).then(res => res.data),
  simulateSurge: (vessels = 5) => simulateCapacitySurge(vessels).then(res => res.data),

  // Dashboard
  getDashboard: () => getAIDashboardOverview().then(res => res.data),
  getTimeline: (hours = 48) => getAIBerthTimeline(hours).then(res => res.data),

  // Alerts
  getAlerts: () => getActiveAIAlerts().then(res => res.data),

  // Validation
  validateConstraints: (vesselId: number, berthId: number, eta?: string) =>
    validateConstraints(vesselId, berthId, eta).then(res => res.data),
};

// ============================================
// Notification Service (Stakeholder Alerts)
// ============================================
export const notificationService = {
  // Send schedule change notification with explainable insights
  notifyScheduleChange: (event: ScheduleChangeEvent) => 
    notifyScheduleChange(event).then(res => res.data),
  
  // Send bulk notifications for multiple events
  notifyBulk: (events: ScheduleChangeEvent[]) => 
    notifyBulkChanges(events).then(res => res.data),
  
  // Get stakeholders associated with a vessel
  getStakeholders: (vesselId: number) => 
    getStakeholdersForVessel(vesselId).then(res => res.data),
  
  // Convenience methods for specific event types
  notifyBerthAllocation: (vesselId: number, berthId: number, vesselName?: string, berthName?: string) =>
    notifyScheduleChange({
      event_type: 'berth_allocation',
      vessel_id: vesselId,
      vessel_name: vesselName,
      berth_id: berthId,
      berth_name: berthName,
      performed_by: 'Port Operations'
    }).then(res => res.data),
  
  notifyETAUpdate: (vesselId: number, previousETA: string, newETA: string, vesselName?: string) =>
    notifyScheduleChange({
      event_type: 'eta_update',
      vessel_id: vesselId,
      vessel_name: vesselName,
      previous_value: previousETA,
      new_value: newETA,
      performed_by: 'Planning System'
    }).then(res => res.data),
  
  notifyArrival: (vesselId: number, ata: string, vesselName?: string) =>
    notifyScheduleChange({
      event_type: 'arrival',
      vessel_id: vesselId,
      vessel_name: vesselName,
      new_value: ata,
      performed_by: 'Harbor Control'
    }).then(res => res.data),
  
  notifyBerthing: (vesselId: number, berthId: number, atb: string, vesselName?: string, berthName?: string) =>
    notifyScheduleChange({
      event_type: 'berthing',
      vessel_id: vesselId,
      vessel_name: vesselName,
      berth_id: berthId,
      berth_name: berthName,
      new_value: atb,
      performed_by: 'Berth Operations'
    }).then(res => res.data),
  
  notifyDeparture: (vesselId: number, berthId: number, atd: string, vesselName?: string, berthName?: string) =>
    notifyScheduleChange({
      event_type: 'departure',
      vessel_id: vesselId,
      vessel_name: vesselName,
      berth_id: berthId,
      berth_name: berthName,
      new_value: atd,
      performed_by: 'Harbor Control'
    }).then(res => res.data),
};