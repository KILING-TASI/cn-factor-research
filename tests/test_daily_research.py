# SPDX-License-Identifier: MIT
import copy,json,math
from pathlib import Path
import pytest
from cn_factor_research.daily_factors import compute,generate
from cn_factor_research.factor_validation import review,residuals,trading_diagnostics
from cn_factor_research.event_research import study

ROOT=Path(__file__).resolve().parents[1]/'examples/daily-teaching'
def sample(name):return json.loads((ROOT/(name+'.json')).read_text(encoding='utf-8'))

def test_momentum_reversal_and_rsi_manual():
    bars=[dict(open=2**i,close=2**i,turnover=.01) for i in range(7)]
    result=compute(bars,5,2)
    assert result['momentum']==31 and result['reversal']==-31
    assert result['rsi_gain_share']==100 and result['rsi_conditional_mean'] is None
    assert result['overnight_turnover_corr'] is None
    assert result['high_price_vol_share'] is None and result['high_vol_price_share'] is None

def test_gap_uses_previous_turnover():
    bars=[]
    for i in range(7):bars.append(dict(close=10+i,open=(9+i)*(1+i*.01),turnover=float(i)))
    assert compute(bars,5,2)['overnight_turnover_corr']==pytest.approx(1)

def test_generate_all_families_and_declared_labels():
    out=generate(sample('daily'))
    assert len(out['factors'])==108 and len(out['panelInputs'])==8
    assert out['panelInputs']['momentum']['dataVersion']=='original-daily-teaching/1'

def test_missing_turnover_is_unknown_not_zero():
    s=sample('daily');s['rows'][0]['history'][-2].pop('turnover')
    r=generate(s)
    assert r['factors'][0]['values']['overnight_turnover_corr'] is None
    assert len(r['panelInputs']['overnight_turnover_corr']['rows'])==107

def test_missing_warmup_preserves_blocked_row():
    s=sample('daily');s['rows'][0]['history']=s['rows'][0]['history'][-20:]
    r=generate(s);assert len(r['factors'])==107 and r['gaps'][0]['allFactorsBlocked']

def test_all_windows_blocked_never_claims_factors_generated():
    s=sample('daily')
    for r in s['rows']:r['history']=r['history'][-20:]
    r=generate(s);assert r['status']=='blocked-no-eligible-samples' and r['panelInputs']=={}

@pytest.mark.parametrize('attack',[lambda s:s['rows'][0].update(factorAvailableAt='2030-01-01T16:00:00+08:00'),lambda s:s['rows'][0].update(membershipAtSignal=False),lambda s:s['rows'][0]['history'][-1].update(availableAt='2030-01-01T16:00:00+08:00'),lambda s:s['rows'][0]['history'][-1].update(volumeShares=True),lambda s:s['rows'][0]['history'][-1].update(high=1),lambda s:s['rows'][0]['history'].reverse(),lambda s:s['rows'][0]['adjustmentEvidence'].update(availableAt='2030-01-01T16:00:00+08:00'),lambda s:s.update(returnUnit='percent'),lambda s:s['parameters'].update(lookbackRecords=True)])
def test_daily_attacks(attack):
    s=sample('daily');attack(s)
    with pytest.raises(ValueError):generate(s)

def test_equivalent_timezone_duplicate_rejected():
    s=sample('daily');r=copy.deepcopy(s['rows'][0]);r['signalAt']='2024-02-10T08:00:00+00:00';s['rows'].append(r)
    with pytest.raises(ValueError):generate(s)

def test_negative_and_positive_events_are_separate():
    s=sample('daily');r=s['rows'][0];b=r['history'][-1];b.update(open=100,close=101,high=102,low=99,volumeShares=100000)
    result=generate(s);events=[e for e in result['events'] if e['security']==r['security'] and e['signalAt']==r['signalAt']]
    assert {e['direction'] for e in events}=={'positive','negative'}
    assert {e['eventType'] for e in events}=={'new_high','high_price_large_volume'}

def test_ols_removes_known_linear_exposure():
    rows=[dict(marketCap=math.exp(i*.2),industry='a' if i%2 else 'b',factor=2+3*i*.2+4*(i%2)) for i in range(12)]
    assert residuals(rows)==[0.0]*12

def test_ols_residual_is_orthogonal():
    rows=[dict(marketCap=math.exp(i*.2),industry='a' if i%2 else 'b',factor=math.sin(i)) for i in range(12)]
    r=residuals(rows)
    assert sum(r)==pytest.approx(0,abs=1e-10)
    assert sum(v*math.log(row['marketCap']) for v,row in zip(r,rows))==pytest.approx(0,abs=1e-10)
    assert sum(v for v,row in zip(r,rows) if row['industry']=='a')==pytest.approx(0,abs=1e-10)

def test_audit_retains_raw_and_neutralized():
    r=review(sample('audit'));assert len(r['candidates'])==8
    assert all(set(c['versions'])=={'raw','neutralized'} for c in r['candidates'])
    assert r['candidates'][0]['versions']['raw']['stages']['test']['tradingDiagnostics'][0]['estimatedCostDrag'] is None
    assert len(r['pairwiseFactorCorrelation'])==28

def test_redundant_factors_expose_pairwise_overlap():
    s=sample('audit');s['candidates']=s['candidates'][:2]
    s['candidates'][1]=copy.deepcopy(s['candidates'][0]);s['candidates'][1]['id']='duplicate-definition'
    r=review(s)
    assert r['pairwiseFactorCorrelation'][0]['stages']['test']['meanRankCorrelation']==pytest.approx(1)

def test_unimplemented_method_never_becomes_execution_ready():
    from cn_factor_research.method_readiness import review as readiness,METHODS
    requirements=METHODS['liquidity-trades'][1]
    s=dict(schemaVersion='factor-method-readiness/1',asOf='2024-01-02T16:00:00+08:00',methods=['liquidity-trades'],capabilities={k:dict(status='verified',source='fixture',evidence='fixture',verifiedAt='2024-01-01T16:00:00+08:00') for k in requirements})
    r=readiness(s)['methods'][0]
    assert r['dataReadyByDeclaration'] and not r['executionReadyByDeclaration'] and r['status']=='not-implemented'

def test_missing_data_not_zero_or_ready():
    from cn_factor_research.method_readiness import review as readiness
    s=dict(schemaVersion='factor-method-readiness/1',asOf='2024-01-02T16:00:00+08:00',methods=['daily-core'],capabilities={})
    assert readiness(s)['methods'][0]['status']=='blocked-data'

def test_readiness_future_evidence_rejected():
    from cn_factor_research.method_readiness import review as readiness
    s=dict(schemaVersion='factor-method-readiness/1',asOf='2024-01-02T16:00:00+08:00',methods=['daily-core'],capabilities={'daily_ohlcv':dict(status='verified',source='fixture',evidence='fixture',verifiedAt='2030-01-01T16:00:00+08:00')})
    with pytest.raises(ValueError):readiness(s)

@pytest.mark.parametrize('attack',[lambda s:s.update(testTouchedDuringSelection=True),lambda s:s.update(selectionFrozenAt=s['split']['testStart']),lambda s:s['candidates'][1]['panel']['rows'].pop(),lambda s:s['candidates'][1]['panel'].update(priceBasis='different'),lambda s:s['candidates'][1]['panel']['rows'][0].update(forwardReturn=.5),lambda s:s['candidates'][0].update(direction=True),lambda s:s.update(oneWayCostBps=-1),lambda s:s['candidates'][0]['panel'].update(dataVersion='other')])
def test_audit_attacks(attack):
    s=sample('audit');attack(s)
    with pytest.raises(ValueError):review(s)

def test_unknown_exposure_blocks_only_neutralization():
    s=sample('audit');s['candidates'][0]['panel']['rows'][0].pop('industry');r=review(s)
    assert r['candidates'][0]['neutralizationBlocked'] and set(r['candidates'][0]['versions'])=={'raw'}

def test_labels_crossing_next_stage_are_purged():
    s=sample('audit');s['candidates']=s['candidates'][:1]
    for r in s['candidates'][0]['panel']['rows'][:12]:r['returnAvailableAt']=s['split']['validationStart']
    out=review(s);assert len(out['candidates'][0]['versions']['raw']['purged'])==12

def test_turnover_and_cost_manual():
    p=dict(groups=2,rows=[dict(signalDate=day,security=code,factor=value) for day,values in [('a',[0,1,2,3]),('b',[3,2,1,0])] for code,value in enumerate(values)])
    r=trading_diagnostics(p,1,10)
    assert r[0]['oneWayTurnover'] is None
    assert r[1]['oneWayTurnover']==1 and r[1]['estimatedCostDrag']==pytest.approx(.002)

def test_event_cooldown_unknown_and_excess_manual():
    r=study(sample('events'));assert len(r['retainedEventIds'])==3 and len(r['suppressed'])==1
    one,five=r['statistics'];assert one['knownCount']==3 and one['meanReturn']==pytest.approx((-.01+.01+.02)/3)
    assert one['meanExcessReturn']==pytest.approx((-.015+.005+.015)/3)
    assert five['totalEvents']==3 and five['unknownCount']==3 and five['meanReturn'] is None

def test_keep_all_has_no_implicit_cooldown():
    s=sample('events');s.update(repeatPolicy='keep-all',cooldownRecords=0)
    assert len(study(s)['retainedEventIds'])==4

@pytest.mark.parametrize('attack',[lambda s:s['events'][0].update(observedUntilAt='2030-01-01T16:00:00+08:00'),lambda s:s['events'][0].update(nextSessionOpenAt=s['events'][0]['signalAt']),lambda s:s['events'][0]['outcomes'][0].update(benchmarkEndAt='2024-03-01T16:00:00+08:00'),lambda s:s['events'][0]['outcomes'][1].update(forwardReturn=0),lambda s:s['events'][0]['outcomes'].append(copy.deepcopy(s['events'][0]['outcomes'][0])),lambda s:s['events'][1].update(signalRecord=30),lambda s:s['events'][1].update(definitionVersion='other'),lambda s:s['events'][0].update(membershipAtSignal=False),lambda s:s.update(horizons=[True,5])])
def test_event_attacks(attack):
    s=sample('events');attack(s)
    with pytest.raises(ValueError):study(s)

def test_late_outcome_retained_as_unknown():
    s=sample('events');s['events'][0]['outcomes'][0]['availableAt']='2030-01-01T16:00:00+08:00'
    r=study(s);assert r['statistics'][0]['knownCount']==2 and r['statistics'][0]['totalEvents']==3

def test_numeric_overflow_is_not_published_as_factor():
    bars=[dict(open=1,close=1,turnover=.1) for _ in range(7)];bars[0]['close']=1e-300;bars[1]['close']=1e300
    with pytest.raises(ValueError):compute(bars,5,2)

def test_mixed_signal_times_in_same_cross_section_rejected():
    s=sample('audit');s['candidates']=s['candidates'][:1]
    for r in s['candidates'][0]['panel']['rows']:r['returnStartAt']='2024-03-10T16:00:00+08:00';r['returnEndAt']='2024-03-11T16:00:00+08:00';r['returnAvailableAt']='2024-03-11T16:00:00+08:00'
    s['candidates'][0]['panel']['rows'][0]['signalAt']='2024-02-10T17:00:00+08:00'
    with pytest.raises(ValueError):review(s)
