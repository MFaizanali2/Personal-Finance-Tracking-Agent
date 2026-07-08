import React from 'react';

interface ProgressBarProps {
  current: number;
  target: number;
  percentage?: number;
  showLabel?: boolean;
  color?: 'blue' | 'green' | 'red' | 'yellow';
  height?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  target,
  percentage,
  showLabel = true,
  color = 'blue',
  height = 'md',
}) => {
  const pct = percentage !== undefined ? percentage : (current / target) * 100;
  const clampedPct = Math.min(100, Math.max(0, pct));

  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };

  const heightClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClasses[height]}`}>
        <div
          className={`${colorClasses[color]} transition-all duration-300 ease-out ${heightClasses[height]}`}
          style={{ width: `${clampedPct}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-gray-600 mt-1">
          {Math.round(clampedPct)}% complete
        </p>
      )}
    </div>
  );
};
