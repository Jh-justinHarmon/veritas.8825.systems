import { useState, useEffect } from 'react';
import { getHistory, type HistoryEntry } from '../api/veritas';

interface HistoryPanelProps {
  onSelectHistory: (sessionId: string) => void;
  currentSessionId?: string;
}

export function HistoryPanel({ onSelectHistory, currentSessionId }: HistoryPanelProps) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const entries = await getHistory(20, 0);
      setHistory(entries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="w-64 border-r border-slate-800/40 bg-slate-950/50 p-4">
        <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider mb-4">
          History
        </div>
        <div className="text-[11px] text-slate-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-64 border-r border-slate-800/40 bg-slate-950/50 p-4">
        <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider mb-4">
          History
        </div>
        <div className="text-[11px] text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="w-64 border-r border-slate-800/40 bg-slate-950/50 flex flex-col">
      <div className="p-4 border-b border-slate-800/40">
        <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider">
          History
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {history.length === 0 ? (
          <div className="p-4 text-[11px] text-slate-600">
            No history yet. Ask a question to get started.
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => onSelectHistory(entry.id)}
                className={`w-full text-left p-3 rounded transition-colors ${
                  entry.id === currentSessionId
                    ? 'bg-slate-800/60 border border-slate-700/60'
                    : 'hover:bg-slate-800/30 border border-transparent'
                }`}
              >
                <div className="text-[11px] text-slate-300 leading-snug mb-1 line-clamp-2">
                  {entry.question}
                </div>
                <div className="flex items-center gap-2 text-[9px] text-slate-600">
                  <span>{formatTimestamp(entry.timestamp)}</span>
                  <span>•</span>
                  <span>{entry.idea_count} ideas</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
