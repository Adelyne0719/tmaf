import fs from 'fs';
async function test() {
  const url = 'https://raw.githubusercontent.com/BSData/wh40k-11e/main/Imperium%20-%20Space%20Wolves.json';
  const response = await fetch(url);
  const json = await response.json();
  const arjac = json.catalogue.sharedSelectionEntries.find(e => e.name === 'Arjac Rockfist');
  fs.writeFileSync('arjac_debug_utf8.json', JSON.stringify(arjac, null, 2), 'utf8');
}
test();
