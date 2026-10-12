# SPDX-License-Identifier: MIT
"""Separate implemented software from declared data readiness."""
from .review_io import instant

METHODS={
 'daily-core':(True,['daily_ohlcv','price_basis','calendar','historical_members']),
 'overnight-turnover':(True,['daily_ohlcv','turnover','price_basis','calendar','historical_members']),
 'conditional-price-volatility':(True,['daily_ohlcv','price_basis','calendar','historical_members']),
 'factor-audit':(True,['factor_panel','market_cap','industry','frozen_split']),
 'event-study':(True,['event_evidence','calendar','outcomes','historical_members']),
 'fundamental-valuation':(False,['financial_disclosures','market_cap','financial_scope','disclosure_versions']),
 'fundamental-quality-cashflow':(False,['financial_disclosures','financial_scope','disclosure_versions','industry']),
 'fundamental-growth':(False,['financial_disclosures','financial_scope','disclosure_versions','low_base_controls']),
 'behavior-salience':(False,['daily_ohlcv','market_benchmark','turnover','price_basis','historical_members']),
 'behavior-cost-disposition':(False,['daily_ohlcv','turnover','share_changes','long_warmup','cost_distribution_assumptions']),
 'trend-minute':(False,['minute_ohlcv','turnover','share_changes','market_cap','industry','intraday_sessions']),
 'liquidity-trades':(False,['trades','active_side','millisecond_timestamps','intraday_sessions']),
 'orderbook-flow':(False,['trades','orders','book_snapshots','sequence_alignment','intraday_sessions']),
 'order-lifecycle':(False,['orders','trades','cancellations','original_order_ids','order_lifecycle','sequence_alignment']),
 'opening-auction':(False,['auction_orders','auction_snapshots','auction_phase_rules','sequence_alignment']),
 'market-order-flow':(False,['orders','order_type_history','exchange_order_semantics','sequence_alignment']),
 'news-attention':(False,['news_archive','first_public_at','deduplication','model_version','entity_mapping']),
 'analyst-revision':(False,['forecasts_archive','forecast_vintage','entity_mapping','price_basis']),
 'seconds-frequency':(False,['seconds_ohlcv','intraday_sessions','aggregation_rules']),
 'production-memory-map':(False,['normalized_binary_layout','cold_warm_cache_benchmarks','precision_checks'])}

def review(spec):
    if spec.get('schemaVersion')!='factor-method-readiness/1':raise ValueError('需要factor-method-readiness/1')
    cutoff=instant(spec['asOf']);ids=spec['methods'];cap=spec['capabilities']
    if not isinstance(ids,list) or not ids or len(ids)>len(METHODS) or len(set(ids))!=len(ids):raise ValueError('方法列表须非空唯一')
    if not isinstance(cap,dict):raise ValueError('数据能力须对象')
    for key,row in cap.items():
        if not isinstance(row,dict):raise ValueError('能力明细须对象')
        if row.get('status') not in ('verified','unknown','missing'):raise ValueError('能力状态须verified/unknown/missing')
        if row['status']=='verified':
            if not row.get('source') or not row.get('evidence') or instant(row['verifiedAt'])>cutoff:raise ValueError('已核能力需来源、依据及截止前核对时点')
    out=[]
    for key in ids:
        if key not in METHODS:raise ValueError('未注册的方法：'+str(key))
        implemented,requirements=METHODS[key]
        missing=[r for r in requirements if cap.get(r,{}).get('status')!='verified']
        out.append(dict(method=key,implemented=implemented,requiredCapabilities=requirements,unverifiedCapabilities=missing,dataReadyByDeclaration=not missing,executionReadyByDeclaration=implemented and not missing,status='not-implemented' if not implemented else 'blocked-data' if missing else 'declared-ready-not-certified'))
    return dict(methodVersion='original-method-readiness/1',conclusion='软件实现与数据准备分开核对；目录、研报或字段名称不代表方法已实现。',methods=out,humanRows=[['核对方法',len(out)],['软件已实现',sum(r['implemented'] for r in out)],['按声明可进入调用',sum(r['executionReadyByDeclaration'] for r in out)]],limitations=['这里只检查声明及证据定位，不下载、不解析、不认证数据真实性或许可权利','已实现表示有本仓入口，不表示完整复现对应券商方法或策略绩效','逐笔、订单簿、新闻、财报、一致预期及内存映射平台当前均未实现；有数据也不会标成可执行','数据字段、单位、首次公开时点、重述版本及交易时段仍需各计算入口逐项检查'])
