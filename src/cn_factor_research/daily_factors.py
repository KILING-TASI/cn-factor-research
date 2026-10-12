# SPDX-License-Identifier: MIT
"""Original daily baselines and conditional price/volatility factors."""
import math,statistics
from .review_io import instant,digest
from .factor_research import corr,ranks

VERSION='original-daily-volume-price/1'
FACTORS={
 'momentum':('窗口动量',1),'reversal':('窗口反转',1),
 'overnight_abs':('平均隔夜跳空绝对值',-1),
 'overnight_turnover_corr':('隔夜跳空与昨日换手相关',-1),
 'rsi_gain_share':('日频涨幅占比RSI（非Wilder平滑）',-1),
 'rsi_conditional_mean':('日频条件均值RSI',-1),
 'high_price_vol_share':('高价格区间波动占比',-1),
 'high_vol_price_share':('高波动区间价格占比',-1)}

def finite(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('数值须明确且有限')
    return float(value)

def integer(value,lo,hi):
    if type(value)!=int or not lo<=value<=hi:raise ValueError('整数参数越界')
    return value

def compute(history,lookback=20,vol_window=5):
    if len(history)<lookback+vol_window:raise ValueError('缺少波动率前置窗口，不补造历史')
    close=[finite(b['close']) for b in history]
    if min(close)<=0:raise ValueError('收盘价须为正')
    returns=[finite(close[i]/close[i-1]-1) for i in range(1,len(close))]
    rs=returns[-lookback:];window=history[-lookback:]
    vol=[statistics.pstdev(returns[i-vol_window:i]) for i in range(len(returns)-lookback+1,len(returns)+1)]
    gaps=[abs(finite(history[i]['open'])/close[i-1]-1) for i in range(len(history)-lookback,len(history))]
    out=dict(momentum=close[-1]/close[-lookback-1]-1,reversal=1-close[-1]/close[-lookback-1],overnight_abs=statistics.mean(gaps))
    gains=[max(r,0) for r in rs];losses=[max(-r,0) for r in rs];den=sum(gains)+sum(losses)
    out['rsi_gain_share']=100*sum(gains)/den if den else None
    up=[r for r in rs if r>0];down=[-r for r in rs if r<0]
    # The conditional-mean version is undefined if one side has no observations.
    out['rsi_conditional_mean']=100*statistics.mean(up)/(statistics.mean(up)+statistics.mean(down)) if up and down else None
    previous=history[-lookback-1:-1]
    turnover=[b.get('turnover') for b in previous]
    if all(t is not None for t in turnover):
        ts=[finite(t) for t in turnover]
        if min(ts)<0:raise ValueError('换手率不能为负')
        out['overnight_turnover_corr']=corr(gaps,ts)
    else:out['overnight_turnover_corr']=None
    prices=[finite(b['close']) for b in window];cut=1+.8*(lookback-1)
    high_price=[i for i,r in enumerate(ranks(prices)) if r>=cut]
    high_vol=[i for i,r in enumerate(ranks(vol)) if r>=cut]
    vm=statistics.mean(vol)
    out['high_price_vol_share']=statistics.mean(vol[i] for i in high_price)/vm if high_price and vm>0 else None
    out['high_vol_price_share']=statistics.mean(prices[i] for i in high_vol)/statistics.mean(prices) if high_vol and vm>0 else None
    for value in out.values():
        if value is not None:finite(value)
    return out

def generate(spec):
    if spec.get('schemaVersion')!='daily-factor-input/1':raise ValueError('需要daily-factor-input/1')
    cutoff=instant(spec['asOf']);p=spec['parameters'];lookback=integer(p['lookbackRecords'],5,120);vol_window=integer(p['volatilityRecords'],2,20)
    integer(spec.get('groups',5),2,10)
    if spec.get('dataKind') not in ('synthetic-teaching','declared-history'):raise ValueError('须声明教学或历史数据')
    if spec.get('volumeBasis')!='shares' or not spec.get('priceBasis') or not spec.get('universeDefinition') or not spec.get('universeVersion') or not spec.get('dataVersion') or spec.get('returnUnit') not in ('decimal-simple-total-return','decimal-simple-adjusted-price-return'):raise ValueError('股数、价格/收益口径、数据与股票池版本必须明确')
    if not isinstance(spec['rows'],list) or not 1<=len(spec['rows'])<=5000:raise ValueError('首版限定1至5000个截面样本')
    results=[];gaps=[];seen=set();panels={k:[] for k in FACTORS};events=[]
    threshold=finite(p.get('volumeMultiple',2))
    if not 1<threshold<=10:raise ValueError('放量阈值须大于1且不超过10')
    for row in spec['rows']:
        signal=instant(row['signalAt']);key=(row['security'],signal)
        if not isinstance(row['security'],str) or not row['security'] or key in seen:raise ValueError('证券身份缺失或信号重复')
        seen.add(key)
        if signal>cutoff or instant(row['factorAvailableAt'])>signal or instant(row['universeAvailableAt'])>signal or row.get('membershipAtSignal') is not True:raise ValueError('因子或当期成员在信号时点未明确可得')
        adjustment=row['adjustmentEvidence']
        if not adjustment.get('source') or instant(adjustment['availableAt'])>signal:raise ValueError('缺少信号时点的价格可比依据')
        history=row['history'];previous=None
        if not isinstance(history,list) or len(history)>300:raise ValueError('历史窗口须为不超过300条的列表')
        for bar in history:
            at=instant(bar['at'])
            if previous is not None and at<=previous or not at<=instant(bar['availableAt'])<=signal:raise ValueError('行情时点、顺序或可得性无效')
            previous=at
            o,h,l,c,v=[finite(bar[k]) for k in ('open','high','low','close','volumeShares')]
            if min(o,h,l,c)<=0 or v<0 or not l<=min(o,c)<=max(o,c)<=h or not bar.get('source'):raise ValueError('行情价格、股数或来源无效')
        if len(history)<lookback+vol_window:
            gaps.append(dict(security=row['security'],signalAt=row['signalAt'],reason='前置窗口不足',allFactorsBlocked=True));continue
        values=compute(history,lookback,vol_window)
        results.append(dict(security=row['security'],signalAt=row['signalAt'],values=values))
        label=row.get('label')
        if label is not None:
            start,end,available=[instant(label[k]) for k in ('returnStartAt','returnEndAt','availableAt')]
            if not signal<=start<end<=available<=cutoff or finite(label['forwardReturn'])<-1 or not label.get('source'):raise ValueError('收益标签时点、数值或来源无效')
        for key,value in values.items():
            if value is None:gaps.append(dict(security=row['security'],signalAt=row['signalAt'],factor=key,reason='字段缺失、单边样本、零波动或常数相关；保持未知'));continue
            if label is not None:
                target=dict(signalDate=signal.date().isoformat(),security=row['security'],signalAt=row['signalAt'],factorAvailableAt=row['factorAvailableAt'],universeAvailableAt=row['universeAvailableAt'],membershipAtSignal=True,factor=value,forwardReturn=label['forwardReturn'],returnStartAt=label['returnStartAt'],returnEndAt=label['returnEndAt'],returnAvailableAt=label['availableAt'])
                for k in ('marketCap','industry','exposureAvailableAt'):
                    if k in row:target[k]=row[k]
                panels[key].append(target)
        # Closing signals. Baseline excludes the current bar; no intraday assertion.
        prior=history[-lookback-1:-1];last=history[-1];base_volume=statistics.mean(finite(b['volumeShares']) for b in prior)
        recent_prices=[finite(b['close']) for b in prior];high=finite(last['close'])>max(recent_prices)
        low=finite(last['close'])<min(recent_prices);large=base_volume>0 and finite(last['volumeShares'])>=threshold*base_volume
        kinds=[]
        if high:kinds.append(('new_high','positive'))
        if high and large:kinds.append(('high_price_large_volume','negative'))
        if low and large:kinds.append(('low_price_large_volume','positive'))
        for kind,direction in kinds:
            events.append(dict(id=digest([row['security'],row['signalAt'],kind]),security=row['security'],eventType=kind,direction=direction,signalAt=row['signalAt'],availableAt=row['factorAvailableAt'],observedUntilAt=last['at'],definitionVersion='original-daily-events/1',lookbackRecords=lookback,volumeMultiple=threshold))
    return dict(methodVersion=VERSION,status='computed' if results else 'blocked-no-eligible-samples',conclusion='已生成日频因子与收盘事件；未知值保留，增强版高频方法未实现。' if results else '没有足够窗口生成因子；已保存逐项缺口，未用合成或零值补齐。',factors=results,gaps=gaps,events=events,
      factorDefinitions=[dict(id=k,name=v[0],hypothesisDirection=v[1]) for k,v in FACTORS.items()],
      panelInputs={k:dict(asOf=spec['asOf'],groups=spec.get('groups',5),rows=v,universeDefinition=spec['universeDefinition'],universeVersion=spec['universeVersion'],dataKind=spec['dataKind'],dataVersion=spec['dataVersion'],priceBasis=spec['priceBasis'],returnUnit=spec['returnUnit']) for k,v in panels.items() if v},
      humanRows=[['已计算截面样本',len(results)],['候选因子定义',len(FACTORS)],['未知或阻断记录',len(gaps)],['日频事件',len(events)]],
      limitations=['原创明确口径的实现，不认证券商历史绩效或逐公式复现','RSI两种定义分别留存；不是Wilder递归平滑，不用单边缺样填零','价格/波动占比使用平均秩阈值保留并列值，可能无高位组；与固定等分组版本有差别','本入口不做行业市值中性化；需在验收中声明暴露字段','短窗口新高不是研报240日新高；大单/放量不能证明实际资金身份','历史成员、公司行动、停牌覆盖及来源真实性仍需核验；事件假设不是买卖指令'])
