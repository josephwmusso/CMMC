import { createContext, useContext, useState, ReactNode } from 'react';

interface WizardAnswer {
  questionId: string;
  answerId: number;
  answerText: string;
  severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | null;
}

interface OrganizationData {
  name: string;
  id: string;
  framework: string;
  industry: string;
  employees?: number;
  cuiTypes?: string[];
  environment?: string;
  techStack?: string[];
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'Admin' | 'Editor' | 'Viewer';
  status: 'Active' | 'Invited' | 'Suspended';
}

interface ApiKey {
  id: string;
  name: string;
  key?: string;
  created: string;
  lastUsed: string;
  permissions: 'Read & Write' | 'Read Only';
}

interface AiConfiguration {
  apiEndpoint: string;
  modelName: string;
  apiKey?: string;
  temperature?: number;
  enabled: boolean;
}

interface AppContextType {
  // Organization
  organization: OrganizationData;
  updateOrganization: (data: Partial<OrganizationData>) => void;
  
  // Wizard
  wizardAnswers: Record<string, WizardAnswer>;
  currentQuestion: number;
  setWizardAnswer: (questionId: string, answer: WizardAnswer) => void;
  setCurrentQuestion: (question: number) => void;
  wizardComplete: boolean;
  setWizardComplete: (complete: boolean) => void;
  
  // Team
  teamMembers: TeamMember[];
  addTeamMember: (member: Omit<TeamMember, 'id'>) => void;
  removeTeamMember: (id: string) => void;
  updateTeamMember: (id: string, data: Partial<TeamMember>) => void;
  
  // API Keys
  apiKeys: ApiKey[];
  addApiKey: (key: Omit<ApiKey, 'id' | 'created' | 'lastUsed'>) => void;
  removeApiKey: (id: string) => void;
  
  // AI Configuration
  aiConfig: AiConfiguration;
  setAiConfig: (config: Partial<AiConfiguration>) => void;
  
  // Settings
  twoFactorEnabled: boolean;
  setTwoFactorEnabled: (enabled: boolean) => void;
  sessionTimeout: string;
  setSessionTimeout: (timeout: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  // Organization state
  const [organization, setOrganization] = useState<OrganizationData>({
    name: 'Apex Defense Solutions',
    id: 'INST76DFCF515AB894FE',
    framework: 'CMMC Level 2 (NIST SP 800-171 Rev 2)',
    industry: 'Defense Contractor',
  });

  // Wizard state
  const [wizardAnswers, setWizardAnswers] = useState<Record<string, WizardAnswer>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [wizardComplete, setWizardComplete] = useState(false);

  // Team state
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { id: '1', name: 'Sarah Chen', email: 'sarah.chen@apex.com', role: 'Admin', status: 'Active' },
    { id: '2', name: 'Michael Torres', email: 'michael.torres@apex.com', role: 'Editor', status: 'Active' },
    { id: '3', name: 'Jessica Park', email: 'jessica.park@apex.com', role: 'Viewer', status: 'Invited' },
  ]);

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    { id: '1', name: 'Production API Key', created: 'Jan 15, 2026', lastUsed: '2 hours ago', permissions: 'Read & Write' },
    { id: '2', name: 'CI/CD Integration', created: 'Dec 3, 2025', lastUsed: '1 day ago', permissions: 'Read Only' },
  ]);

  // AI Configuration state
  const [aiConfig, setAiConfig] = useState<AiConfiguration>({
    apiEndpoint: 'https://api.openai.com/v1',
    modelName: 'gpt-3.5-turbo',
    apiKey: '',
    temperature: 0.7,
    enabled: false,
  });

  // Settings state
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [sessionTimeout, setSessionTimeout] = useState('30 minutes');

  const updateOrganization = (data: Partial<OrganizationData>) => {
    setOrganization(prev => ({ ...prev, ...data }));
  };

  const setWizardAnswer = (questionId: string, answer: WizardAnswer) => {
    setWizardAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const addTeamMember = (member: Omit<TeamMember, 'id'>) => {
    const newMember = {
      ...member,
      id: Date.now().toString(),
    };
    setTeamMembers(prev => [...prev, newMember]);
  };

  const removeTeamMember = (id: string) => {
    setTeamMembers(prev => prev.filter(m => m.id !== id));
  };

  const updateTeamMember = (id: string, data: Partial<TeamMember>) => {
    setTeamMembers(prev => prev.map(m => m.id === id ? { ...m, ...data } : m));
  };

  const addApiKey = (key: Omit<ApiKey, 'id' | 'created' | 'lastUsed'>) => {
    const newKey = {
      ...key,
      id: Date.now().toString(),
      created: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      lastUsed: 'Never',
    };
    setApiKeys(prev => [...prev, newKey]);
  };

  const removeApiKey = (id: string) => {
    setApiKeys(prev => prev.filter(k => k.id !== id));
  };

  const updateAiConfig = (config: Partial<AiConfiguration>) => {
    setAiConfig(prev => ({ ...prev, ...config }));
  };

  return (
    <AppContext.Provider
      value={{
        organization,
        updateOrganization,
        wizardAnswers,
        currentQuestion,
        setWizardAnswer,
        setCurrentQuestion,
        wizardComplete,
        setWizardComplete,
        teamMembers,
        addTeamMember,
        removeTeamMember,
        updateTeamMember,
        apiKeys,
        addApiKey,
        removeApiKey,
        aiConfig,
        setAiConfig: updateAiConfig,
        twoFactorEnabled,
        setTwoFactorEnabled,
        sessionTimeout,
        setSessionTimeout,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}