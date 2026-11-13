"""Execute standalone notebook code cells headlessly, preserving prior artifacts."""
import contextlib
import json
import os
from pathlib import Path
import matplotlib


def main():
    root = Path(__file__).resolve().parent
    notebook = json.loads((root/'bb84_wdm_qiskit.ipynb').read_text(encoding='utf-8'))
    out = root/'results'/'notebook-revalidation'
    out.mkdir(parents=True, exist_ok=True)
    matplotlib.use('Agg')
    namespace = {'__name__': '__main__'}
    previous = Path.cwd()
    count = 0
    try:
        os.chdir(out)
        with (out/'execution.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
            for index, cell in enumerate(notebook['cells']):
                if cell['cell_type'] == 'code':
                    exec(compile(''.join(cell['source']), f'notebook-cell-{index}', 'exec'), namespace)
                    count += 1
    finally:
        os.chdir(previous)
    (out/'status.json').write_text(json.dumps({'code_cells_completed':count,
        'method':'Sequential Python execution, Agg backend; not a Jupyter kernel test'}, indent=2))
    print(f'Completed {count} notebook code cells')


if __name__ == '__main__':
    main()
