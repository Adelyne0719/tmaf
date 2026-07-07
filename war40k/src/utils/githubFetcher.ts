export interface Ability {
  name: string;
  description: string;
  phase: string;
}

export interface Weapon {
  name: string;
  range: string;
  a: string;
  bsws: string;
  s: string;
  ap: string;
  d: string;
  keywords: string;
  type: 'Ranged' | 'Melee';
}

export interface UnitStats {
  m: string;
  t: string;
  sv: string;
  w: string;
  ld: string;
  oc: string;
  insv: string;
}

export interface DetachmentData {
  name: string;
  rules: Ability[];
  stratagems: Ability[];
}

export interface UnitData {
  name: string;
  abilities: Ability[];
  allowedBodyguards?: string[];
  stats?: UnitStats;
  rangedWeapons: Weapon[];
  meleeWeapons: Weapon[];
  keywords: string[];
}

export interface FactionDataResult {
  units: UnitData[];
  detachments: DetachmentData[];
  coreRules?: Ability[];
}

const GITHUB_BASE = "https://raw.githubusercontent.com/BSData/wh40k-11e/main/";

export function determinePhase(desc: string): string {
  if (!desc) return 'Other / Any Phase';
  const fullText = desc.toLowerCase();
  
  const phases: string[] = [];
  
  if (fullText.includes('any phase')) return 'Other / Any Phase';
  
  const whenMatch = fullText.match(/when:(.*?)(?:\n|$)/);
  if (whenMatch) {
      const whenText = whenMatch[1];
      if (whenText.includes('command phase')) phases.push('Command Phase');
      if (whenText.includes('movement phase')) phases.push('Movement Phase');
      if (whenText.includes('shooting phase')) phases.push('Shooting Phase');
      if (whenText.includes('charge phase')) phases.push('Charge Phase');
      if (whenText.includes('fight phase')) phases.push('Fight Phase');
      
      if (phases.length > 0) return Array.from(new Set(phases)).join(', ');
  }
  
  const dClean = fullText.replace(/in a turn in which it advanced/gi, '');
  const d = dClean;
  
  if (d.includes('command phase')) phases.push('Command Phase');
  if (d.includes('movement phase') || d.includes('advance') || d.includes('fall back') || d.includes('normal move') || d.includes('set up') || d.includes('arrives from reserves')) phases.push('Movement Phase');
  if (d.includes('shooting phase') || d.includes('ranged attack') || d.includes('shoot') || d.includes('firing')) phases.push('Shooting Phase');
  if (d.includes('charge phase') || d.includes('charge roll') || d.includes('charge')) phases.push('Charge Phase');
  if (d.includes('fight phase') || d.includes('melee attack') || d.includes('fight')) phases.push('Fight Phase');
  
  if (d.includes('makes an attack') || d.includes('selected to attack') || d.includes('an attack that targets')) {
      const isRanged = d.includes('ranged weapon');
      const isMelee = d.includes('melee weapon');

      if (!isMelee && !phases.includes('Shooting Phase')) phases.push('Shooting Phase');
      if (!isRanged && !phases.includes('Fight Phase')) phases.push('Fight Phase');
  }
  
  if (phases.length === 0) return 'Other / Any Phase';
  
  // Deduplicate and return
  return Array.from(new Set(phases)).join(', ');
}

function getChar(profile: any, name: string): string {
  if (!profile.characteristics) return '-';
  const c = profile.characteristics.find((ch: any) => ch.name === name);
  return c && c.$text ? c.$text : '-';
}

function traverseJsonForProfiles(node: any, allDocs: any[], profilesOut: any[]) {
  if (!node) return;
  
  if (node.profiles) {
    node.profiles.forEach((p: any) => profilesOut.push(p));
  }

  if (node.infoLinks) {
    node.infoLinks.forEach((link: any) => {
      if (link.type === 'profile' && link.targetId) {
        for (const doc of allDocs) {
          const sp = doc.catalogue?.sharedProfiles?.find((p: any) => p.id === link.targetId);
          if (sp) profilesOut.push(sp);
        }
      }
    });
  }

  if (node.selectionEntries) {
    node.selectionEntries.forEach((child: any) => {
      traverseJsonForProfiles(child, allDocs, profilesOut);
    });
  }

  if (node.selectionEntryGroups) {
    node.selectionEntryGroups.forEach((group: any) => {
      traverseJsonForProfiles(group, allDocs, profilesOut);
    });
  }

  if (node.entryLinks) {
    node.entryLinks.forEach((link: any) => {
      const linkName = (link.name || '').toLowerCase();
      // Skip bloated shared items to keep lists clean
      if (linkName.includes('crusade') || linkName.includes('enhancements') || linkName.includes('weapon modifications')) {
         return;
      }
      
      if (link.type === 'selectionEntry' && link.targetId) {
        for (const doc of allDocs) {
          const se = doc.catalogue?.sharedSelectionEntries?.find((e: any) => e.id === link.targetId);
          if (se) {
            traverseJsonForProfiles(se, allDocs, profilesOut);
          }
        }
      }
    });
  }
}

export async function fetchFactionData(factionFileName: string): Promise<FactionDataResult> {
  const jsonName = factionFileName.endsWith('.json') 
    ? factionFileName 
    : factionFileName.replace('.cat', '') + '.json';
  const url = `${GITHUB_BASE}${encodeURIComponent(jsonName)}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${jsonName} from wh40k-11e`);
  }
  const mainDoc = await response.json();
  const allDocs = [mainDoc];
  
  if (mainDoc.catalogue?.catalogueLinks) {
    const promises = mainDoc.catalogue.catalogueLinks.map(async (catLink: any) => {
      if (catLink.name) {
        try {
          const linkUrl = `${GITHUB_BASE}${encodeURIComponent(catLink.name + '.json')}`;
          const r = await fetch(linkUrl);
          if (r.ok) {
            const linkJson = await r.json();
            allDocs.push(linkJson);
          }
        } catch (e) {
          console.warn("Failed to fetch linked catalogue", catLink.name);
        }
      }
    });
    await Promise.all(promises);
  }

  const unitsData: UnitData[] = [];
  
  // Collect units from sharedSelectionEntries across all fetched docs
  for (const doc of allDocs) {
    const unitEntries = (doc.catalogue?.sharedSelectionEntries || []).filter(
      (e: any) => e.type === 'unit' || e.type === 'model'
    );
    
    for (const entry of unitEntries) {
      const unitName = entry.name;
      if (!unitName) continue;

      let existingUnit = unitsData.find(u => u.name === unitName);
      if (!existingUnit) {
        existingUnit = { 
          name: unitName, 
          abilities: [], 
          allowedBodyguards: [],
          rangedWeapons: [],
          meleeWeapons: [],
          keywords: [],
          stats: { m: '-', t: '-', sv: '-', w: '-', ld: '-', oc: '-', insv: '-' }
        };
        unitsData.push(existingUnit);
      }
      
      // Extract Keywords
      if (entry.categoryLinks) {
        entry.categoryLinks.forEach((cat: any) => {
          let kname = cat.name;
          if (kname && kname !== unitName) {
            if (kname.startsWith('Faction: ')) kname = kname.replace('Faction: ', '');
            if (!existingUnit!.keywords.includes(kname)) {
              existingUnit!.keywords.push(kname);
            }
          }
        });
      }
      
      const profiles: any[] = [];
      traverseJsonForProfiles(entry, allDocs, profiles);

      for (const p of profiles) {
        const typeName = p.typeName;
        const pName = p.name || '';
        
        if (typeName === 'Unit') {
          existingUnit.stats!.m = getChar(p, 'M');
          existingUnit.stats!.t = getChar(p, 'T');
          existingUnit.stats!.sv = getChar(p, 'Sv') !== '-' ? getChar(p, 'Sv') : getChar(p, 'SV');
          existingUnit.stats!.w = getChar(p, 'W');
          existingUnit.stats!.ld = getChar(p, 'LD');
          existingUnit.stats!.oc = getChar(p, 'OC');
          const insvChar = getChar(p, 'InSv') !== '-' ? getChar(p, 'InSv') : getChar(p, 'INV');
          if (insvChar !== '-') {
             existingUnit.stats!.insv = insvChar;
          }
        }
        
        if (pName === 'Invulnerable Save' && existingUnit.stats) {
          const raw = getChar(p, 'Description') || '';
          const match = raw.match(/(\d\+)/);
          existingUnit.stats.insv = match ? match[1] : '-';
        }

        if (typeName === 'Abilities' || typeName === 'Ability') {
          const description = getChar(p, 'Description');
          if (description && description !== '-') {
            const phase = determinePhase(description);
            if (!existingUnit.abilities.some(a => a.name === pName)) {
              existingUnit.abilities.push({ name: pName, description, phase });
            }
            
            if (existingUnit.stats && existingUnit.stats.insv === '-') {
                const insvMatch = description.match(/(\d\+)\s+invulnerable save/i);
                if (insvMatch) {
                    existingUnit.stats.insv = insvMatch[1];
                }
            }
            
            if (pName.toLowerCase() === 'leader') {
              const attachIndex = description.toLowerCase().indexOf('can be attached to the following units:');
              if (attachIndex !== -1) {
                existingUnit.allowedBodyguards = existingUnit.allowedBodyguards || [];
                const listText = description.substring(attachIndex + 'can be attached to the following units:'.length);
                const listLines = listText.split('\n');
                for (const listLine of listLines) {
                  const trimmedList = listLine.trim();
                  if (!trimmedList) continue;
                  if (trimmedList.toLowerCase().includes('even if') || trimmedList.toLowerCase().includes('you must') || trimmedList.length > 60) break;
                  const bgName = trimmedList.replace(/^[■\-*•]\s*/, '').trim();
                  if (bgName && !existingUnit.allowedBodyguards.includes(bgName)) {
                    existingUnit.allowedBodyguards.push(bgName);
                  }
                }
              }
            }
          }
        }
        
        if (typeName === 'Ranged Weapons') {
          const cleanName = pName.replace(/^➤\s*/, '').trim();
          if (!existingUnit.rangedWeapons.some(w => w.name === cleanName)) {
            existingUnit.rangedWeapons.push({
              name: cleanName,
              range: getChar(p, 'Range'),
              a: getChar(p, 'A'),
              bsws: getChar(p, 'BS'),
              s: getChar(p, 'S'),
              ap: getChar(p, 'AP'),
              d: getChar(p, 'D'),
              keywords: getChar(p, 'Keywords'),
              type: 'Ranged'
            });
          }
        }
        
        if (typeName === 'Melee Weapons') {
          const cleanName = pName.replace(/^➤\s*/, '').trim();
          if (!existingUnit.meleeWeapons.some(w => w.name === cleanName)) {
            existingUnit.meleeWeapons.push({
              name: cleanName,
              range: getChar(p, 'Range'),
              a: getChar(p, 'A'),
              bsws: getChar(p, 'WS'),
              s: getChar(p, 'S'),
              ap: getChar(p, 'AP'),
              d: getChar(p, 'D'),
              keywords: getChar(p, 'Keywords'),
              type: 'Melee'
            });
          }
        }
      }
    }
  }

  // Parse Detachments
  const detachmentsDB: DetachmentData[] = [];
  
  for (const doc of allDocs) {
    const detGroups = (doc.catalogue?.sharedSelectionEntryGroups || []).filter(
      (g: any) => g.name === 'Detachment' || g.name === 'Detachment Choice'
    );
    
    for (const group of detGroups) {
      const selections = group.selectionEntries || [];
      for (const det of selections) {
        const detName = det.name;
        if (!detName) continue;
        
        const existingDet = detachmentsDB.find(d => d.name === detName);
        if (existingDet) continue;
        
        const detData: DetachmentData = {
          name: detName,
          rules: [],
          stratagems: []
        };
        
        // Extract rules that are stored directly on the detachment object
        if (det.rules && Array.isArray(det.rules)) {
           det.rules.forEach((r: any) => {
              if (r.description) {
                 detData.rules.push({
                    name: r.name || detName,
                    description: r.description,
                    phase: determinePhase(r.description)
                 });
              }
           });
        }

        const dProfiles: any[] = [];
        traverseJsonForProfiles(det, allDocs, dProfiles);
        
        for (const p of dProfiles) {
          const typeName = p.typeName;
          const pName = p.name || '';
          if (typeName === 'Stratagem') {
            const desc = getChar(p, 'Description');
            if (desc && desc !== '-') {
               detData.stratagems.push({ name: pName, description: desc, phase: determinePhase(desc) });
            }
          } else if (typeName === 'Abilities' || typeName === 'Ability') {
            const desc = getChar(p, 'Description');
            if (desc && desc !== '-') {
               // Avoid duplicating if we already added it via det.rules
               if (!detData.rules.some(r => r.description === desc)) {
                  detData.rules.push({ name: pName, description: desc, phase: determinePhase(desc) });
               }
            }
          }
        }
        
        detachmentsDB.push(detData);
      }
    }
  }

  return {
    units: unitsData,
    detachments: detachmentsDB,
    coreRules: []
  };
}
