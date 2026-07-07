const fs = require('fs');
const path = require('path');
const d = JSON.parse(fs.readFileSync(path.join(__dirname, 'wh40k-11e', 'Imperium - Space Wolves.json'), 'utf8'));

console.log(d.catalogue.sharedSelectionEntries[0].name);
console.log(d.catalogue.sharedSelectionEntries[0].profiles[3].name);

const profiles = [];
const findP = (node) => { 
  if(node.profiles) profiles.push(...node.profiles); 
  if(node.selectionEntries) node.selectionEntries.forEach(findP); 
  if(node.entryLinks) node.entryLinks.forEach(findP); 
  if(node.sharedSelectionEntries) node.sharedSelectionEntries.forEach(findP); 
}; 
findP(d.catalogue); 
const strats = profiles.filter(p => p.typeName === 'Stratagem' || p.name.includes('Stratagem')); 
console.log('Found stratagems:', strats.length);
if (strats.length > 0) {
  console.log(strats[0].name);
}
