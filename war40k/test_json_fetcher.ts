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
}

const GITHUB_BASE = "https://raw.githubusercontent.com/BSData/wh40k-11e/main/";

function determinePhase(desc: string): string {
  const d = desc.toLowerCase();
  if (d.includes('command phase')) return 'Command Phase';
  if (d.includes('movement phase')) return 'Movement Phase';
  if (d.includes('shooting phase')) return 'Shooting Phase';
  if (d.includes('charge phase')) return 'Charge Phase';
  if (d.includes('fight phase')) return 'Fight Phase';
  return 'Other / Any Phase';
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
          const sp = doc.catalogue.sharedProfiles?.find((p: any) => p.id === link.targetId);
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
      // Skip bloated shared items (same logic as before)
      if (linkName.includes('crusade') || linkName.includes('enhancements') || linkName.includes('weapon modifications')) {
         return;
      }
      
      if (link.type === 'selectionEntry' && link.targetId) {
        for (const doc of allDocs) {
          const se = doc.catalogue.sharedSelectionEntries?.find((e: any) => e.id === link.targetId);
          if (se) {
            traverseJsonForProfiles(se, allDocs, profilesOut);
          }
        }
      }
    });
  }
}

export async function fetchFactionData(factionFileName: string): Promise<FactionDataResult> {
  const jsonName = factionFileName.replace('.cat', '') + '.json';
  const url = `${GITHUB_BASE}${encodeURIComponent(jsonName)}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${jsonName}`);
  }
  const mainDoc = await response.json();
  const allDocs = [mainDoc];
  
  if (mainDoc.catalogue.catalogueLinks) {
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
  
  // Units are in sharedSelectionEntries with type="unit" or "model"
  const unitEntries = (mainDoc.catalogue.sharedSelectionEntries || []).filter(
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
        keywords: []
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
      
      if (typeName === 'Unit' && !existingUnit.stats) {
        existingUnit.stats = {
          m: getChar(p, 'M'),
          t: getChar(p, 'T'),
          sv: getChar(p, 'Sv') !== '-' ? getChar(p, 'Sv') : getChar(p, 'SV'),
          w: getChar(p, 'W'),
          ld: getChar(p, 'LD'),
          oc: getChar(p, 'OC'),
          insv: '-'
        };
      }
      
      if (pName === 'Invulnerable Save' && existingUnit.stats) {
        existingUnit.stats.insv = getChar(p, 'Description') || '-';
      }

      if (typeName === 'Abilities' || typeName === 'Ability') {
        const description = getChar(p, 'Description');
        if (description && description !== '-') {
          const phase = determinePhase(description);
          if (!existingUnit.abilities.some(a => a.name === pName)) {
            existingUnit.abilities.push({ name: pName, description, phase });
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

  // Parse Detachments
  const detachmentsDB: DetachmentData[] = [];
  
  for (const doc of allDocs) {
    const detGroups = (doc.catalogue.sharedSelectionEntryGroups || []).filter(
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
               detData.rules.push({ name: pName, description: desc, phase: determinePhase(desc) });
            }
          }
        }
        
        detachmentsDB.push(detData);
      }
    }
  }

  return {
    units: unitsData,
    detachments: detachmentsDB
  };
}
