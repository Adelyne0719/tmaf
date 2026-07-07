import { Shield, ArrowLeft } from 'lucide-react';
import type { DetachmentData } from '../utils/githubFetcher';

interface DetachmentProfileViewProps {
  detachment: DetachmentData;
  onBack: () => void;
}

export function DetachmentProfileView({ detachment, onBack }: DetachmentProfileViewProps) {
  return (
    <div className="flex flex-col h-full animate-fade-in">
      <div className="flex items-center gap-3 mb-4 xl:mb-6 border-b border-slate-700 pb-3 xl:pb-4 shrink-0">
        <button 
          onClick={onBack}
          className="p-1 hover:bg-slate-800 rounded-full text-slate-400 hover:text-slate-200 transition-colors"
          title="Back to Checklist"
        >
          <ArrowLeft className="w-5 h-5 xl:w-6 xl:h-6" />
        </button>
        <Shield className="w-5 h-5 xl:w-6 xl:h-6 text-purple-400" />
        <h2 className="text-xl xl:text-2xl font-bold">{detachment.name}</h2>
      </div>

      <div className="flex-grow overflow-y-auto pr-2 custom-scrollbar space-y-6 xl:space-y-8">
        
        {/* Detachment Rules */}
        {detachment.rules.length > 0 && (
          <div>
            <h3 className="text-sm xl:text-base font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" />
              Detachment Rules & Enhancements
            </h3>
            <div className="space-y-3">
              {detachment.rules.map((rule, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-slate-700 rounded-lg p-3 xl:p-4">
                  <div className="font-bold text-emerald-400 mb-2">{rule.name}</div>
                  <div className="text-xs xl:text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{rule.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stratagems */}
        {detachment.stratagems.length > 0 && (
          <div>
            <h3 className="text-sm xl:text-base font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-blue-400" />
              Stratagems
            </h3>
            <div className="space-y-3">
              {detachment.stratagems.map((strat, idx) => (
                <div key={idx} className="bg-blue-900/10 border border-blue-900/50 rounded-lg p-3 xl:p-4">
                  <div className="font-bold text-blue-400 mb-1">{strat.name}</div>
                  <div className="text-[10px] xl:text-xs text-blue-300/70 mb-2 uppercase tracking-wider">{strat.phase}</div>
                  <div className="text-xs xl:text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{strat.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
