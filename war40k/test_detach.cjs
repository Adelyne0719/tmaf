const fs = require('fs');

const sm = fs.readFileSync('sm_full.xml', 'utf8');
const sw = fs.readFileSync('sw_full.xml', 'utf8');

function findDetachmentGroups(xml) {
  const matches = xml.match(/<selectionEntryGroup[^>]*name="Detachment"[^>]*>([\s\S]*?)<\/selectionEntryGroup>/g);
  if (matches) {
     matches.forEach(m => {
       const entries = m.match(/<selectionEntry[^>]*name="([^"]+)"/g);
       console.log('Found Detachments:', entries);
     });
  }
}
console.log('Space Marines:');
findDetachmentGroups(sm);
console.log('Space Wolves:');
findDetachmentGroups(sw);
