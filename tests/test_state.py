import tempfile
from pathlib import Path

from src.state import State


def test_state_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "ckpt.sqlite"
        st = State(str(db))
        a = st.get("PRJ")
        assert a == (0, None, None)
        st.update("PRJ", 10, "KEY-1", "2024-01-01")
        b = st.get("PRJ")
        assert b == (10, "KEY-1", "2024-01-01")
