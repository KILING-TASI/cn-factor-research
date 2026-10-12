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
        print('基础入口：pattern identify/study、panel、trials、catalog、doctor；仅需标准库。')
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
