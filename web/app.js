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
  temporalUF2026:'./dados/temporal_uf_2026.csv'
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
  chart.setAttribute('aria-label','Volume das 27 UFs com logs a cada 15 minutos, eleição '+state.year+', '+state.round+'º turno. Passe sobre as barras para os valores.');
  setText('timelineNote','Curva de logs das 27 UFs, sem os votos do exterior (ZZ), em horário de Brasília. Este gráfico não muda com o filtro de estado e não representa a distribuição de todos os votos nacionais. Votos depois das 17h podem ser regulares quando havia eleitores na fila.');
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
    const count=metricCount(state.year,state.round,uf,metric);
    if(count!==null){const small=node('small','rank-absolute',number(count));small.title=countLabel(state.year,state.round,uf,metric);val.append(small);}
    row.append(name,track,val);
    row.addEventListener('click',()=>{
      state.uf=uf;document.getElementById('ufFilter').value=uf;render();
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
    el.textContent='O recorte “Brasil” inclui as 27 UFs e o eleitorado do exterior (ZZ) nos totais de aptos, comparecimento, abstenção, brancos, nulos e votos válidos. Para analisar apenas quem votou fora do país, selecione “Exterior (ZZ)”. Os indicadores de biometria e horários dos logs continuam restritos às 27 UFs, devido às diferenças de registro no exterior; nenhuma modalidade revela como uma pessoa votou.';
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
        const td=node('td',value===null?'na':null,formatDifference(value,'count'));
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
function mapColor(share) {
  if(share===null)return '#e2eae6';
  const v=Math.max(0,Math.min(100,share));
  return 'hsl(173 '+Math.round(28+v*.20)+'% '+Math.round(94-v*.57)+'%)';
}
function geoPolygons(geometry) {
  return geometry.type==='Polygon'?[geometry.coordinates]:geometry.type==='MultiPolygon'?geometry.coordinates:[];
}
function renderMap() {
  const svg=document.getElementById('brMap');svg.replaceChildren();
  const features=data.geometry.features;
  const points=features.flatMap(f=>geoPolygons(f.geometry).flat(2));
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(512/(maxX-minX),474/(maxY-minY));
  const offsetX=(560-(maxX-minX)*scale)/2,offsetY=(520-(maxY-minY)*scale)/2;
  const project=([lon,lat])=>[(offsetX+(lon-minX)*scale).toFixed(1),(offsetY+(maxY-lat)*scale).toFixed(1)];
  const ns='http://www.w3.org/2000/svg';
  let selectedPath=null;
  // Um contorno acima dos estados evita bordas encobertas sem mover os alvos clicáveis.
  const outline=document.createElementNS(ns,'path');
  outline.setAttribute('class','map-outline');
  outline.setAttribute('aria-hidden','true');
  outline.setAttribute('pointer-events','none');
  outline.setAttribute('fill','none');
  const showOutline=path=>{
    if(path){outline.setAttribute('d',path.getAttribute('d'));outline.removeAttribute('display');}
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
    const share=result?candidateShare(result.v13,result.valid):null;
    path.setAttribute('d',pathData);
    path.setAttribute('fill-rule','evenodd');
    path.setAttribute('class','map-state'+(state.uf===uf?' selected':''));
    path.setAttribute('fill',mapColor(share));
    path.setAttribute('tabindex','0');
    path.setAttribute('role','button');
    path.setAttribute('aria-label',ufNames[uf]+': candidato nº 13, '+percent(share)+'. Selecionar estado');
    const title=document.createElementNS(ns,'title');
    title.textContent=ufNames[uf]+' · candidato 13: '+percent(share);
    path.append(title);
    const tooltip=()=>setText('mapHover',ufNames[uf]+' · Lula (13): '+percent(share)+' dos votos válidos');
    const highlight=()=>{showOutline(path);tooltip();};
    const restore=()=>{showOutline(selectedPath);setMapHint();};
    path.addEventListener('mouseenter',highlight);
    path.addEventListener('focus',highlight);
    path.addEventListener('mouseleave',restore);
    path.addEventListener('blur',restore);
    const select=()=>{
      state.uf=uf;
      document.getElementById('ufFilter').value=uf;
      render();
    };
    path.addEventListener('click',select);
    path.addEventListener('keydown',event=>{
      if(event.key==='Enter'||event.key===' '){event.preventDefault();select();}
    });
    svg.append(path);
    if(state.uf===uf)selectedPath=path;
  }
  svg.append(outline);
  showOutline(selectedPath);
  setMapHint();
}
function setMapHint(){
  if(state.uf==='ZZ')setText('mapHover','Exterior (ZZ) não é desenhado no mapa do território brasileiro. Seus votos estão detalhados ao lado.');
  else if(state.uf==='BR')setText('mapHover','Clique em uma das 27 UFs para ver seus resultados presidenciais.');
  else {
    const v=voteData(state.year,state.round,state.uf);
    setText('mapHover',ufNames[state.uf]+' selecionado · Lula (13): '+(v?pctOfValid(v.v13,v.valid):'—'));
  }
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
function render() {
  if(!data)return;
  renderCoverage();renderKpis();renderScopeInfo();renderMap();renderPresidentialVotes();renderTrend();renderTimeline();renderRanking();renderComparison();renderDelta();renderAbsoluteDeltas();
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
    const mapResponse=await fetch('./dados/brasil-ufs.geojson',{cache:'no-cache'});
    if(!mapResponse.ok)throw new Error('Malha territorial: '+mapResponse.status);
    const geometry=await mapResponse.json();
    data={indicators:new Map(loaded.indicators.map(r=>[key(r.ano,r.turno,r.abrangencia),r])),timeline2022:loaded.timeline2022,timeline2026:loaded.timeline2026,
      votesByYear:{'2022':new Map(loaded.votes2022.map(r=>[r.uf,r])),'2026':new Map(loaded.votes2026.map(r=>[r.uf,r]))},
      biometryByYear:{'2022':new Map(loaded.bio2022.map(r=>[r.turno+'-'+r.uf,r])),'2026':new Map(loaded.bio2026.map(r=>[r.turno+'-'+r.uf,r]))},
      temporalUFByYear:{'2022':new Map(loaded.temporalUF2022.map(r=>[r.turno+'-'+r.uf,r])),'2026':new Map(loaded.temporalUF2026.map(r=>[r.turno+'-'+r.uf,r]))},geometry};
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