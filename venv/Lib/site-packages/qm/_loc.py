import traceback
import os
from pathlib import Path


def _get_loc():
    qm_package_dir = Path(os.path.abspath(__file__)).parent
    trace = [i for i in traceback.extract_stack() if qm_package_dir not in Path(i.filename).parents][-1]
    return 'File "{}", line {}: {} '.format(trace.filename, trace.lineno, trace.line)
