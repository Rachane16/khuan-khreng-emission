/* Calendar-aware chart data, shared by the browser and Node behavior checks. */
(function(root,factory){const api=factory();if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.ChartData=api;})(typeof globalThis!=="undefined"?globalThis:this,function(){
 const valid=s=>/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s+"T00:00:00Z"))&&new Date(s+"T00:00:00Z").toISOString().slice(0,10)===s;
 function shift(day,offset){if(!valid(day))throw Error("Invalid calendar date");const d=new Date(day+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+offset);return d.toISOString().slice(0,10);}
 function series(index,first,last,source="ALL",peat=true){
  if(!valid(first)||!valid(last)||first>last)throw Error("เลือกช่วงวันที่ให้ถูกต้อง");
  if((Date.parse(last)-Date.parse(first))/86400000>365)throw Error("เลือกช่วงกราฟได้สูงสุด 366 วัน");
  const saved=new Map((index.daily||[]).map(r=>[r.date,r])),rows=[];
  for(let day=first;day<=last;day=shift(day,1)){
   const row=saved.get(day),summary=row?.by_source?.[source]||(source==="ALL"?row:null),status=source==="ALL"?row?.data_state:row?.source_status?.[source];
   const count=summary?.observation_count??summary?.observations;
   const unavailable=!summary||(["error","unavailable","not_configured"].includes(status)&&!count);
   const fuels=(summary?.fuels||[]).filter(f=>peat||!f.peat_scenario);
   const value=unavailable?null:(peat?summary.emission_kg:summary.emission_without_peat_kg);
   rows.push({date:day,state:unavailable?"missing":(status==="ok"||(!status&&row?.data_state==="ok")?"ok":"partial"),
    value:Number.isFinite(value)?value:null,fuels:unavailable?[]:fuels,observations:count??null});
  }
  return rows;
 }
 return {series,shift,valid};
});
