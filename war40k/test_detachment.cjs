const https = require('https');

https.get('https://raw.githubusercontent.com/BSData/wh40k-10e/main/Imperium%20-%20Adeptus%20Astartes%20-%20Space%20Wolves.cat', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    if (data.includes('Veterans of the Fang')) {
       console.log('Veterans of the Fang found in SW .cat!');
    } else {
       console.log('Veterans of the Fang NOT FOUND in SW .cat!');
    }
    
    if (data.includes('Saga of the Hunter')) {
       console.log('Saga of the Hunter found in SW .cat!');
    } else {
       console.log('Saga of the Hunter NOT FOUND in SW .cat!');
    }

    https.get('https://raw.githubusercontent.com/BSData/wh40k-10e/main/Imperium%20-%20Adeptus%20Astartes.cat', (res2) => {
      let data2 = '';
      res2.on('data', chunk => data2 += chunk);
      res2.on('end', () => {
         if (data2.includes('Veterans of the Fang')) console.log('Veterans of the Fang found in SM .cat!');
         if (data2.includes('Saga of the Hunter')) console.log('Saga of the Hunter found in SM .cat!');
      });
    });
  });
});
