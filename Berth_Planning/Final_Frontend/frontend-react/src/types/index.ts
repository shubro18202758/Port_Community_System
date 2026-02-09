// Vessel Types
export interface Vessel {
  vesselId: number;
  vesselName: string;
  imo: string;
  mmsi: string;
  vesselType: string;
  loa: number;
  beam: number;
  draft: number;
  grossTonnage: number;
  cargoType?: string;
  cargoVolume?: number;
  cargoUnit?: string;
  flag?: string;
  flagState?: string;
  flagStateName?: string;
  priority?: number;
  status?: string;
  createdAt: string;
  updatedAt: string;
}

// Berth Types
export interface Berth {
  berthId: number;
  berthCode: string;
  berthName: string;
  terminalId: number;
  terminalName?: string;
  terminalCode?: string;
  portId?: number;
  portName?: string;
  portCode?: string;
  length: number;
  depth?: number;
  maxDraft: number;
  maxLOA?: number;
  numberOfCranes: number;
  berthType?: string;
  cargoTypes?: string;
  bollardCount?: number;
  latitude?: number;
  longitude?: number;
  status?: string;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

// Schedule Types
export interface Schedule {
  scheduleId: number;
  vesselId: number;
  vesselName?: string;
  vesselType?: string;
  berthId: number;
  berthName?: string;
  eta: string;
  predictedETA?: string;
  etd: string;
  ata?: string;
  atb?: string;
  atd?: string;
  status: string;
  priority?: number;
  cargoType?: string;
  cargoVolume?: number;
  cargoQuantity?: number;
  cargoUnit?: string;
  notes?: string;
  dwellTime?: number;
  waitingTime?: number;
  optimizationScore?: number;
  isOptimized?: boolean;
  conflictCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

// Port Types
export interface Port {
  portId: number;
  portCode: string;
  portName: string;
  country: string;
  latitude: number;
  longitude: number;
  timeZone: string;
  isActive: boolean;
}

// Terminal Types
export interface Terminal {
  terminalId: number;
  terminalCode: string;
  terminalName: string;
  portId: number;
  portName?: string;
  terminalType: string;
  operatingHours: string;
  isActive: boolean;
}

// Dashboard Types
export interface DashboardMetrics {
  totalVessels: number;
  vesselsScheduled: number;
  vesselsApproaching: number;
  vesselsBerthed: number;
  vesselsDeparted: number;
  vesselsInQueue: number;
  totalBerths: number;
  availableBerths: number;
  occupiedBerths: number;
  berthUtilization: number;
  activeConflicts: number;
  todayArrivals: number;
  todayDepartures: number;
  averageWaitingTime: number;
}

export interface BerthStatus {
  berthId: number;
  berthCode: string;
  berthName: string;
  status: string;
  currentVessel?: string;
  vesselETA?: string;
  vesselETD?: string;
  numberOfCranes: number;
  berthType?: string;
}

// AI Suggestion Types
export interface BerthSuggestion {
  rank: number;
  berthId: number;
  berthName: string;
  berthCode: string;
  score: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  proposedETA: string;
  proposedETD: string;
  estimatedWaitMinutes: number;
  reasoning: string[];
  constraints: ConstraintCheck;
}

export interface ConstraintCheck {
  hardConstraintsMet: number;
  hardConstraintsTotal: number;
  softConstraintScore: number;
  violations: ConstraintViolation[];
}

export interface ConstraintViolation {
  constraintId: string;
  constraintName: string;
  severity: string;
  message: string;
}

export interface SuggestionResponse {
  vesselId: number;
  vesselName: string;
  requestedAt: string;
  suggestions: BerthSuggestion[];
  message?: string;
}

// Prediction Types
export interface ETAPrediction {
  vesselId: number;
  vesselName: string;
  originalETA: string;
  predictedETA: string;
  deviationMinutes: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  factors: string[];
}

// Allocation Result Types
export interface AllocationResultDto {
  success: boolean;
  scheduleId?: number;
  message: string;
  warnings: string[];
  conflicts: ConflictDto[];
}

export interface ConflictDto {
  conflictId: number;
  conflictType: string;
  description: string;
  severity: number;
  status: string;
}

// Resource Types
export interface Resource {
  resourceId: number;
  resourceType: string;
  resourceName: string;
  capacity: number;
  isAvailable: boolean;
  maintenanceSchedule?: string;
  createdAt: string;
}

// Vessel Tracking Types (AIS/Real-time)
export interface VesselPosition {
  vesselId?: number;
  mmsi: string;
  vesselName: string;
  imo?: string;
  vesselType?: string;
  latitude: number;
  longitude: number;
  speed: number;
  course: number;
  heading?: number;
  destination?: string;
  declaredETA?: string;
  predictedETA?: string;
  distanceToPort?: number;
  phase?: 'arriving' | 'approaching' | 'at_port' | 'departing' | 'en_route';
  timestamp: string;
}

export interface PortLocation {
  portCode: string;
  portName: string;
  latitude: number;
  longitude: number;
  boundingBox: {
    minLat: number;
    minLon: number;
    maxLat: number;
    maxLon: number;
  };
}

// ============================================
// AI Service Types
// ============================================

// AI Service Health
export interface AIServiceHealth {
  status: string;
  timestamp: string;
  claudeStatus?: string;
  ollamaStatus?: string;
  embeddingModelStatus?: string;
  chromaDbStatus?: string;
  chunksCount?: number;
  gpuAvailable?: boolean;
  gpuName?: string;
  gpuMemoryUsed?: number;
  gpuMemoryTotal?: number;
}

// AI Model Info
export interface AIModelInfo {
  status: string;
  modelName?: string;
  modelLoaded?: boolean;
  gpuEnabled?: boolean;
  gpuName?: string;
  memoryUsage?: number;
  inferenceTime?: number;
}

// AI ETA Prediction (Claude-powered)
export interface AIETAPrediction {
  vesselId: number;
  vesselName?: string;
  originalEta?: string;
  predictedEta: string;
  confidence: number;
  confidenceLevel?: 'HIGH' | 'MEDIUM' | 'LOW';
  deviationMinutes?: number;
  factors?: string[];
  weatherImpact?: number;
  portConditions?: string;
  reasoning?: string;
  ragContext?: string[];
}

// AI Berth Suggestion
export interface AIBerthSuggestion {
  rank: number;
  berthId: number;
  berthName: string;
  berthCode?: string;
  score: number;
  confidence: number;
  confidenceLevel?: 'HIGH' | 'MEDIUM' | 'LOW';
  proposedEta?: string;
  proposedEtd?: string;
  estimatedWaitMinutes?: number;
  reasoning?: string[];
  constraints?: ConstraintCheck;
  optimizationScore?: number;
}

// AI Chat
export interface AIChatRequest {
  message: string;
  sessionId?: string;
}

export interface AIChatResponse {
  text: string;
  intent: string;
  entities: Record<string, unknown>;
  structuredData?: {
    vessels?: AIChatVesselData[];
    berths?: AIChatBerthData[];
    schedules?: AIChatScheduleData[];
    conflicts?: AIConflict[];
    charts?: AIChatChartData;
  };
  actions: AIChatAction[];
  confidence: number;
}

export interface AIChatVesselData {
  vesselId: number;
  vesselName: string;
  imoNumber?: string;
  eta?: string;
  predictedEta?: string;
  status?: string;
  berth?: string;
  confidence?: number;
  readiness?: string;
  cargoType?: string;
}

export interface AIChatBerthData {
  berthId: number;
  berthName: string;
  status: string;
  currentVessel?: string;
  nextAvailable?: string;
  maxLOA?: number;
  maxDraft?: number;
}

export interface AIChatScheduleData {
  scheduleId: number;
  vesselName: string;
  berthName: string;
  eta: string;
  etd?: string;
  status: string;
}

export interface AIChatChartData {
  type: 'demand' | 'latency' | 'traffic' | 'performance' | 'utilization';
  title: string;
  data: Array<Record<string, unknown>>;
  explanation: string;
}

export interface AIChatAction {
  label: string;
  type: 'view-vessel' | 'view-berth' | 'view-schedule' | 'run-simulation' | 'detect-conflicts' | 'navigate';
  vesselId?: number;
  berthId?: number;
  scheduleId?: number;
  simulationType?: string;
  route?: string;
}

// AI RAG Explanation
export interface AIExplanationRequest {
  query: string;
  contextCategory?: string;
  additionalContext?: string;
}

export interface AIExplanationResponse {
  query: string;
  explanation: string;
  sources: AISource[];
  confidence: number;
  timestamp: string;
}

export interface AISource {
  content: string;
  source: string;
  relevanceScore: number;
  category?: string;
}

// AI Search Results
export interface AISearchResult {
  content: string;
  source: string;
  score: number;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface AIHybridSearchResult {
  query: string;
  results: AISearchResult[];
  method: string;
  totalResults: number;
}

// AI Conflict Detection
export interface AIConflict {
  conflictId: string;
  type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
  description: string;
  affectedVessels: number[];
  affectedBerths?: number[];
  startTime?: string;
  endTime?: string;
  suggestedResolution?: string;
  autoResolvable: boolean;
}

// AI What-If Simulation
export interface AIWhatIfRequest {
  scenarioType: 'delay' | 'berth_closure' | 'capacity_surge' | 'custom';
  vesselId?: number;
  berthId?: number;
  delayHours?: number;
  durationHours?: number;
  additionalVessels?: number;
  description?: string;
}

export interface AIWhatIfResult {
  scenarioId: string;
  scenarioType: string;
  description: string;
  impact: {
    affectedVessels: number;
    cascadingDelays: number;
    utilizationChange: number;
    costImpact?: number;
  };
  recommendations: string[];
  alternativeScenarios?: AIWhatIfResult[];
  timestamp: string;
}

// AI Multi-Agent Processing
export interface AIVesselArrivalProcessing {
  vesselId: number;
  vesselName?: string;
  success: boolean;
  stages: AIProcessingStage[];
  finalDecision?: {
    assignedBerthId?: number;
    assignedBerthName?: string;
    proposedEta?: string;
    proposedEtd?: string;
    confidence?: number;
  };
  alerts?: AIAlert[];
  executionTime?: number;
  timestamp: string;
}

export interface AIProcessingStage {
  stageName: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: Record<string, unknown>;
  error?: string;
  duration?: number;
}

// AI Alerts
export interface AIAlert {
  alertId: string;
  type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  message: string;
  affectedEntities?: {
    vesselIds?: number[];
    berthIds?: number[];
    scheduleIds?: number[];
  };
  suggestedAction?: string;
  timestamp: string;
  acknowledged: boolean;
}

// AI Dashboard Overview
export interface AIDashboardOverview {
  aiServiceStatus: string;
  activeConflicts: number;
  pendingAlerts: number;
  etaPredictions: number;
  berthOptimizations: number;
  ragQueriesProcessed: number;
  averageResponseTime: number;
  gpuUtilization?: number;
  modelStatus: {
    claude: string;
    ollama: string;
    embeddings: string;
  };
}
