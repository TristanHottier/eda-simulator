import subprocess
import tempfile
import os

os.environ['SPICE_LIB_DIR'] = r'C:\ngspice\Spice64\share\ngspice\scripts'

netlist = """* Test
V1 in 0 DC 5
R1 in out 1k
R2 out 0 1k
.op
.control
run
print all
.endc
.end
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False) as f:
    f.write(netlist)
    path = f.name

r = subprocess.run(
    [r'C:\ngspice\Spice64\bin\ngspice.exe', '-b', path],
    capture_output=True,
    text=True
)

print('=== STDOUT ===')
print(r.stdout[: 1000] if r.stdout else '(empty)')
print('=== STDERR ===')
print(r.stderr[:500] if r.stderr else '(empty)')
print(f'=== Return code: {r.returncode} ===')
os.unlink(path)