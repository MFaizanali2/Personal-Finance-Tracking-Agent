import { Target, TrendingUp, CheckCircle, DollarSign } from 'lucide-react';
import { formatCurrency } from '@/utils';

export default function GoalStats({ goals = [] }) {
  if (goals.length === 0) return null;

  const active = goals.filter((g) => g.status === 'active');
  const completed = goals.filter((g) => g.status === 'completed');
  const totalTarget = goals.reduce((s, g) => s + (g.target_amount || 0), 0);
  const totalSaved = goals.reduce((s, g) => s + (g.current_amount || 0), 0);
  const overallPct = totalTarget > 0 ? Math.round((totalSaved / totalTarget) * 100) : 0;
  const avgProgress = goals.length > 0
    ? Math.round(goals.reduce((s, g) => s + ((g.current_amount || 0) / (g.target_amount || 1)) * 100, 0) / goals.length)
    : 0;

  const stats = [
    { label: 'Active Goals', value: active.length, icon: Target, color: 'text-primary-600' },
    { label: 'Completed', value: completed.length, icon: CheckCircle, color: 'text-green-600' },
    { label: 'Overall Progress', value: `${overallPct}%`, icon: TrendingUp, color: 'text-blue-600' },
    { label: 'Total Saved', value: formatCurrency(totalSaved), icon: DollarSign, color: 'text-purple-600' },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.label} className="card p-4 flex items-center gap-3">
            <Icon size={24} className={`shrink-0 ${stat.color}`} />
            <div className="min-w-0">
              <p className="text-xs text-gray-500 truncate">{stat.label}</p>
              <p className="text-xl font-bold truncate">{stat.value}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
