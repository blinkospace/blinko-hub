(async () => {
  const mySiteUrl = window.location.origin;
  
  // 1. 自动从本地缓存提取真正的 Authorization Token
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
    console.error('解析 Token 失败:', e);
  }

  if (!token) {
    console.error('❌ 未找到 Token！请确保你已经在当前网页上登录了 Blinko 账号。');
    return;
  }

  console.log('🔑 登录 Token 提取成功！开始拉取 Hub 站点列表...');

  // 2. 拉取 Hub 站点
  const hubRes = await fetch('https://cdn.jsdelivr.net/gh/Inverstar/blinko-hub@main/index.json');
  const hubData = await hubRes.json();
  const sites = hubData.sites || [];
  
  console.log(`✅ 成功获取 ${sites.length} 个站点，开始批量关注...`);

  // 3. 循环关注
  let successCount = 0;
  for (const site of sites) {
    if (!site.url || site.url.replace(/\/$/, '') === mySiteUrl.replace(/\/$/, '')) {
      continue;
    }
    
    try {
      console.log(`➡️ 正在关注: ${site.title} (${site.url})...`);
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
        console.log(`  └ 🟢 关注成功: ${site.title}`);
      } else {
        console.warn(`  └ 🟡 提示/已有关注 (${site.title}):`, result.message || result.error || JSON.stringify(result));
      }
    } catch (err) {
      console.error(`  └ 🔴 关注失败 (${site.title}):`, err.message);
    }
  }

  console.log(`🎉 批量关注完成！共成功关注 ${successCount} 个站点。刷新页面后即可在 Hub 看到聚合动态！`);
})();
