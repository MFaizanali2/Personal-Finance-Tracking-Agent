import { useEffect } from 'react';
import { RefreshCw, DollarSign, TrendingUp, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import useStore from '@/store';
import { formatCurrency } from '@/utils';

const cards = [
  { key: 'totalAmount', label: 'Total Spent', icon: DollarSign, color: 'bg-blue-500', format: (v) => formatCurrency(v) },
  { key: 'count', label: 'Transactions', icon: TrendingUp, color: 'bg-green-500', format: (v) => `${v || 0}` },
  { key: 'average', label: 'Average', icon: TrendingUp, color: 'bg-purple-500', format: (v) => formatCurrency(v) },
  {
    key: 'confirmed',
    label: 'Confirmed',
    icon: CheckCircle,
    color: 'bg-emerald-500',
    format: (v) => `${v || 0}`,
  },
  {
    key: 'pending',
    label: 'Pending',
    icon: Clock,
    color: 'bg-yellow-500',
    format: (v) => `${v || 0}`,
  },
  {
    key: 'flagged',
    label: 'Flagged',
    icon: AlertTriangle,
    color: 'bg-red-500',
    format: (v) => `${v || 0}`,
  },
];

export default function SummaryDashboard() {
  const summary = useStore((s) => s.summary);
  const transactions = useStore((s) => s.transactions);
  const fetchSummary = useStore((s) => s.fetchSummary);

  useEffect(() => {
    fetchSummary();
  }, [transactions]);

  if (!summary || summary.count === 0) {
    return (
      <div className="card text-center py-6">
        <p className="text-gray-400">No data to summarize</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
        <button onClick={fetchSummary} className="btn-outline text-xs">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {cards.map(({ key, label, icon: Icon, color, format }) => (
          <div key={key} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
            <div className="flex items-center gap-2 mb-1">
              <div className={`${color} rounded-full p-1 text-white`}>
                <Icon size={14} />
              </div>
              <span className="text-xs text-gray-500">{label}</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{format(summary[key])}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
