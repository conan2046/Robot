(() => {
  'use strict';
  const app = document.querySelector('#app');
  const state = { data: null, query: '', page: 1, modal: null };

  const escapeHtml = (v='') => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const enabledProducts = () => (state.data?.products || []).filter(p => p.enabled !== false).sort((a,b)=>(a.sort||0)-(b.sort||0));
  const category = id => state.data.categories.find(c => c.id === id);
  const type = id => (state.data.types || []).find(t => t.id === id);
  const countCategory = id => id === 'all' ? enabledProducts().length : enabledProducts().filter(p => p.category === id).length;
  const pageSize = () => Math.max(1, Number(state.data?.site?.pageSize || 12));

  function route() {
    const path = location.pathname.replace(/\/+$/, '') || '/';
    const m = path.match(/^\/category\/([^/]+)$/);
    const params = new URLSearchParams(location.search);
    return m ? { name:'category', id:decodeURIComponent(m[1]), product:params.get('product') || '' } : { name:'home', id:'all', product:'' };
  }
  function navigate(url) {
    history.pushState({}, '', url);
    state.query=''; state.page=1; state.modal=null;
    render();
  }
  window.addEventListener('popstate', () => { state.query=''; state.page=1; state.modal=null; render(); });

  function matches(p) {
    const q = state.query.trim().toLowerCase();
    if (!q) return true;
    const cat = category(p.category)?.name || '';
    const tp = type(p.type)?.name || '';
    return [p.title,p.description,cat,tp,...(p.tags||[])].filter(Boolean).some(v => String(v).toLowerCase().includes(q));
  }
  function paginate(items) {
    const size = pageSize();
    const total = Math.max(1, Math.ceil(items.length/size));
    state.page = Math.min(Math.max(1,state.page),total);
    return { items:items.slice((state.page-1)*size,state.page*size), total };
  }
  function placeholder(label, kind='image') {
    return `<div class="placeholder"><span class="placeholder-icon">${kind==='video'?'▣':'♟'}</span><span>${escapeHtml(label||'暂无素材')}</span><small>暂无素材</small></div>`;
  }
  function mediaImage(url, alt, label) {
    return `${placeholder(label||alt)}${url?`<img class="js-media-img" src="${escapeHtml(url)}" alt="${escapeHtml(alt)}">`:''}`;
  }
  function header(activeId) {
    const tabs=[{id:'all',name:'全部',sort:0},...state.data.categories.slice().sort((a,b)=>(a.sort||0)-(b.sort||0))];
    return `<header class="header"><div class="container">
      <h1>${escapeHtml(state.data.site.title)}</h1><p class="subtitle">${escapeHtml(state.data.site.subtitle)}</p>
      <div class="search"><span class="search-icon">⌕</span><input id="searchInput" value="${escapeHtml(state.query)}" placeholder="搜索标题 / 标签 / 系列 / 展示类型..."></div>
      <nav class="tabs">${tabs.map(c=>`<a class="tab ${c.id===activeId?'active':''}" data-nav href="${c.id==='all'?'/':`/category/${encodeURIComponent(c.id)}`}">${escapeHtml(c.name)} <span class="tab-count">${countCategory(c.id)}</span></a>`).join('')}</nav>
    </div></header>`;
  }
  function cardPreview(p) {
    const videos=p.videos||[], images=p.images||[];
    // 列表预览固定优先级：视频 > 图片 > cover > 占位。
    // 有视频时，即使同时有图片，也始终把卡片表现为视频内容。
    if (videos.length) {
      const v=videos[0];
      return { kind:'video', src:v.poster||p.cover||'', label:v.title||p.title };
    }
    if (images.length) {
      const i=images[0];
      return { kind:'image', src:i.url||p.cover||'', label:i.title||p.title };
    }
    if (p.cover) return { kind:'cover', src:p.cover, label:p.title };
    return { kind:'empty', src:'', label:p.title };
  }
  function productCard(p) {
    const cat=category(p.category)?.name||'';
    const tp=type(p.type)?.name||'';
    const href=`/category/${encodeURIComponent(p.category)}?product=${encodeURIComponent(p.id)}`;
    const preview=cardPreview(p);
    const isVideo=preview.kind==='video';
    const coverCls=productOrientation(p)===0?'cover-landscape':'cover-portrait';
    return `<a class="product-card" data-nav href="${href}">
      <div class="product-cover ${coverCls}">${mediaImage(preview.src,p.title,preview.label)}<span class="badge">${escapeHtml(tp||'产品展示')}</span>${isVideo?'<span class="play-badge">▶</span>':''}</div>
      <div class="card-body"><h3 class="card-title">${escapeHtml(p.title)}</h3><div class="series-mini">系列：${escapeHtml(cat)}</div><p class="card-desc">${escapeHtml(p.description||'')}</p><div class="meta"><span>▧ ${p.images?.length||0} 图片</span><span>▣ ${p.videos?.length||0} 视频</span></div></div>
    </a>`;
  }
  function pageNumbers(total,current) {
    if(total<=7) return Array.from({length:total},(_,i)=>i+1);
    const out=[1]; let start=Math.max(2,current-2), end=Math.min(total-1,current+2);
    if(start>2) out.push('…'); for(let i=start;i<=end;i++) out.push(i); if(end<total-1) out.push('…'); out.push(total); return out;
  }
  function pagination(total) {
    if(total<=1) return '';
    return `<nav class="pagination" aria-label="分页">
      <button class="page-btn" data-page="${state.page-1}" ${state.page<=1?'disabled':''}>上一页</button>
      ${pageNumbers(total,state.page).map(n=>n==='…'?'<span class="ellipsis">…</span>':`<button class="page-btn ${n===state.page?'active':''}" data-page="${n}">${n}</button>`).join('')}
      <button class="page-btn" data-page="${state.page+1}" ${state.page>=total?'disabled':''}>下一页</button>
    </nav>`;
  }
  function footer() {
    const s=state.data.site;
    return `<footer class="footer"><div class="container"><div>${escapeHtml(s.footer||'')}</div>
      ${s.qrImage?`<div class="qr-wrap"><img class="qr" src="${escapeHtml(s.qrImage)}" alt="联系二维码"><span>扫码联系</span></div>`:''}
      <div>合作咨询：电话 ${escapeHtml(s.phone||'')}</div>${s.address?`<div>${escapeHtml(s.address)}</div>`:''}<div>${escapeHtml(s.copyright||'')}</div></div></footer>`;
  }
  // 产品展示朝向：视频优先，其次图片（与 cardPreview 一致）。
  // 0=横版（landscape）排前，1=竖版（portrait）排后。
  function productOrientation(p) {
    const v=(p.videos||[])[0], i=(p.images||[])[0];
    const m=v||i;
    if(!m) return 1;
    return m.orientation==='landscape' ? 0 : 1;
  }
  function home() {
    // 首页「全部」：先横版后竖版（组内按 sort 升序）；横版铺满后竖版整体另起一行，不回填空位。
    const all=enabledProducts().filter(matches).sort((a,b)=> (productOrientation(a)-productOrientation(b)) || ((a.sort||0)-(b.sort||0))); const pg=paginate(all);
    if(!pg.items.length) return `${header('all')}<main class="main"><div class="container"><div class="empty">没有找到匹配产品</div></div></main>${footer()}`;
    const land=pg.items.filter(p=>productOrientation(p)===0);
    const port=pg.items.filter(p=>productOrientation(p)===1);
    const grids=[land,port].filter(g=>g.length).map(g=>`<div class="product-grid">${g.map(productCard).join('')}</div>`).join('');
    return `${header('all')}<main class="main"><div class="container">${grids}${pagination(pg.total)}</div></main>${footer()}`;
  }
  function mediaAspect(item,type) {
    const r=Number(item?.aspectRatio);
    if (Number.isFinite(r) && r>0.2 && r<5) return { ratio:r, known:true };
    if (item?.orientation==='landscape') return { ratio:16/9, known:true };
    if (item?.orientation==='portrait') return { ratio:9/16, known:true };
    return { ratio:type==='video'?9/16:3/4, known:false };
  }
  function mediaCard(item,type,p) {
    const src=type==='image'?item.url:(item.poster||p.cover||'');
    const aspect=mediaAspect(item,type);
    return `<button class="media-card" data-media-type="${type}" data-product="${escapeHtml(p.id)}" data-media-title="${escapeHtml(item.title)}" data-media-url="${escapeHtml(item.url||'')}" data-media-poster="${escapeHtml(item.poster||'')}">
      <div class="media-frame" data-auto-aspect="${aspect.known?'0':'1'}" style="aspect-ratio:${aspect.ratio}">${mediaImage(src,item.title,item.title)}${type==='video'?'<span class="play-badge">▶</span>':''}</div><div class="media-label">${escapeHtml(item.title)}</div></button>`;
  }
  function productSection(p,cat) {
    const tp=type(p.type)?.name||'';
    const videos=p.videos||[], images=p.images||[];
    // 详情同样使用：视频优先，其次图片。没有的区块不显示。
    const videoBlock=videos.length?`<h3 class="media-heading">视频（${videos.length}）</h3><div class="media-grid">${videos.map(v=>mediaCard(v,'video',p)).join('')}</div>`:'';
    const imageBlock=images.length?`<h3 class="media-heading">图片（${images.length}）</h3><div class="media-grid">${images.map(i=>mediaCard(i,'image',p)).join('')}</div>`:'';
    const emptyBlock=!videos.length&&!images.length?'<div class="empty-media">该内容暂未上传图片或视频</div>':'';
    return `<section class="product-section"><div class="product-head"><div><h2>${escapeHtml(p.title)}</h2><p>${escapeHtml(p.description||'')}</p></div><span class="series">系列：${escapeHtml(cat?.name||'')}${tp?` · 类型：${escapeHtml(tp)}`:''}</span></div>
      ${videoBlock}${imageBlock}${emptyBlock}</section>`;
  }
  function categoryPage(r) {
    const cat=category(r.id); if(!cat) return `${header(r.id)}<main class="main"><div class="container empty">分类不存在</div></main>${footer()}`;
    let products=enabledProducts().filter(p=>p.category===r.id && (!r.product||p.id===r.product)).filter(matches);
    let total=1; if(!r.product){const pg=paginate(products);products=pg.items;total=pg.total;} else state.page=1;
    return `${header(r.id)}<main class="main"><div class="container">${products.length?products.map(p=>productSection(p,cat)).join(''):`<div class="empty">${r.product?'未找到该产品':'该分类暂无匹配产品'}</div>`}${r.product?'':pagination(total)}</div></main>${footer()}`;
  }
  function modalHtml() {
    const m=state.modal;if(!m)return '';
    if(m.type==='video') return `<div class="overlay" id="overlay"><div class="modal video-modal-shell"><button class="modal-close" aria-label="关闭">×</button><div class="video-modal-wrap"><video class="video-modal" src="${escapeHtml(m.url)}" ${m.poster?`poster="${escapeHtml(m.poster)}"`:''} controls autoplay playsinline></video><div class="modal-title">${escapeHtml(m.title)}</div></div></div></div>`;
    return `<div class="overlay" id="overlay"><div class="modal"><button class="modal-close" aria-label="关闭">×</button><img class="image-modal" src="${escapeHtml(m.url)}" alt="${escapeHtml(m.title)}"><div class="modal-title">${escapeHtml(m.title)}</div></div></div>`;
  }
  function ageGate() {
    const cfg=state.data.site.ageCheck||{}; if(!cfg.enabled||localStorage.getItem('robot-showcase-access-confirmed'))return '';
    return `<div class="overlay" id="ageOverlay"><div class="age-card"><h2>${escapeHtml(cfg.title||'访问确认')}</h2><p>${escapeHtml(cfg.message||'请确认后继续浏览。')}</p><div class="age-actions"><button class="primary" id="ageConfirm">${escapeHtml(cfg.confirmText||'继续浏览')}</button><button class="secondary" id="ageExit">${escapeHtml(cfg.exitText||'退出')}</button></div></div></div>`;
  }
  function bind() {
    document.querySelectorAll('[data-nav]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();navigate(a.getAttribute('href'));}));
    document.querySelector('#searchInput')?.addEventListener('input',e=>{state.query=e.target.value;state.page=1;render(); requestAnimationFrame(()=>{const i=document.querySelector('#searchInput');i?.focus();i?.setSelectionRange(state.query.length,state.query.length);});});
    document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>{const n=Number(b.dataset.page);if(n>0){state.page=n;render();scrollTo({top:0,behavior:'smooth'});}}));
    document.querySelectorAll('[data-media-type]').forEach(b=>b.addEventListener('click',()=>{const url=b.dataset.mediaUrl||'';if(!url)return;state.modal={type:b.dataset.mediaType,title:b.dataset.mediaTitle||'',url,poster:b.dataset.mediaPoster||''};render();}));
    document.querySelectorAll('.js-media-img').forEach(img=>{
      img.addEventListener('error',()=>img.classList.add('hidden'));
      const adjust=()=>{
        const frame=img.closest('.media-frame[data-auto-aspect="1"]');
        if(frame && img.naturalWidth>0 && img.naturalHeight>0){
          frame.style.aspectRatio=`${img.naturalWidth}/${img.naturalHeight}`;
        }
      };
      img.addEventListener('load',adjust);
      if(img.complete) adjust();
    });
    document.querySelector('.modal-close')?.addEventListener('click',()=>{state.modal=null;render();});
    document.querySelector('#overlay')?.addEventListener('click',e=>{if(e.target.id==='overlay'){state.modal=null;render();}});
    document.querySelector('#ageConfirm')?.addEventListener('click',()=>{localStorage.setItem('robot-showcase-access-confirmed','1');render();});
    document.querySelector('#ageExit')?.addEventListener('click',()=>{location.href=state.data.site.ageCheck?.exitUrl||'about:blank';});
  }
  function render() {
    const r=route(); app.innerHTML=`<div class="shell">${r.name==='home'?home():categoryPage(r)}</div>${modalHtml()}${ageGate()}`; bind();
  }
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.modal){state.modal=null;render();}});
  async function boot(){try{const res=await fetch('./data/site-data.json',{cache:'no-store'});if(!res.ok)throw new Error();state.data=await res.json();render();}catch(e){app.innerHTML='<div class="empty">数据加载失败，请检查 ./data/site-data.json</div>';}}
  boot();
})();
