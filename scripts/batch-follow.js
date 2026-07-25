/**
 * Blinko Hub Batch Follow Script
 * 
 * Usage:
 * 1. Open your Blinko site in a web browser and sign in.
 * 2. Press F12 (or right-click -> Inspect) to open Developer Tools, and switch to the 'Console' tab.
 * 3. Copy and paste the contents of this script into the Console and press Enter.
 */

(async () => {
  const mySiteUrl = window.location.origin;
  
  // 1. Extract authentication token from localStorage
  let token = '';
  try {
    const rawTokenData = localStorage.getItem('blinkoToken');
    if (rawTokenData) {
      const parsed = JSON.parse(rawTokenData);
      token = parsed.token || (parsed.value && parsed.value.token) || '';
    }
    if (!token) {
      token = localStorage.getItem('token') || '';
    }
  } catch (e) {
    console.error('Failed to parse token:', e);
  }

  if (!token) {
    console.error('❌ Authentication token not found! Make sure you are logged into your Blinko site.');
    return;
  }

  console.log('🔑 Authentication token retrieved successfully! Fetching Hub site list...');

  // 2. Fetch Hub site list
  const hubRes = await fetch('https://cdn.jsdelivr.net/gh/Inverstar/blinko-hub@main/index.json');
  const hubData = await hubRes.json();
  const sites = hubData.sites || [];
  
  console.log(`✅ Successfully fetched ${sites.length} sites. Starting batch follow...`);

  // 3. Batch follow loop
  let successCount = 0;
  for (const site of sites) {
    if (!site.url || site.url.replace(/\/$/, '') === mySiteUrl.replace(/\/$/, '')) {
      continue;
    }
    
    try {
      console.log(`➡️ Following: ${site.title} (${site.url})...`);
      const res = await fetch('/api/v1/follows/follow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          siteUrl: site.url,
          mySiteUrl: mySiteUrl
        })
      });
      
      const result = await res.json();
      if (res.ok && !result.error && result.success !== false) {
        successCount++;
        console.log(`  └ 🟢 Success: ${site.title}`);
      } else {
        console.warn(`  └ 🟡 Skip/Notice (${site.title}):`, result.message || result.error || JSON.stringify(result));
      }
    } catch (err) {
      console.error(`  └ 🔴 Failed (${site.title}):`, err.message);
    }
  }

  console.log(`🎉 Batch follow complete! Successfully followed ${successCount} sites. Refresh the page to view aggregated posts!`);
})();
