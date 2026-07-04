import AgentStatus from '@/components/AgentStatus';

export default function AgentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agent Console</h1>
        <p className="text-sm text-gray-500 mt-1">
          Monitor the ReACT agent's reasoning, actions, and state.
        </p>
      </div>
      <AgentStatus />
    </div>
  );
}
