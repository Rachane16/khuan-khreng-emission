"use strict";
const $ = (id) => document.getElementById(id);
const COLORS = {GRASS:"#9aa95a",LEPIRONIA:"#48aaa0",M_CAJU:"#3c7654",PADDY:"#c4ae62",PEAT:"#b2845d"};
const LABELS = {GRASS:["หญ้า","GRASS"],LEPIRONIA:["กระจูด","LEPIRONIA"],M_CAJU:["เสม็ดขาว","MELALEUCA"],
 PADDY:["ฟางข้าว","PADDY / RICE"],PEAT:["ดินพรุ 0–10 cm","PEAT · SCENARIO"],
 M_CAJU_SURFACE_LOWLAND:["เสม็ด · surface fuel","litter + undergrowth"],
 M_CAJU_LEAVES_BARK_LOWLAND:["เสม็ด · leaves + bark","ใบและเปลือก"]};
const SOURCE_NAMES={MODIS_NRT:"MODIS Terra / Aqua",VIIRS_SNPP_NRT:"VIIRS S-NPP",VIIRS_NOAA20_NRT:"VIIRS NOAA-20",VIIRS_NOAA21_NRT:"VIIRS NOAA-21",ALL:"ทุกดาวเทียม"};
const state={index:{dates:[],daily:[]},status:{},parameters:null,project:null,day:null,source:"ALL",peat:true,map:null,boundary:null,landuse:{},dailyLayer:null,request:0};
const format=(n,d=2)=>Number.isFinite(n)?new Intl.NumberFormat("en-US",{minimumFractionDigits:0,maximumFractionDigits:d}).format(n):"—";
const safe=(s)=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const today=()=>new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Bangkok",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
const dateText=(s)=>new Intl.DateTimeFormat("th-TH",{timeZone:"Asia/Bangkok",day:"numeric",month:"long",year:"numeric"}).format(new Date(s+"T12:00:00+07:00"));
const clockText=(s)=>s?new Intl.DateTimeFormat("th-TH",{timeZone:"Asia/Bangkok",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",hour12:false}).format(new Date(s)):"—";
async function json(path){const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw new Error("ไม่พบข้อมูลที่ต้องการ ("+r.status+")");if(path.endsWith(".gz")){if(!window.DecompressionStream)throw new Error("โปรดใช้เบราว์เซอร์รุ่นใหม่เพื่อเปิดชั้นแผนที่");return new Response(r.body.pipeThrough(new DecompressionStream("gzip"))).json();}return r.json();}
function fuelColor(code){return COLORS[code.startsWith("M_CAJU")?"M_CAJU":code]||"#8da290";}
function fuelName(code){const a=LABELS[code]||[code,""];return '<span class="fuel-label"><i style="background:'+fuelColor(code)+'"></i><span class="fuel-name">'+safe(a[0])+'<small>'+safe(a[1])+'</small></span></span>';}
function emission(summary){return summary?(state.peat?summary.emission_kg:summary.emission_without_peat_kg):null;}
function setMapMessage(title,detail,show=true){$("map-message").hidden=!show;$("map-message").innerHTML='<span class="map-message-icon">⌖</span><strong>'+safe(title)+'</strong><span>'+safe(detail)+'</span>';}
function currentSummary(){
 if(!state.day)return null;
 const result=state.day.by_source[state.source];
 if(state.source!=="ALL" && state.day.source_status[state.source]?.state!=="ok" && !result?.observation_count)return null;
 return result;
}
function renderStatus(){
 const s=state.status;
 const title={awaiting_key:"พร้อมแสดงแผนที่ · รอเชื่อม FIRMS MAP_KEY",ok:"อัปเดตข้อมูล FIRMS สำเร็จ",partial:"ข้อมูลดาวเทียมอัปเดตไม่ครบ",error:"การอัปเดตขัดข้อง · ใช้ข้อมูลที่บันทึกไว้"};
 $("connection-title").textContent=title[s.state]||"ยังไม่มีข้อมูลเชื่อมต่อ";
 $("connection-detail").textContent=s.state==="awaiting_key"?"ขอบเขตและเชื้อเพลิงเป็นข้อมูลจริงของโครงการ ยังไม่มีข้อมูล Active Fires จาก API":s.message||"";
 $("connection-label").textContent={awaiting_key:"AWAITING CONNECTION",ok:"NRT DATA",partial:"PARTIAL DATA",error:"STALE DATA"}[s.state]||"OFFLINE";
 $("connection-banner").classList.toggle("ok",s.state==="ok");
 $("source-status").innerHTML=Object.keys(SOURCE_NAMES).filter(k=>k!=="ALL").map(k=>{
 const q=s.sources?.[k]||{},v=q.state||"not_configured";
 const text={ok:"อัปเดตแล้ว",error:"ขัดข้อง",not_configured:"รอเชื่อมต่อ",unavailable:"ยังไม่มีข้อมูลใหม่"}[v]||v;
 return '<div class="source-item"><i class="source-dot '+safe(v)+'"></i><span>'+SOURCE_NAMES[k]+'</span><span class="source-state">'+safe(text)+(q.max_date?'<small>ล่าสุด '+safe(q.max_date)+'</small>':'')+'</span></div>';
 }).join("");
 $("last-update").textContent=s.last_success_utc?"อัปเดตครบทุกแหล่งล่าสุด "+clockText(s.last_success_utc)+" น.":s.last_partial_success_utc?"อัปเดตบางแหล่งล่าสุด "+clockText(s.last_partial_success_utc)+" น.":"ยังไม่มีการอัปเดตจาก FIRMS";
}
function renderParameters(){
 const value=(p,key)=>format(p[key],3)+(p[key+"_plus_minus"]!==undefined?" ± "+format(p[key+"_plus_minus"],3):p[key+"_range"]?" ("+p[key+"_range"].map(v=>format(v,3)).join("–")+")":"");
 $("parameter-table").innerHTML=state.parameters.fuels.map(p=>'<tr><td>'+fuelName(p.code)+'</td><td>'+value(p,"rho")+'</td><td>'+value(p,"eta")+'</td><td>'+value(p,"ef_pm25")+'</td></tr>').join("");
}
function render(){
 const summary=currentSummary(),valid=!!summary;
 $("metric-count").textContent=valid?format(summary.observation_count,0):"—";
 $("metric-area").textContent=valid?format(summary.ground_area_ha):"—";
 $("metric-emission").textContent=valid?format(emission(summary)):"—";
 $("metric-unclassified").textContent=valid?format(summary.surface_unclassified_ha):"—";
 $("emission-unit").textContent="kg · "+(state.peat?"รวมสถานการณ์ดินพรุ":"เฉพาะเชื้อเพลิงเหนือดิน");
 $("selected-day-label").textContent=dateText($("date-input").value)+" · "+SOURCE_NAMES[state.source]+(state.day?.data_state==="partial"?" · ข้อมูลบางส่วน":"")+($("date-input").value===today()?" · วันปัจจุบันยังไม่ครบวัน":"");
 $("map-subtitle").textContent=SOURCE_NAMES[state.source]+" / "+$("date-input").value+" / เวลาไทย";
 $("export-button").disabled=!valid;
 $("fuel-table").innerHTML=state.parameters.fuels.map(p=>{
 const r=summary?.fuels.find(f=>f.code===p.code),excluded=p.code==="PEAT"&&!state.peat;
 return '<tr class="'+(p.code==="PEAT"?"peat-row ":"")+(excluded?"excluded":"")+'"><td>'+fuelName(p.code)+'</td><td>'+format(r?.area_ha)+'</td><td>'+(excluded?"ไม่รวม":format(r?.emission_kg))+'</td></tr>';
 }).join("");
 $("table-total").textContent=format(emission(summary));
 drawFires();
 renderTrend();
}
function drawFires(){
 if(!state.map)return;
 if(state.dailyLayer){state.map.removeLayer(state.dailyLayer);state.dailyLayer=null;}
 const summary=currentSummary();
 if(!state.day || !summary){
   setMapMessage(state.status.state==="awaiting_key"?"ยังไม่ได้เชื่อมข้อมูล FIRMS":"ยังไม่มีข้อมูลของวันที่เลือก",
    state.status.state==="awaiting_key"?"แสดงขอบเขตและชั้นเชื้อเพลิงจริง":"เลือกวันอื่นจากประวัติ หรือรอการดึงข้อมูล",true);
   return;
 }
 if(!summary.observation_count){
   setMapMessage("ไม่พบ Active Fire ในข้อมูลที่ได้รับ",state.day.data_state==="partial"?"บางแหล่งยังอัปเดตไม่ครบ":"ตามวันที่และดาวเทียมที่เลือก",true);
   return;
 }
 setMapMessage("","",false);
 const selected=state.day.footprints.features.filter(f=>state.source==="ALL"||f.properties.source===state.source);
 state.dailyLayer=L.geoJSON({type:"FeatureCollection",features:selected},{
   pane:"fire",style:{color:"#c96527",weight:1.3,fillColor:"#ed8b49",fillOpacity:.5},
   onEachFeature:(feature,layer)=>{const p=feature.properties;layer.bindPopup('<strong>'+safe(SOURCE_NAMES[p.source])+'</strong><br>ตรวจพบ: '+safe(clockText(p.acquired_utc))+' น.<br>Confidence: '+safe(p.confidence)+'<br>FRP: '+format(p.frp_mw)+' MW<br>ขนาดพิกเซล: '+format(p.scan_km,3)+' × '+format(p.track_km,3)+' km');}
 }).addTo(state.map);
}
function renderTrend(){
 const rows=(state.index.daily||[]).slice(-7);
 if(!rows.length){
  $("trend").innerHTML='<div class="trend-empty"><svg viewBox="0 0 100 50" aria-hidden="true"><path d="M5 40H95M10 32l20-8 18 4 18-15 24-5" fill="none" stroke="#c1d2bc" stroke-width="2"/><circle cx="66" cy="13" r="3" fill="#94b38b"/></svg>ประวัติรายวันจะแสดงเมื่อเชื่อม FIRMS แล้ว</div>';
  $("date-history").innerHTML="";return;
 }
 const width=340,height=150,base=115,max=Math.max(1,...rows.map(r=>emission(r)||0)),gap=width/rows.length;
 let svg='<svg viewBox="0 0 '+width+' '+height+'" role="img" aria-label="กราฟ emission รายวันของทุกดาวเทียม" width="100%" height="100%"><line x1="0" y1="'+base+'" x2="'+width+'" y2="'+base+'" stroke="#dce7d5"/>';
 rows.forEach((r,i)=>{
  const value=emission(r)||0,h=value/max*85,x=i*gap+gap*.22,y=base-h;
  svg+='<rect x="'+x+'" y="'+y+'" width="'+gap*.56+'" height="'+Math.max(h,1)+'" rx="3" fill="'+(r.date===$("date-input").value?"#ce8c50":"#81aa86")+'"><title>'+r.date+': '+format(value)+' kg</title></rect><text x="'+(i*gap+gap*.5)+'" y="'+(base+19)+'" text-anchor="middle" fill="#8a9c87" font-size="9">'+r.date.slice(5)+'</text>';
 });
 $("trend").innerHTML=svg+"</svg>";
 $("date-history").innerHTML=rows.map(r=>'<button data-date="'+r.date+'" class="'+(r.date===$("date-input").value?"active":"")+'">'+r.date.slice(5)+'</button>').join("");
 $("date-history").querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{$("date-input").value=b.dataset.date;loadDay();}));
}
async function loadDay(){
 const ticket=++state.request,day=$("date-input").value;
 state.day=null;
 if(state.index.dates.includes(day)){
  try{const data=await json("data/daily/"+day+".json");if(ticket!==state.request)return;state.day=data;}
  catch(e){$("connection-detail").textContent="เปิดข้อมูลรายวันไม่สำเร็จ กรุณาลองโหลดใหม่";}
 }
 if(ticket===state.request)render();
}
async function refresh(){
 $("refresh-button").disabled=true;
 try{
 [state.index,state.status]=await Promise.all([json("data/index.json"),json("data/status.json")]);
 renderStatus();await loadDay();
 }catch(e){$("connection-title").textContent="โหลดข้อมูลไม่สำเร็จ";$("connection-detail").textContent=e.message;}
 finally{$("refresh-button").disabled=false;}
}
function initializeMap(boundary){
 if(!window.L){setMapMessage("โหลดเครื่องมือแผนที่ไม่สำเร็จ","ไฟล์ Leaflet ไม่พร้อมใช้งาน");return;}
 state.map=L.map("map",{preferCanvas:true,zoomControl:false});
 L.control.zoom({position:"topright"}).addTo(state.map);
 L.control.scale({imperial:false,position:"bottomright"}).addTo(state.map);
 state.map.createPane("landuse");state.map.getPane("landuse").style.zIndex=410;
 state.map.createPane("fire");state.map.getPane("fire").style.zIndex=440;
 state.map.createPane("boundary");state.map.getPane("boundary").style.zIndex=450;state.map.getPane("boundary").style.pointerEvents="none";
 L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',maxZoom:19}).addTo(state.map);
 state.boundary=L.geoJSON(boundary,{pane:"boundary",style:{color:"#285b4b",weight:1.7,dashArray:"6 5",fill:false}}).addTo(state.map);
 state.map.fitBounds(state.boundary.getBounds(),{padding:[25,25]});
 drawFires();
}
async function loadLanduse(){
 try{
 const data=await json("data/landuse_layers.geojson.gz");
 if(!state.map)return;
 data.features.forEach(f=>{
  const code=f.properties.landuse_code;
  state.landuse[code]=L.geoJSON(f,{pane:"landuse",style:{color:COLORS[code],weight:.4,opacity:.7,fillColor:COLORS[code],fillOpacity:code==="PEAT"?.2:.32},
  onEachFeature:(feature,layer)=>layer.bindPopup("<strong>"+safe(LABELS[code][0])+"</strong><br>พื้นที่ในขอบเขต: "+format(feature.properties.area_ha)+" ha")});
  if($("layer-"+code).checked)state.landuse[code].addTo(state.map);
 });
 $("layer-load-status").textContent="Landuse 5 ชั้น · ข้อมูลพื้นที่จริง";
 }catch(e){$("layer-load-status").textContent="โหลด Landuse ไม่สำเร็จ · ลองโหลดหน้าใหม่";$("layer-load-status").classList.add("error-message");}
}
function exportCsv(){
 const summary=currentSummary();if(!summary)return;
 const header=["date_thailand","source","fuel","area_ha","rho_tonne_dm_ha","eta","ef_g_kg","emission_kg","included_in_total"];
 const rows=summary.fuels.map(r=>[$("date-input").value,state.source,r.code,r.area_ha,r.rho,r.eta,r.ef_pm25,r.emission_kg,!r.peat_scenario||state.peat]);
 const csv=[header,...rows].map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(",")).join("\r\n");
 const blob=new Blob(["\ufeff"+csv],{type:"text/csv;charset=utf-8"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="pkk-emission-"+$("date-input").value+"-"+state.source+".csv";a.click();URL.revokeObjectURL(url);
}
async function init(){
 $("date-input").value=today();$("date-input").max=today();
 $("layer-controls").innerHTML=Object.keys(COLORS).map(code=>'<label><input type="checkbox" id="layer-'+code+'" '+(code!=="PEAT"?"checked":"")+'><span>'+LABELS[code][0]+'</span><i class="layer-color" style="background:'+COLORS[code]+'"></i></label>').join("");
 Object.keys(COLORS).forEach(code=>$("layer-"+code).addEventListener("change",e=>{const layer=state.landuse[code];if(layer&&state.map){if(e.target.checked)layer.addTo(state.map);else state.map.removeLayer(layer);}}));
 $("date-input").addEventListener("change",()=>{if($("date-input").value)loadDay();});
 $("sensor-select").addEventListener("change",e=>{state.source=e.target.value;render();});
 $("include-peat").addEventListener("change",e=>{state.peat=e.target.checked;render();});
 $("refresh-button").addEventListener("click",refresh);
 $("export-button").addEventListener("click",exportCsv);
 $("fit-map").addEventListener("click",()=>{if(state.map&&state.boundary)state.map.fitBounds(state.boundary.getBounds(),{padding:[25,25]});});
 for(const [button,dialog] of [["parameters-button","parameters-dialog"],["method-button","method-dialog"]])$(button).addEventListener("click",()=>$(dialog).showModal());
 document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>$(b.dataset.close).close()));
 for(const [id,offset] of [["prev-day",-1],["next-day",1]])$(id).addEventListener("click",()=>{
  const d=new Date($("date-input").value+"T12:00:00Z");d.setUTCDate(d.getUTCDate()+offset);const value=d.toISOString().slice(0,10);if(value<=today()){$("date-input").value=value;loadDay();}
 });
 try{
 const [project,parameters,boundary]=await Promise.all([json("data/project.json"),json("data/parameters.json"),json("data/study_area.geojson")]);
 state.project=project;state.parameters=parameters;
 $("study-area").innerHTML=format(project.study_area_ha,0)+" <small>ha</small>";
 renderParameters();initializeMap(boundary);await refresh();loadLanduse();
 }catch(e){$("connection-title").textContent="ข้อมูลโครงการยังไม่พร้อม";$("connection-detail").textContent=e.message;setMapMessage("เปิดข้อมูลโครงการไม่สำเร็จ","ตรวจการเตรียมไฟล์และการเชื่อมต่อ");}
}
init();
