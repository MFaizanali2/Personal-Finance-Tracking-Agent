import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import useStore from '@/store';

interface ToastData {
  message: string;
  type: 'success' | 'error' | 'info';
}

export default function Toast() {
  const toast = useStore((s: { toast: ToastData | null }) => s.toast) as ToastData | null;
  const clearToast = useStore((s: { clearToast: () => void }) => s.clearToast) as () => void;

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(clearToast, 4000);
      return () => clearTimeout(timer);
    }
  }, [toast, clearToast]);

  if (!toast) return null;

  const bg =
    toast.type === 'success'
      ? 'bg-green-600'
      : toast.type === 'error'
        ? 'bg-red-600'
        : 'bg-blue-600';

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className={`${bg} text-white rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 max-w-sm`}>
        <span className="text-sm flex-1">{toast.message}</span>
        <button onClick={clearToast} className="hover:opacity-80">
          <X size={16} />
        </button>
      </div>
    </div>
  );
}
