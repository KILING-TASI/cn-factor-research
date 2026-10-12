# SPDX-License-Identifier: MIT
import argparse,json,sys,importlib.util
from pathlib import Path
from . import __version__

def main(argv=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    args=list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('-h','--help'):
        print('量化因子研究：从声明行情核对信号、形态、CNN与试验记录。')
        print('最短教学：cn-factor-research demo --out-dir reports/first-demo')
        print('因子/验收/事件教学：cn-factor-research research-demo --out-dir reports/first-research')
        print('基础入口：daily generate、audit review、event study、plan review、pattern identify/study、panel、trials、catalog、doctor；仅需标准库。')
        print('可选CNN：cnn validate/train/walk-forward/predict/bridge/compare；训练和预测需 [cnn]。')
        print('股票池、复权、单位和时点需明确资料；不自动联网取数或安装，不覆盖旧结果。')
        return 0
    if args[0]=='cnn':
        from .cnn_cli import main as cnn_main
        return cnn_main(args[1:])
    if args[0]=='pattern':
        from .candle_patterns import main as pattern_main
        return pattern_main(args[1:])
    if args[0] in ('panel','trials','factor'):
        from .factor_cli import main as factor_main
        return factor_main(args[1:] if args[0]=='factor' else args)
    if args[0] in ('daily','audit','event','plan'):
        from .review_io import cli
        from .daily_factors import generate
        from .factor_validation import review
        from .event_research import study
        from .method_readiness import review as readiness
        handlers={'daily':({'generate':generate},'日频因子与事件'), 'audit':({'review':review},'因子统一验收'), 'event':({'study':study},'事件研究'),'plan':({'review':readiness},'方法与数据准备核对')}
        routes,title=handlers[args[0]];before=sys.argv
        try:
            sys.argv=[before[0],*args[1:]]
            return cli(routes,title)
        finally:sys.argv=before
    try:
        from ._entry import resources
        root=resources()
        if args[0]=='catalog':
            p=argparse.ArgumentParser(description='已实现因子家族与状态');p.add_argument('--json',action='store_true');a=p.parse_args(args[1:])
            data=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
            if a.json:print(json.dumps(data,ensure_ascii=False,indent=2))
            else:
                for row in data['families']:print(row['name']+'：'+row['status']+'；'+row['scope'])
            return 0
        if args[0]=='doctor':
            p=argparse.ArgumentParser(description='检查软件，不认证数据或模型效果');p.add_argument('--json',action='store_true');a=p.parse_args(args[1:])
            data=dict(repository='cn-factor-research',version=__version__,pythonReady=sys.version_info>=(3,10),
                      resourceDirectory=str(root),torchInstalled=importlib.util.find_spec('torch') is not None,
                      dataChecked=False,networkAccess=False)
            if a.json:print(json.dumps(data,ensure_ascii=False,indent=2))
            else:print('基础功能可运行；CNN可选组件'+('已安装' if data['torchInstalled'] else '未安装')+'。数据和模型效果未核验。')
            return 0 if data['pythonReady'] else 2
        if args[0]=='research-demo':
            p=argparse.ArgumentParser(description='原创合成的日频因子、验收及事件教学');p.add_argument('--out-dir',required=True,type=Path);a=p.parse_args(args[1:])
            if a.out_dir.exists():raise ValueError('输出目录已存在，旧结果保留')
            from .review_io import read,publish
            from .daily_factors import generate
            from .factor_validation import review
            from .event_research import study
            from .method_readiness import review as readiness
            folder=root/'examples/daily-teaching'
            inputs={k:read(folder/(v+'.json')) for k,v in [('daily','daily'),('audit','audit'),('event','events'),('plan','readiness')]}
            print('阶段：检查日频输入并生成原创教学因子。',file=sys.stderr)
            d=generate(inputs['daily']);print('阶段：核对冻结切分、暴露控制与候选重叠。',file=sys.stderr)
            reviewed=review(inputs['audit']);print('阶段：核对事件期限、未知结果和方法准备。',file=sys.stderr)
            e=study(inputs['event']);ready=readiness(inputs['plan'])
            result=dict(methodVersion='original-research-demo/1',dataKind='synthetic-teaching',conclusion='原创合成教学已完成：日频因子、统一验收、事件研究和数据准备核对。',daily=d,audit=reviewed,event=e,readiness=ready,humanRows=[['资料性质','虚构证券与收益；非真实市场'],['日频定义',len(d['factorDefinitions'])],['验收候选',len(reviewed['candidates'])],['未知事件期限记录',len(e['unknown'])],['高频与基本面方法','待数据及实现，不认证就绪']],limitations=['教学检验运行流程，不证明真实选股能力或券商绩效','未知值不补零；事件期限、基准、重复触发与完整缺口见底稿','行业市值残差与因子相关性不证明组合增量；测试不参与重新选型','目标权重成本估算不是实际成交或账户净值','高频、基本面、新闻与行为专门模型尚未实现；方法目录不等于软件就绪'])
            out=publish(inputs,result,a.out_dir,'量化因子研究：日频与事件教学')
            print('原创合成教学报告已生成：'+str(out/'report.html'));return 0
        if args[0]=='demo':
            p=argparse.ArgumentParser(description='原创合成形态教学，零必需依赖');p.add_argument('--out-dir',required=True,type=Path);a=p.parse_args(args[1:])
            from .review_io import read,publish
            from .candle_patterns import identify
            if a.out_dir.exists():raise ValueError('输出目录已存在，旧结果保留')
            spec=read(root/'examples/cnn-teaching/patterns.json');result=identify(spec)
            out=publish(spec,result,a.out_dir,'量化因子研究：形态教学')
            print('原创合成教学报告已生成：'+str(out/'report.html'))
            print('下一步：核对形态条件和未知成交资料；需要CNN对照时安装 [cnn]。')
            return 0
        raise ValueError('未知入口，请用 cn-factor-research --help 查看')
    except (ValueError,KeyError,OSError,TypeError) as error:
        print('未完成：'+str(error),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
