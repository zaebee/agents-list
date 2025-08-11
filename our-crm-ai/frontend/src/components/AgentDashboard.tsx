import React from 'react';
import { Bot, Play, Settings, Zap, Brain, Cpu } from 'lucide-react';
import { useAgents } from '../contexts/AgentContext';

export default function AgentDashboard() {
  const { agents, systemStatus, loading, testAgent } = useAgents();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'busy':
        return 'bg-blue-100 text-blue-800';
      case 'offline':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'mistral':
        return <Zap className="text-orange-500" />;
      case 'anthropic':
        return <Brain className="text-purple-500" />;
      case 'openai':
        return <Cpu className="text-green-500" />;
      default:
        return <Bot className="text-blue-500" />;
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'mistral':
        return 'bg-orange-100';
      case 'anthropic':
        return 'bg-purple-100';
      case 'openai':
        return 'bg-green-100';
      default:
        return 'bg-blue-100';
    }
  };

  const getProviderBorder = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'mistral':
        return 'border-l-orange-400';
      case 'anthropic':
        return 'border-l-purple-400';
      case 'openai':
        return 'border-l-green-400';
      default:
        return 'border-l-blue-400';
    }
  };

  const getProviderName = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'mistral':
        return 'Mistral AI';
      case 'anthropic':
        return 'Anthropic';
      case 'openai':
        return 'OpenAI';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center text-white">
          <div className="loading-spinner w-12 h-12 mx-auto mb-4"></div>
          <p>Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white/95 backdrop-blur-sm rounded-xl p-6 shadow-lg">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">AI Agent Dashboard</h1>
        <p className="text-gray-600">Monitor and manage your AI agents</p>
      </div>

      {/* System Status */}
      {systemStatus && (
        <div className="bg-white/95 backdrop-blur-sm rounded-xl p-6 shadow-lg">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">{systemStatus.total_agents}</div>
              <div className="text-sm text-gray-600">Total Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{systemStatus.active_agents}</div>
              <div className="text-sm text-gray-600">Active Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{agents.filter(a => a.provider?.toLowerCase() === 'mistral').length}</div>
              <div className="text-sm text-gray-600">Mistral Agents</div>
            </div>
            <div className="text-center">
              <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                systemStatus.system_status === 'ready' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {systemStatus.system_status}
              </div>
              <div className="text-sm text-gray-600 mt-1">System Status</div>
            </div>
          </div>
          
          {/* Provider breakdown */}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">AI Providers</h3>
            <div className="flex flex-wrap gap-3">
              {['mistral', 'anthropic', 'openai'].map(provider => {
                const count = agents.filter(a => a.provider?.toLowerCase() === provider).length;
                if (count === 0) return null;
                return (
                  <div key={provider} className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${getProviderColor(provider)}`}>
                    {getProviderIcon(provider)}
                    <span className="text-sm font-medium">{getProviderName(provider)}</span>
                    <span className="text-xs bg-white px-2 py-1 rounded-full">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.length === 0 ? (
          <div className="col-span-full card text-center py-12">
            <Bot size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No agents available</h3>
            <p className="text-gray-500">Agents will appear here when they are configured.</p>
          </div>
        ) : (
          agents.map((agent) => (
            <div key={agent.id} className={`card hover:shadow-xl transition-shadow border-l-4 ${getProviderBorder(agent.provider)}`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${getProviderColor(agent.provider)}`}>
                    {getProviderIcon(agent.provider)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <span>{getProviderName(agent.provider)}</span>
                      <span>•</span>
                      <span className="font-mono text-xs">{agent.model}</span>
                    </div>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>

              <p className="text-gray-700 text-sm mb-4">{agent.description}</p>

              {agent.specializations.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs font-medium text-gray-600 mb-2">Specializations</div>
                  <div className="flex flex-wrap gap-1">
                    {agent.specializations.map((spec, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                      >
                        {spec}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex space-x-2">
                <button
                  onClick={() => testAgent(agent.id)}
                  className="btn-primary flex-1 text-sm py-2 flex items-center justify-center space-x-1"
                >
                  <Play size={16} />
                  <span>Test</span>
                </button>
                <button className="btn-outline flex-1 text-sm py-2 flex items-center justify-center space-x-1">
                  <Settings size={16} />
                  <span>Config</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}