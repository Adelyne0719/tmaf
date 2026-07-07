const https = require('https');

https.get('https://raw.githubusercontent.com/BSData/wh40k-11e/main/Imperium%20-%20Adeptus%20Astartes.cat', (res) => {
  console.log('Status:', res.statusCode);
  if (res.statusCode === 200) {
     console.log('wh40k-11e EXISTS!');
  } else {
     console.log('wh40k-11e NOT FOUND. Trying 10e instead...');
  }
});
