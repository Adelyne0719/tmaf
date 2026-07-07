const fs = require('fs');

const d = JSON.parse(fs.readFileSync('./wh40k-11e/Imperium - Space Marines.json', 'utf8'));

// Find a character to see allowedBodyguards and stats
const character = d.catalogue.sharedSelectionEntries.find(e => e.name && e.name.includes('Captain'));
console.log(JSON.stringify(character, null, 2).substring(0, 3000));
