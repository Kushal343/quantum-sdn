"""Create the portable source/results bundle, excluding local runtimes and secrets."""
from pathlib import Path
import os
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'dist'/'qkd-sdn-linux-project.zip'
    out.parent.mkdir(exist_ok=True)
    excluded={'.git','.cache','.runtime','__pycache__','.pytest_cache','.venv',
              '.venv-sdn','.venv-linux','.agents','.codex','dist','archives'}
    files=[]
    for folder,dirs,names in os.walk(root):
        dirs[:]=[name for name in dirs if name not in excluded]
        for name in names:
            p=Path(folder)/name
            if name=='.env' or name.startswith('.env.') or p.suffix in ('.zip','.pyc','.pyo'):continue
            files.append((p,p.relative_to(root)))
    with ZipFile(out,'w',compression=ZIP_DEFLATED) as archive:
        for p,rel in sorted(files):archive.write(p,Path('qkd-sdn')/rel)
    with ZipFile(out) as archive:
        if archive.testzip() is not None:raise RuntimeError('Archive integrity failure')
        names=set(archive.namelist())
        for needed in ('README.md','linux/README.md','linux/Dockerfile.ryu','sdn/ryu_app.py','qkd_sdn/hybrid.py',
                       'experiments/pareto_experiments.py','tools/report_pareto.py','results/hybrid/FINDINGS.md',
                       'experiments/normal_comparison.py','reports/PROFESSOR_BRIEF.md',
                       'results/normal-comparison/comparison.csv'):
            if 'qkd-sdn/'+needed not in names:raise RuntimeError('Missing bundle member: '+needed)
    print(f'Created {out} ({out.stat().st_size:,} bytes, {len(files)} files)')


if __name__=='__main__':main()
