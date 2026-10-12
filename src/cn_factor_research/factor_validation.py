# SPDX-License-Identifier: MIT
"""Frozen-split, paired factor review; standard library OLS diagnostics."""
import math,statistics
from .review_io import instant
from .daily_factors import finite
from .factor_research import panel,ranks,corr

def residuals(rows):
    """OLS via twice-reorthogonalized QR; deficient design is explicitly blocked."""
    n=len(rows)
    if any(not isinstance(r['industry'],str) or not r['industry'] for r in rows):raise ValueError('行业身份缺失')
    industries=sorted({r['industry'] for r in rows})
    if len(industries)>64 or n*(len(industries)+1)>250000:raise ValueError('中性化类别或矩阵规模超出本轮上限')
    if n<=len(industries)+2:raise ValueError('中性化样本不足以保留残差自由度')
    cap=[math.log(finite(r['marketCap'])) for r in rows]
    sd=statistics.pstdev(cap)
    if not sd:raise ValueError('市值暴露为常数，无法识别市值中性化')
    columns=[[1.0]*n,[(x-statistics.mean(cap))/sd for x in cap]]+[[float(r['industry']==industry) for r in rows] for industry in industries[1:]]
    if n<=len(columns)+1:raise ValueError('中性化样本不足以保留残差自由度')
    qs=[]
    for column in columns:
        v=list(column)
        for _ in range(2):
            for q in qs:
                projection=sum(a*b for a,b in zip(q,v));v=[a-projection*b for a,b in zip(v,q)]
        norm=math.sqrt(sum(x*x for x in v))
        if norm<1e-9:raise ValueError('行业/市值设计矩阵秩不足，未伪造中性化结果')
        qs.append([x/norm for x in v])
    y=[finite(r['factor']) for r in rows];res=list(y)
    for q in qs:
        projection=sum(a*b for a,b in zip(q,y));res=[a-projection*b for a,b in zip(res,q)]
    if max(map(abs,res),default=0)<max(1,max(map(abs,y),default=0))*1e-10:res=[0.0]*n
    return res

def neutralize(p):
    dates={}
    for row in p['rows']:
        if finite(row['marketCap'])<=0 or instant(row['exposureAvailableAt'])>instant(row['signalAt']):raise ValueError('市值/行业暴露无效或晚于信号')
        dates.setdefault(row['signalDate'],[]).append(row)
    out=[]
    for day,rows in sorted(dates.items()):out.extend(dict(r,factor=v) for r,v in zip(rows,residuals(rows)))
    return dict(p,rows=out)

def trading_diagnostics(p,direction,cost):
    daily={}
    for r in p['rows']:daily.setdefault(r['signalDate'],[]).append(r)
    previous=None;result=[]
    for day,rows in sorted(daily.items()):
        signed=[direction*finite(r['factor']) for r in rows];rk=ranks(signed);groups=p['groups'];n=len(rows)
        top=[r for rank,r in zip(rk,rows) if min(groups,int((rank-1)*groups/n)+1)==groups]
        if not top:result.append(dict(signalDate=day,status='unknown-empty-top-group',oneWayTurnover=None,estimatedCostDrag=None));previous=None;continue
        weights={r['security']:1/len(top) for r in top}
        turnover=None if previous is None else sum(abs(weights.get(k,0)-previous.get(k,0)) for k in set(weights)|set(previous))/2
        result.append(dict(signalDate=day,status='conditional-target-weights-only',topGroupCount=len(top),oneWayTurnover=turnover,estimatedCostDrag=None if turnover is None or cost is None else 2*turnover*cost/10000))
        previous=weights
    return result

def review(spec):
    if spec.get('schemaVersion')!='factor-validation/1':raise ValueError('需要factor-validation/1')
    if spec.get('testTouchedDuringSelection') is not False or not spec.get('selectionRule') or not spec.get('dataVersion'):raise ValueError('须冻结选型规则、数据版本并明确测试期未参与选型')
    stages=spec['split'];times={k:instant(stages[k]) for k in ('trainStart','trainEnd','validationStart','validationEnd','testStart','testEnd')}
    if not times['trainStart']<=times['trainEnd']<times['validationStart']<=times['validationEnd']<times['testStart']<=times['testEnd']<=instant(spec['asOf']):raise ValueError('时间切分顺序无效')
    if instant(spec['selectionFrozenAt'])>=times['testStart']:raise ValueError('选型冻结不早于测试期')
    candidates=spec['candidates']
    if not isinstance(candidates,list) or not 1<=len(candidates)<=32 or len({c['id'] for c in candidates})!=len(candidates):raise ValueError('候选身份须唯一，首版不超过32个')
    reference=None;universe=None;out=[];cost=spec.get('oneWayCostBps')
    if cost is not None and not 0<=finite(cost)<=10000:raise ValueError('单边成本假设无效')
    for c in candidates:
        direction=c['direction']
        if type(direction)!=int or direction not in (-1,1):raise ValueError('方向须事先声明为1或-1')
        p=c['panel']
        if not isinstance(p['rows'],list) or not 1<=len(p['rows'])<=5000:raise ValueError('验收候选样本须1至5000')
        base=panel(p)
        if any(instant(r['signalAt'])>instant(spec['asOf']) for r in p['rows']):raise ValueError('候选信号晚于复查截止')
        same_day={}
        for r in p['rows']:same_day.setdefault(r['signalDate'],set()).add(instant(r['signalAt']))
        if any(len(v)>1 for v in same_day.values()):raise ValueError('同一截面混用不同信号时点')
        if instant(p['asOf'])!=instant(spec['asOf']) or p.get('dataVersion')!=spec['dataVersion']:raise ValueError('候选截止时间或数据版本不一致')
        if not p.get('priceBasis') or p.get('returnUnit') not in ('decimal-simple-total-return','decimal-simple-adjusted-price-return'):raise ValueError('候选价格或收益口径缺失')
        identity=(p['universeDefinition'],p['universeVersion'],p['groups'],p['priceBasis'],p['returnUnit'])
        keys={(r['security'],instant(r['signalAt']).isoformat()):(r['forwardReturn'],instant(r['returnStartAt']).isoformat(),instant(r['returnEndAt']).isoformat(),instant(r['returnAvailableAt']).isoformat()) for r in p['rows']}
        if reference is None:reference=keys;universe=identity
        elif reference!=keys or universe!=identity:raise ValueError('候选样本、标签窗口、股票池或分组不同；不得静默取交集比较')
        versions={'raw':p};blocked=None
        if spec.get('neutralization')=='log-market-cap-and-industry':
            try:versions['neutralized']=neutralize(p)
            except (ValueError,KeyError,TypeError) as error:blocked=str(error)
        elif spec.get('neutralization')!='none':raise ValueError('不支持此中性化口径')
        item=dict(id=c['id'],direction=direction,neutralizationBlocked=blocked,versions={})
        for name,source in versions.items():
            reports={};purged=[];outside=[]
            for stage,next_stage in (('train','validation'),('validation','test'),('test',None)):
                rows=[]
                for r in source['rows']:
                    signal=instant(r['signalAt'])
                    if not times[stage+'Start']<=signal<=times[stage+'End']:continue
                    if next_stage and instant(r['returnAvailableAt'])>=times[next_stage+'Start']:
                        purged.append(dict(security=r['security'],signalAt=r['signalAt'],stage=stage));continue
                    rows.append(dict(r,factor=direction*finite(r['factor'])))
                reports[stage]=panel(dict(source,rows=rows)) if rows else dict(status='blocked-no-stage-samples',daily=[],meanRankIC=None)
                if name=='neutralized' and 'limitations' in reports[stage]:
                    reports[stage]['limitations']=[x for x in reports[stage]['limitations'] if '行业市值中性化' not in x]+['本验收已控制声明的行业/对数市值；原始面板入口本身不做中性化']
                if stage=='test':reports[stage]['tradingDiagnostics']=trading_diagnostics(dict(source,rows=rows),direction,cost)
            for r in source['rows']:
                at=instant(r['signalAt'])
                if not any(times[s+'Start']<=at<=times[s+'End'] for s in ('train','validation','test')):outside.append(dict(security=r['security'],signalAt=r['signalAt']))
            item['versions'][name]=dict(stages=reports,purged=purged,outsideDeclaredStages=outside,testAssessment='descriptive-only' if reports['test'].get('meanRankIC') is not None else 'blocked-no-defined-test-rankIC')
        out.append(item)
    paired=[]
    for i,left in enumerate(candidates):
        for right in candidates[i+1:]:
            by_key={(r['security'],instant(r['signalAt'])):r for r in right['panel']['rows']}
            by_day={}
            for r in left['panel']['rows']:
                other=by_key[(r['security'],instant(r['signalAt']))]
                by_day.setdefault(r['signalDate'],[]).append((left['direction']*finite(r['factor']),right['direction']*finite(other['factor'])))
            stage_stats={}
            for stage in ('train','validation','test'):
                values=[]
                for day,pairs in sorted(by_day.items()):
                    at=instant(next(r['signalAt'] for r in left['panel']['rows'] if r['signalDate']==day))
                    if times[stage+'Start']<=at<=times[stage+'End']:
                        value=corr(ranks([a for a,b in pairs]),ranks([b for a,b in pairs]))
                        values.append(dict(signalDate=day,rankCorrelation=value))
                valid=[r['rankCorrelation'] for r in values if r['rankCorrelation'] is not None]
                stage_stats[stage]=dict(daily=values,meanRankCorrelation=statistics.mean(valid) if valid else None)
            paired.append(dict(left=left['id'],right=right['id'],stages=stage_stats))
    return dict(methodVersion='original-frozen-factor-validation/1',conclusion='候选已按相同样本与预声明方向逐项验收；测试结果不参与重新排名选型。',candidates=out,pairwiseFactorCorrelation=paired,oneWayCostBps=cost,
      humanRows=[['声明候选数',len(out)],['选型规则',spec['selectionRule']],['中性化口径',spec['neutralization']],['交易成本','未提供' if cost is None else str(cost)+'基点（单边假设）']],
      limitations=['测试隔离依据由输入声明，程序不能证明研究者未看过测试结果','行业市值中性化只控制声明暴露，不等于完整Barra风险模型','因子相关性只检查信息重叠，不证明组合增量；跨日均值不作显著性结论','成本仅按目标等权权重变化估算；首次建仓未知，不是撮合或账户净收益','IC与分层结果未校正重叠标签及时间依赖；不计算显著性、DSR/PBO或自动认证有效','不因测试成绩修改方向、参数或选择赢家；敏感性候选也须提前留档','历史成员、退市、停牌、T+1和涨跌停成交边界仍需单独核验'])
