const fs = require('fs');
const https = require('https');

https.get('https://raw.githubusercontent.com/BSData/wh40k-11e/main/Space%20Wolves.json', (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    const json = JSON.parse(data);
    const arjac = json.sharedSelectionEntries.find(e => e.name === 'Arjac Rockfist');
    fs.writeFileSync('debug_inv.json', JSON.stringify(arjac, null, 2));
    console.log('done');
  });
});
