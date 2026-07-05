import { formatPercent } from '@/utils';

const colorMap = {
  green: 'bg-green-500',
  blue: 'bg-blue-500',
  primary: 'bg-primary-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
};

export default function ProgressBar({ value = 0, max = 100, color = 'primary', showLabel = false, size = 'md', className = '' }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const height = size === 'sm' ? 'h-1.5' : size === 'lg' ? 'h-4' : 'h-2.5';
  const barColor = pct >= 100 ? colorMap.red : pct >= 80 ? colorMap.yellow : colorMap[color] || colorMap.primary;

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-500">{formatPercent(pct / 100)}</span>
          <span className="font-medium">{Math.round(pct)}%</span>
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${height}`}>
        <div className={`${height} rounded-full transition-all duration-500 ${barColor}`}
             style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
