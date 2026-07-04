import GoalForm from '@/components/GoalForm';
import GoalDashboard from '@/components/GoalDashboard';

export default function GoalsPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Savings Goals</h1>
      </div>
      <div className="mb-8">
        <GoalForm />
      </div>
      <GoalDashboard />
    </div>
  );
}
