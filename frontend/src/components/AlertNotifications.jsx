import { useEffect } from 'react';
import { Bell, AlertTriangle, Info, X, CheckCircle } from 'lucide-react';
import useStore from '@/store';
import { ALERT_SEVERITY_COLORS } from '@/constants';

const severityIcons = {
  critical: AlertTriangle,
  warning: AlertTriangle,
  info: Info,
};

export default function AlertNotifications() {
  const { alerts, alertSummary, fetchAlerts, fetchAlertSummary, dismissAlert } = useStore();

  useEffect(() => {
    fetchAlerts();
    fetchAlertSummary();
  }, [fetchAlerts, fetchAlertSummary]);

  return (
    <div>
      {alertSummary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="card p-4 flex items-center gap-3">
            <Bell size={24} className="text-primary-600" />
            <div><p className="text-sm text-gray-500">Total Alerts</p><p className="text-2xl font-bold">{alertSummary.total}</p></div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <AlertTriangle size={24} className="text-red-600" />
            <div><p className="text-sm text-gray-500">Critical</p><p className="text-2xl font-bold text-red-600">{alertSummary.critical}</p></div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <AlertTriangle size={24} className="text-yellow-600" />
            <div><p className="text-sm text-gray-500">Warnings</p><p className="text-2xl font-bold text-yellow-600">{alertSummary.warning}</p></div>
          </div>
        </div>
      )}

      {alerts.length === 0 && (
        <div className="card p-8 text-center text-gray-500">
          <CheckCircle size={48} className="mx-auto mb-3 text-green-400" />
          <p>No active alerts. Everything looks good!</p>
        </div>
      )}

      <div className="space-y-3">
        {alerts.map((alert, i) => {
          const Icon = severityIcons[alert.severity] || Info;
          return (
            <div key={alert._id || i} className={`border-l-4 rounded-lg p-4 flex items-start justify-between gap-3 ${ALERT_SEVERITY_COLORS[alert.severity] || 'bg-gray-100 border-gray-400'}`}>
              <div className="flex items-start gap-3">
                <Icon size={20} className="mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">{alert.message}</p>
                  <p className="text-xs opacity-70 mt-1">{alert.type?.replace(/_/g, ' ')}</p>
                  {alert.category && <span className="text-xs px-1.5 py-0.5 rounded bg-white/50 mt-1 inline-block">{alert.category}</span>}
                </div>
              </div>
              <button onClick={() => { if (alert._id) dismissAlert(alert._id); }} className="shrink-0 opacity-50 hover:opacity-100 transition-opacity" title="Dismiss">
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
