import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { CheckCircle2, AlertTriangle, Info, XCircle, X, Ship, Anchor, Bell } from 'lucide-react';

export interface Toast {
  id: string;
  type: 'success' | 'warning' | 'info' | 'error' | 'vessel-arrival' | 'vessel-departure' | 'berth-update';
  title: string;
  message: string;
  timestamp: Date;
  duration?: number; // ms, default 5000
}

interface ToastContextValue {
  addToast: (toast: Omit<Toast, 'id' | 'timestamp'>) => void;
  removeToast: (id: string) => void;
  toasts: Toast[];
}

const ToastContext = createContext<ToastContextValue>({
  addToast: () => {},
  removeToast: () => {},
  toasts: [],
});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id' | 'timestamp'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const newToast: Toast = { ...toast, id, timestamp: new Date() };
    setToasts(prev => [...prev, newToast]);

    // Auto-remove
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast, toasts }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

const TOAST_STYLES: Record<Toast['type'], { icon: React.ReactNode; bg: string; border: string; iconColor: string }> = {
  success: { icon: <CheckCircle2 className="w-4 h-4" />, bg: '#ECFDF5', border: '#059669', iconColor: '#059669' },
  warning: { icon: <AlertTriangle className="w-4 h-4" />, bg: '#FFFBEB', border: '#D97706', iconColor: '#D97706' },
  info: { icon: <Info className="w-4 h-4" />, bg: '#EFF6FF', border: '#2563EB', iconColor: '#2563EB' },
  error: { icon: <XCircle className="w-4 h-4" />, bg: '#FEF2F2', border: '#DC2626', iconColor: '#DC2626' },
  'vessel-arrival': { icon: <Ship className="w-4 h-4" />, bg: '#ECFDF5', border: '#059669', iconColor: '#059669' },
  'vessel-departure': { icon: <Ship className="w-4 h-4" />, bg: '#EFF6FF', border: '#2563EB', iconColor: '#2563EB' },
  'berth-update': { icon: <Anchor className="w-4 h-4" />, bg: '#F5F3FF', border: '#7C3AED', iconColor: '#7C3AED' },
};

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[200] flex flex-col-reverse gap-2" style={{ maxWidth: 380 }}>
      {toasts.slice(-5).map((toast, idx) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} index={idx} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove, index }: { toast: Toast; onRemove: (id: string) => void; index: number }) {
  const [isVisible, setIsVisible] = useState(false);
  const style = TOAST_STYLES[toast.type];

  useEffect(() => {
    requestAnimationFrame(() => setIsVisible(true));
  }, []);

  return (
    <div
      className="rounded-lg shadow-xl overflow-hidden transition-all duration-300"
      style={{
        backgroundColor: style.bg,
        border: `1.5px solid ${style.border}`,
        transform: isVisible ? 'translateX(0)' : 'translateX(120%)',
        opacity: isVisible ? 1 : 0,
        minWidth: 320,
      }}
    >
      <div className="flex items-start gap-2.5 p-3">
        <span className="flex-shrink-0 mt-0.5" style={{ color: style.iconColor }}>{style.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-bold" style={{ color: 'var(--foreground)' }}>{toast.title}</div>
          <div className="text-[11px] mt-0.5 leading-relaxed" style={{ color: 'var(--muted-foreground)' }}>{toast.message}</div>
          <div className="text-[9px] mt-1" style={{ color: 'var(--muted-foreground)' }}>
            {toast.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="flex-shrink-0 p-0.5 rounded hover:bg-black/5 transition-colors"
          style={{ border: 'none', cursor: 'pointer', background: 'transparent' }}
        >
          <X className="w-3.5 h-3.5" style={{ color: 'var(--muted-foreground)' }} />
        </button>
      </div>
      {/* Progress bar */}
      <div className="h-0.5 w-full" style={{ backgroundColor: `${style.border}20` }}>
        <div
          className="h-full transition-none"
          style={{
            backgroundColor: style.border,
            animation: `toast-progress ${(toast.duration ?? 5000) / 1000}s linear forwards`,
          }}
        />
      </div>
    </div>
  );
}
