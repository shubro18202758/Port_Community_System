import { useState } from 'react';
import { CheckCircle2, Circle, Anchor, Building2, Link2, Cpu, Users, Shield, Sparkles } from 'lucide-react';
import { PortDetailsStep } from './steps/port-details-step';
import { IntegrationStep } from './steps/integration-step';
import { TerminalSetupStep } from './steps/terminal-setup-step';
import { BerthSpecificationsStep } from './steps/berth-specifications-step';
import { ResourcesStep } from './steps/resources-step';
import { ConstraintsStep } from './steps/constraints-step';
import { ReviewStep } from './steps/review-step';
import { getSamplePortData } from './sample-port-data';

export interface PortData {
  portName: string;
  portCode: string;
  unlocode: string;
  country: string;
  timezone: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  contactEmail: string;
  contactPhone: string;
}

export interface IntegrationData {
  systemType: 'maritime_single_window' | 'port_community_system' | 'ais' | 'manual' | null;
  apiEndpoint?: string;
  apiKey?: string;
  dataSync: {
    vesselCalls: boolean;
    falForms: boolean;
    cargoManifest: boolean;
    crewLists: boolean;
  };
  syncFrequency: 'realtime' | 'hourly' | 'daily';
}

export interface Terminal {
  id: string;
  name: string;
  code: string;
  terminalType: 'container' | 'bulk' | 'ro-ro' | 'multi-purpose';
  operatingCompany: string;
  operationalHours: string;
}

export interface BerthSpec {
  id: string;
  terminalId: string;
  name: string;
  length: number;
  maxDraft: number;
  maxLOA: number;
  maxBeam: number;
  maxDWT: number;
  bollards: number;
  fenders: number;
  reeferPoints: number;
  freshWater: boolean;
  bunkering: boolean;
}

export interface Equipment {
  id: string;
  terminalId: string;
  type: 'STS' | 'RTG' | 'MHC' | 'RMG' | 'Reach Stacker';
  name: string;
  capacity: number;
  status: 'operational' | 'maintenance' | 'idle';
}

export interface HumanResource {
  role: string;
  count: number;
  shifts: number;
  availability: string;
}

export interface Constraint {
  id: string;
  type: 'weather' | 'tide' | 'environmental' | 'safety' | 'operational';
  name: string;
  description: string;
  threshold?: string;
  action: string;
}

export interface OnboardingData {
  port: PortData | null;
  integration: IntegrationData | null;
  terminals: Terminal[];
  berths: BerthSpec[];
  equipment: Equipment[];
  humanResources: HumanResource[];
  constraints: Constraint[];
}

interface PortOnboardingWizardProps {
  onComplete: (data: OnboardingData) => void;
  onCancel: () => void;
}

const steps = [
  { id: 'port', title: 'Port Details', icon: Anchor },
  { id: 'integration', title: 'System Integration', icon: Link2 },
  { id: 'terminals', title: 'Terminal Setup', icon: Building2 },
  { id: 'berths', title: 'Berth Specifications', icon: Cpu },
  { id: 'resources', title: 'Resources & Equipment', icon: Users },
  { id: 'constraints', title: 'Safety & Constraints', icon: Shield },
  { id: 'review', title: 'Review & Confirm', icon: CheckCircle2 },
];

export function PortOnboardingWizard({ onComplete, onCancel }: PortOnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    port: null,
    integration: null,
    terminals: [],
    berths: [],
    equipment: [],
    humanResources: [],
    constraints: [],
  });
  const [showSamplePrompt, setShowSamplePrompt] = useState(true);

  const loadSampleData = () => {
    const sampleData = getSamplePortData();
    setOnboardingData(sampleData);
    setShowSamplePrompt(false);
  };

  const startFresh = () => {
    setShowSamplePrompt(false);
  };

  const updateData = <K extends keyof OnboardingData>(
    key: K,
    value: OnboardingData[K]
  ) => {
    setOnboardingData(prev => ({ ...prev, [key]: value }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete(onboardingData);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: // Port Details
        return onboardingData.port !== null;
      case 1: // Integration
        return onboardingData.integration !== null;
      case 2: // Terminals
        return onboardingData.terminals.length > 0;
      case 3: // Berths
        return onboardingData.berths.length > 0;
      case 4: // Resources
        return onboardingData.equipment.length > 0;
      case 5: // Constraints
        return true; // Optional step
      case 6: // Review
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="size-full flex flex-col bg-gradient-to-br from-gray-50 to-white">
      {/* Sample Data Prompt */}
      {showSamplePrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                style={{ backgroundColor: 'var(--kale-sky)' }}>
                <Sparkles className="w-8 h-8" style={{ color: 'var(--kale-blue)' }} />
              </div>
              <h2 style={{ color: 'var(--kale-blue)', fontSize: '1.5rem', fontWeight: 700 }}>
                Welcome to SmartBerth AI
              </h2>
              <p className="mt-2" style={{ color: 'var(--muted-foreground)' }}>
                Get started quickly with sample data or configure your own port from scratch
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Load Sample Data into Wizard */}
              <button
                onClick={loadSampleData}
                className="p-5 rounded-lg border-2 transition-all hover:border-solid text-left"
                style={{ borderColor: 'var(--kale-blue)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5" style={{ color: 'var(--kale-blue)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>Customize Sample</span>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                  Load Singapore data and customize each step
                </p>
              </button>

              {/* Start Fresh */}
              <button
                onClick={startFresh}
                className="p-5 rounded-lg border-2 border-dashed transition-all hover:border-solid text-left"
                style={{ borderColor: 'var(--border)' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Anchor className="w-5 h-5" style={{ color: 'var(--muted-foreground)' }} />
                  <span style={{ fontWeight: 600 }}>Configure My Port</span>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                  Set up your own port from scratch
                </p>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="px-8 py-6 border-b bg-white shadow-sm" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto">
          <h1 style={{ color: 'var(--kale-blue)', fontSize: '1.75rem', fontWeight: 700 }}>
            SmartBerth AI Onboarding
          </h1>
          <p className="mt-2" style={{ color: 'var(--muted-foreground)' }}>
            Configure your port and terminal infrastructure for AI-powered berthing optimization
          </p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="px-8 py-6 border-b bg-white" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isCompleted = index < currentStep;
              const isCurrent = index === currentStep;

              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center transition-all"
                      style={{
                        backgroundColor: isCompleted
                          ? 'var(--kale-blue)'
                          : isCurrent
                          ? 'var(--kale-teal)'
                          : 'var(--muted)',
                        color: isCompleted || isCurrent ? 'white' : 'var(--muted-foreground)',
                      }}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-6 h-6" />
                      ) : (
                        <Icon className="w-6 h-6" />
                      )}
                    </div>
                    <div className="mt-2 text-sm text-center" style={{ 
                      color: isCurrent ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                      fontWeight: isCurrent ? 600 : 400
                    }}>
                      {step.title}
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className="h-0.5 flex-1 mx-2"
                      style={{
                        backgroundColor: isCompleted ? 'var(--kale-blue)' : 'var(--border)',
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        <div className="max-w-6xl mx-auto">
          {currentStep === 0 && (
            <PortDetailsStep
              data={onboardingData.port}
              onChange={(data) => updateData('port', data)}
            />
          )}
          {currentStep === 1 && (
            <IntegrationStep
              data={onboardingData.integration}
              onChange={(data) => updateData('integration', data)}
            />
          )}
          {currentStep === 2 && (
            <TerminalSetupStep
              data={onboardingData.terminals}
              onChange={(data) => updateData('terminals', data)}
            />
          )}
          {currentStep === 3 && (
            <BerthSpecificationsStep
              terminals={onboardingData.terminals}
              data={onboardingData.berths}
              onChange={(data) => updateData('berths', data)}
            />
          )}
          {currentStep === 4 && (
            <ResourcesStep
              terminals={onboardingData.terminals}
              equipment={onboardingData.equipment}
              humanResources={onboardingData.humanResources}
              onEquipmentChange={(data) => updateData('equipment', data)}
              onHumanResourcesChange={(data) => updateData('humanResources', data)}
            />
          )}
          {currentStep === 5 && (
            <ConstraintsStep
              data={onboardingData.constraints}
              onChange={(data) => updateData('constraints', data)}
            />
          )}
          {currentStep === 6 && <ReviewStep data={onboardingData} />}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="px-8 py-6 border-t bg-white shadow-lg" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button
            onClick={onCancel}
            className="px-6 py-3 rounded-lg transition-colors text-sm"
            style={{
              color: 'var(--muted-foreground)',
              fontWeight: 600,
            }}
          >
            Cancel Onboarding
          </button>
          <div className="flex gap-3">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="px-6 py-3 rounded-lg transition-colors border disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: 'var(--border)',
                color: 'var(--kale-blue)',
                fontWeight: 600,
              }}
            >
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className="px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: canProceed() ? 'var(--kale-blue)' : 'var(--muted)',
                color: 'white',
                fontWeight: 600,
              }}
            >
              {currentStep === steps.length - 1 ? 'Complete Onboarding' : 'Continue'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}