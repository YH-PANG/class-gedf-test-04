#!/usr/bin/env python3
"""Probe CLASS shooting at draws from gedf_01.yaml's cosmological refs."""

import argparse
import math
import random
import subprocess
import tempfile
from pathlib import Path


REFS = {
    "omega_b": (0.02237, 0.0003, 0.017, 0.027),
    "omega_cdm": (0.12, 0.0024, 0.09, 0.15),
    "theta": (1.04092, 0.00062, 1.038, 1.044),
    "logA": (3.044, 0.028, 2.6, 3.5),
    "n_s": (0.98, 0.0084, 0.9, 1.1),
    "tau_reio": (0.054, 0.01, 0.0, 0.1),
    "log10z_c": (3.5, 0.05, 3.0, 3.75),
    "f_gedf": (0.1, 0.02, 0.001, 0.5),
    "f_gedf_2": (0.1, 0.02, 0.001, 0.5),
    "log10z_c_2": (3.9, 0.05, 3.75, 4.5),
}


def draw(rng, ref):
    mean, sigma, lower, upper = ref
    while True:
        value = rng.gauss(mean, sigma)
        if lower <= value <= upper:
            return value


def make_ini(values):
    ac1 = 1.0 / (1.0 + 10.0 ** values["log10z_c"])
    ac2 = 1.0 / (1.0 + 10.0 ** values["log10z_c_2"])
    return f"""
omega_b = {values['omega_b']:.17g}
omega_cdm = {values['omega_cdm']:.17g}
100*theta_s = {values['theta']:.17g}
A_s = {math.exp(values['logA']) * 1e-10:.17g}
n_s = {values['n_s']:.17g}
tau_reio = {values['tau_reio']:.17g}
wi_edf = -1
wf_edf = 1
s_a_gedf = 3
ac_gedf = {ac1:.17g}
f_gedf = {values['f_gedf']:.17g}
wi_gedf_2 = -1
wf_gedf_2 = 1
s_a_gedf_2 = 3
ac_gedf_2 = {ac2:.17g}
f_gedf_2 = {values['f_gedf_2']:.17g}
N_ncdm = 1
m_ncdm = 0.06
N_ur = 2.0308
T_cmb = 2.7255
YHe = BBN
recombination = HyRec
lensing = no
output = tCl
l_max_scalars = 20
input_verbose = 0
background_verbose = 0
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260713)
    parser.add_argument("--class-exe", type=Path, default=Path("./class"))
    args = parser.parse_args()
    class_exe = args.class_exe.resolve()
    rng = random.Random(args.seed)
    failures = []

    with tempfile.TemporaryDirectory(prefix="class-gedf-refs-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "output").mkdir()
        ini = tmp_path / "point.ini"
        for index in range(args.n):
            values = {name: draw(rng, ref) for name, ref in REFS.items()}
            ini.write_text(make_ini(values), encoding="ascii")
            result = subprocess.run(
                [str(class_exe), ini.name],
                cwd=tmp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if result.returncode:
                failures.append((index, values, result.stdout))
                print(f"{index:03d}: FAIL")
            else:
                print(f"{index:03d}: OK")

    print(f"success={args.n - len(failures)}/{args.n}")
    for index, values, output in failures[:3]:
        print(f"\nFailure {index}: {values}\n{output[-2000:]}")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
