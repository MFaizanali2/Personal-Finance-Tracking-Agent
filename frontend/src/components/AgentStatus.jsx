import { useEffect, useState, useRef } from 'react';
import {
  RefreshCw,
  Brain,
  Zap,
  Eye,
  RotateCcw,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import useStore from '@/store';

const STEP_ICONS = {
  think: Brain,
  act: Zap,
  observe: Eye,
  reflect: RotateCcw,
};

const STEP_COLORS = {
  think: 'border-blue-400 bg-blue-50 text-blue-700',
  act: 'border-orange-400 bg-orange-50 text-orange-700',
  observe: 'border-green-400 bg-green-50 text-green-700',
  reflect: 'border-purple-400 bg-purple-50 text-purple-700',
};

export default function AgentStatus() {
  const agentStatus = useStore((s) => s.agentStatus);
  const fetchAgentStatus = useStore((s) => s.fetchAgentStatus);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchAgentStatus();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchAgentStatus, 5000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh]);

  if (!agentStatus) {
    return (
      <div className="card flex items-center justify-center py-12">
        <Loader2 size={24} className="animate-spin text-primary-600" />
        <span className="ml-2 text-gray-500">Loading agent state...</span>
      </div>
    );
  }

  const memory = agentStatus.memory_summary || {};
  const thoughts = memory.total_thoughts || 0;
  const actions = memory.total_actions || 0;
  const observations = memory.total_observations || 0;
  const reflections = memory.total_reflections || 0;

  const steps = [
    { label: 'Think', count: thoughts, icon: STEP_ICONS.think, color: STEP_COLORS.think },
    { label: 'Act', count: actions, icon: STEP_ICONS.act, color: STEP_COLORS.act },
    { label: 'Observe', count: observations, icon: STEP_ICONS.observe, color: STEP_COLORS.observe },
    { label: 'Reflect', count: reflections, icon: STEP_ICONS.reflect, color: STEP_COLORS.reflect },
  ];

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="text-primary-600" size={20} />
            Agent ReACT Status
          </h2>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300"
              />
              Auto-refresh (5s)
            </label>
            <button onClick={fetchAgentStatus} className="btn-outline text-xs">
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-xs text-gray-500 block mb-1">Thinking State</span>
            <p className="text-sm text-gray-800 font-medium">
              {agentStatus.thinking_state || 'Idle'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-xs text-gray-500 block mb-1">Executed Actions</span>
            <div className="flex flex-wrap gap-1">
              {(agentStatus.executed_actions || []).length > 0 ? (
                agentStatus.executed_actions.map((a, i) => (
                  <span key={i} className="badge-blue text-[10px]">
                    {a}
                  </span>
                ))
              ) : (
                <span className="text-sm text-gray-400">None</span>
              )}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-xs text-gray-500 block mb-1">Cycle Count</span>
            <p className="text-lg font-bold text-gray-900">{agentStatus.current_cycle || 0}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <span className="text-xs text-gray-500 block mb-1">Errors</span>
            <p
              className={`text-lg font-bold ${(agentStatus.error_count || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}
            >
              {agentStatus.error_count || 0}
            </p>
          </div>
        </div>

        <div className="relative">
          <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 hidden sm:block" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {steps.map(({ label, count, icon: Icon, color }, i) => (
              <div key={label} className="relative flex flex-col items-center">
                <div
                  className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 ${color} mb-2`}
                >
                  <Icon size={18} />
                </div>
                <span className="text-xs font-medium text-gray-700">{label}</span>
                <span className="text-lg font-bold text-gray-900">{count}</span>
                {i < steps.length - 1 && (
                  <div className="hidden sm:block absolute top-5 left-[60%] w-[80%] h-0.5 bg-gray-200" />
                )}
              </div>
            ))}
          </div>
        </div>

        {agentStatus.task_complete && (
          <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 rounded-lg px-3 py-2 text-sm">
            <CheckCircle2 size={16} />
            Task complete
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Latest Reflection</h3>
        <p className="text-sm text-gray-600">
          {memory.latest_reflection || 'No reflections yet'}
        </p>
        <h3 className="text-sm font-semibold text-gray-900 mt-4 mb-3">Latest Thought</h3>
        <p className="text-sm text-gray-600">
          {memory.latest_thought || 'No thoughts yet'}
        </p>
      </div>
    </div>
  );
}
