import { AlertTriangle, X } from 'lucide-react';

export default function ConfirmDialog({ open, title = 'Confirm', message = 'Are you sure?', confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'danger', onConfirm, onCancel }) {
  if (!open) return null;

  const confirmColors = variant === 'danger'
    ? 'bg-red-600 hover:bg-red-700'
    : variant === 'warning'
    ? 'bg-yellow-600 hover:bg-yellow-700'
    : 'bg-primary-600 hover:bg-primary-700';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onCancel}>
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-full bg-red-100">
              <AlertTriangle size={20} className="text-red-600" />
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="btn btn-secondary">{cancelLabel}</button>
          <button onClick={onConfirm} className={`btn text-white ${confirmColors}`}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}
