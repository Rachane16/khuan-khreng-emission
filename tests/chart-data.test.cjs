const assert=require("node:assert/strict");
const {series,shift}=require("../web/chart-data.js");
const fuel=(code,value,peat=false)=>({code,emission_kg:value,peat_scenario:peat});
const all={observation_count:2,emission_kg:10,emission_without_peat_kg:4,fuels:[fuel("GRASS",4),fuel("PEAT",6,true)]};
const snpp={observation_count:0,emission_kg:0,emission_without_peat_kg:0,fuels:[]};
const index={daily:[{date:"2026-08-15",data_state:"ok",by_source:{ALL:all,VIIRS_SNPP_NRT:snpp},source_status:{VIIRS_SNPP_NRT:"ok"}},
{date:"2026-08-17",data_state:"partial",by_source:{ALL:all,VIIRS_SNPP_NRT:snpp},source_status:{VIIRS_SNPP_NRT:"unavailable"}}]};
const days=series(index,"2026-08-15","2026-08-17");
assert.deepEqual(days.map(d=>d.value),[10,null,10]);
assert.deepEqual(days.map(d=>d.state),["ok","missing","partial"]);
assert.equal(series(index,"2026-08-15","2026-08-15","ALL",false)[0].value,4);
assert.equal(series(index,"2026-08-15","2026-08-15","ALL",false)[0].fuels.length,1);
assert.equal(series(index,"2026-08-15","2026-08-17","VIIRS_SNPP_NRT")[0].value,0);
assert.equal(series(index,"2026-08-15","2026-08-17","VIIRS_SNPP_NRT")[2].value,null);
assert.equal(series(index,"2026-07-17","2026-08-15").length,30);
assert.equal(shift("2024-03-01",-1),"2024-02-29");
assert.throws(()=>series(index,"2026-02-30","2026-03-01"));
assert.throws(()=>series(index,"2026-08-17","2026-08-15"));
console.log("Calendar chart behavior: missing dates, partial sources, peat toggle and 30-day windows passed.");
