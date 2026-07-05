import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ size = 24, text = 'Loading...', className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 text-gray-400 ${className}`}>
      <Loader2 size={size} className="animate-spin mb-2" />
      {text && <p className="text-sm">{text}</p>}
    </div>
  );
}
