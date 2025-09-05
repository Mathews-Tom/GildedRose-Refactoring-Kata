import io
import sys
import subprocess
import os
from typing import TextIO

from approvaltests import verify

def test_gilded_rose_approvals() -> None:
    orig_sysout: TextIO = sys.stdout
    try:
        fake_stdout = io.StringIO()
        sys.stdout = fake_stdout

        # Run texttest_fixture.py as a subprocess with 30 days
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'texttest_fixture.py'), '30'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )

        answer: str = result.stdout
    finally:
        sys.stdout = orig_sysout

    verify(answer)

if __name__ == "__main__":
    test_gilded_rose_approvals()