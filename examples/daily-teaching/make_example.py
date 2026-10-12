# SPDX-License-Identifier: MIT
"""Original fictional samples; no real securities or market data."""
import json,math,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from cn_factor_research.daily_factors import generate,FACTORS
out=Path(__file__).parent;tz=timezone(timedelta(hours=8))
def at(day,hour=16):return datetime(2024,1,1,hour,tzinfo=tz)+timedelta(days=day)
rows=[]
for day in (40,41,42,50,51,52,60,61,62):
    signal=at(day).isoformat()
    for s in range(12):
        history=[];close=10+s
        for i in range(30):
            previous=close;close*=1+.005*math.sin(i*1.1+s)+.0004*(s-5)
            o=previous*(1+.003*math.cos(i*.7+s))
            history.append(dict(at=(at(day)-timedelta(days=29-i)).isoformat(),availableAt=(at(day)-timedelta(days=29-i)).isoformat(),open=o,high=max(o,close)*1.01,low=min(o,close)*.99,close=close,volumeShares=1000+100*s+30*i,turnover=.01+.001*(i%7+s),source='original-synthetic-teaching'))
        row=dict(security='TEACHING-'+str(s),signalAt=signal,factorAvailableAt=signal,universeAvailableAt=at(0).isoformat(),membershipAtSignal=True,adjustmentEvidence=dict(source='original-fiction-no-actions',availableAt=at(0).isoformat()),history=history,marketCap=1e8*(s+1),industry='fiction-industry-'+str(s%2),exposureAvailableAt=signal,label=dict(returnStartAt=signal,returnEndAt=at(day+2).isoformat(),availableAt=at(day+2).isoformat(),forwardReturn=.005*math.sin(s+day*.2),source='original-synthetic-teaching'))
        rows.append(row)
daily=dict(schemaVersion='daily-factor-input/1',asOf=at(70).isoformat(),dataKind='synthetic-teaching',dataVersion='original-daily-teaching/1',universeDefinition='12 invented securities; synthetic dates are not an exchange calendar',universeVersion='fiction/1',priceBasis='synthetic-consistent-no-actions',volumeBasis='shares',returnUnit='decimal-simple-total-return',groups=3,parameters=dict(lookbackRecords=20,volatilityRecords=5,volumeMultiple=2),rows=rows)
generated=generate(daily)
audit=dict(schemaVersion='factor-validation/1',asOf=daily['asOf'],dataVersion=daily['dataVersion'],testTouchedDuringSelection=False,selectionRule='All eight definitions retained; directions frozen before teaching test dates; no performance selection',selectionFrozenAt=at(59).isoformat(),neutralization='log-market-cap-and-industry',oneWayCostBps=10,split=dict(trainStart=at(40).isoformat(),trainEnd=at(42).isoformat(),validationStart=at(50).isoformat(),validationEnd=at(52).isoformat(),testStart=at(60).isoformat(),testEnd=at(62).isoformat()),candidates=[dict(id=k,direction=FACTORS[k][1],panel=v) for k,v in generated['panelInputs'].items()])
events=[]
for i,day in enumerate((40,41,45,50)):
    entry=at(day+1,9).replace(minute=30).isoformat();end=at(day+2).isoformat()
    events.append(dict(id='fiction-event-'+str(i),security='TEACHING-0',eventType='fiction-positive',direction='positive',definitionVersion='original-fiction-event/1',signalRecord=day,signalAt=at(day).isoformat(),availableAt=at(day).isoformat(),observedUntilAt=at(day).isoformat(),membershipAtSignal=True,universeAvailableAt=at(0).isoformat(),nextSessionOpenAt=entry,calendarSource='original-fiction-calendar-not-exchange',outcomes=[dict(horizonRecords=1,status='known',returnStartAt=entry,returnEndAt=end,availableAt=end,forwardReturn=.01*(i-1),benchmarkReturn=.005,benchmarkStartAt=entry,benchmarkEndAt=end,benchmarkSource='original-fiction-benchmark',source='original-synthetic-teaching'),dict(horizonRecords=5,status='unknown')]))
event=dict(schemaVersion='event-study-input/1',asOf=at(70).isoformat(),dataKind='synthetic-teaching',returnUnit='decimal-simple-total-return',dataVersion=daily['dataVersion'],universeDefinition=daily['universeDefinition'],universeVersion=daily['universeVersion'],repeatPolicy='cooldown',cooldownRecords=2,horizons=[1,5],entryBasis='declared-next-session-open',events=events)
readiness=dict(schemaVersion='factor-method-readiness/1',asOf=at(70).isoformat(),methods=['daily-core','factor-audit','event-study','fundamental-quality-cashflow','behavior-salience','trend-minute','order-lifecycle','opening-auction'],capabilities={k:dict(status='verified',source='original-synthetic-teaching',evidence='Fictional resource declaration; no real-market certification',verifiedAt=at(0).isoformat()) for k in ['daily_ohlcv','price_basis','calendar','historical_members','factor_panel','frozen_split','event_evidence','outcomes']})
for name,data in [('daily.json',daily),('audit.json',audit),('events.json',event),('readiness.json',readiness)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
print('Original teaching inputs prepared.')
