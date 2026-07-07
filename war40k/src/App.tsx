import { useState, useEffect } from 'react';
import { parseRoster } from './utils/rosterParser';
import type { ParsedUnit, RosterMeta } from './utils/rosterParser';
import { fetchFactionData, type UnitData, type DetachmentData, type Ability, determinePhase } from './utils/githubFetcher';
import { Shield, Swords, Crosshair, Loader2, Info, GripVertical, Users, X, ShieldAlert, ChevronLeft, Menu, ChevronDown, ChevronUp } from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import type { DropResult } from '@hello-pangea/dnd';
import { UnitProfileView } from './components/UnitProfileView';
import { DetachmentProfileView } from './components/DetachmentProfileView';

const PHASES = [
  'Command Phase',
  'Movement Phase',
  'Shooting Phase',
  'Charge Phase',
  'Fight Phase',
  'Command Phase (Battle-shock)',
  'Deployment',
  'Other / Any Phase'
];

function filterAbilityForLeader(abilityDesc: string, attachedBodyguardName: string | null): string | null {
    const sentences = abilityDesc.split(/(?<=\.)\s+/).map(s => s.trim()).filter(s => s.length > 0);
    const validSentences: string[] = [];
    
    for (const sentence of sentences) {
        const leadingMatches = [...sentence.matchAll(/(?:lead(?:s|ing)|attached to) (?:an?\s+)?([a-z0-9'’\-\s]+?)\s+unit/gi)];
        
        if (leadingMatches.length === 0) {
            validSentences.push(sentence);
            continue;
        }
        
        if (!attachedBodyguardName) continue;
        
        const bgName = attachedBodyguardName.toLowerCase();
        let sentenceMatches = false;
        
        for (const match of leadingMatches) {
            let reqBg = match[1].trim().toLowerCase();
            reqBg = reqBg.replace(/^(friendly|enemy)\s+/i, '');

            if (['adeptus astartes', 'space wolves', 'infantry', 'character', 'mounted', 'vehicle', 'jump pack', 'phobos', 'terminator', 'gravis'].includes(reqBg) || reqBg === '') {
                sentenceMatches = true; 
                break;
            }
            if (bgName.includes(reqBg) || reqBg.includes(bgName)) {
                sentenceMatches = true;
                break;
            }
        }
        
        if (sentenceMatches) {
            validSentences.push(sentence);
        }
    }
    
    if (validSentences.length === 0) return null;
    
    return validSentences.join(' ');
}

function guessCatFileName(text: string): string {
  // First try to extract from title if it matches BattleScribe format (SuperFaction - Faction - SubFaction)
  const firstLine = text.split('\n')[0];
  if (firstLine && firstLine.includes(' - ')) {
    const parts = firstLine.split(' - ').map(p => p.trim());
    if (parts.length >= 2) {
      let faction = parts[1];
      
      // Handle Adeptus Astartes sub-factions
      if (faction === 'Adeptus Astartes' || faction === 'Space Marines') {
         faction = 'Space Marines';
         if (parts.length >= 3) {
            const sub = parts[2];
            if (sub.includes('Space Wolves')) return 'Imperium - Space Wolves.json';
            else if (sub.includes('Blood Angels')) return 'Imperium - Blood Angels.json';
            else if (sub.includes('Dark Angels')) return 'Imperium - Dark Angels.json';
            else if (sub.includes('Black Templars')) return 'Imperium - Black Templars.json';
            else if (sub.includes('Deathwatch')) return 'Imperium - Deathwatch.json';
         }
         return 'Imperium - Space Marines.json';
      }
      
      return `${parts[0]} - ${faction}.json`.replace('Adeptus Astartes', 'Imperium');
    }
  }

  // Fallback to text search
  if (text.includes('Space Wolves')) return 'Imperium - Space Wolves.json';
  if (text.includes('Adeptus Astartes') || text.includes('Space Marines')) return 'Imperium - Space Marines.json';

  // Absolute fallback
  return 'Imperium - Space Wolves.json';
}

function getPhaseUIInfo(phase: string) {
  switch (phase) {
    case 'Command Phase': return { num: '1', eng: 'COMMAND' };
    case 'Movement Phase': return { num: '2', eng: 'MOVEMENT' };
    case 'Shooting Phase': return { num: '3', eng: 'SHOOTING' };
    case 'Charge Phase': return { num: '4', eng: 'CHARGE' };
    case 'Fight Phase': return { num: '5', eng: 'FIGHT' };
    case 'Command Phase (Battle-shock)': return { num: '!', eng: 'BATTLE-SHOCK' };
    case 'Deployment': return { num: '0', eng: 'DEPLOYMENT' };
    default: return { num: '?', eng: 'OTHER' };
  }
}

function PhaseChecklistTable({ checklists, filterUnitIds }: { checklists: Record<string, any[]>, filterUnitIds?: string[] }) {
  const [activeTurn, setActiveTurn] = useState<'my' | 'opp'>('my');

  return (
    <div className="border border-slate-600 rounded-xl overflow-hidden bg-slate-900 flex flex-col text-sm xl:text-base">
       {/* Mobile Turn Toggle (Hidden in landscape since we have enough width) */}
       <div className="flex xl:hidden border-b border-slate-600 bg-slate-800">
          <button 
             onClick={() => setActiveTurn('my')}
             className={`flex-1 py-3 text-center font-bold text-sm transition-colors ${activeTurn === 'my' ? 'bg-blue-600/20 text-blue-400 border-b-2 border-blue-500' : 'text-slate-400 hover:bg-slate-700/50'}`}
          >
             MY TURN
          </button>
          <button 
             onClick={() => setActiveTurn('opp')}
             className={`flex-1 py-3 text-center font-bold text-sm transition-colors ${activeTurn === 'opp' ? 'bg-orange-600/20 text-orange-400 border-b-2 border-orange-500' : 'text-slate-400 hover:bg-slate-700/50'}`}
          >
             OPP TURN
          </button>
       </div>

       {/* Table Header */}
       <div className="flex bg-slate-400 text-slate-900 font-bold border-b border-slate-600">
          <div className="w-10 landscape:w-1/6 xl:w-24 p-2 xl:p-3 text-center border-r border-slate-500 flex items-center justify-center shrink-0">
             <span className="landscape:hidden xl:hidden text-xs" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}>PHASE</span>
             <span className="hidden landscape:inline xl:inline">PHASE</span>
          </div>
          <div className={`p-2 xl:p-3 flex-1 border-r border-slate-500 flex items-center gap-2 ${activeTurn === 'my' ? 'flex' : 'hidden xl:flex'} xl:w-5/12`}>
             <span className="hidden xl:inline">MY TURN</span>
             <span className="xl:hidden">Active Abilities</span>
          </div>
          <div className={`p-2 xl:p-3 flex-1 flex items-center gap-2 ${activeTurn === 'opp' ? 'flex' : 'hidden xl:flex'} xl:w-5/12`}>
             <span className="hidden xl:inline">OPP TURN</span>
             <span className="xl:hidden">Active Abilities</span>
          </div>
       </div>

       {/* Table Body */}
       <div className="flex flex-col divide-y divide-slate-600">
         {PHASES.map(phase => {
           let items = checklists[phase];
           if (!items || items.length === 0) return null;
           
           if (filterUnitIds) {
             items = items.filter((item: any) => filterUnitIds.includes(item.unit.id));
           }

           if (items.length === 0) return null;

           // Filter out passive/setup abilities that clutter the checklist
           const isIgnored = (name: string) => {
              const n = name.toLowerCase();
              return n === 'leader' || n.includes('damaged:') || n === 'storm shield' || n === 'champion of the kingsguard' || n === 'embarking within transports' || n === 'iron priest' || n === 'deep strike' || n === 'infiltrators' || n === 'scouts' || n === 'lone operative' || n === 'stealth' || n === 'deadly demise' || n === 'feel no pain' || n === 'invulnerable save' || n === 'fights first' || n === 'hover';
           };

           const myTurnItems = items.filter((item: any) => {
             if (isIgnored(item.ability.name)) return false;
             const cat = categorizeTurn(item.ability.description);
             return cat === 'my' || cat === 'both';
           });
           const oppTurnItems = items.filter((item: any) => {
             if (isIgnored(item.ability.name)) return false;
             const cat = categorizeTurn(item.ability.description);
             return cat === 'opp' || cat === 'both';
           });
           
           if (myTurnItems.length === 0 && oppTurnItems.length === 0) return null;

           const uiInfo = getPhaseUIInfo(phase);

           const renderItem = (item: any, idx: number) => (
             <div key={idx} className="flex gap-2 items-start py-2 xl:py-3 border-t border-slate-700/50 first:border-0">
                <div className="text-slate-500 mt-0.5 shrink-0 text-xs">■</div>
                <div className="leading-snug text-sm xl:text-base w-full">
                   <span className={`font-bold ${item.isStratagem ? 'text-red-400' : item.isDetachment ? 'text-purple-400' : item.ability.name.includes('[Enhancement]') ? 'text-amber-400' : 'text-slate-200'}`}>
                     {item.ability.name.replace('[Enhancement]', '★ ')} {item.isStratagem && <span className="text-red-400/80">(1CP)</span>}
                   </span>
                   <span className="text-slate-600 mx-1.5">—</span>
                   <span className="text-slate-300 font-semibold">{item.unit.name.replace('Detachment: ', '')}</span>
                   <p className="text-xs xl:text-sm text-slate-400 whitespace-pre-line mt-1.5 leading-relaxed">{item.ability.description}</p>
                </div>
             </div>
           );

           return (
             <div key={phase} className="flex min-h-[80px]">
                {/* Phase Column */}
                <div className="w-10 landscape:w-1/6 xl:w-24 bg-slate-400/90 text-slate-900 border-r border-slate-600 flex flex-col items-center justify-center py-4 px-1 xl:p-2 shrink-0">
                   <div className="text-xl xl:text-3xl font-black mb-2 xl:mb-1">{uiInfo.num}</div>
                   <div className="font-bold text-[10px] tracking-widest landscape:hidden xl:hidden" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}>{uiInfo.eng}</div>
                   <div className="font-bold text-sm xl:text-base tracking-wider hidden landscape:block xl:block">{uiInfo.eng}</div>
                </div>
                {/* My Turn Column */}
                <div className={`p-3 xl:p-4 flex-1 border-r border-slate-600 bg-slate-800/80 hover:bg-slate-800 transition-colors ${activeTurn === 'my' ? 'block' : 'hidden xl:block'} xl:w-5/12`}>
                   {myTurnItems.map((item, idx) => renderItem(item, idx))}
                   {myTurnItems.length === 0 && <div className="text-slate-500 italic text-sm text-center py-4 xl:hidden">No abilities this turn</div>}
                </div>
                {/* Opp Turn Column */}
                <div className={`p-3 xl:p-4 flex-1 bg-slate-900/80 hover:bg-slate-900 transition-colors ${activeTurn === 'opp' ? 'block' : 'hidden xl:block'} xl:w-5/12`}>
                   {oppTurnItems.map((item, idx) => renderItem(item, idx))}
                   {oppTurnItems.length === 0 && <div className="text-slate-500 italic text-sm text-center py-4 xl:hidden">No abilities this turn</div>}
                </div>
             </div>
           );
         })}
       </div>
    </div>
  );
}

function categorizeTurn(description: string): 'my' | 'opp' | 'both' {
  if (!description) return 'both';
  const d = description.toLowerCase();
  
  if (/any phase/i.test(d) || /either player's turn/i.test(d) || /both player/i.test(d)) {
      return 'both';
  }

  // Replace "your opponent" with "enemy" to prevent "your" from matching
  const strippedOpp = d.replace(/your opponent's/g, 'enemy').replace(/your opponent/g, 'enemy');
  
  const hasMyPhase = /your \w+ phase/i.test(strippedOpp) || /your turn/i.test(strippedOpp);
  const hasOpponentPhase = /enemy \w+ phase/i.test(strippedOpp) || /enemy turn/i.test(strippedOpp);

  if (hasOpponentPhase && !hasMyPhase) return 'opp';
  if (hasMyPhase && !hasOpponentPhase) return 'my';
  if (hasMyPhase && hasOpponentPhase) return 'both';

  // Fallback heuristics for abilities that don't explicitly mention phases
  const isMy = /declare a charge/i.test(strippedOpp) || /charge move/i.test(strippedOpp) || /advanced/i.test(strippedOpp) || /normal move/i.test(strippedOpp) || /fell back/i.test(strippedOpp) || /selected to shoot/i.test(strippedOpp);
  
  if (isMy) return 'my';
  
  return 'both';
}

function App() {
  const [rosterText, setRosterText] = useState(() => localStorage.getItem('rosterText') || '');
  const [parsedUnits, setParsedUnits] = useState<ParsedUnit[]>(() => {
    const saved = localStorage.getItem('parsedUnits');
    return saved ? JSON.parse(saved) : [];
  });
  const [rosterMeta, setRosterMeta] = useState<RosterMeta | null>(() => {
    const saved = localStorage.getItem('rosterMeta');
    return saved ? JSON.parse(saved) : null;
  });
  const [orderedUnitIds, setOrderedUnitIds] = useState<string[]>(() => {
    const saved = localStorage.getItem('orderedUnitIds');
    return saved ? JSON.parse(saved) : [];
  });
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  
  const [attachments, setAttachments] = useState<Record<string, string>>(() => {
    const saved = localStorage.getItem('attachments');
    return saved ? JSON.parse(saved) : {};
  }); 

  useEffect(() => { localStorage.setItem('rosterText', rosterText); }, [rosterText]);
  useEffect(() => { localStorage.setItem('parsedUnits', JSON.stringify(parsedUnits)); }, [parsedUnits]);
  useEffect(() => { localStorage.setItem('rosterMeta', JSON.stringify(rosterMeta)); }, [rosterMeta]);
  useEffect(() => { localStorage.setItem('orderedUnitIds', JSON.stringify(orderedUnitIds)); }, [orderedUnitIds]);
  useEffect(() => { localStorage.setItem('attachments', JSON.stringify(attachments)); }, [attachments]); 
  const [database, setDatabase] = useState<UnitData[]>([]);
  const [detachmentsDB, setDetachmentsDB] = useState<DetachmentData[]>([]);
  const [coreRules, setCoreRules] = useState<Ability[]>([]);
  const [fallbackRules, setFallbackRules] = useState<{detachment: string, name: string, description: string, phase: string}[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mobileTab, setMobileTab] = useState<'roster' | 'checklist'>('roster');
  const [isRosterPanelCollapsed, setIsRosterPanelCollapsed] = useState(false);
  const [isRosterInputCollapsed, setIsRosterInputCollapsed] = useState(() => {
    const saved = localStorage.getItem('parsedUnits');
    return saved && JSON.parse(saved).length > 0;
  });

  useEffect(() => {
    fetch('/custom_rules.txt')
      .then(res => {
         if (res.ok) return res.text();
         return '';
      })
      .then(text => {
         if (!text.trim()) return;
         const lines = text.split('\n');
         let currentDetachment = 'Global';
         let currentName = '';
         let currentDesc = '';
         const rules: any[] = [];
         
         const addRule = () => {
            if (currentName) {
               rules.push({
                 detachment: currentDetachment,
                 name: currentName.trim(),
                 description: currentDesc.trim(),
                 phase: determinePhase(currentDesc)
               });
            }
         };

         for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('#')) {
               addRule();
               currentDetachment = trimmed.substring(1).trim();
               currentName = '';
               currentDesc = '';
               continue;
            }
            
            const match = trimmed.match(/^([A-Za-z0-9'’\- ]+):\s*(.+)$/);
            const isKeyword = match && ['WHEN', 'TARGET', 'EFFECT', 'RESTRICTIONS', 'ELIGIBLE IF', 'WHILE SHOOTING', 'AFTER SHOOTING'].includes(match[1].trim().toUpperCase());
            
            if (match && !isKeyword) {
               addRule();
               currentName = match[1];
               currentDesc = match[2];
            } else if (currentName && trimmed) {
               currentDesc += '\n' + trimmed;
            }
         }
         addRule();
         setFallbackRules(rules);
      })
      .catch(err => console.error("Could not load custom_rules.txt", err));
  }, []);

  const handleParse = async () => {
    const { meta, units } = parseRoster(rosterText);
    setParsedUnits(units);
    setRosterMeta(meta);
    setOrderedUnitIds(units.map(u => u.id));
    setAttachments({});
    setSelectedUnitId(null);

    const catFileName = guessCatFileName(rosterText);
    if (catFileName) {
      try {
        setIsLoading(true);
        const dbResult = await fetchFactionData(catFileName);
        setDatabase(dbResult.units);
        setDetachmentsDB(dbResult.detachments);
        setCoreRules(dbResult.coreRules || []);
      } catch (err: any) {
        setError("Failed to load database from GitHub: " + err.message);
      } finally {
        setIsLoading(false);
        setMobileTab('checklist');
        setIsRosterInputCollapsed(true);
      }
    }
  };

  const onDragEnd = (result: DropResult) => {
    const { source, destination, combine, draggableId } = result;

    if (combine) {
      const targetId = combine.draggableId;
      const draggedUnit = parsedUnits.find(u => u.id === draggableId);
      const targetUnit = parsedUnits.find(u => u.id === targetId);
      
      if (draggedUnit && targetUnit) {
        const isDraggedBodyguard = !draggedUnit.category.includes('Character') && !draggedUnit.category.includes('Epic Hero') && !draggedUnit.category.includes('Vehicle') && !draggedUnit.category.includes('Monster');
        const isTargetLeader = targetUnit.category.includes('Character') || targetUnit.category.includes('Epic Hero');
        
        let isAllowedByLeader = true;
        const dbLeader = database.find(d => d.name.toLowerCase() === targetUnit.name.toLowerCase() || targetUnit.name.toLowerCase().includes(d.name.toLowerCase()));
        if (dbLeader?.allowedBodyguards && dbLeader.allowedBodyguards.length > 0) {
          isAllowedByLeader = dbLeader.allowedBodyguards.some(bg => 
            draggedUnit.name.toLowerCase().includes(bg.toLowerCase()) || bg.toLowerCase().includes(draggedUnit.name.toLowerCase())
          );
        }

        if (isDraggedBodyguard && isTargetLeader && isAllowedByLeader) {
          const oldBodyguardId = attachments[targetId];
          setAttachments(prev => ({ ...prev, [targetId]: draggableId }));
          setOrderedUnitIds(prev => {
            let newIds = prev.filter(id => id !== draggableId);
            if (oldBodyguardId && oldBodyguardId !== draggableId) {
              newIds.push(oldBodyguardId);
            }
            return newIds;
          });
        }
      }
      return;
    }

    if (!destination) return;
    if (source.index === destination.index) return;

    setOrderedUnitIds(prev => {
      const newIds = Array.from(prev);
      const [removed] = newIds.splice(source.index, 1);
      newIds.splice(destination.index, 0, removed);
      return newIds;
    });
  };

  const handleDetach = (leaderId: string, bodyguardId: string) => {
    setAttachments(prev => {
      const newAtt = { ...prev };
      delete newAtt[leaderId];
      return newAtt;
    });
    setOrderedUnitIds(prev => [...prev, bodyguardId]);
  };

  const checklists: Record<string, any[]> = {};
  PHASES.forEach(p => checklists[p] = []);
  
  parsedUnits.forEach(u => {
    const dbUnit = database.find(d => d.name.toLowerCase() === u.name.toLowerCase() || u.name.toLowerCase().includes(d.name.toLowerCase()));
    if (dbUnit) {
      dbUnit.abilities.forEach(ability => {
        const attachedBodyguardId = attachments[u.id];
        const attachedBodyguard = attachedBodyguardId ? parsedUnits.find(bg => bg.id === attachedBodyguardId) : null;
        
        const filteredDesc = filterAbilityForLeader(ability.description, attachedBodyguard?.name || null);
        if (!filteredDesc) {
            return; 
        }

        const dynamicPhaseStr = determinePhase(filteredDesc);
        const phases = dynamicPhaseStr ? dynamicPhaseStr.split(', ') : ['Other / Any Phase'];
        
        phases.forEach(p => {
           const phaseKey = checklists[p] ? p : 'Other / Any Phase';
           if (!checklists[phaseKey].some(item => item.ability.name === ability.name && item.unit.name === u.name)) {
              checklists[phaseKey].push({ unit: u, ability: { ...ability, description: filteredDesc } });
           }
        });
      });
      
      // Inject Enhancements from Detachments if this unit is equipped with them
      if (rosterMeta && rosterMeta.detachments.length > 0) {
         rosterMeta.detachments.forEach(detName => {
            const detData = detachmentsDB.find(d => detName.includes(d.name) || d.name.includes(detName));
            if (detData) {
               detData.rules.forEach(r => {
                  // If the rule is an Enhancement and the unit's text has it, attach it to this unit!
                  if (u.rawText.includes(r.name)) {
                     const phase = checklists[r.phase] ? r.phase : 'Other / Any Phase';
                     checklists[phase].push({
                        unit: u,
                        ability: { ...r, name: `[Enhancement] ${r.name}` }
                     });
                  }
               });
            }
         });
      }
    }
  });

  if (rosterMeta && rosterMeta.detachments.length > 0) {
    rosterMeta.detachments.forEach(detName => {
      const detData = detachmentsDB.find(d => detName.includes(d.name) || d.name.includes(detName));
      if (detData) {
        detData.rules.forEach(r => {
          const phases = r.phase ? r.phase.split(', ') : ['Other / Any Phase'];
          phases.forEach(p => {
             const phaseKey = checklists[p] ? p : 'Other / Any Phase';
             checklists[phaseKey].push({
               unit: { id: 'det', name: `Detachment: ${detData.name}` },
               ability: r,
               isDetachment: true
             });
          });
        });
        detData.stratagems.forEach(s => {
          const phases = s.phase ? s.phase.split(', ') : ['Other / Any Phase'];
          phases.forEach(p => {
             const phaseKey = checklists[p] ? p : 'Other / Any Phase';
             checklists[phaseKey].push({
               unit: { id: 'strat', name: `Stratagem` },
               ability: s,
               isStratagem: true
             });
          });
        });
      }
    });
  }

  // Inject Core Rules (Core Stratagems)
  if (coreRules && coreRules.length > 0) {
      coreRules.forEach(r => {
          const phases = r.phase ? r.phase.split(', ') : ['Other / Any Phase'];
          phases.forEach((p: string) => {
             const phaseKey = checklists[p] ? p : 'Other / Any Phase';
             checklists[phaseKey].push({
               unit: { id: 'core', name: `Core Stratagem` },
               ability: r,
               isStratagem: true
             });
          });
      });
  }

  // Inject Fallback Rules if they match the selected detachment (or are global)
  fallbackRules.forEach(r => {
      let shouldInject = false;
      if (r.detachment === 'Global') {
         shouldInject = true;
      } else if (rosterMeta && rosterMeta.detachments.length > 0) {
         shouldInject = rosterMeta.detachments.some(detName => 
            detName.includes(r.detachment) || r.detachment.includes(detName)
         );
      }

      if (shouldInject) {
         const isStratagem = r.detachment === 'Global' || /\[\d+CP\]/.test(r.name) || /\[\d+CP\]/.test(r.description);
         const isDetachment = !isStratagem;

         let unitName = `Detachment: ${r.detachment}`;
         if (r.detachment === 'Global') unitName = 'Core Stratagem';
         else if (isStratagem) unitName = `${r.detachment} Stratagem`;

         const phases = r.phase.split(', ');
         phases.forEach(p => {
            const phaseKey = checklists[p] ? p : 'Other / Any Phase';
            checklists[phaseKey].push({
              unit: { id: 'fallback', name: unitName },
              ability: r,
              isDetachment: isDetachment,
              isStratagem: isStratagem
            });
         });
      }
  });

  return (
    <div className="h-screen bg-[#0f172a] text-slate-200 flex flex-col font-sans overflow-hidden">
      {/* Main Content Area */}
      <div className="flex-1 p-4 xl:p-6 flex flex-col landscape:flex-row xl:flex-row gap-4 xl:gap-6 overflow-hidden">
      
      <div className={`transition-all duration-300 ${isRosterPanelCollapsed ? 'w-10 min-w-[40px]' : 'w-full landscape:w-1/3 xl:w-1/4 min-w-[280px]'} flex-col gap-4 xl:gap-6 h-full overflow-hidden ${mobileTab === 'roster' ? 'flex' : 'hidden landscape:flex xl:flex'} shrink-0`}>
        {isRosterPanelCollapsed ? (
          <div 
            onClick={() => setIsRosterPanelCollapsed(false)}
            className="h-full glass-panel border border-slate-700/50 flex flex-col items-center justify-center py-4 cursor-pointer hover:bg-slate-800 transition-colors"
          >
            <Menu className="w-5 h-5 text-slate-400 mb-6" />
            <span className="text-slate-400 font-bold text-xs tracking-widest whitespace-nowrap" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}>ROSTER</span>
          </div>
        ) : (
          <>
            <div className="glass-panel p-4 xl:p-6 flex flex-col border border-slate-700/50 shrink-0 relative">
              <div className="flex items-center gap-3 mb-3 justify-between">
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 xl:w-6 xl:h-6 text-blue-500" />
                  <h1 className="text-lg xl:text-xl font-bold tracking-tight">Roster Input</h1>
                </div>
                <div className="flex items-center gap-2">
                  {parsedUnits.length > 0 && (
                    <button onClick={() => setIsRosterInputCollapsed(!isRosterInputCollapsed)} className="text-slate-400 hover:text-white p-1 rounded-md bg-slate-800 transition-colors" title={isRosterInputCollapsed ? 'Expand Roster Input' : 'Collapse Roster Input'}>
                      {isRosterInputCollapsed ? <ChevronDown className="w-5 h-5" /> : <ChevronUp className="w-5 h-5" />}
                    </button>
                  )}
                  <button 
                     onClick={() => setIsRosterPanelCollapsed(true)} 
                     className="hidden landscape:flex xl:flex p-1 rounded-md text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                     title="Collapse Sidebar"
                  >
                     <ChevronLeft className="w-5 h-5" />
                  </button>
                </div>
              </div>
          
          {!isRosterInputCollapsed && (
            <>
              <textarea
                className="w-full h-20 p-3 rounded-lg bg-slate-900/50 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-sm text-slate-300 resize-none custom-scrollbar"
                placeholder="Paste your 10th Edition roster here..."
                value={rosterText}
                onChange={(e) => setRosterText(e.target.value)}
              />
              <p className="text-xs text-slate-400 mt-2 text-center opacity-70">
                Paste your NewRecruit or BattleScribe roster plain text here
              </p>

              <button
                onClick={handleParse}
                disabled={isLoading || !rosterText.trim()}
                className="mt-3 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white py-2 xl:py-3 rounded-lg font-semibold flex justify-center items-center gap-2 transition-colors text-sm xl:text-base"
              >
                {isLoading ? <Loader2 className="w-4 h-4 xl:w-5 xl:h-5 animate-spin" /> : 'Parse Units'}
              </button>
              
              {error && (
                <div className="mt-3 p-2 xl:p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-200 text-xs xl:text-sm flex gap-2">
                  <Info className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        <div className="glass-panel p-4 xl:p-6 border border-slate-700/50 flex-grow flex flex-col min-h-0">
          <h2 className="text-xl xl:text-2xl font-bold mb-3 flex items-center gap-2 border-b border-slate-700 pb-3">
            <Users className="w-5 h-5 xl:w-6 xl:h-6 text-blue-400" />
            Unit Roster
          </h2>
          
          <p className="text-[10px] xl:text-xs text-slate-400 mb-3">
            Drag a unit onto a Character/Epic Hero to attach them. Drag to reorder.
          </p>

          <div className="flex-grow overflow-y-auto pr-2 custom-scrollbar">
            {parsedUnits.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
                No units parsed.
              </div>
            ) : (
              <>
                <div className="mb-4">
                  {rosterMeta && (
                    <div className="mb-3 px-3 py-2 bg-blue-900/30 border border-blue-500/30 rounded-lg">
                      <h3 className="text-lg font-bold text-blue-100">{rosterMeta.armyName}</h3>
                      <p className="text-xs text-blue-300">{rosterMeta.totalPoints} pts</p>
                    </div>
                  )}
                  {rosterMeta?.detachments.map((det, idx) => (
                    <div 
                      key={idx}
                      onClick={() => { setSelectedUnitId(`detachment-${det}`); setMobileTab('checklist'); }}
                      className="mb-2 w-full p-3 bg-purple-900/30 border border-purple-500/50 hover:bg-purple-900/50 hover:border-purple-400 rounded-lg cursor-pointer transition-all flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-purple-500/20 rounded-md group-hover:bg-purple-500/30 transition-colors">
                          <ShieldAlert className="w-4 h-4 xl:w-5 xl:h-5 text-purple-400" />
                        </div>
                        <div>
                          <h3 className="font-bold text-sm xl:text-base text-purple-100 group-hover:text-white transition-colors">
                            Detachment
                          </h3>
                          <p className="text-xs text-purple-300">
                            {det}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <DragDropContext onDragEnd={onDragEnd}>
                  <Droppable droppableId="roster-list" isCombineEnabled>
                  {(provided) => (
                    <div {...provided.droppableProps} ref={provided.innerRef}>
                      {orderedUnitIds.map((id, index) => {
                        const unit = parsedUnits.find(u => u.id === id)!;
                        const attachedBodyguardId = attachments[id];
                        const attachedBodyguard = attachedBodyguardId ? parsedUnits.find(u => u.id === attachedBodyguardId) : null;

                        return (
                          <Draggable key={id} draggableId={id} index={index}>
                            {(provided, snapshot) => {
                              let combineStyle = '';
                              if (snapshot.combineTargetFor) {
                                const draggedUnit = parsedUnits.find(u => u.id === snapshot.combineTargetFor);
                                const targetUnit = unit;
                                
                                let isAllowed = false;
                                if (draggedUnit && targetUnit) {
                                  const isDraggedBodyguard = !draggedUnit.category.includes('Character') && !draggedUnit.category.includes('Epic Hero') && !draggedUnit.category.includes('Vehicle') && !draggedUnit.category.includes('Monster');
                                  const isTargetLeader = targetUnit.category.includes('Character') || targetUnit.category.includes('Epic Hero');
                                  
                                  const dbLeader = database.find(d => d.name.toLowerCase() === targetUnit.name.toLowerCase() || targetUnit.name.toLowerCase().includes(d.name.toLowerCase()));
                                  let isAllowedByLeader = true;
                                  if (dbLeader?.allowedBodyguards && dbLeader.allowedBodyguards.length > 0) {
                                    isAllowedByLeader = dbLeader.allowedBodyguards.some(bg => 
                                      draggedUnit.name.toLowerCase().includes(bg.toLowerCase()) || bg.toLowerCase().includes(draggedUnit.name.toLowerCase())
                                    );
                                  }
                          
                                  if (isDraggedBodyguard && isTargetLeader && isAllowedByLeader) {
                                    isAllowed = true;
                                  }
                                }
                          
                                if (isAllowed) {
                                   combineStyle = 'shadow-[0_0_20px_rgba(16,185,129,0.8)] border-emerald-500 bg-emerald-900/60 z-50 scale-105';
                                } else {
                                   combineStyle = 'shadow-[0_0_20px_rgba(239,68,68,0.8)] border-red-500 bg-red-900/60 z-50 scale-105';
                                }
                              }

                              return (
                              <div ref={provided.innerRef} {...provided.draggableProps} style={provided.draggableProps.style} className={`mb-3 rounded-lg border border-slate-700 bg-slate-800/80 transition-all duration-200 ${combineStyle}`}>
                                <div className="p-3 flex items-center gap-3">
                                  <div {...provided.dragHandleProps} className="text-slate-500 hover:text-slate-300">
                                    <GripVertical className="w-5 h-5" />
                                  </div>
                                  <div className="flex-grow">
                                    <button className="font-semibold text-slate-200 hover:text-blue-400 hover:underline text-left block" onClick={() => { setSelectedUnitId(unit.id); setMobileTab('checklist'); }}>
                                      {unit.name}
                                    </button>
                                    <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                                      <span>{unit.modelCount} model{unit.modelCount !== 1 ? 's' : ''}</span>
                                      <span className="opacity-50">•</span>
                                      <span className="font-bold text-blue-400/90">{unit.points} pts</span>
                                    </div>
                                  </div>
                                </div>
                                {attachedBodyguard && (
                                  <div className="border-t border-slate-700 bg-slate-900/50 p-2 rounded-b-lg">
                                    <div className="flex items-center text-sm py-1 px-2 border-l-2 border-emerald-500 ml-2">
                                      <div className="flex-grow">
                                        <button className="font-semibold text-emerald-300 hover:text-emerald-400 hover:underline text-left block" onClick={() => { setSelectedUnitId(attachedBodyguard.id); setMobileTab('checklist'); }}>
                                          {attachedBodyguard.name}
                                        </button>
                                        <div className="text-[11px] text-emerald-500/60 mt-0.5 flex items-center gap-1.5">
                                          <span>{attachedBodyguard.modelCount} model{attachedBodyguard.modelCount !== 1 ? 's' : ''}</span>
                                          <span className="opacity-50">•</span>
                                          <span className="font-bold text-emerald-600/80">{attachedBodyguard.points} pts</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3 shrink-0">
                                        <button onClick={() => handleDetach(unit.id, attachedBodyguard.id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                                          <X className="w-4 h-4" />
                                        </button>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}}
                          </Draggable>
                        );
                      })}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
              </>
            )}
          </div>
        </div>
        </>
      )}
    </div>

      <div className={`transition-all duration-300 flex-1 flex-col gap-4 xl:gap-6 min-w-[320px] h-full overflow-hidden ${mobileTab === 'checklist' ? 'flex' : 'hidden landscape:flex xl:flex'}`}>
        <div className="glass-panel p-4 xl:p-6 border border-slate-700/50 flex-grow flex flex-col min-h-0">
          {selectedUnitId ? (
            (() => {
              if (selectedUnitId.startsWith('detachment-') && rosterMeta && rosterMeta.detachments.length > 0) {
                const searchName = selectedUnitId.replace('detachment-', '');
                const detData = detachmentsDB.find(d => searchName.includes(d.name) || d.name.includes(searchName));
                if (detData) {
                  return <DetachmentProfileView detachment={detData} onBack={() => setSelectedUnitId(null)} />;
                } else {
                  return (
                    <div className="flex flex-col h-full animate-fade-in">
                      <div className="flex items-center gap-3 mb-4 shrink-0">
                        <button onClick={() => setSelectedUnitId(null)} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors">
                          <X className="w-5 h-5" />
                        </button>
                        <h2 className="text-2xl font-bold text-slate-100 flex-grow">{searchName}</h2>
                      </div>
                      <div className="flex-grow flex flex-col items-center justify-center text-slate-400 border border-slate-700/50 rounded-xl bg-slate-800/30 p-6 text-center">
                        <ShieldAlert className="w-12 h-12 text-orange-500 mb-4 opacity-80" />
                        <h3 className="text-lg font-bold text-slate-200 mb-2">Detachment Data Not Found</h3>
                        <p className="text-sm max-w-md">
                          We couldn't find the rules for <strong>{searchName}</strong> in the official 10th Edition Github database. 
                          If you are using a custom 11th edition test roster or a modified database, its specific rules won't be available here.
                        </p>
                      </div>
                    </div>
                  );
                }
              }
              const unit = parsedUnits.find(u => u.id === selectedUnitId);
              const dbUnit = unit ? database.find(d => d.name.toLowerCase() === unit.name.toLowerCase() || unit.name.toLowerCase().includes(d.name.toLowerCase())) : null;
              
              if (unit && dbUnit) {
                 const relevantIds = [selectedUnitId];
                 
                 const attachedBodyguardId = attachments[selectedUnitId];
                 if (attachedBodyguardId) relevantIds.push(attachedBodyguardId);
                 
                 const leaderEntry = Object.entries(attachments).find(([_, b]) => b === selectedUnitId);
                 if (leaderEntry) relevantIds.push(leaderEntry[0]);
                 
                 return (
                    <div className="flex flex-col xl:flex-row h-full w-full gap-4 xl:gap-6 overflow-y-auto xl:overflow-hidden custom-scrollbar">
                       <div className="w-full xl:w-1/2 h-auto xl:h-full xl:overflow-y-auto custom-scrollbar xl:pr-2 pb-4 xl:pb-0 border-b xl:border-b-0 xl:border-r border-slate-700/50 flex-shrink-0">
                          <UnitProfileView unitData={dbUnit} parsedUnit={unit} onBack={() => setSelectedUnitId(null)} />
                       </div>
                       
                       <div className="w-full xl:w-1/2 h-auto xl:h-full flex flex-col pt-2 xl:pt-0">
                          <h3 className="text-lg xl:text-xl font-bold mb-3 flex items-center gap-2 shrink-0">
                             <Crosshair className="w-5 h-5 xl:w-6 xl:h-6 text-emerald-500" />
                             Unit Checklist
                          </h3>
                          <div className="xl:flex-grow xl:overflow-y-auto custom-scrollbar pr-1 pb-10">
                             <PhaseChecklistTable checklists={checklists} filterUnitIds={relevantIds} />
                          </div>
                       </div>
                    </div>
                 );
              }
              return null;
            })()
          ) : (
            <>
              <h2 className="text-xl xl:text-2xl font-bold mb-4 xl:mb-6 flex items-center gap-2 border-b border-slate-700 pb-3 xl:pb-4 shrink-0">
                <Swords className="w-5 h-5 xl:w-6 xl:h-6 text-emerald-500" />
                Phase Checklist
              </h2>
              <div className="flex-grow overflow-y-auto pr-2 custom-scrollbar">
                {parsedUnits.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
                    <Crosshair className="w-10 h-10 xl:w-12 xl:h-12 mb-3 opacity-50" />
                    <p className="text-sm xl:text-base">Paste Roster to build your list.</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {rosterMeta && rosterMeta.detachments.map(detName => {
                      const detData = detachmentsDB.find(d => detName.includes(d.name) || d.name.includes(detName));
                      if (!detData) return null;
                      return (
                        <div 
                          key={detName}
                          className="p-3 bg-gradient-to-r from-purple-900/40 to-slate-900/40 border-2 border-purple-800/50 rounded-lg shadow-sm cursor-pointer hover:border-purple-600 transition-colors"
                          onClick={() => { setSelectedUnitId(`detachment-${detData.name}`); setMobileTab('checklist'); }}
                        >
                          <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-purple-400" />
                            <span className="font-bold text-slate-200">Detachment: {detData.name}</span>
                          </div>
                        </div>
                      );
                    })}
                    <PhaseChecklistTable checklists={checklists} />
            </div>
          )}
          </div>
          </>
          )}
        </div>
      </div>
      
      </div>

      {/* Mobile Bottom Tab Bar */}
      <div className="landscape:hidden xl:hidden bg-slate-900 border-t border-slate-700 p-2 flex justify-around shrink-0 pb-safe">
        <button 
          onClick={() => setMobileTab('roster')}
          className={`flex-1 flex flex-col items-center justify-center p-2 rounded-lg transition-colors ${mobileTab === 'roster' ? 'text-blue-400 bg-blue-900/30' : 'text-slate-400 hover:text-slate-300'}`}
        >
          <Users className="w-6 h-6 mb-1" />
          <span className="text-xs font-bold">Roster</span>
        </button>
        <button 
          onClick={() => setMobileTab('checklist')}
          className={`flex-1 flex flex-col items-center justify-center p-2 rounded-lg transition-colors ${mobileTab === 'checklist' ? 'text-emerald-400 bg-emerald-900/30' : 'text-slate-400 hover:text-slate-300'}`}
        >
          <Swords className="w-6 h-6 mb-1" />
          <span className="text-xs font-bold">Checklist</span>
        </button>
      </div>

    </div>
  )
}

export default App;
