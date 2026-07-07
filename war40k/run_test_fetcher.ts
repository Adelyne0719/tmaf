import { fetchFactionData } from './test_json_fetcher.js';

async function run() {
  try {
    const data = await fetchFactionData('Imperium - Space Wolves.cat');
    console.log('Units:', data.units.length);
    console.log('Detachments:', data.detachments.length);
    
    const arjac = data.units.find(u => u.name === 'Arjac Rockfist');
    console.log('Arjac:', JSON.stringify(arjac, null, 2).substring(0, 500));
    
    const saga = data.detachments.find(d => d.name === 'Saga of the Hunter');
    console.log('Saga Detachment:', !!saga);
    if (saga) {
       console.log('Saga rules:', saga.rules.length, 'Saga stratagems:', saga.stratagems.length);
    }
  } catch (e) {
    console.error(e);
  }
}

run();
