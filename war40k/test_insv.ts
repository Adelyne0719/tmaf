import fs from 'fs';
import https from 'https';
import xml2js from 'xml2js';

function getChar(profile: any, charName: string): string {
  if (!profile.characteristics || !profile.characteristics[0] || !profile.characteristics[0].characteristic) return '-';
  const chars = profile.characteristics[0].characteristic;
  const c = chars.find((c: any) => c.$ && c.$.name === charName);
  if (c && c._) return c._.trim();
  return '-';
}

function traverseJsonForProfiles(node: any, allDocs: any[], results: any[]) {
  if (!node) return;
  if (node.profiles && node.profiles[0] && node.profiles[0].profile) {
    node.profiles[0].profile.forEach((p: any) => {
      if (p.$) results.push({ ...p.$, characteristics: p.characteristics });
    });
  }
  if (node.infoLinks && node.infoLinks[0] && node.infoLinks[0].infoLink) {
    node.infoLinks[0].infoLink.forEach((link: any) => {
      if (link.$ && link.$.type === 'profile' && link.$.targetId) {
        let foundProfile: any = null;
        for (const doc of allDocs) {
          const walk = (n: any) => {
            if (!n) return;
            if (n.sharedProfiles && n.sharedProfiles[0] && n.sharedProfiles[0].profile) {
              const match = n.sharedProfiles[0].profile.find((sp: any) => sp.$ && sp.$.id === link.$.targetId);
              if (match) foundProfile = { ...match.$, characteristics: match.characteristics };
            }
            if (!foundProfile && n.sharedSelectionEntries && n.sharedSelectionEntries[0] && n.sharedSelectionEntries[0].selectionEntry) {
              for (const e of n.sharedSelectionEntries[0].selectionEntry) walk(e);
            }
          };
          walk(doc);
          if (foundProfile) break;
        }
        if (foundProfile) results.push(foundProfile);
      }
    });
  }
  if (node.selectionEntries && node.selectionEntries[0] && node.selectionEntries[0].selectionEntry) {
    node.selectionEntries[0].selectionEntry.forEach((e: any) => traverseJsonForProfiles(e, allDocs, results));
  }
  if (node.selectionEntryGroups && node.selectionEntryGroups[0] && node.selectionEntryGroups[0].selectionEntryGroup) {
    node.selectionEntryGroups[0].selectionEntryGroup.forEach((g: any) => {
      if (g.selectionEntries && g.selectionEntries[0] && g.selectionEntries[0].selectionEntry) {
        g.selectionEntries[0].selectionEntry.forEach((e: any) => traverseJsonForProfiles(e, allDocs, results));
      }
    });
  }
}

const parser = new xml2js.Parser();
const xml = fs.readFileSync('e:\\Programing\\Divelopment\\war40k\\test_arjac.xml', 'utf8');

parser.parseString(xml, (err: any, result: any) => {
  const catalogue = result.catalogue;
  const docs = [catalogue];
  
  const entries = catalogue.sharedSelectionEntries[0].selectionEntry;
  const arjac = entries.find((e: any) => e.$.name === 'Arjac Rockfist');
  
  let stats: any = { insv: '-' };
  const profiles: any[] = [];
  traverseJsonForProfiles(arjac, docs, profiles);
  
  for (const p of profiles) {
    const typeName = p.typeName;
    const pName = p.name || '';
    
    if (typeName === 'Unit' && stats.insv === '-') {
       // just checking insv
    }
    
    if (pName === 'Invulnerable Save') {
      const raw = getChar(p, 'Description') || '';
      console.log('raw desc:', raw);
      const match = raw.match(/(\d\+)/);
      stats.insv = match ? match[1] : '-';
    }

    if (typeName === 'Abilities' || typeName === 'Ability') {
      const description = getChar(p, 'Description');
      if (description && description !== '-' && stats.insv === '-') {
         const insvMatch = description.match(/(\d\+)\s+invulnerable save/i);
         if (insvMatch) {
             stats.insv = insvMatch[1];
         }
      }
    }
  }
  console.log('Final Arjac Stats:', stats);
});
