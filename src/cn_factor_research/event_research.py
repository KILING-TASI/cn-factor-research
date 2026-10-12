# SPDX-License-Identifier: MIT
"""Evidence-bound event studies, without executable-order claims."""
import statistics
from .review_io import instant
from .daily_factors import finite,integer

def quantile(values,q):
    data=sorted(values);x=(len(data)-1)*q;i=int(x)
    return data[i] if i==len(data)-1 else data[i]+(data[i+1]-data[i])*(x-i)

def study(spec):
    if spec.get('schemaVersion')!='event-study-input/1':raise ValueError('需要event-study-input/1')
    cutoff=instant(spec['asOf']);cooldown=integer(spec['cooldownRecords'],0,120)
    if spec.get('dataKind') not in ('synthetic-teaching','declared-history') or spec.get('returnUnit') not in ('decimal-simple-total-return','decimal-simple-adjusted-price-return'):raise ValueError('事件数据性质和收益单位必须明确')
    if spec.get('repeatPolicy') not in ('keep-all','cooldown') or spec['repeatPolicy']=='keep-all' and cooldown!=0:raise ValueError('重复触发规则不一致')
    horizons=spec['horizons']
    if not isinstance(horizons,list) or not horizons or len(horizons)>10 or any(type(h)!=int for h in horizons) or len(set(horizons))!=len(horizons):raise ValueError('收益期限须唯一整数且不超过10个')
    for h in horizons:integer(h,1,256)
    if not spec.get('universeDefinition') or not spec.get('universeVersion') or not spec.get('dataVersion') or spec.get('entryBasis')!='declared-next-session-open':raise ValueError('须明确股票池/数据版本及次交易日开盘基准')
    events=spec['events']
    if not isinstance(events,list) or not 1<=len(events)<=5000:raise ValueError('事件数须1至5000')
    ids=set();keys=set();last={};used=[];suppressed=[];unknown=[];buckets={};record_times={};signal_records={};definitions={}
    for e in sorted(events,key=lambda e:(instant(e['signalAt']),e['security'],e['eventType'])):
        identity=(e['security'],e['eventType'],instant(e['signalAt']))
        if not isinstance(e['id'],str) or not e['id'] or e['id'] in ids or identity in keys:raise ValueError('事件ID或身份重复')
        ids.add(e['id']);keys.add(identity);signal=instant(e['signalAt']);record=integer(e['signalRecord'],0,10000000)
        if not isinstance(e['security'],str) or not e['security'] or not isinstance(e['eventType'],str) or not e['eventType'] or not e.get('definitionVersion'):raise ValueError('事件证券、类型或定义版本缺失')
        definition=(e['definitionVersion'],e['direction'])
        if e['eventType'] in definitions and definitions[e['eventType']]!=definition:raise ValueError('同类事件混用定义版本或方向')
        definitions[e['eventType']]=definition
        if e['direction'] not in ('positive','negative') or not instant(e['observedUntilAt'])<=instant(e['availableAt'])<=signal<=cutoff:raise ValueError('事件方向或观察/可得时点无效')
        if e.get('membershipAtSignal') is not True or instant(e['universeAvailableAt'])>signal:raise ValueError('未确认事件时点成员')
        entry=instant(e['nextSessionOpenAt'])
        if entry<=signal or not e.get('calendarSource'):raise ValueError('次交易日开盘时点及日历依据缺失')
        sr=(e['security'],signal);rt=(e['security'],record)
        if sr in signal_records and signal_records[sr]!=record or rt in record_times and record_times[rt]!=signal:raise ValueError('交易记录编号与信号时间不一致')
        signal_records[sr]=record;record_times[rt]=signal
        prior=[r for (security,r),at in record_times.items() if security==e['security'] and at<signal]
        if prior and record<=max(prior):raise ValueError('交易记录编号未随时间递增')
        outcomes=e['outcomes']
        if not isinstance(outcomes,list) or len({o['horizonRecords'] for o in outcomes})!=len(outcomes):raise ValueError('事件收益期限重复或格式无效')
        if any(type(o['horizonRecords'])!=int or o['horizonRecords'] not in horizons for o in outcomes):raise ValueError('出现未预声明的收益期限')
        confirmed={}
        for o in outcomes:
            if o.get('status')=='unknown':
                if o.get('forwardReturn') is not None or o.get('benchmarkReturn') is not None:raise ValueError('未知结果不能夹带收益数值')
                continue
            if o.get('status')!='known':raise ValueError('收益状态须known或unknown')
            start,end,available=[instant(o[k]) for k in ('returnStartAt','returnEndAt','availableAt')]
            if start!=entry or not start<end<=available or not o.get('source'):raise ValueError('事件收益窗口或来源不一致')
            value=finite(o['forwardReturn'])
            if value<-1:raise ValueError('简单收益小于-100%')
            benchmark=o.get('benchmarkReturn')
            if benchmark is not None:
                if instant(o['benchmarkStartAt'])!=start or instant(o['benchmarkEndAt'])!=end or not o.get('benchmarkSource'):raise ValueError('基准窗口或来源不同')
                if finite(benchmark)<-1:raise ValueError('基准简单收益小于-100%')
            if available<=cutoff:confirmed[o['horizonRecords']]=(value,None if benchmark is None else value-benchmark)
        repeat=(e['security'],e['eventType'])
        if spec['repeatPolicy']=='cooldown' and repeat in last and record-last[repeat]<=cooldown:
            suppressed.append(dict(id=e['id'],reason='预声明冷却期内重复触发'));continue
        last[repeat]=record;used.append(e['id'])
        for h in horizons:
            key=(e['eventType'],e['direction'],h);bucket=buckets.setdefault(key,dict(total=0,returns=[],excess=[]));bucket['total']+=1
            if h not in confirmed:unknown.append(dict(id=e['id'],horizonRecords=h,reason='缺失、声明未知或截止后才可得'));continue
            value,excess=confirmed[h];bucket['returns'].append(value)
            if excess is not None:bucket['excess'].append(excess)
    stats=[]
    for (kind,direction,h),b in sorted(buckets.items()):
        values=b['returns'];excess=b['excess'];n=len(values)
        stats.append(dict(eventType=kind,direction=direction,horizonRecords=h,totalEvents=b['total'],knownCount=n,unknownCount=b['total']-n,meanReturn=statistics.mean(values) if n else None,medianReturn=statistics.median(values) if n else None,q25=quantile(values,.25) if n else None,q75=quantile(values,.75) if n else None,positiveReturnShare=sum(v>0 for v in values)/n if n else None,hypothesisDirectionMatchedShare=sum(v>0 if direction=='positive' else v<0 for v in values)/n if n else None,meanExcessReturn=statistics.mean(excess) if excess else None,knownBenchmarkCount=len(excess)))
    return dict(methodVersion='original-causal-event-study/1',conclusion='事件条件、重复触发及各期限已知收益分别留档；正负信号分开统计，不自动认定有效。',statistics=stats,retainedEventIds=used,suppressed=suppressed,unknown=unknown,humanRows=[['声明事件',len(events)],['保留事件',len(used)],['按规则抑制',len(suppressed)],['未知期限记录',len(unknown)]],limitations=['观察窗口结束后才可使用；次日开盘是声明研究基准，不认证可成交','胜率只统计已知结果，未知仍计入事件总数；没有概率模型或独立事件假设','重复事件及同股跨期限结果相关，不输出显著性或年化策略收益','收益/基准类型、交易日编号与日历来源由输入声明；未自动认证逐日间隔','未包含交易成本、涨跌停、停牌、T+1及资金通道模拟；组合条件交由PDE','正负方向仅为预声明假设；未将放量、羊群或资金流标签认定为实际交易者身份'])
