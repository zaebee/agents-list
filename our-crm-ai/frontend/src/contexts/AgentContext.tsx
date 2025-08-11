import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../services/api';

export interface Agent {
  id: string;
  name: string;
  description: string;
  provider: string;
  model: string;
  status: 'available' | 'demo' | 'busy' | 'offline';
  specializations: string[];
  capabilities: string[];
}

export interface AgentSystemStatus {
  system_status: 'ready' | 'demo_mode' | 'offline';
  total_agents: number;
  active_agents: number;
  demo_agents: number;
  providers: {
    [key: string]: {
      configured: boolean;
      status: string;
      agents: string[];
    };
  };
  timestamp: string;
}

interface AgentContextType {
  agents: Agent[];
  systemStatus: AgentSystemStatus | null;
  loading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  testAgent: (agentId: string) => Promise<void>;
  selectedAgent: Agent | null;
  setSelectedAgent: (agent: Agent | null) => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

interface AgentProviderProps {
  children: ReactNode;
}

export const AgentProvider: React.FC<AgentProviderProps> = ({ children }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [systemStatus, setSystemStatus] = useState<AgentSystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // Fetch agents on mount and periodically
  useEffect(() => {
    fetchAgents();
    fetchSystemStatus();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAgents();
      fetchSystemStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getAgents();
      setAgents(response.agents || []);
    } catch (error: any) {
      // Fallback to demo data if API is not available
      console.warn('API not available, using demo data');
      const demoAgents: Agent[] = [
        {
          id: 'business-analyst-demo',
          name: 'Business Analyst',
          description: 'Analyzes business requirements, market research, and strategic planning with Claude 3 Sonnet.',
          provider: 'anthropic',
          model: 'claude-3-sonnet-20240229',
          status: 'available',
          specializations: ['business analysis', 'requirements gathering', 'market research'],
          capabilities: ['Strategic planning', 'Requirements analysis', 'Market research'],
        },
        {
          id: 'code-reviewer-demo',
          name: 'Code Reviewer',
          description: 'Reviews code quality, suggests improvements, and ensures best practices using Mistral Large.',
          provider: 'mistral',
          model: 'mistral-large-latest',
          status: 'available',
          specializations: ['code review', 'quality assurance', 'best practices', 'refactoring'],
          capabilities: ['Code analysis', 'Security review', 'Performance optimization'],
        },
        {
          id: 'data-analyst-demo',
          name: 'Data Analyst',
          description: 'Performs statistical analysis, data visualization, and reporting with Mistral Medium.',
          provider: 'mistral',
          model: 'mistral-medium-latest',
          status: 'available',
          specializations: ['data analysis', 'statistical analysis', 'data visualization', 'reporting'],
          capabilities: ['Statistical modeling', 'Data visualization', 'Report generation'],
        },
        {
          id: 'technical-writer-demo',
          name: 'Technical Writer',
          description: 'Creates technical documentation, user guides, and API documentation using Mistral Small.',
          provider: 'mistral',
          model: 'mistral-small-latest',
          status: 'available',
          specializations: ['technical documentation', 'user guides', 'api documentation', 'content creation'],
          capabilities: ['Documentation creation', 'Content strategy', 'API documentation'],
        },
        {
          id: 'backend-architect-demo',
          name: 'Backend Architect',
          description: 'Designs scalable backend systems, APIs, and database architecture with GPT-4.',
          provider: 'openai',
          model: 'gpt-4',
          status: 'available',
          specializations: ['backend development', 'system architecture', 'database design'],
          capabilities: ['System design', 'API architecture', 'Database optimization'],
        },
        {
          id: 'security-auditor-demo',
          name: 'Security Auditor',
          description: 'Conducts security audits, vulnerability assessments, and compliance checks.',
          provider: 'anthropic',
          model: 'claude-3-sonnet-20240229',
          status: 'available',
          specializations: ['security audit', 'vulnerability assessment', 'compliance'],
          capabilities: ['Security analysis', 'Threat modeling', 'Compliance verification'],
        },
      ];
      setAgents(demoAgents);
      const errorMessage = error.response?.data?.error || 'Using demo data - API not available';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await apiService.getSystemStatus();
      setSystemStatus(response);
    } catch (error: any) {
      // Fallback to demo status
      const demoStatus: AgentSystemStatus = {
        system_status: 'demo_mode',
        total_agents: 6,
        active_agents: 6,
        demo_agents: 6,
        providers: {
          mistral: {
            configured: true,
            status: 'demo_mode',
            agents: ['code-reviewer-demo', 'data-analyst-demo', 'technical-writer-demo'],
          },
          anthropic: {
            configured: true,
            status: 'demo_mode',
            agents: ['business-analyst-demo', 'security-auditor-demo'],
          },
          openai: {
            configured: true,
            status: 'demo_mode',
            agents: ['backend-architect-demo'],
          },
        },
        timestamp: new Date().toISOString(),
      };
      setSystemStatus(demoStatus);
      console.error('Failed to fetch system status, using demo data:', error);
    }
  };

  const testAgent = async (agentId: string) => {
    try {
      const agent = agents.find(a => a.id === agentId);
      if (!agent) return;

      toast.info(`Testing ${agent.name}...`);
      
      await apiService.executeTask({
        agent_id: agentId,
        task: 'Hello! This is a test message. Please respond to confirm you are working correctly.'
      });

      toast.success(`${agent.name} test completed successfully!`);
      
      // Refresh agents to get updated status
      await fetchAgents();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Agent test failed';
      toast.error(errorMessage);
    }
  };

  const value: AgentContextType = {
    agents,
    systemStatus,
    loading,
    error,
    fetchAgents,
    fetchSystemStatus,
    testAgent,
    selectedAgent,
    setSelectedAgent,
  };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
};

export const useAgents = (): AgentContextType => {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgents must be used within an AgentProvider');
  }
  return context;
};