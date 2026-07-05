import { AlertTriangle, Info, CheckCircle, X } from 'lucide-react';

const styles = {
  critical: { icon: AlertTriangle, bg: 'bg-red-50 border-red-200 text-red-800', iconColor: 'text-red-500' },
  warning: { icon: AlertTriangle, bg: 'bg-yellow-50 border-yellow-200 text-yellow-800', iconColor: 'text-yellow-500' },
  info: { icon: Info, bg: 'bg-blue-50 border-blue-200 text-blue-800', iconColor: 'text-blue-500' },
  success: { icon: CheckCircle, bg: 'bg-green-50 border-green-200 text-green-800', iconColor: 'text-green-500' },
};

export default function AlertBanner({ severity = 'info', message, onDismiss, className = '' }) {
  const style = styles[severity] || styles.info;
  const Icon = style.icon;

  if (!message) return null;

  return (
    <div className={`flex items-start gap-3 p-4 rounded-lg border ${style.bg} ${className}`}>
      <Icon size={18} className={`shrink-0 mt-0.5 ${style.iconColor}`} />
      <p className="text-sm flex-1">{message}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 opacity-60 hover:opacity-100 transition-opacity">
          <X size={16} />
        </button>
      )}
    </div>
  );
}
