const fs = require('fs');

fetch('https://raw.githubusercontent.com/BSData/wh40k-10e/main/Imperium%20-%20Space%20Wolves.cat')
  .then(r => r.text())
  .then(xml => {
    const lines = xml.split('\n');
    let inArjac = false;
    for(let i=0; i<lines.length; i++) {
      if(lines[i].includes('name="Arjac Rockfist"')) inArjac = true;
      if(inArjac && lines[i].includes('name="Leader"')) {
        console.log(lines.slice(i, i+15).join('\n'));
        break;
      }
    }
  });
