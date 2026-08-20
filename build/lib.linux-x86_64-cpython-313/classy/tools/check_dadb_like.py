#!/usr/bin/env python3
"""Small executable-level regression checks for the DADB-like component."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def read_table(path: Path):
    header = ""
    with path.open() as stream:
        for line in stream:
            if line.startswith("#") and re.search(r"\b1:", line):
                header = line
    names = [x.strip() for x in re.split(r"(?:^|\s+)\d+:", header.lstrip("# ")) if x.strip()]
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data[None, :]
    if len(names) != data.shape[1]:
        raise RuntimeError(f"Could not parse {path} header ({len(names)} names, {data.shape[1]} columns)")
    return {name: data[:, i] for i, name in enumerate(names)}


def run_case(exe: Path, directory: Path, name: str, extra: str):
    root = directory / f"{name}_"
    ini = directory / f"{name}.ini"
    ini.write_text(
        f"""h = 0.68
omega_b = 0.0224
omega_cdm = 0.122541
A_s = 2.1e-9
n_s = 0.965
tau_reio = 0.054
gauge = synchronous
output = tCl,pCl,lCl,mPk
l_max_scalars = 1200
P_k_max_h/Mpc = 0.5
z_pk = 0
k_output_values = 1e-5,0.068,0.136
root = {root}
write background = yes
write parameters = yes
{extra}
"""
    )
    completed = subprocess.run([str(exe), str(ini)], text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"{name} failed:\n{completed.stdout}\n{completed.stderr}")
    background = read_table(next(directory.glob(f"{name}_*background.dat")))
    pk = np.loadtxt(next(directory.glob(f"{name}_*pk.dat")))
    cl = np.loadtxt(next(directory.glob(f"{name}_*cl.dat")))
    perts = sorted(directory.glob(f"{name}_*perturbations_k*_s.dat"))
    return background, pk, cl, [read_table(p) for p in perts]


def expect_failure(exe: Path, directory: Path, name: str, text: str, message: str):
    ini = directory / f"{name}.ini"
    ini.write_text(text)
    completed = subprocess.run([str(exe), str(ini)], text=True, capture_output=True)
    combined = completed.stdout+completed.stderr
    assert completed.returncode != 0 and message in combined, combined


def relmax(a, b, floor=1e-100):
    return float(np.max(np.abs(a-b)/np.maximum(np.maximum(np.abs(a), np.abs(b)), floor)))


def at_z(bg, key, z):
    order = np.argsort(bg["z"])
    return float(np.interp(z, bg["z"][order], bg[key][order]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--class-exe", type=Path, default=Path("./class"))
    args = parser.parse_args()
    exe = args.class_exe.resolve()
    defaults = """dadb_like = yes
dadb_F_d = 0.30
dadb_Delta_e = 0
dadb_z_e = 3500
dadb_p_e = 6
dadb_Delta_l = 0.08
dadb_z_l = 0.43
dadb_p_l = 6
dadb_epsilon_X = 0.25
dadb_z_X = 0.08
dadb_p_X = 20
dadb_perturbation_mode = drag_only
dadb_beta5 = 0.5
dadb_kC_hmpc = 0.05
"""
    with tempfile.TemporaryDirectory(prefix="class_dadb_") as tmp:
        directory = Path(tmp)
        base, pk_base, cl_base, _ = run_case(exe, directory, "base", "dadb_like = no\n")
        off, pk_off, cl_off, _ = run_case(exe, directory, "off", "")
        fzero, pk_fzero, cl_fzero, _ = run_case(
            exe, directory, "fzero", defaults.replace("dadb_F_d = 0.30", "dadb_F_d = 0")
        )
        const, pk_const, cl_const, _ = run_case(
            exe, directory, "const", defaults.replace("dadb_Delta_l = 0.08", "dadb_Delta_l = 0")
            .replace("dadb_epsilon_X = 0.25", "dadb_epsilon_X = 0")
        )
        drag, pk_drag, cl_drag, pert_drag = run_case(exe, directory, "drag", defaults)
        beta0, pk_beta0, _, pert_beta0 = run_case(
            exe, directory, "beta0", defaults.replace("dadb_perturbation_mode = drag_only", "dadb_perturbation_mode = qs_yukawa")
            .replace("dadb_beta5 = 0.5", "dadb_beta5 = 0")
        )
        fifth, pk_fifth, cl_fifth, pert_fifth = run_case(
            exe, directory, "fifth", defaults.replace("dadb_perturbation_mode = drag_only", "dadb_perturbation_mode = qs_yukawa")
        )
        expect_failure(
            exe, directory, "newtonian_rejected",
            "h=0.68\nomega_b=0.0224\nomega_cdm=0.122541\ngauge=newtonian\n"
            +defaults+"output=mPk\n",
            "supports synchronous gauge only",
        )
        expect_failure(
            exe, directory, "negative_x_rejected",
            "h=0.68\nomega_b=0.0224\nomega_cdm=0.8\ngauge=synchronous\n"
            +defaults+"output=mPk\n",
            "non-physical DADB rho_X",
        )

        # Disabled limits and the constant-mass/Lambda-like limit.
        assert relmax(pk_base[:, 1], pk_off[:, 1]) < 1e-13
        assert relmax(cl_base[:, 1:], cl_off[:, 1:]) < 1e-13
        assert relmax(pk_base[:, 1], pk_fzero[:, 1]) < 1e-13
        assert relmax(cl_base[:, 1:], cl_fzero[:, 1:]) < 1e-13
        const_pk_rel = relmax(pk_base[:, 1], pk_const[:, 1])
        const_cl_rel = relmax(cl_base[:, 1:], cl_const[:, 1:])
        assert const_pk_rel < 2e-8, f"constant-limit P(k) mismatch {const_pk_rel}"
        assert const_cl_rel < 2e-8, f"constant-limit C_l mismatch {const_cl_rel}"

        z = drag["z"]
        a = 1/(1+z)
        M = drag["DADB M"]
        q = drag["DADB q"]
        rho_d = drag["(.)rho_dadb_d"]
        rho_X = drag["(.)rho_dadb_X"]
        wX = drag["DADB w_X"]
        H = drag["H [1/Mpc]"]
        rho_tot = drag["(.)rho_tot"]
        order = np.argsort(np.log(a))
        x = np.log(a[order])
        interior = slice(4, -4)
        q_num = np.gradient(np.log(M[order]), x, edge_order=2)
        rd_res = np.gradient(rho_d[order], x, edge_order=2)+3*rho_d[order]-q[order]*rho_d[order]
        rx_res = (np.gradient(rho_X[order], x, edge_order=2)
                  +3*(1+wX[order])*rho_X[order]+q[order]*rho_d[order])
        assert abs(M[-1]-1) < 5e-14
        assert np.max(np.abs(q_num[interior]-q[order][interior])) < 2e-6
        assert np.max(np.abs(rd_res[interior])/np.maximum(rho_d[order][interior], 1e-100)) < 2e-5
        assert np.max(np.abs(rx_res[interior])/np.maximum(rho_X[order][interior], 1e-100)) < 2e-5
        assert abs(H[-1]**2/rho_tot[-1]-1) < 2e-10
        assert np.all(np.isfinite(H)) and np.all(H > 0)
        assert np.all(np.isfinite(M)) and np.all(M > 0)
        assert np.all(np.isfinite(rho_d)) and np.all(rho_d >= 0)
        assert np.all(np.isfinite(rho_X)) and np.all(rho_X >= 0)
        for key, values in drag.items():
            if key.startswith("(.)rho") and "eff" not in key:
                assert np.all(np.isfinite(values)), key

        # Notebook background benchmark.
        iq = int(np.argmax(q))
        mstar = at_z(drag, "DADB M", 1089)
        assert abs(mstar-0.930881) < 2e-6
        assert abs(q[iq]-0.12) < 2e-5
        assert abs(z[iq]-0.43) < 3e-3
        assert abs(drag["DADB w_eff"][-1]+0.75) < 2e-10
        weff = drag["DADB w_eff"]
        rhoeff = drag["(.)rho_dadb_eff"]
        assert np.all(np.isnan(weff[rhoeff <= 0]))
        valid = (z < 3) & (rhoeff > 0) & np.isfinite(weff)
        zv, fv = z[valid], weff[valid]+1
        changes = np.where(fv[:-1]*fv[1:] < 0)[0]
        assert len(changes) > 0
        j = changes[-1]
        zcross = float(zv[j]-fv[j]*(zv[j+1]-zv[j])/(fv[j+1]-fv[j]))
        assert abs(zcross-0.320) < 5e-3

        # Drag sign, fifth-force zero limit, scale response, and horizon window.
        assert q[iq] > 0 and 1+q[iq] > 1  # coefficient of -Hconf theta_d
        assert relmax(pk_drag[:, 1], pk_beta0[:, 1]) < 2e-10
        high = pk_fifth[:, 0] > 0.08*0.68
        assert np.mean(pk_fifth[high, 1]/pk_beta0[high, 1]) > 1
        low0 = pert_beta0[0]["delta_dadb"]
        low5 = pert_fifth[0]["delta_dadb"]
        n_early = max(4, min(len(low0), len(low5))//10)
        assert relmax(low0[:n_early], low5[:n_early], floor=1e-30) < 2e-5

        print("PASS: disabled and F_d=0 limits reproduce baseline")
        print("PASS: constant mass plus epsilon_X=0 reproduces Lambda-like baseline")
        print("PASS: M(1), analytic q, both continuity equations, flatness, and positivity")
        print(f"PASS: notebook background M(z*)={mstar:.8f}, qmax={q[iq]:.8f}, z(qmax)={z[iq]:.5f}, zcross={zcross:.5f}")
        print("PASS: beta5=0 limit, high-k fifth-force enhancement, superhorizon suppression")
        print("PASS: Newtonian gauge and negative physical rho_X are rejected")
        print(f"diagnostic max |Delta H/H| vs baseline = {relmax(H, base['H [1/Mpc]']):.6g}")
        pk_base_on_drag = np.interp(pk_drag[:, 0], pk_base[:, 0], pk_base[:, 1])
        print(f"diagnostic max relative P(k) change (drag) = {relmax(pk_drag[:,1], pk_base_on_drag):.6g}")
        print(f"diagnostic max relative C_l change (drag) = {relmax(cl_drag[:,1:], cl_base[:,1:]):.6g}")
        print(f"diagnostic max relative C_l change (fifth) = {relmax(cl_fifth[:,1:], cl_base[:,1:]):.6g}")
        for zz in (0., 0.5, 1., 1089.):
            print(f"H_DADB/H_base(z={zz:g}) = {at_z(drag,'H [1/Mpc]',zz)/at_z(base,'H [1/Mpc]',zz):.8f}")
        for kh in (0.01, 0.10, 0.20):
            kval = kh*0.68
            p0 = np.interp(kval, pk_base[:, 0], pk_base[:, 1])
            pd = np.interp(kval, pk_drag[:, 0], pk_drag[:, 1])
            p5 = np.interp(kval, pk_fifth[:, 0], pk_fifth[:, 1])
            print(f"P_DADB/P_base(k={kh:.2f} h/Mpc): drag={pd/p0:.8f} fifth={p5/p0:.8f}")
        for ell in (30, 200, 1000):
            c0 = np.interp(ell, cl_base[:, 0], cl_base[:, 1])
            cd = np.interp(ell, cl_drag[:, 0], cl_drag[:, 1])
            print(f"TT_DADB/TT_base(ell={ell}) = {cd/c0:.8f}")


if __name__ == "__main__":
    main()
