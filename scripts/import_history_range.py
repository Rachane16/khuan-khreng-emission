"""One-time historical import in resumable 31-day batches."""
import argparse, calendar, getpass, json, os, sys, time
from datetime import datetime,timedelta,date
from urllib.request import urlopen
import fire_pipeline as m
import backfill_firms as b

def month_start(day,months):
    serial=day.year*12+day.month-1-months
    year,month=divmod(serial,12); month+=1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))

def wait_for_quota(key):
    # NASA transactions are not one-to-one with HTTP calls.
    for _ in range(21):
        try:
            with urlopen("https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY="+key,timeout=30) as r:
                data=json.load(r)
            current=int(data["current_transactions"]);limit=int(data["transaction_limit"])
        except Exception:
            raise RuntimeError("Unable to verify FIRMS quota; import paused without exposing credentials") from None
        if current<limit*.8: return
        print("Waiting for FIRMS quota reset.",flush=True);time.sleep(30)
    raise RuntimeError("FIRMS quota remained busy; retry the saved range later")

def run(first,last,key,root=m.ROOT):
    if not first<=last<=datetime.now(m.BANGKOK).date(): raise ValueError("Invalid historical range")
    target=root/"web/data/import_status.json"
    completed=[]
    cursor=first
    while cursor<=last:
        end=min(last,cursor+timedelta(days=30))
        wait_for_quota(key)
        m.write_json(target,{"state":"running","start":first.isoformat(),"end":last.isoformat(),
            "completed_batches":completed,"active_batch":[cursor.isoformat(),end.isoformat()]})
        print("Importing "+cursor.isoformat()+" .. "+end.isoformat(),flush=True)
        b.backfill(cursor.isoformat(),end.isoformat(),root,key)
        completed.append([cursor.isoformat(),end.isoformat()])
        cursor=end+timedelta(days=1)
    m.write_json(target,{"state":"complete","start":first.isoformat(),"end":last.isoformat(),
        "completed_batches":completed,"completed_utc":datetime.now(m.UTC).isoformat()})
    print("Historical range import complete.",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--months",type=int,default=3,choices=range(1,37))
    p.add_argument("--start-date");p.add_argument("--end-date");p.add_argument("--prompt-key",action="store_true")
    a=p.parse_args();today=datetime.now(m.BANGKOK).date()
    first=date.fromisoformat(a.start_date) if a.start_date else month_start(today,a.months)
    last=date.fromisoformat(a.end_date) if a.end_date else today-timedelta(days=1)
    key=getpass.getpass("FIRMS MAP_KEY (hidden): ") if a.prompt_key else os.environ.get("FIRMS_MAP_KEY","")
    if not key: raise RuntimeError("FIRMS_MAP_KEY is not configured")
    run(first,last,key)
if __name__=="__main__":
    try:main()
    except (RuntimeError,ValueError) as e: print(str(e),file=sys.stderr);sys.exit(2)
