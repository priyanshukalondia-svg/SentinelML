import { AlertCircle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import clsx from "clsx";

type ToastTone = "success" | "error" | "warning" | "info";

interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastContextValue {
  push: (toast: Omit<Toast, "id">) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const ICONS: Record<ToastTone, ReactNode> = {
  success: <CheckCircle2 size={18} className="text-healthy-dot" />,
  error: <XCircle size={18} className="text-critical-dot" />,
  warning: <AlertCircle size={18} className="text-warning-dot" />,
  info: <Info size={18} className="text-info-dot" />,
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const push = useCallback((toast: Omit<Toast, "id">) => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  }, []);

  const dismiss = (id: number) => setToasts((prev) => prev.filter((t) => t.id !== id));

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex w-80 flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={clsx(
              "pointer-events-auto animate-fade-in rounded-xl border border-border bg-surface p-3.5 shadow-popover"
            )}
          >
            <div className="flex items-start gap-2.5">
              {ICONS[toast.tone]}
              <div className="flex-1">
                <p className="text-sm font-semibold text-ink">{toast.title}</p>
                {toast.description && <p className="mt-0.5 text-xs text-ink-muted">{toast.description}</p>}
              </div>
              <button onClick={() => dismiss(toast.id)} className="text-ink-faint hover:text-ink-muted">
                <X size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
