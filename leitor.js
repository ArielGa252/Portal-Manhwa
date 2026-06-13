const STORAGE_KEY='portal_manhwas_progress_v2';
const THEME_KEY='portal_manhwas_theme';
const $=s=>document.querySelector(s);
const params=new URLSearchParams(location.search);
const id=params.get('id')||'';
const title=params.get('title')||'Obra';
const cap=Number(params.get('cap')||0);
let state=loadState(),fitNormal=false;
function loadState(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY))||{}}catch{return {}}}
function saveState(){localStorage.setItem(STORAGE_KEY,JSON.stringify(state))}
function getProgress(key){state[key] ||= {read:[],current:0,favorite:false,finished:false};return state[key]}
async function readJson(url,fallback){try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(r.status);return await r.json()}catch{return fallback}}
async function init(){if(localStorage.getItem(THEME_KEY)==='light')document.documentElement.classList.add('light');$('#readerTitle').textContent=title;$('#readerInfo').textContent=`Capítulo ${cap}`;$('#backToManga').href=`manhwa.html?id=${encodeURIComponent(id)}&title=${encodeURIComponent(title)}`;$('#markReadBtn').onclick=markRead;$('#fitBtn').onclick=()=>{fitNormal=!fitNormal;$('#readerPages').classList.toggle('fit-normal',fitNormal);$('#fitBtn').textContent=fitNormal?'Tela cheia':'Largura'};const data=await readJson(`data/capitulos/${id}-${cap}.json`,null);const images=normalizeImages(data);renderImages(images)}
function normalizeImages(data){if(!data)return[];if(Array.isArray(data))return data.map(x=>typeof x==='string'?x:(x.src||x.url||x.imagem)).filter(Boolean);return(data.imagens||data.images||data.paginas||data.pages||[]).map(x=>typeof x==='string'?x:(x.src||x.url||x.imagem)).filter(Boolean)}
function renderImages(images){const pages=$('#readerPages');if(!images.length){$('#readerEmpty').classList.remove('hidden');return}pages.innerHTML=images.map((src,i)=>`<img src="${src}" alt="Página ${i+1}" loading="lazy" onerror="this.outerHTML='<div class=&quot;page-error&quot;>Erro ao carregar página ${i+1}</div>'">`).join('');markRead(false)}
function markRead(showAlert=true){const p=getProgress(id);if(!p.read.includes(cap))p.read.push(cap);p.current=Math.max(Number(p.current||0),cap);p.read.sort((a,b)=>a-b);saveState();if(showAlert)alert('Capítulo marcado como lido!')}
init();
