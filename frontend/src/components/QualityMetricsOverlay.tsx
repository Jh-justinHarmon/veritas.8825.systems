/**
 * Quality Metrics Overlay
 * 
 * Small overlay in top right showing synthesis mode and quality metrics.
 * For demo purposes - shows input-agnostic proof live.
 */

interface QualityMetrics {
  idea_count: number;
  paragraphs_per_idea: number;
  tier_diversity: number;
  citation_density: number;
  concept_clarity: number;
  source_coverage: number;
}

interface QualityMetricsOverlayProps {
  mode: 'raw' | 'abstracted';
  metrics: QualityMetrics | null;
  onToggleMode: () => void;
}

export function QualityMetricsOverlay({ mode, metrics, onToggleMode }: QualityMetricsOverlayProps) {
  if (!metrics) return null;

  return (
    <div className="fixed top-4 right-4 bg-slate-900/95 border border-slate-700 rounded-lg p-3 text-xs font-mono z-50 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-700">
        <span className="text-slate-400">Mode:</span>
        <button
          onClick={onToggleMode}
          className="px-3 py-1.5 rounded transition-colors text-xs font-semibold"
          style={{
            backgroundColor: mode === 'raw' ? 'rgb(59 130 246 / 0.2)' : 'rgb(168 85 247 / 0.2)',
            color: mode === 'raw' ? 'rgb(147 197 253)' : 'rgb(216 180 254)',
            border: mode === 'raw' ? '1px solid rgb(59 130 246 / 0.5)' : '1px solid rgb(168 85 247 / 0.5)'
          }}
        >
          {mode === 'raw' ? 'RAW' : 'ABSTRACTED'}
        </button>
      </div>
      
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Ideas:</span>
          <span className="text-slate-200">{metrics.idea_count}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Tiers:</span>
          <span className="text-slate-200">{metrics.tier_diversity}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Cite/Para:</span>
          <span className="text-slate-200">{metrics.citation_density.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Coverage:</span>
          <span className="text-slate-200">{(metrics.source_coverage * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      <div className="mt-2 pt-2 border-t border-slate-700 text-[10px] text-slate-500">
        Input-agnostic proof
      </div>
    </div>
  );
}
