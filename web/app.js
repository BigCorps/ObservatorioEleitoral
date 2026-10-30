/* Observatório Eleitoral — painel estático e verificável.
   Os números exibidos vêm exclusivamente dos CSVs gerados no repositório.
   Ausência de campo significa ausência de dado, nunca zero. */
'use strict';

const ufNames = {
  BR:'Brasil (27 UFs + exterior)', AC:'Acre',AL:'Alagoas',AP:'Amapá',AM:'Amazonas',
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
  pct_votos_apos_17h:'Votos após 17h',pct_brancos_nulos:'Brancos + nulos',
  pct_validos:'Votos válidos',comparecimento:'Comparecimento'
};
const files = {
  indicators:'./dados/indicadores.csv',
  timeline2022:'./dados/votos_por_15min_2022.csv',
  timeline2026:'./dados/votos_por_15min_2026.csv',
  votes2022:'./dados/presidente_2022.csv',
  votes2026:'./dados/presidente_2026.csv',
  bio2022:'./dados/biometria_2022.csv',
  bio2026:'./dados/biometria_2026.csv',
  temporalUF2022:'./dados/temporal_uf_2022.csv',
  temporalUF2026:'./dados/temporal_uf_2026.csv',
  audits2022:'./dados/reconciliacao_2022.csv',
  audits2026:'./dados/reconciliacao_2026.csv',
  discrepancies:'./dados/quadro_discrepancias.csv'
};
const state = {year:'2022',round:'2',uf:'BR',mapCandidate:'lider',trendMetric:'pct_abstencao',rankingMetric:'pct_abstencao',triagemTeste:'concentracao90'};
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
function syncDockSize() {
  const dock=document.getElementById('filterDock');
  document.documentElement.style.setProperty('--dock-current-height',dock.offsetHeight+'px');
}
function syncControls() {
  for(const [id,field] of [['yearFilter','year'],['roundFilter','round'],['ufFilter','uf'],['trendMetric','trendMetric'],['rankingMetric','rankingMetric']]) {
    const element=document.getElementById(id);
    if(element)element.value=state[field];
  }
  document.querySelectorAll('input[name="mapCandidate"]').forEach(input=>{
    input.checked=input.value===state.mapCandidate;
  });
  const current=state.year+' · '+state.round+'º turno · '+(state.uf==='BR'?'Brasil + exterior':state.uf==='ZZ'?'Exterior':ufNames[state.uf]);
  setText('dockCurrent',current);
  document.getElementById('triagemTeste').value=state.triagemTeste;
}
function selectScope(uf) {
  state.uf=uf;
  render();
}
function setUpFilters() {
  const scope=document.getElementById('ufFilter');
  const exterior=node('option',null,'Exterior (ZZ) · votação fora do país');exterior.value='ZZ';scope.append(exterior);
  Object.keys(ufNames).filter(uf=>uf!=='BR'&&uf!=='ZZ').sort((a,b)=>ufNames[a].localeCompare(ufNames[b],'pt-BR')).forEach(uf=>{
    const opt=node('option',null,uf+' · '+ufNames[uf]);opt.value=uf;scope.append(opt);
  });
  for(const [id,field] of [['yearFilter','year'],['roundFilter','round'],['ufFilter','uf'],['trendMetric','trendMetric'],['rankingMetric','rankingMetric']]) {
    document.getElementById(id).addEventListener('change',event=>{
      state[field]=event.target.value;
      render();
    });
  }
  document.querySelectorAll('input[name="mapCandidate"]').forEach(input=>{
    input.addEventListener('change',event=>{
      if(event.target.checked){state.mapCandidate=event.target.value;render();}
    });
  });
  document.getElementById('triagemTeste').addEventListener('change',event=>{state.triagemTeste=event.target.value;renderTriagem();});
  document.getElementById('resetButton').addEventListener('click',()=>{
    Object.assign(state,{year:'2022',round:'2',uf:'BR',mapCandidate:'lider',trendMetric:'pct_abstencao',rankingMetric:'pct_abstencao',triagemTeste:'concentracao90'});
    render();
  });
  const dock=document.getElementById('filterDock');
  const toggle=document.getElementById('dockToggle');
  function setCollapsed(collapsed){
    dock.classList.toggle('is-collapsed',collapsed);
    toggle.setAttribute('aria-expanded',String(!collapsed));
    toggle.firstChild.textContent=collapsed?'Abrir filtros ':'Ocultar filtros ';
    syncDockSize();
  }
  toggle.addEventListener('click',()=>setCollapsed(!dock.classList.contains('is-collapsed')));
  const compact=window.matchMedia('(max-width:720px)');
  setCollapsed(compact.matches);
  compact.addEventListener?.('change',event=>setCollapsed(event.matches));
  if(typeof ResizeObserver!=='undefined')new ResizeObserver(syncDockSize).observe(dock);
  window.addEventListener('resize',syncDockSize);
  syncControls();
}
function has2026Round2Logs(){return !!data&&[...data.temporalUFByYear['2026'].keys()].some(k=>k.startsWith('2-'));}
function renderCoverage() {
  const partial=state.year==='2026'&&state.round==='2'&&!has2026Round2Logs();
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
  for(const [id,field] of [['kpiAbstentionCount','pct_abstencao'],['kpiBlankNullCount','pct_brancos_nulos'],['kpiBioNoRegCount','pct_hab_sem_biometria_log'],['kpiBiometryCount','pct_hab_manual_apos_falha_log'],['kpiBioConfirmedCount','pct_hab_biometrica_log'],['kpiLateCount','pct_votos_apos_17h']])
    setText(id,countLabel(state.year,state.round,state.uf,field));
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
  chart.setAttribute('aria-label',metricNames[state.trendMetric]+' por turno no recorte '+ufNames[state.uf]+'. '+combinations.map(([y,t],i)=>y+' '+t+'º turno: '+(values[i]===null?'não disponível':(absolute?number(values[i]):percent(values[i]))+'; '+countLabel(y,t,state.uf,state.trendMetric))).join('; '));
  combinations.forEach(([year,round],i)=>{
    const col=node('div','trend-col'+(values[i]===null?' empty':''));
    const val=node('div','trend-value',values[i]===null?'Pendente':absolute?number(values[i]):percent(values[i]));
    const holder=node('div','trend-bar-wrap');
    const bar=node('div','trend-bar'+(year===state.year&&round===state.round?' selected':''));
    bar.style.height=(values[i]===null?0:Math.max(1,values[i]/max*100))+'%';
    holder.append(bar);
    const count=metricCount(year,round,state.uf,state.trendMetric);
    const meta=node('div','trend-count');
    meta.append(node('strong',null,count===null?'—':absolute?'Eleitores':number(count)),node('span',null,absolute?'que votaram':countUnit(state.trendMetric)));
    col.append(val,meta,holder,node('div','trend-label',year+' · '+round+'º'));
    chart.append(col);
  });
  setText('trendNote','Escala com base zero, proporcional ao maior valor exibido. '+(available.length<4?'Alguns turnos não possuem este dado publicado.':'Valores do recorte selecionado.')+' Os números absolutos vêm dos totais eleitorais por UF ou dos registros de logs. Para Brasil, biometria e horários continuam limitados às 27 UFs; a zona ZZ só entra nos totais eleitorais.');
}
function renderTimeline() {
  const chart=document.getElementById('timelineChart');
  const tag=document.getElementById('timelineTag');
  chart.replaceChildren();
  chart.classList.remove('regional-timeline');
  if(state.uf!=='BR'){
    const row=data.temporalUFByYear[state.year]?.get(state.round+'-'+state.uf);
    const total=numeric(row?.votos),a17=numeric(row?.votos_apos_17h);
    const a18=numeric(row?.votos_apos_18h),a19=numeric(row?.votos_apos_19h);
    tag.textContent=state.uf==='ZZ'?'EXTERIOR • HORÁRIO LOCAL':'LOGS DE '+state.uf+' • HORÁRIO DE BRASÍLIA';
    if([total,a17,a18,a19].some(v=>v===null)||total<=0){
      chart.append(node('p','empty-chart','Dados de horário de '+ufNames[state.uf]+' ainda não disponíveis para esse turno.'));
      chart.setAttribute('aria-label','Sem dados temporais para '+ufNames[state.uf]);
      setText('timelineNote','Não há logs disponíveis para '+ufNames[state.uf]+' nesse turno. O gráfico do Brasil não é mostrado como se fosse do estado.');
      return;
    }
    const bins=[
      ['Até 17h',total-a17,false],
      ['17h–18h',a17-a18,true],
      ['18h–19h',a18-a19,true],
      ['Após 19h',a19,true]
    ];
    if(bins.some(b=>b[1]<0)||bins.reduce((sum,b)=>sum+b[1],0)!==total){
      chart.append(node('p','empty-chart','Os totais de horário não estão reconciliados neste recorte.'));
      setText('timelineNote','Dados inconsistentes: não exibimos contagens calculadas sem reconciliação.');
      return;
    }
    chart.classList.add('regional-timeline');
    const max=Math.max(1,...bins.map(b=>b[1]));
    bins.forEach(([label,votes,late])=>{
      const col=node('div','regional-bin');
      const count=node('strong','regional-count',number(votes));
      const track=node('div','regional-bar-track');
      const bar=node('div','regional-bar'+(late?' is-late':''));
      bar.style.height=(votes===0?0:Math.max(2,votes/max*100))+'%';
      const period=node('span','regional-period',label);
      const pct=node('small','regional-percent',percent(votes/total*100));
      track.append(bar);col.append(count,track,period,pct);
      col.title=label+': '+number(votes)+' votos ('+percent(votes/total*100)+')';
      chart.append(col);
    });
    chart.setAttribute('aria-label',ufNames[state.uf]+': '+bins.map(b=>b[0]+': '+number(b[1])+' votos').join('; '));
    setText('timelineNote',ufNames[state.uf]+' · '+number(total)+' votações em '+number(row.secoes_com_log)+' seções com logs. As quatro faixas são contagens reais, não estimativas de 15 minutos. '+(state.uf==='ZZ'?'Horários locais do exterior, não convertidos para Brasília.':'Horário de Brasília.')+' Votações após 17h podem ser regulares.');
    return;
  }
  tag.textContent='LOGS DAS 27 UFs • HORÁRIO DE BRASÍLIA';
  const rows=(state.year==='2022'?data.timeline2022:data.timeline2026)
    .filter(r=>r.turno===state.round&&r.abrangencia.startsWith('BR'))
    .sort((a,b)=>Number(a.minuto_do_dia)-Number(b.minuto_do_dia));
  if(!rows.length){
    chart.append(node('p','empty-chart','Ainda não há logs publicados para exibir esta distribuição.'));
    chart.setAttribute('aria-label','Sem dados temporais para Brasil nesse turno');
    setText('timelineNote','A distribuição nacional desse turno ainda depende de logs. Não mostramos dados estimados.');
    return;
  }
  const max=Math.max(1,...rows.map(r=>Number(r.votos)||0));
  rows.forEach(r=>{
    const votes=Number(r.votos)||0,late=Number(r.minuto_do_dia)>=1020;
    const bar=node('div','time-bar'+(late?' late':''));
    bar.style.height=Math.max(1,votes/max*100)+'%';
    bar.title=r.faixa+' — '+number(votes)+' votos';
    bar.setAttribute('aria-label',bar.title);
    chart.append(bar);
  });
  chart.setAttribute('aria-label','Distribuição dos logs das 27 UFs a cada 15 minutos em '+state.year+', '+state.round+'º turno');
  setText('timelineNote','Curva de 15 minutos apenas das 27 UFs, em horário de Brasília. Os votos do exterior são excluídos deste gráfico de horários. Votações após 17h podem ser regulares.');
}
function rankingDenominator(year,round,uf,field) {
  const votes=voteData(year,round,uf);
  if(['pct_abstencao','pct_brancos','pct_nulos'].includes(field)){
    if(!votes)return null;
    return field==='pct_abstencao'?votes.electorate:votes.turnout;
  }
  if(field==='pct_votos_apos_17h')return technicalCount(year,round,uf,'temporal','votos');
  if(field==='pct_hab_sem_biometria_log'||field==='pct_hab_manual_apos_falha_log'){
    const keys=['log_votantes_biometria','log_votantes_manual_apos_falha',
      'log_votantes_sem_biometria_cadastrada','log_votantes_sem_etapa_biometrica'];
    const values=keys.map(k=>technicalCount(year,round,uf,'biometry',k));
    if(values.some(v=>v===null))return null;
    return values.reduce((sum,v)=>sum+v,0);
  }
  return null;
}
function renderRankingTotal(metric,availableRows) {
  const countEl=document.getElementById('rankingTotalCount');
  const pctEl=document.getElementById('rankingTotalPercent');
  const note=document.getElementById('rankingTotalNote');
  const national=document.getElementById('rankingNational');
  national.replaceChildren();
  national.hidden=true;
  const seen=[];
  for(const {uf} of availableRows){
    const n=metricCount(state.year,state.round,uf,metric);
    const d=rankingDenominator(state.year,state.round,uf,metric);
    if(n===null||d===null||d<=0||n<0||n>d)continue;
    seen.push({uf,n,d});
  }
  if(!seen.length){
    countEl.textContent='—';pctEl.textContent='—';
    note.textContent='Sem registros suficientes para esse indicador e turno. Ausência de dados não significa zero.';
    return;
  }
  const n=seen.reduce((sum,r)=>sum+r.n,0);
  const d=seen.reduce((sum,r)=>sum+r.d,0);
  countEl.textContent=number(n)+' '+countUnit(metric);
  pctEl.textContent=percent(n/d*100);
  const scope=seen.length===27?'27 UFs':'somente '+seen.length+' das 27 UFs com dados';
  note.textContent='Total de '+scope+'. Percentual calculado por '+number(n)+' ÷ '+number(d)+', sem somar os percentuais individuais. '+(metric.startsWith('pct_hab_')?'Base: habilitações classificadas nos logs.':metric==='pct_votos_apos_17h'?'Base: votações registradas nos logs.':metric==='pct_abstencao'?'Base: eleitores aptos.':'Base: eleitores que compareceram.');
  if(['pct_abstencao','pct_brancos','pct_nulos'].includes(metric)&&seen.length===27){
    const br=metricCount(state.year,state.round,'BR',metric);
    const denom=rankingDenominator(state.year,state.round,'BR',metric);
    if(br!==null&&denom>0){
      national.hidden=false;
      national.append(node('span',null,'Brasil com exterior (ZZ):'),
        node('strong',null,number(br)+' '+countUnit(metric)+' · '+percent(br/denom*100)));
    }
  }
}
function renderRanking() {
  const metric=state.rankingMetric;
  const list=document.getElementById('stateRanking');
  list.replaceChildren();
  setText('rankingTitle',metricNames[metric]+' por estado');
  const rows=Object.keys(ufNames).filter(uf=>uf!=='BR'&&uf!=='ZZ').map(uf=>({uf,value:metricValue(state.year,state.round,uf,metric)})).filter(x=>x.value!==null).sort((a,b)=>b.value-a.value);
  if(!rows.length){
    list.append(node('p','empty-chart','Esse indicador depende de logs ainda não disponíveis para o turno selecionado.'));
    renderRankingTotal(metric,rows);
    return;
  }
  renderRankingTotal(metric,rows);
  const max=Math.max(1,...rows.map(x=>x.value));
  rows.forEach(({uf,value})=>{
    const row=node('button','rank-row'+(uf===state.uf?' active':''));row.type='button';
    row.title='Abrir '+ufNames[uf];
    row.setAttribute('aria-label',ufNames[uf]+': '+percent(value)+'. Filtrar o painel');
    const name=node('span','rank-uf',uf);
    const track=node('span','rank-track');
    const fill=node('span','rank-fill');fill.style.width=Math.max(1,value/max*100)+'%';track.append(fill);
    const val=node('span','rank-value',percent(value));
    const count=metricCount(state.year,state.round,uf,metric);
    if(count!==null){const small=node('small','rank-absolute',number(count));small.title=countLabel(state.year,state.round,uf,metric);val.append(small);}
    row.append(name,track,val);
    row.addEventListener('click',()=>{
      selectScope(uf);
      document.getElementById('painel').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
    });
    list.append(row);
  });
}
function renderComparison() {
  setText('comparisonScope',state.uf==='ZZ'?'Exterior (ZZ)':ufNames[state.uf]);
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
    ['Primeiro voto (horário típico)','mediana_primeiro_voto_h','time'],
    ['Último voto (horário típico)','mediana_ultimo_voto_h','time']
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
    el.textContent='O recorte “Brasil” inclui as 27 UFs e o eleitorado do exterior (ZZ) nos totais de aptos, comparecimento, abstenção, brancos, nulos e votos válidos. Para analisar apenas quem votou fora do país, selecione “Exterior (ZZ)”. Os indicadores de biometria e horários dos logs continuam restritos às 27 UFs, devido às diferenças de registro no exterior; nenhuma modalidade revela como uma pessoa votou.';
  }else{
    el.textContent=ufNames[state.uf]+': dados estaduais por turno. Os percentuais biométricos são calculados sobre as habilitações nos logs disponíveis, não sobre o cadastro geral. Variações não demonstram irregularidade isoladamente.';
  }
}
function signedDifference(a,b){
  return a===null||b===null?null:b-a;
}
function differenceClass(value) {
  return value===null?'na':value>0?'is-positive':value<0?'is-negative':'is-zero';
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
      const td=node('td',differenceClass(v),formatDifference(v,type));
      if(v===null)td.title='Comparação pendente: faltam dados para este par';
      tr.append(td);
    });
    tbody.append(tr);
  }
}

function renderAbsoluteDeltas() {
  const groups=[
    ['RESULTADOS DA VOTAÇÃO · ABRANGÊNCIA SELECIONADA',[
      ['Eleitores aptos','aptos'],['Comparecimento','comparecimento'],
      ['Abstenções','pct_abstencao'],['Votos válidos','pct_validos'],
      ['Votos brancos','pct_brancos'],['Votos nulos','pct_nulos'],
      ['Brancos + nulos','pct_brancos_nulos'],
      ['Lula (13)','votos_13'],['Número 22*','votos_22']]],
    ['REGISTROS TÉCNICOS · COBERTURA DOS LOGS',[
      ['Sem biometria cadastrada (log)','pct_hab_sem_biometria_log'],
      ['Biometria não reconhecida (log)','pct_hab_manual_apos_falha_log'],
      ['Biometria confirmada (log)','pct_hab_biometrica_log'],
      ['Votos após 17h (log)','pct_votos_apos_17h']]]
  ];
  const body=document.getElementById('absoluteDeltaBody');body.replaceChildren();
  for(const [group,fields] of groups) {
    const header=node('tr','absolute-group'),title=node('th',null,group);
    title.scope='rowgroup';title.colSpan=6;header.append(title);body.append(header);
    for(const [label,field] of fields) {
      const [a,b,c,d]=[['2022','1'],['2022','2'],['2026','1'],['2026','2']]
        .map(([year,round])=>metricCount(year,round,state.uf,field));
      const delta22=signedDifference(a,b),delta26=signedDifference(c,d);
      const values=[delta22,delta26,signedDifference(delta22,delta26),signedDifference(a,c),signedDifference(b,d)];
      const row=node('tr');row.append(node('td',null,label));
      values.forEach((value)=>{
        const td=node('td',differenceClass(value),formatDifference(value,'count'));
        if(value===null)td.title='Comparação pendente: contagem indisponível para este par';
        row.append(td);
      });
      body.append(row);
    }
  }
}

/* Geometria derivada das Malhas Territoriais do IBGE, distribuída como CC0.
   Mapa desenhado no navegador a partir de GeoJSON estático do repositório. */
function voteData(year,round,uf) {
  if(!data)return null;
  const rows=data.votesByYear[year];
  const regionRows=uf==='BR'?[...rows.values()]:[rows.get(uf)].filter(Boolean);
  if(!regionRows.length)return null;
  const suffix=round==='1'?'1t':'2t';
  const sum=key=>regionRows.reduce((t,r)=>t+(numeric(r[key+'_'+suffix])||0),0);
  const valid=sum('validos'),v13=sum('votos_13'),v22=sum('votos_22');
  return {valid,v13,v22,other:Math.max(0,valid-v13-v22),turnout:sum('comparecimento'),electorate:sum('aptos'),absent:sum('abstencoes'),blanks:sum('brancos'),nulls:sum('nulos')};
}
function technicalCount(year,round,uf,kind,field) {
  if(kind==='biometry' && uf==='ZZ')return null;
  const source=(kind==='biometry'?data?.biometryByYear:data?.temporalUFByYear)?.[year];
  if(!source)return null;
  const scopes=uf==='BR'?Object.keys(ufNames).filter(x=>x!=='BR'&&x!=='ZZ'):[uf];
  const rows=scopes.map(x=>source.get(round+'-'+x));
  if(rows.some(r=>!r||numeric(r[field])===null))return null;
  return rows.reduce((total,r)=>total+Number(r[field]),0);
}
function metricCount(year,round,uf,field) {
  const votes=voteData(year,round,uf);
  if(!votes)return null;
  const ballotCounts={
    comparecimento:votes.turnout,pct_abstencao:votes.absent,
    pct_brancos:votes.blanks,pct_nulos:votes.nulls,
    pct_brancos_nulos:votes.blanks+votes.nulls,
    pct_validos:votes.valid,votos_13:votes.v13,votos_22:votes.v22,
    aptos:votes.electorate
  };
  if(Object.hasOwn(ballotCounts,field))return ballotCounts[field];
  const bioFields={
    pct_hab_biometrica_log:'log_votantes_biometria',
    pct_hab_manual_apos_falha_log:'log_votantes_manual_apos_falha',
    pct_hab_sem_biometria_log:'log_votantes_sem_biometria_cadastrada'
  };
  if(Object.hasOwn(bioFields,field))return technicalCount(year,round,uf,'biometry',bioFields[field]);
  if(field==='pct_votos_apos_17h')return technicalCount(year,round,uf,'temporal','votos_apos_17h');
  return null;
}
function countUnit(field) {
  if(field==='comparecimento')return 'pessoas';
  if(field==='pct_abstencao')return 'abstenções';
  if(field.startsWith('pct_hab_'))return 'habilitações (logs)';
  if(field==='pct_votos_apos_17h')return 'votos (logs)';
  return 'votos';
}
function countLabel(year,round,uf,field) {
  const n=metricCount(year,round,uf,field);
  return n===null?'Quantidade não disponível':number(n)+' '+countUnit(field);
}
function candidateShare(votes,valid) {return valid>0?votes/valid*100:null;}
function pctOfValid(n,v) {return v>0?percent(n/v*100):'—';}
function mapColor(share,candidate) {
  if(share===null)return '#e2eae6';
  const v=Math.max(0,Math.min(100,share));
  return candidate==='13'
    ? 'hsl(4 '+Math.round(42+v*.22)+'% '+Math.round(97-v*.43)+'%)'
    : 'hsl(147 '+Math.round(32+v*.19)+'% '+Math.round(96-v*.39)+'%)';
}
function mapLeaderColor(v) {
  if(!v||v.valid<=0)return '#e2eae6';
  if(v.v13===v.v22)return '#c4cecc';
  const margin=Math.min(100,Math.abs(v.v13-v.v22)/v.valid*100);
  return v.v13>v.v22
    ? 'hsl(4 51% '+Math.round(89-margin*.55)+'%)'
    : 'hsl(147 40% '+Math.round(89-margin*.5)+'%)';
}
function geoPolygons(geometry) {
  return geometry.type==='Polygon'?[geometry.coordinates]:geometry.type==='MultiPolygon'?geometry.coordinates:[];
}
function candidate22Name(year) {return year==='2022'?'Jair Bolsonaro':'Flávio Bolsonaro';}
function setMapStatus(uf) {
  const target=document.getElementById('mapHover');
  target.replaceChildren();
  if(uf==='ZZ') {
    target.append(node('strong',null,'Exterior (ZZ)'),node('span',null,'Não aparece na malha dos estados; resultados eleitorais ao lado.'));
    return;
  }
  if(uf==='BR') {
    target.append(node('strong',null,'Brasil: 27 UFs + exterior'),node('span',null,'Clique em um estado; selecione Exterior no filtro para ver ZZ.'));
    return;
  }
  const votes=voteData(state.year,state.round,uf);
  target.append(node('strong',null,ufNames[uf]));
  target.append(node('span',null,'Lula (13): '+(votes?pctOfValid(votes.v13,votes.valid):'—')));
  target.append(node('span',null,candidate22Name(state.year)+' (22): '+(votes?pctOfValid(votes.v22,votes.valid):'—')));
}
// Une as bordas externas da malha das 27 UFs, sem contornar fronteiras internas.
// A malha publicada compartilha as mesmas coordenadas nas arestas entre estados.
function nationalBorderPath(features,project) {
  const edges=new Map();
  const edgeId=(a,b)=>a<b?a+'|'+b:b+'|'+a;
  for(const feature of features) {
    for(const polygon of geoPolygons(feature.geometry)) {
      for(const ring of polygon) {
        for(let i=0;i<ring.length-1;i++) {
          const a=ring[i].join(','),b=ring[i+1].join(',');
          if(a===b)continue;
          const key=edgeId(a,b);
          const prev=edges.get(key);
          if(prev)prev.count++;
          else edges.set(key,{a,b,count:1});
        }
      }
    }
  }
  const adjacency=new Map();
  const link=(from,to)=>{
    if(!adjacency.has(from))adjacency.set(from,[]);
    adjacency.get(from).push(to);
  };
  const border=[];
  for(const edge of edges.values()) {
    if(edge.count!==1)continue;
    border.push(edge);
    link(edge.a,edge.b);link(edge.b,edge.a);
  }
  // Se a malha tiver vértices incompatíveis, não desenhar contorno falso.
  if(!border.length||[...adjacency.values()].some(neighbors=>neighbors.length!==2))return '';
  const visited=new Set();
  const rings=[];
  for(const edge of border){
    const initial=edgeId(edge.a,edge.b);
    if(visited.has(initial))continue;
    const start=edge.a;
    let current=start,previous=null;
    const coords=[start];
    for(let guard=0;guard<=border.length;guard++){
      const neighbors=adjacency.get(current);
      const next=neighbors[0]===previous?neighbors[1]:neighbors[0];
      const k=edgeId(current,next);
      if(visited.has(k))break;
      visited.add(k);
      coords.push(next);
      previous=current;current=next;
      if(current===start)break;
    }
    if(coords[coords.length-1]!==start)return '';
    rings.push(coords);
  }
  if(visited.size!==border.length)return '';
  return rings.map(ring=>ring.map((p,i)=>{
    const [x,y]=project(p.split(',').map(Number));
    return (i===0?'M':'L')+x+','+y;
  }).join(' ')+' Z').join(' ');
}
function renderMap() {
  const mode=state.mapCandidate;
  const leader=mode==='lider';
  setText('mapColorTitle',leader?'Quem recebeu mais votos entre 13 e 22?':'Participação de '+(mode==='13'?'Lula (13)':candidate22Name(state.year)+' (22)'));
  document.getElementById('mapGradient').className='map-gradient '+(leader?'map-bicolor':mode==='13'?'candidate-13':'candidate-22');
  setText('mapLegendStart',leader?'Lula (13)':'Menor percentual');
  setText('mapLegendEnd',leader?candidate22Name(state.year)+' (22)':'Maior percentual');
  setText('mapColorExplanation',leader
    ? 'Cada UF aparece em vermelho quando Lula (13) teve mais votos e em verde quando o nº 22 teve mais votos. A intensidade representa a diferença entre eles. No 1º turno, veja também os demais candidatos à direita. O exterior entra nos totais nacionais, mas não aparece na malha.'
    : 'A tonalidade indica o percentual do nº '+mode+' entre os votos válidos: vermelho para 13 e verde para 22. Isso não significa irregularidade. O exterior está incluído nos totais nacionais, mas não aparece na malha.');
  const svg=document.getElementById('brMap');svg.replaceChildren();
  const features=data.geometry.features;
  const points=features.flatMap(f=>geoPolygons(f.geometry).flat(2));
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(512/(maxX-minX),474/(maxY-minY));
  const offsetX=(560-(maxX-minX)*scale)/2,offsetY=(520-(maxY-minY)*scale)/2;
  const project=([lon,lat])=>[(offsetX+(lon-minX)*scale).toFixed(1),(offsetY+(maxY-lat)*scale).toFixed(1)];
  const ns='http://www.w3.org/2000/svg';
  const nationalOutline=nationalBorderPath(features,project);
  let selectedPath=state.uf==='BR'?nationalOutline:null;
  const outline=document.createElementNS(ns,'path');
  outline.setAttribute('class','map-outline');
  outline.setAttribute('aria-hidden','true');
  outline.setAttribute('pointer-events','none');
  outline.setAttribute('fill','none');
  const showOutline=path=>{
    if(path){outline.setAttribute('d',typeof path==='string'?path:path.getAttribute('d'));outline.removeAttribute('display');}
    else outline.setAttribute('display','none');
  };
  for(const feature of features) {
    const uf=feature.properties.sigla;
    const geos=geoPolygons(feature.geometry);
    const pathData=geos.map(polygon=>polygon.map(ring=>ring.map((coord,i)=>{
      const [x,y]=project(coord);
      return (i===0?'M':'L')+x+','+y;
    }).join(' ')+' Z').join(' ')).join(' ');
    const path=document.createElementNS(ns,'path');
    const result=voteData(state.year,state.round,uf);
    const share=result?candidateShare(mode==='22'?result.v22:result.v13,result.valid):null;
    const pairText=ufNames[uf]+' · Lula (13): '+(result?pctOfValid(result.v13,result.valid):'—')+
      ' · '+candidate22Name(state.year)+' (22): '+(result?pctOfValid(result.v22,result.valid):'—');
    path.setAttribute('d',pathData);
    path.setAttribute('fill-rule','evenodd');
    path.setAttribute('class','map-state'+(state.uf===uf?' selected':''));
    path.setAttribute('fill',leader?mapLeaderColor(result):mapColor(share,mode));
    path.setAttribute('tabindex','0');
    path.setAttribute('role','button');
    path.setAttribute('aria-label',pairText+'. Selecionar estado');
    const title=document.createElementNS(ns,'title');
    title.textContent=pairText;
    path.append(title);
    const highlight=()=>{showOutline(path);setMapStatus(uf);};
    const restore=()=>{showOutline(selectedPath);setMapStatus(state.uf);};
    path.addEventListener('mouseenter',highlight);
    path.addEventListener('focus',highlight);
    path.addEventListener('mouseleave',restore);
    path.addEventListener('blur',restore);
    const select=()=>selectScope(uf);
    path.addEventListener('click',select);
    path.addEventListener('keydown',event=>{
      if(event.key==='Enter'||event.key===' '){event.preventDefault();select();}
    });
    svg.append(path);
    if(state.uf===uf)selectedPath=path;
  }
  svg.append(outline);
  showOutline(selectedPath);
  setMapStatus(state.uf);
}
function appendCandidateRow(target,name,numberId,votes,valid,className) {
  const row=node('div','candidate-row');
  const top=node('div','candidate-top');
  const label=node('div','candidate-name',name);
  label.append(node('span','candidate-number',numberId));
  const stats=node('div','candidate-value',pctOfValid(votes,valid));
  stats.append(node('span','candidate-count',number(votes)+' votos'));
  top.append(label,stats);
  const track=node('div','candidate-track');
  const fill=node('span','candidate-fill '+className);
  fill.style.width=(valid>0?Math.max(0,Math.min(100,votes/valid*100)):0)+'%';
  track.append(fill);row.append(top,track);target.append(row);
}
function renderPresidentialVotes() {
  const result=voteData(state.year,state.round,state.uf);
  const region=ufNames[state.uf];
  setText('voteScope',region);
  const candidate22=state.year==='2022'?'Jair Bolsonaro':'Flávio Bolsonaro';
  setText('voteContext',state.year+' · '+state.round+'º turno · '+(state.uf==='BR'?'27 UFs + exterior (ZZ)':state.uf==='ZZ'?'eleitorado no exterior':'UF selecionada'));
  const bars=document.getElementById('voteBars');bars.replaceChildren();
  const summary=document.getElementById('voteSummary');summary.replaceChildren();
  if(!result||!result.valid) {
    bars.append(node('p','empty-chart','Ainda não há dados presidenciais completos para este recorte.'));
  }else{
    appendCandidateRow(bars,'Lula','Nº 13',result.v13,result.valid,'n13');
    appendCandidateRow(bars,candidate22,'Nº 22',result.v22,result.valid,'n22');
    if(state.round==='1')appendCandidateRow(bars,'Demais candidatos','1º turno',result.other,result.valid,'other');
    for(const [label,value] of [['Votos válidos',result.valid],['Comparecimento',result.turnout]]){
      const item=node('div');item.append(node('span',null,label),node('strong',null,number(value)));summary.append(item);
    }
  }
  const table=document.getElementById('voteTableBody');table.replaceChildren();
  for(const [year,round] of [['2022','1'],['2022','2'],['2026','1'],['2026','2']]){
    const r=voteData(year,round,state.uf),tr=node('tr',year===state.year&&round===state.round?'active-turn':null);
    tr.append(node('td',null,year+' · '+round+'º turno'));
    if(!r||!r.valid){
      for(let i=0;i<4;i++)tr.append(node('td','na','—'));
    }else{
      const addCandidate=(votes,label)=>{
        const td=node('td',null,number(votes)+' ('+pctOfValid(votes,r.valid)+')');
        if(label)td.append(node('small',null,label));
        tr.append(td);
      };
      addCandidate(r.v13,null);
      addCandidate(r.v22,year==='2022'?'Jair Bolsonaro':'Flávio Bolsonaro');
      tr.append(node('td',null,round==='1'?number(r.other)+' ('+pctOfValid(r.other,r.valid)+')':'—'));
      tr.append(node('td',null,number(r.valid)));
    }
    table.append(tr);
  }
}
function renderAuditFocus(rows) {
  const selected=rows.filter(r=>{
    const found=numeric(r.divergencias),explained=numeric(r.explicadas);
    return found!==null&&explained!==null&&found>explained;
  });
  const remaining=selected.reduce((total,r)=>total+Number(r.divergencias)-Number(r.explicadas),0);
  setText('auditFocusYear',state.year==='2022'?'2022 · dois turnos':(has2026Round2Logs()?'2026 · dois turnos':'2026 · apenas 1º turno'));
  setText('auditUnexplained',number(remaining));
  setText('auditTestsCount',number(selected.length)+' verificações com apontamentos pendentes');
  setText('auditVotesAffected','Não determinado');
  setText('auditVotesPercent','Não calculável');
  setText('auditFocusExplanation','Esses '+number(remaining)+' apontamentos são diferenças não explicadas em testes de consistência de '+state.year+'. Podem envolver o mesmo registro em mais de uma comparação. Incluem campos biométricos e divergências de contadores dos logs: NÃO são '+number(remaining)+' votos identificados como irregulares. Sem detalhamento individual validado, não é possível estabelecer o número de votos únicos envolvidos nem sua porcentagem no resultado.');
  const link=document.getElementById('auditFocusLink');
  link.href='https://github.com/BigCorps/ObservatorioEleitoral/blob/main/resultados/'+state.year+'/reconciliacao_resumo.csv';
  const breakdown=document.getElementById('auditFocusBreakdown');
  breakdown.replaceChildren();
  const titleFor=r=>{
    if(r.teste==='B2')return 'Campos de biometria entre versões do BU';
    if(r.campo==='biometria_nh_vs_liberacao_manual_no_log')return 'Biometria: boletim × registro da urna';
    if(r.campo==='comparecimento_vs_votos_computados')return 'Comparecimento: boletim × registro da urna';
    if(r.campo==='comparecimento_vs_votos_presidente_mais_nulos_suspensao')return 'Comparecimento: conferência alternativa dos registros';
    return r.teste+' · '+r.campo;
  };
  for(const r of selected){
    const residual=numeric(r.divergencias)-numeric(r.explicadas);
    const checked=numeric(r.registros_comparados);
    const item=node('div','audit-breakdown-row');
    item.append(node('span','audit-breakdown-name',titleFor(r)),
      node('strong',null,number(residual)+' '+(residual===1?'apontamento':'apontamentos')));
    const ratio=node('small',null,checked>0
      ? new Intl.NumberFormat('pt-BR',{minimumFractionDigits:4,maximumFractionDigits:4}).format(residual/checked*100)+'% dos '+number(checked)+' registros comparados neste teste'
      : 'Base não disponível');
    item.append(ratio);
    breakdown.append(item);
  }
  if(!selected.length)breakdown.append(node('p',null,'Nenhum apontamento pendente registrado nos testes resumidos desta base.'));
}
function renderTriagem() {
  const cards=document.getElementById('triagemCards'),history=document.getElementById('triagemHistory');
  const body=document.getElementById('triagemRows');
  cards.replaceChildren();history.replaceChildren();body.replaceChildren();
  const all=data.triagemResumos?.[state.year]||[];
  const row=all.find(x=>x.uf===state.uf&&x.turno===state.round&&x.teste===state.triagemTeste);
  const status=document.getElementById('triagemStatus');
  const note=document.getElementById('triagemExplanation');
  const examplesNote=document.getElementById('triagemExamplesNote');
  const testesEntreTurnos=new Set(['mudanca20','mudanca30','mudanca40','virada13_22','comparecimento20','brancos_nulos15','combinados']);
  const notApplicable=state.round==='1'&&testesEntreTurnos.has(state.triagemTeste);
  const card=(label,value)=>{const el=node('div','triagem-stat');
    el.append(node('small',null,label),node('strong',null,value));cards.append(el);};
  if(!row||notApplicable||(numeric(row.secoes_elegiveis)===0&&!['unanimidade','qualquer'].includes(state.triagemTeste))){
    status.textContent=notApplicable
      ? 'Não aplicável ao 1º turno: este teste precisa de resultados dos dois turnos da mesma eleição.'
      : row?'Não há seções com base suficiente para executar este teste no recorte selecionado.'
          :'Ainda não há triagem validada publicada para '+state.year+', '+state.round+'º turno, '+ufNames[state.uf]+'.';
    note.textContent=notApplicable
      ? 'Esse indicador compara a mudança do 1º para o 2º turno. No 1º turno não há diferença entre turnos para medir. O traço (—) não significa zero casos.'
      : row?'As seções elegíveis são zero. O indicador é indisponível neste recorte, não uma taxa de 0%.'
           :'O processamento dos resultados por seção é independente dos logs. Enquanto a base de triagem não for gerada e conferida, nenhum número é estimado.';
    card('Seções sinalizadas','—');card('Votos nas seções','—');card('Seções elegíveis','—');
  }else{
    status.textContent=row.descricao+' · '+state.year+' · '+state.round+'º turno · '+ufNames[state.uf]+' · Fonte: '+row.fonte;
    card('Seções sinalizadas',number(row.secoes_sinalizadas));
    card('Percentual das elegíveis',percent(row.pct_secoes_sinalizadas));
    card('Votos válidos nessas seções',number(row.votos_validos_em_secoes_sinalizadas));
    card('Percentual dos válidos no recorte',percent(row.pct_validos_em_secoes_sinalizadas));
    note.textContent='Base: '+number(row.secoes_elegiveis)+' seções elegíveis de '+number(row.secoes_com_dados)+' com dados; '+number(row.votos_validos_no_recorte)+' votos válidos no recorte. '+row.criterio+'. Os votos indicados são todos os votos dessas seções, NÃO votos irregulares.'+
      (state.triagemTeste==='qualquer'?' Esta união inclui inversões relativas entre 13 e 22, frequentes em segundos turnos. Uma seção aparece uma vez no total, mas as categorias de testes podem se sobrepor.':'');
  }
  for(const year of ['2022','2026']) for(const round of ['1','2']) {
    const sample=(data.triagemResumos?.[year]||[]).find(x=>x.uf===state.uf&&x.turno===round&&x.teste===state.triagemTeste);
    const el=node('div','triagem-history-item');
    const eligible=sample&&numeric(sample.secoes_elegiveis)>0;
    const na=sample&&round==='1'&&testesEntreTurnos.has(state.triagemTeste);
    el.append(node('small',null,year+' · '+round+'º turno'),
      node('strong',null,eligible?number(sample.secoes_sinalizadas)+' seções':'—'),
      node('span',null,eligible?percent(sample.pct_secoes_sinalizadas)+' das elegíveis':na?'Não aplicável':sample?'Sem base elegível':'Aguardando dados'));
    history.append(el);
  }
  const examples=(data.triagemExemplos?.[state.year]||[])
    .filter(x=>x.abrangencia===state.uf&&x.turno===state.round&&x.teste===state.triagemTeste)
    .slice(0,15);
  examplesNote.textContent=examples.length
    ? 'Exibindo até '+examples.length+' exemplos por intensidade do teste. Eles não representam todos os casos. Consulte os CSVs no repositório para reproduzir os cálculos.'
    : 'Sem exemplos publicados neste recorte. Isso pode refletir dados pendentes ou nenhum caso elegível; verifique o resumo acima.';
  for(const r of examples){
    const tr=node('tr');
    const place=node('td',null,r.uf+' · '+r.nome_municipio+' · Z'+r.zona+' · S'+r.secao);
    place.append(node('small','triagem-place-detail','Local '+r.local));
    tr.append(place,node('td',null,number(r.validos)),
      node('td',null,percent(r.pct_13)+' / '+percent(r.pct_22)),
      node('td',null,state.triagemTeste==='combinados'?number(r.intensidade)+' grupos':state.triagemTeste==='qualquer'?number(r.intensidade)+' marcações':state.triagemTeste==='unanimidade'?'100,00%':percent(r.intensidade)),
      node('td',null,r.referencia_pares==='indisponivel'?'Sem referência por pares':r.referencia_pares==='mesmo_local'?'Mesmo local':'Mesma zona'));
    body.append(tr);
  }
  if(!examples.length){const tr=node('tr'),td=node('td',null,'Nenhum exemplo disponível neste recorte.');td.colSpan=5;tr.append(td);body.append(tr);}
}
function renderAudit() {
  const cards=document.getElementById('auditStatusCards');
  cards.replaceChildren();
  const record=(heading,status,details,className)=>{
    const card=node('article','audit-status-card '+className);
    card.append(node('span','audit-card-heading',heading),node('strong',null,status),node('p',null,details));
    cards.append(card);
  };
  record('ELEIÇÕES DE 2022','2 turnos processados','BUs, resultados e logs reconciliados; ainda existem observações sem explicação documental completa.','');
  record('ELEIÇÕES DE 2026 · 1º TURNO','Processado','BU em CSV, BU binário, logs e resultados oficiais reconciliados seção a seção.','');
  if(has2026Round2Logs())record('ELEIÇÕES DE 2026 · 2º TURNO','Logs e BUs processados','BU em CSV consolidado (Dados Abertos, SHA-512 oficial conferido) reconciliado com os arquivos de urna do Portal de Resultados e com o resultado oficial por seção: 0 divergências de votos em 499.207 seções.','');
  else record('ELEIÇÕES DE 2026 · 2º TURNO','Dados técnicos pendentes','Resultados por seção disponíveis; BU e logs ainda não integram as verificações técnicas desta base.','audit-pending');
  const rows=data.auditsByYear[state.year]||[];
  renderAuditFocus(rows);
  const both=state.year==='2022'||has2026Round2Logs();
  setText('auditTableTitle','Testes documentais de '+state.year+(both?' · dois turnos':' · primeiro turno'));
  setText('auditCoverageChip',state.year+(both?': ambos os turnos':': apenas primeiro turno'));
  setText('auditTableNote','Quadro nacional histórico de '+state.year+(both?' (dados dos dois turnos).':' (somente o 1º turno).')+' Não é filtrado por UF, pois o resumo oficializado no repositório está agregado por ano. A tabela apresenta testes com diferenças, explicadas ou pendentes; cada linha conta comparações, não seções únicas nem votos irregulares.');
  const body=document.getElementById('auditTableBody');
  body.replaceChildren();
  const relevant=rows.filter(r=>(numeric(r.divergencias)||0)>0);
  relevant.forEach(r=>{
    const tr=node('tr'),delta=numeric(r.divergencias),explained=numeric(r.explicadas);
    const left=(delta!==null&&explained!==null)?Math.max(0,delta-explained):null;
    const name=node('td',null,(r.teste||'')+' · '+(r.descricao||r.campo||''));
    name.title=(r.fonte_a||'')+' × '+(r.fonte_b||'')+' / '+(r.campo||'');
    tr.append(name,node('td',null,number(r.registros_comparados)),node('td',null,number(delta)),node('td',null,number(explained)),node('td',left>0?'audit-not-explained':'',number(left)));
    body.append(tr);
  });
  if(!relevant.length){const row=node('tr'),cell=node('td',null,rows.length?'Nenhuma diferença registrada nos testes desta base.':'Resumo de reconciliação indisponível.');cell.colSpan=5;row.append(cell);body.append(row);}
}
const discCategories=['Diferença estatística','Diferença explicada','Incompatibilidade documental pendente','Não verificado'];
function renderDiscrepancies() {
  const rows=(data.discrepancies||[]).filter(r=>r.ano===state.year&&r.turno===state.round&&discCategories.includes(r.categoria));
  setText('discTitle','Discrepâncias de '+state.year+' · '+state.round+'º turno');
  setText('discChip','Filtro: '+state.year+' · '+state.round+'º turno');
  const cards=document.getElementById('discCards');
  cards.replaceChildren();
  for(const cat of discCategories){
    const sub=rows.filter(r=>r.categoria===cat);
    const sum=f=>sub.reduce((t,r)=>t+(numeric(r[f])||0),0);
    const votes=sub.filter(r=>numeric(r.votos_com_registro_divergente)!==null);
    const card=node('article','audit-status-card'+(cat==='Não verificado'?' audit-pending':''));
    const status=cat==='Não verificado'?number(sub.length)+' verificações':cat==='Diferença estatística'?number(sub.length)+' resultados':number(sum('apontamentos'))+' apontamentos';
    const detail=cat==='Diferença estatística'?'Testes com efeito estatisticamente significativo após correção para múltiplas comparações; não são apontamentos documentais nem votos.'
      :cat==='Não verificado'?'Dependem de arquivos oficiais ainda não publicados.'
      :number(sum('secoes_distintas'))+' seções por teste'+(votes.length?' · '+number(votes.reduce((t,r)=>t+numeric(r.votos_com_registro_divergente),0))+' votos com registro divergente entre fontes':'');
    card.append(node('span','audit-card-heading',cat.toUpperCase()),node('strong',null,status),node('p',null,detail));
    cards.append(card);
  }
  const body=document.getElementById('discTableBody');
  body.replaceChildren();
  for(const r of rows){
    const tr=node('tr'),first=node('td');
    first.append(node('span',null,r.categoria+' · '+r.teste+' · '+r.campo));
    if(r.observacao)first.append(node('small',null,' — '+r.observacao));
    const cell=v=>{const n=numeric(v);const td=node('td',n===null?'na':null,n===null?'—':number(n));return td;};
    tr.append(first,node('td',null,r.turno+'º'),cell(r.apontamentos),cell(r.secoes_distintas),cell(r.votos_com_registro_divergente));
    body.append(tr);
  }
  if(!rows.length){const row=node('tr'),c=node('td',null,'Quadro indisponível.');c.colSpan=5;row.append(c);body.append(row);}
}

/* Simulação aritmética do crescimento líquido do nº 13, sem inferência de voto individual. */
let simRates=null;
const simKeys=['reducao','terceira','flavio'];
const simIds={reducao:'simReducao',terceira:'simTerceira',flavio:'simFlavio'};
function simMetrics(){
 const rows=data?.votesByYear?.['2026'];
 if(!rows||rows.size!==28)return null;
 const all=[...rows.values()];
 const n=k=>all.reduce((total,r)=>total+Number(r[k]),0);
 const required=['validos_1t','votos_13_1t','votos_22_1t','votos_13_2t','brancos_1t','nulos_1t','brancos_2t','nulos_2t','abstencoes_1t','abstencoes_2t'];
 if(all.some(r=>required.some(k=>numeric(r[k])===null)))return null;
 const third=n('validos_1t')-n('votos_13_1t')-n('votos_22_1t');
 const invalid=n('brancos_1t')+n('nulos_1t')-n('brancos_2t')-n('nulos_2t');
 const abstention=n('abstencoes_1t')-n('abstencoes_2t');
 const goal=n('votos_13_2t')-n('votos_13_1t');
 if(third<=0||invalid+abstention<=0||goal<=0||n('votos_22_1t')<=0)return null;
 return {goal,invalid,abstention,pools:{reducao:invalid+abstention,terceira:third,flavio:n('votos_22_1t')}};
}
function renderSimulator(){
 const m=simMetrics();if(!m)return;
 if(!simRates)simRates={reducao:80,terceira:100*(m.goal-0.8*m.pools.reducao-0.03*m.pools.flavio)/m.pools.terceira,flavio:3};
 let total=0;
 for(const key of simKeys){
  const cap=Math.min(100,100*m.goal/m.pools[key]);
  const input=document.getElementById(simIds[key]);input.max=String(cap);input.value=String(simRates[key]);
  const votes=m.pools[key]*simRates[key]/100;total+=votes;
  setText(simIds[key]+'Pct',df.format(simRates[key])+'%');
  setText(simIds[key]+'Base','Base: '+number(m.pools[key])+' votos');
  setText(simIds[key]+'Votes',number(votes)+' votos');
  document.getElementById('simBar'+key[0].toUpperCase()+key.slice(1)).style.width=(100*votes/m.goal)+'%';
 }
 setText('simTotal',number(total));setText('simTarget',number(m.goal));
 setText('simDifference',number(Math.abs(m.goal-total))+' votos');
 setText('simAssumptions','Saldos nacionais: '+number(m.invalid)+' votos brancos/nulos a menos e '+number(m.abstention)+' abstenções a menos. A terceira via exclui os votos de 13 e 22.');
}
function simAdjust(changed,value){
 const m=simMetrics();if(!m)return;
 if(!simRates)renderSimulator();
 const p=m.pools;const raw=Number(value);
 if(!Number.isFinite(raw))return;
 const next=Math.max(0,Math.min(100*m.goal/p[changed],100,raw));
 const [a,b]=simKeys.filter(x=>x!==changed);
 const remaining=m.goal-p[changed]*next/100;
 const previousA=p[a]*simRates[a]/100,previousB=p[b]*simRates[b]/100;
 const weight=previousA+previousB>0?previousA/(previousA+previousB):p[a]/(p[a]+p[b]);
 const votesA=Math.max(Math.max(0,remaining-p[b]),Math.min(Math.min(p[a],remaining),remaining*weight));
 const votesB=remaining-votesA;
 simRates={...simRates,[changed]:next,[a]:100*votesA/p[a],[b]:100*votesB/p[b]};
 renderSimulator();
}
function simReset(){simRates=null;renderSimulator();}
function setUpSimulator(){
 for(const key of simKeys)document.getElementById(simIds[key]).addEventListener('input',e=>simAdjust(key,e.target.value));
 document.getElementById('simReset').addEventListener('click',simReset);
}


function renderBioHora(){
  const year=document.getElementById('bioHoraYear')?.value||'2026';
  const group=document.getElementById('bioHoraScope')?.value||'1';
  const all=(data?.bioHoraCoortes||[]).filter(x=>x.ano===year&&x.turno==='2'&&x.uf==='BR');
  const body=document.getElementById('bioHoraCohorts');
  if(!body)return;
  body.replaceChildren();
  if(all.length===2 && all.some(x=>x.tardia_2t==='1') && all.some(x=>x.tardia_2t==='0')){
    document.getElementById('bioHoraStatus').textContent='Cruzamento publicado: '+year+', segundo turno, Brasil sem exterior. As taxas são calculadas sobre habilitações classificadas.';
    for(const flag of ['1','0']){
      const r=all.find(x=>x.tardia_2t===flag);
      const tr=node('tr');tr.append(node('th',null,flag==='1'?'Com voto após 17h':'Demais seções'));
      tr.append(node('td',null,number(r.secoes)));tr.append(node('td',null,number(r.classificados)));
      tr.append(node('td',null,percent(r.pct_manual)));tr.append(node('td',null,percent(r.pct_sem_cadastro)));
      body.append(tr);
    }
  }else{
    document.getElementById('bioHoraStatus').textContent='Cruzamento individual ainda não publicado. Os números horários e de seções concentradas acima já estão calculados.';
    const tr=node('tr'),td=node('td',null,'Aguardando execução do módulo nos Parquets locais e publicação dos CSVs.');td.colSpan=5;tr.append(td);body.append(tr);
  }
  const bands=(data?.bioHoraFaixas||[]).filter(x=>x.ano===year&&x.turno==='2'&&x.uf==='BR'&&x.tardia_2t===group).sort((a,b)=>a.faixa_manual.localeCompare(b.faixa_manual));
  const b=document.getElementById('bioHoraBands');b.replaceChildren();
  if(!bands.length){
    const tr=node('tr'),td=node('td',null,'Os valores por faixa ainda não foram calculados no ambiente local.');td.colSpan=5;tr.append(td);b.append(tr);
  }else for(const r of bands){
    const tr=node('tr');tr.append(node('th',null,r.faixa_manual));
    tr.append(node('td',null,number(r.secoes)));
    tr.append(node('td',null,number(r.manuais_apos_falha)));
    tr.append(node('td',null,percent(r.pct13_validos_secao)));
    tr.append(node('td',null,percent(r.pct22_validos_secao)));
    b.append(tr);
  }
}
function render() {
  if(!data)return;
  renderBioHora();
  renderSimulator();syncControls();renderTriagem();renderAudit();renderDiscrepancies();renderCoverage();renderKpis();renderScopeInfo();renderMap();renderPresidentialVotes();renderTrend();renderTimeline();renderRanking();renderComparison();renderDelta();renderAbsoluteDeltas();
}
async function init() {
  setUpFilters();setUpSimulator();
  for(const id of ['bioHoraYear','bioHoraScope']){
    document.getElementById(id)?.addEventListener('change',renderBioHora);
  }
  try{
    const entries=await Promise.all(Object.entries(files).map(async ([name,path])=>{
      const response=await fetch(path,{cache:'no-cache'});
      if(!response.ok)throw new Error('Arquivo '+path+': '+response.status);
      return [name,parseCSV(await response.text())];
    }));
    const loaded=Object.fromEntries(entries);
    // CSVs por seção: só existem quando a análise nos Parquets locais foi concluída.
    const [bioHoraCoortes,bioHoraFaixas]=await Promise.all([
      fetch('./dados/biometria_secoes_tardias_por_uf.csv',{cache:'no-cache'})
        .then(r=>r.ok?r.text():'').then(s=>s?parseCSV(s):[]).catch(()=>[]),
      fetch('./dados/biometria_secoes_tardias_faixas_votos.csv',{cache:'no-cache'})
        .then(r=>r.ok?r.text():'').then(s=>s?parseCSV(s):[]).catch(()=>[])
    ]);
    const mapResponse=await fetch('./dados/brasil-ufs.geojson',{cache:'no-cache'});
    if(!mapResponse.ok)throw new Error('Malha territorial: '+mapResponse.status);
    const geometry=await mapResponse.json();
    // Estes artefatos são opcionais até a execução da triagem em dados oficiais.
    const triagemResumos={},triagemExemplos={};
    await Promise.all(['2022','2026'].map(async year=>{
      const load=async type=>{
        try{
          const r=await fetch('./dados/triagem_'+type+'_'+year+'.csv',{cache:'no-cache'});
          return r.ok?parseCSV(await r.text()):[];
        }catch(e){return [];}
      };
      [triagemResumos[year],triagemExemplos[year]]=await Promise.all([load('resumo'),load('exemplos')]);
    }));
    data={bioHoraCoortes,bioHoraFaixas,indicators:new Map(loaded.indicators.map(r=>[key(r.ano,r.turno,r.abrangencia),r])),timeline2022:loaded.timeline2022,timeline2026:loaded.timeline2026,
      votesByYear:{'2022':new Map(loaded.votes2022.map(r=>[r.uf,r])),'2026':new Map(loaded.votes2026.map(r=>[r.uf,r]))},
      biometryByYear:{'2022':new Map(loaded.bio2022.map(r=>[r.turno+'-'+r.uf,r])),'2026':new Map(loaded.bio2026.map(r=>[r.turno+'-'+r.uf,r]))},
      temporalUFByYear:{'2022':new Map(loaded.temporalUF2022.map(r=>[r.turno+'-'+r.uf,r])),'2026':new Map(loaded.temporalUF2026.map(r=>[r.turno+'-'+r.uf,r]))},
      auditsByYear:{'2022':loaded.audits2022,'2026':loaded.audits2026},discrepancies:loaded.discrepancies,triagemResumos,triagemExemplos,geometry};
    if(!geometry.features||geometry.features.length!==27)throw new Error('Malha territorial incompleta');
    if(!data.indicators.size)throw new Error('Indicadores vazios');
    render();
  }catch(err){
    console.error('Falha ao carregar dados do Observatório:',err);
    document.getElementById('loadError').hidden=false;
    document.getElementById('coverageBadge').textContent='Falha no carregamento';
  }
}
document.addEventListener('DOMContentLoaded',init);