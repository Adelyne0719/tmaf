import { Swords, Crosshair, ArrowLeft, Zap } from 'lucide-react';
import type { UnitData } from '../utils/githubFetcher';
import type { ParsedUnit } from '../utils/rosterParser';

interface UnitProfileViewProps {
  unitData: UnitData;
  parsedUnit: ParsedUnit;
  onBack: () => void;
}

export function UnitProfileView({ unitData, parsedUnit, onBack }: UnitProfileViewProps) {
  const { stats, abilities, keywords } = unitData;

  const filterWeapons = (weapons: any[]) => {
    if (!weapons || weapons.length === 0) return [];
    const equipped = weapons.filter(w => parsedUnit.rawText.toLowerCase().includes(w.name.toLowerCase()));
    return equipped.length > 0 ? equipped : weapons;
  };

  const rangedWeapons = filterWeapons(unitData.rangedWeapons);
  const meleeWeapons = filterWeapons(unitData.meleeWeapons);

  return (
    <div className="flex flex-col h-auto xl:h-full xl:overflow-hidden animate-fade-in">
      <div className="flex items-center gap-3 mb-4 shrink-0">
        <button 
          onClick={onBack}
          className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          title="Back to Checklist"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h2 className="text-2xl font-bold text-slate-100 flex-grow">{unitData.name}</h2>
      </div>

      <div className="flex-grow xl:overflow-y-auto pr-2 custom-scrollbar space-y-6 pb-6">
        
        {/* Base Stats */}
        {stats && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <table className="w-full text-sm text-center">
              <thead className="bg-slate-800/80 text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">M</th>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">T</th>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">SV</th>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">W</th>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">LD</th>
                  <th className="py-2 px-3 font-semibold border-b border-slate-700">OC</th>
                  {stats.insv !== '-' && <th className="py-2 px-3 font-semibold border-b border-slate-700 text-blue-400">InSv</th>}
                </tr>
              </thead>
              <tbody className="text-slate-200 font-medium">
                <tr>
                  <td className="py-3 px-3">{stats.m}</td>
                  <td className="py-3 px-3">{stats.t}</td>
                  <td className="py-3 px-3">{stats.sv}</td>
                  <td className="py-3 px-3">{stats.w}</td>
                  <td className="py-3 px-3">{stats.ld}</td>
                  <td className="py-3 px-3">{stats.oc}</td>
                  {stats.insv !== '-' && <td className="py-3 px-3 text-blue-400 font-bold">{stats.insv}</td>}
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Ranged Weapons */}
        {rangedWeapons.length > 0 && (
          <div>
            <h3 className="text-sm xl:text-base font-bold text-slate-300 uppercase tracking-wider mb-2 xl:mb-3 flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-blue-400" />
              Ranged Weapons
            </h3>
            <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-800/50 custom-scrollbar">
              <table className="w-full text-left text-xs xl:text-sm whitespace-nowrap">
                <thead className="bg-slate-700/50 text-slate-300">
                  <tr>
                    <th className="p-2 xl:p-3 font-semibold">Weapon</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">Range</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">A</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">BS</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">S</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">AP</th>
                    <th className="p-2 xl:p-3 font-semibold text-center">D</th>
                    <th className="p-2 xl:p-3 font-semibold">Keywords</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {rangedWeapons.map((w, idx) => (
                    <tr key={idx} className="text-slate-300">
                      <td className="py-2 px-3 font-medium text-slate-200">{w.name}</td>
                      <td className="py-2 px-2 text-center">{w.range}</td>
                      <td className="py-2 px-2 text-center">{w.a}</td>
                      <td className="py-2 px-2 text-center">{w.bsws}</td>
                      <td className="py-2 px-2 text-center">{w.s}</td>
                      <td className="py-2 px-2 text-center">{w.ap}</td>
                      <td className="py-2 px-2 text-center">{w.d}</td>
                      <td className="py-2 px-2 text-xs text-orange-300/80 italic">{w.keywords}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Melee Weapons */}
        {meleeWeapons.length > 0 && (
        <div>
          <h3 className="text-sm xl:text-base font-bold text-slate-300 uppercase tracking-wider mb-2 xl:mb-3 flex items-center gap-2">
            <Swords className="w-4 h-4 text-red-400" />
            Melee Weapons
          </h3>
          <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-800/50 custom-scrollbar">
            <table className="w-full text-left text-xs xl:text-sm whitespace-nowrap">
              <thead className="bg-slate-700/50 text-slate-300">
                <tr>
                  <th className="p-2 xl:p-3 font-semibold">Weapon</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">Range</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">A</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">WS</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">S</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">AP</th>
                  <th className="p-2 xl:p-3 font-semibold text-center">D</th>
                  <th className="p-2 xl:p-3 font-semibold">Keywords</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {meleeWeapons.map((w, idx) => (
                    <tr key={idx} className="text-slate-300">
                      <td className="py-2 px-3 font-medium text-slate-200">{w.name}</td>
                      <td className="py-2 px-2 text-center">{w.range}</td>
                      <td className="py-2 px-2 text-center">{w.a}</td>
                      <td className="py-2 px-2 text-center">{w.bsws}</td>
                      <td className="py-2 px-2 text-center">{w.s}</td>
                      <td className="py-2 px-2 text-center">{w.ap}</td>
                      <td className="py-2 px-2 text-center">{w.d}</td>
                      <td className="py-2 px-2 text-xs text-orange-300/80 italic">{w.keywords}</td>
                    </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        )}

        {/* Abilities */}
        {abilities.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              <h3 className="font-bold text-slate-200 text-sm uppercase tracking-wide">Abilities</h3>
            </div>
            {abilities.map((ab, idx) => (
              <div key={idx} className="bg-slate-800/40 p-3 rounded-lg border border-slate-700">
                <h4 className="font-bold text-slate-200 text-sm mb-1">{ab.name}</h4>
                <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">{ab.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Keywords */}
        {keywords.length > 0 && (
          <div className="pt-4 border-t border-slate-700/50">
            <h3 className="font-bold text-slate-500 text-xs uppercase tracking-wide mb-2">Keywords</h3>
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw, idx) => (
                <span key={idx} className="px-2 py-1 rounded bg-slate-800 text-slate-300 text-xs border border-slate-700 font-medium uppercase">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
