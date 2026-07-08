import React from 'react';

export type AlertType = 'success' | 'error' | 'warning' | 'info';

interface AlertBannerProps {
  type: AlertType;
  message: string;
  onClose?: () => void;
  closeable?: boolean;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  message,
  onClose,
  closeable = true,
}) => {
  const bgColors = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  };

  const textColors = {
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800',
  };

  const iconEmojis = {
    success: '\u2705',
    error: '\u274c',
    warning: '\u26a0\ufe0f',
    info: '\u2139\ufe0f',
  };

  return (
    <div className={`p-4 border rounded-lg flex justify-between items-center ${bgColors[type]}`}>
      <div className={`flex items-center gap-3 ${textColors[type]}`}>
        <span className="text-xl">{iconEmojis[type]}</span>
        <p className="text-sm font-medium">{message}</p>
      </div>
      {closeable && onClose && (
        <button onClick={onClose} className={`text-lg cursor-pointer ${textColors[type]}`}>
          {'\u2715'}
        </button>
      )}
    </div>
  );
};
