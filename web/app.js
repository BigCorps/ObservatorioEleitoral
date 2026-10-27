/* Observatório Eleitoral — painel estático e verificável.
   Os números exibidos vêm exclusivamente dos CSVs gerados no repositório.
   Ausência de campo significa ausência de dado, nunca zero. */
'use strict';

const ufNames = {
  BR:'Brasil (27 UFs)', AC:'Acre',AL:'Alagoas',AP:'Amapá',AM:'Amazonas',
  BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',
  GO:'Goiás',MA:'Maranhão',MT:'Mato Grosso',MS:'Mato Grosso do Sul',
  MG:'Minas Gerais',PA:'Pará',PB:'Paraíba',PR:'Paraná',PE:'Pernambuco',
  PI:'Piauí',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RS:'Rio Grande do Sul',
  RO:'Rondônia',RR:'Roraima',SC:'Santa Catarina',SP:'São Paulo',
  SE:'Sergipe',TO:'Tocantins',ZZ:'Exterior (ZZ)'
};
const metricNames = {
  pct_abstencao:'Abstenção',pct_brancos:'Votos brancos',pct_nulos:'Votos nulos',
  pct_hab_sem_biometria_log:'Sem biometria cadastrada',
  pct_hab_manual_apos_falha_log:'Biometria não reconhecida (liberação manual)',
  pct_votos_apos_17h:'Votos após 17h',comparecimento:'Comparecimento'
};
const files = {
  indicators:'./dados/indicadores.csv',
  timeline2022:'./dados/votos_por_15min_2022.csv',
  timeline2026:'./dados/votos_por_15min_2026.csv'
};
const state = {year:'2022',round:'2',uf:'BR',trendMetric:'pct_abstencao',rankingMetric:'pct_abstencao'};
let data = null;
const nf = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0});
const df = new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});

function parseCSV(source) {
  const text = source.replace(/^\uFEFF/,'');
  const rows = [];
  let row=[], field='', quoted=false;
  for (let i=0;i<text.length;i++) {
    const c=text[i];
    if (c==='"') {
      if (quoted && text[i+1]==='"') { field+='"'; i++; }
      else quoted=!quoted;
    } else if (c===',' && !quoted) { row.push(field); field=''; }
    else if ((c==='\n'||c==='\r') && !quoted) {
      if (c==='\r' && text[i+1]==='\n') i++;
      row.push(field);
      if (row.some(x=>x!=='')) rows.push(row);
      row=[]; field='';
    } else field+=c;
  }
  if (field!==''||row.length) { row.push(field); rows.push(row); }
  const headers=rows.shift()||[];
  return rows.map(values=>Object.fromEntries(headers.map((h,i)=>[h.trim(),values[i]??''])));
}
function numeric(value) {
  if (value===null||value===undefined||value==='') return null;
  const n=Number(value);
  return Number.isFinite(n)?n:null;
}
function number(value){const n=numeric(value);return n===null?'—':nf.format(n);}
function percent(value){const n=numeric(value);return n===null?'—':df.format(n)+'%';}
function timeFromDecimal(value) {
  const n=numeric(value);
  if(n===null)return '—';
  const rounded=Math.round(n*60);
  return String(Math.floor(rounded/60)%24).padStart(2,'0')+':'+String(rounded%60).padStart(2,'0');
}
function key(year,round,uf){return year+'-'+round+'-'+uf;}
function indicator(year,round,uf) {return data?.indicators.get(key(year,round,uf))||null;}
const biometricFields=new Set(['pct_hab_biometrica_log','pct_hab_manual_apos_falha_log','pct_hab_sem_biometria_log','pct_biometria_nao_habilitados_bu']);
function effectiveMetric(year,round,uf,field) {
  if(uf==='ZZ' && biometricFields.has(field)) return null;
  return numeric(indicator(year,round,uf)?.[field]);
}
function metricValue(year,round,uf,field) {
  if(field==='pct_brancos_nulos') {
    const a=effectiveMetric(year,round,uf,'pct_brancos');
    const b=effectiveMetric(year,round,uf,'pct_nulos');
    return a===null||b===null?null:a+b;
  }
  return effectiveMetric(year,round,uf,field);
}
function node(tag,className,text) {
  const el=document.createElement(tag);
  if(className)el.className=className;
  if(text!==undefined)el.textContent=text;
  return el;
}
function setText(id,value) {document.getElementById(id).textContent=value;}
function setUpFilters() {
  const select=document.getElementById('ufFilter');
  const exterior=node('option',null,'Exterior (ZZ) · votação fora do país'); exterior.value='ZZ';select.append(exterior);
  Object.keys(ufNames).filter(uf=>uf!=='BR'&&uf!=='ZZ').sort((a,b)=>ufNames[a].localeCompare(ufNames[b],'pt-BR')).forEach(uf=>{
    const opt=node('option',null,uf+' · '+ufNames[uf]);opt.value=uf;select.append(opt);
  });
  for(const [id,field] of [['yearFilter','year'],['roundFilter','round'],['ufFilter','uf'],['trendMetric','trendMetric'],['rankingMetric','rankingMetric']]){
    const el=document.getElementById(id);
    el.value=state[field];
    el.addEventListener('change',()=>{state[field]=el.value;render();});
  }
  document.getElementById('resetButton').addEventListener('click',()=>{
    Object.assign(state,{year:'2022',round:'2',uf:'BR',trendMetric:'pct_abstencao',rankingMetric:'pct_abstencao'});
    for(const [id,field] of [['yearFilter','year'],['roundFilter','round'],['ufFilter','uf'],['trendMetric','trendMetric'],['rankingMetric']])
      document.getElementById(id).value=state[field];
    render();
  });
}
function renderCoverage() {
  const partial=state.year==='2026'&&state.round==='2';
  const badge=document.getElementById('coverageBadge');
  badge.textContent=partial?'2026 · 2º turno: BU e logs pendentes':state.uf==='ZZ'?'Exterior · cobertura de logs específica':'BU e logs processados · confira cobertura';
  badge.classList.toggle('partial',partial||state.uf==='ZZ');
}
function renderKpis() {
  const d=indicator(state.year,state.round,state.uf)||{};
  setText('kpiAttendance',number(d.comparecimento));
  setText('kpiAttendanceSub',numeric(d.aptos)===null?'Eleitores que votaram':number(d.aptos)+' eleitores aptos');
  setText('kpiAbstention',percent(d.pct_abstencao));
  const blank=numeric(d.pct_brancos),nullVotes=numeric(d.pct_nulos);
  setText('kpiBlankNull',blank===null||nullVotes===null?'—':percent(blank+nullVotes));
  setText('kpiBioNoReg',percent(effectiveMetric(state.year,state.round,state.uf,'pct_hab_sem_biometria_log')));
  setText('kpiBiometry',percent(effectiveMetric(state.year,state.round,state.uf,'pct_hab_manual_apos_falha_log')));
  setText('kpiBioConfirmed',percent(effectiveMetric(state.year,state.round,state.uf,'pct_hab_biometrica_log')));
  setText('kpiLate',percent(d.pct_votos_apos_17h));
  const first=timeFromDecimal(d.mediana_primeiro_voto_h),last=timeFromDecimal(d.mediana_ultimo_voto_h);
  setText('kpiClock',first==='—'||last==='—'?'—':first+' → '+last);
}
function renderTrend() {
  const chart=document.getElementById('trendChart');
  chart.replaceChildren();
  const combinations=[['2022','1'],['2022','2'],['2026','1'],['2026','2']];
  const values=combinations.map(([year,round])=>metricValue(year,round,state.uf,state.trendMetric));
  const available=values.filter(v=>v!==null);
  const max=Math.max(1,...available);
  const absolute=state.trendMetric==='comparecimento';
  chart.setAttribute('aria-label',metricNames[state.trendMetric]+' por turno no recorte '+ufNames[state.uf]+'. '+combinations.map(([y,t],i)=>y+' '+t+'º turno: '+(values[i]===null?'não disponível':absolute?number(values[i]):percent(values[i]))).join('; '));
  combinations.forEach(([year,round],i)=>{
    const col=node('div','trend-col'+(values[i]===null?' empty':''));
    const val=node('div','trend-value',values[i]===null?'Pendente':absolute?number(values[i]):percent(values[i]));
    const holder=node('div','trend-bar-wrap');
    const bar=node('div','trend-bar'+(year===state.year&&round===state.round?' selected':''));
    bar.style.height=(values[i]===null?0:Math.max(1,values[i]/max*100))+'%';
    holder.append(bar);
    col.append(val,holder,node('div','trend-label',year+' · '+round+'º'));
    chart.append(col);
  });
  setText('trendNote','Escala com base zero, proporcional ao maior valor exibido. '+(available.length<4?'Alguns turnos não possuem este dado publicado.':'Valores do recorte selecionado.')+' Comparações de biometria e horário exigem considerar regras e cobertura de logs.');
}
function renderTimeline() {
  const chart=document.getElementById('timelineChart');
  chart.replaceChildren();
  if(state.uf==='ZZ'){
    chart.append(node('p','empty-chart','Curva de 15 minutos do exterior ainda não publicada neste conjunto consolidado.'));
    chart.setAttribute('aria-label','Distribuição de votos por horário do exterior não disponível');
    setText('timelineNote','Para o exterior, o painel oferece comparecimento e indicadores por turno, mas não uma curva de votação por 15 minutos.');
    return;
  }
  const all=(state.year==='2022'?data.timeline2022:data.timeline2026);
  const rows=all.filter(r=>r.turno===state.round && r.abrangencia.startsWith('BR')).sort((a,b)=>Number(a.minuto_do_dia)-Number(b.minuto_do_dia));
  if(!rows.length){
    chart.append(node('p','empty-chart','Ainda não há logs publicados para exibir esta distribuição.'));
    chart.setAttribute('aria-label','Dados de horário não disponíveis para o turno selecionado');
    setText('timelineNote','2026, 2º turno: distribuição por horário pendente dos arquivos de log do TSE.');
    return;
  }
  const max=Math.max(1,...rows.map(r=>Number(r.votos)||0));
  rows.forEach(r=>{
    const votes=Number(r.votos)||0;
    const late=Number(r.minuto_do_dia)>=1020;
    const bar=node('div','time-bar'+(late?' late':''));
    bar.style.height=Math.max(1,votes/max*100)+'%';
    bar.title=r.faixa+' — '+number(votes)+' votos';
    bar.setAttribute('aria-label',bar.title);
    chart.append(bar);
  });
  chart.setAttribute('aria-label','Volume nacional de votos a cada 15 minutos, eleição '+state.year+', '+state.round+'º turno. Passe sobre as barras para os valores.');
  setText('timelineNote','Curva nacional (27 UFs, sem exterior) em horário de Brasília. Este gráfico não muda com o filtro de estado. Votos depois das 17h podem ser regulares quando havia eleitores na fila.');
}
function renderRanking() {
  const metric=state.rankingMetric;
  const list=document.getElementById('stateRanking');
  list.replaceChildren();
  setText('rankingTitle',metricNames[metric]+' por estado');
  const rows=Object.keys(ufNames).filter(uf=>uf!=='BR'&&uf!=='ZZ').map(uf=>({uf,value:metricValue(state.year,state.round,uf,metric)})).filter(x=>x.value!==null).sort((a,b)=>b.value-a.value);
  if(!rows.length){
    list.append(node('p','empty-chart','Esse indicador depende de logs ainda não disponíveis para o turno selecionado.'));
    return;
  }
  const max=Math.max(1,...rows.map(x=>x.value));
  rows.forEach(({uf,value})=>{
    const row=node('button','rank-row'+(uf===state.uf?' active':''));row.type='button';
    row.title='Abrir '+ufNames[uf];
    row.setAttribute('aria-label',ufNames[uf]+': '+percent(value)+'. Filtrar o painel');
    const name=node('span','rank-uf',uf);
    const track=node('span','rank-track');
    const fill=node('span','rank-fill');fill.style.width=Math.max(1,value/max*100)+'%';track.append(fill);
    const val=node('span','rank-value',percent(value));
    row.append(name,track,val);
    row.addEventListener('click',()=>{
      state.uf=uf;document.getElementById('ufFilter').value=uf;render();
      document.getElementById('painel').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
    });
    list.append(row);
  });
}
function renderComparison() {
  setText('comparisonScope',state.uf==='ZZ'?'Exterior (ZZ)':ufNames[state.uf]+(state.uf==='BR'?' · sem exterior':''));
  const rows=[
    ['Comparecimento','comparecimento','number'],
    ['Abstenção','pct_abstencao','percent'],
    ['Votos brancos','pct_brancos','percent'],
    ['Votos nulos','pct_nulos','percent'],
    ['Brancos + nulos','pct_brancos_nulos','percent'],
    ['Sem biometria cadastrada (log)','pct_hab_sem_biometria_log','percent'],
    ['Biometria não reconhecida (log)','pct_hab_manual_apos_falha_log','percent'],
    ['Biometria confirmada (log)','pct_hab_biometrica_log','percent'],
    ['Votos após 17h (log)','pct_votos_apos_17h','percent'],
    ['Primeiro voto (mediana)','mediana_primeiro_voto_h','time'],
    ['Último voto (mediana)','mediana_ultimo_voto_h','time']
  ];
  const target=document.getElementById('comparisonBody');target.replaceChildren();
  for(const [label,field,type] of rows){
    const tr=node('tr');
    const th=node('td',null,label);tr.append(th);
    for(const [year,round] of [['2022','1'],['2022','2'],['2026','1'],['2026','2']]){
      const raw=metricValue(year,round,state.uf,field);
      const value=type==='number'?number(raw):type==='percent'?percent(raw):timeFromDecimal(raw);
      const td=node('td',value==='—'?'na':null,value);
      if(value==='—')td.title='Dado ainda não disponível';
      tr.append(td);
    }
    target.append(tr);
  }
}

function renderScopeInfo() {
  const el=document.getElementById('scopeDisclaimer');
  if(state.uf==='ZZ'){
    const d=indicator(state.year,state.round,'ZZ')||{};
    const sections=numeric(d.secoes),logs=numeric(d.secoes_com_log);
    const coverage=sections&&logs!==null?(' Cobertura dos logs: '+number(logs)+' de '+number(sections)+' seções.'): ' Logs técnicos ainda não disponíveis para este recorte.';
    el.textContent='Exterior (ZZ): resultados oficiais por seção apresentados separadamente das 27 UFs.'+coverage+' As categorias biométricas não são diretamente comparáveis às utilizadas no território nacional; aparecem como não aplicáveis. Não é possível associar modalidade de identificação a candidato.';
  }else if(state.uf==='BR'){
    el.textContent='O recorte “Brasil” soma as 27 UFs, sem o eleitorado no exterior. Para conferir o exterior, selecione “Exterior (ZZ)”. Percentuais de biometria referem-se às habilitações nos logs disponíveis; nenhuma modalidade revela como uma pessoa votou.';
  }else{
    el.textContent=ufNames[state.uf]+': dados estaduais por turno. Os percentuais biométricos são calculados sobre as habilitações nos logs disponíveis, não sobre o cadastro geral. Variações não demonstram irregularidade isoladamente.';
  }
}
function signedDifference(a,b){
  return a===null||b===null?null:b-a;
}
function formatDifference(value,type){
  if(value===null||!Number.isFinite(value))return '—';
  const prefix=value>0?'+':value<0?'−':'';
  const n=Math.abs(value);
  return prefix+(type==='count'?number(Math.round(n)):df.format(n)+' p.p.');
}
function renderDelta(){
  const rows=[
    ['Comparecimento','comparecimento','count'],
    ['Abstenção','pct_abstencao','pp'],
    ['Brancos + nulos','pct_brancos_nulos','pp'],
    ['Votos brancos','pct_brancos','pp'],
    ['Votos nulos','pct_nulos','pp'],
    ['Sem biometria cadastrada (log)','pct_hab_sem_biometria_log','pp'],
    ['Biometria não reconhecida (log)','pct_hab_manual_apos_falha_log','pp'],
    ['Votos após 17h (log)','pct_votos_apos_17h','pp']
  ];
  const tbody=document.getElementById('deltaBody');tbody.replaceChildren();
  for(const [label,field,type] of rows){
    const [a,b,c,d]=[['2022','1'],['2022','2'],['2026','1'],['2026','2']].map(([year,round])=>metricValue(year,round,state.uf,field));
    const delta22=signedDifference(a,b),delta26=signedDifference(c,d);
    const compareDeltas=delta22===null||delta26===null?null:delta26-delta22;
    const values=[delta22,delta26,compareDeltas,signedDifference(a,c),signedDifference(b,d)];
    const tr=node('tr');tr.append(node('td',null,label));
    values.forEach(v=>{
      const td=node('td',v===null?'na':null,formatDifference(v,type));
      if(v===null)td.title='Comparação pendente: faltam dados para este par';
      tr.append(td);
    });
    tbody.append(tr);
  }
}
function render() {
  if(!data)return;
  renderCoverage();renderKpis();renderScopeInfo();renderTrend();renderTimeline();renderRanking();renderComparison();renderDelta();
}
async function init() {
  setUpFilters();
  try{
    const entries=await Promise.all(Object.entries(files).map(async ([name,path])=>{
      const response=await fetch(path,{cache:'no-cache'});
      if(!response.ok)throw new Error('Arquivo '+path+': '+response.status);
      return [name,parseCSV(await response.text())];
    }));
    const loaded=Object.fromEntries(entries);
    data={indicators:new Map(loaded.indicators.map(r=>[key(r.ano,r.turno,r.abrangencia),r])),timeline2022:loaded.timeline2022,timeline2026:loaded.timeline2026};
    if(!data.indicators.size)throw new Error('Indicadores vazios');
    render();
  }catch(err){
    console.error('Falha ao carregar dados do Observatório:',err);
    document.getElementById('loadError').hidden=false;
    document.getElementById('coverageBadge').textContent='Falha no carregamento';
  }
}
document.addEventListener('DOMContentLoaded',init);