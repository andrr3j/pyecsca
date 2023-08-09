import numpy as np
from pyecsca.sca import Trace


def test_basic():
    trace = Trace(np.array([10, 15, 24], dtype=np.dtype("i1")))
    assert trace is not None
    assert "Trace" in str(trace)
    assert trace.trace_set is None
