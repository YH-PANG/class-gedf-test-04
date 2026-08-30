"""Evaluate three-bin GEDF background curves with its ABI-matched classy build."""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import sys

import numpy as np
from classy import Class


def evaluate_background(task):
    index, z_grid, row = task
    params = {
        "H0": float(row["H0"]),
        "omega_b": float(row["omega_b"]),
        "omega_cdm": float(row["omega_cdm"]),
        "N_ncdm": 1,
        "m_ncdm": 0.06,
        "N_ur": 2.0308,
        "T_cmb": 2.7255,
        # A numeric value avoids the prebuilt wrapper's obsolete absolute BBN path;
        # YHe does not enter the background quantities used here.
        "YHe": 0.245,
        "use_exp_gedf": "yes",
        "q_gedf": 20.0,
        "w_1": float(row["w_1"]),
        "w_2": float(row["w_2"]),
        "w_3": float(row["w_3"]),
        "z_12": float(row["z_12"]),
        "z_23": float(row["z_23"]),
        "f_gedf": float(row["f_gedf"]),
        "has_gedf_perturbations": "no",
    }
    model = Class()
    try:
        model.set(params)
        model.compute()
        background = model.get_background()
        bg_z = np.asarray(background["z"])
        order = np.argsort(bg_z)
        w_bg = np.asarray(background["(.)w_gedf"])
        f_bg = (
            np.asarray(background["(.)rho_gedf"])
            / np.asarray(background["(.)rho_tot"])
        )
        w_curve = np.interp(z_grid, bg_z[order], w_bg[order])
        f_curve = np.interp(z_grid, bg_z[order], f_bg[order])
        derived_f = model.get_current_derived_parameters(["f_gedf"])["f_gedf"]
        return index, w_curve, f_curve, derived_f
    finally:
        model.struct_cleanup()
        model.empty()


def main(input_path: str, output_path: str) -> None:
    data = np.load(input_path)
    z_grid = data["z"]
    count = len(data["H0"])
    w_curves = np.empty((count, z_grid.size))
    f_curves = np.empty_like(w_curves)
    derived_f = np.empty(count)

    rows = [
        {name: data[name][index] for name in data.files if name != "z"}
        for index in range(count)
    ]
    tasks = [(index, z_grid, rows[index]) for index in range(count)]
    with ProcessPoolExecutor(max_workers=min(4, count)) as executor:
        for completed, (index, w_curve, f_curve, f_value) in enumerate(
            executor.map(evaluate_background, tasks, chunksize=1), start=1
        ):
            w_curves[index] = w_curve
            f_curves[index] = f_curve
            derived_f[index] = f_value
            if completed % 64 == 0 or completed == count:
                print(
                    f"CLASS backgrounds completed: {completed}/{count}", flush=True
                )

    np.savez(
        output_path,
        z=z_grid,
        w_curves=w_curves,
        f_curves=f_curves,
        derived_f=derived_f,
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: gedf_3bins_class_worker.py INPUT.npz OUTPUT.npz")
    main(sys.argv[1], sys.argv[2])
