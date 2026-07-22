#!/usr/bin/env python3
"""Compare fresh and reused classy instances on identical GEDF points."""

import math
import random
import argparse

from classy import Class

from check_gedf_reference_points import REFS, draw


def class_params(values, full=False):
    params = {
        "omega_b": values["omega_b"],
        "omega_cdm": values["omega_cdm"],
        "100*theta_s": values["theta"],
        "A_s": math.exp(values["logA"]) * 1e-10,
        "n_s": values["n_s"],
        "tau_reio": values["tau_reio"],
        "wi_edf": -1.0,
        "wf_edf": 1.0,
        "s_a_gedf": 3.0,
        "ac_gedf": 1.0 / (1.0 + 10.0 ** values["log10z_c"]),
        "f_gedf": values["f_gedf"],
        "wi_gedf_2": -1.0,
        "wf_gedf_2": 1.0,
        "s_a_gedf_2": 3.0,
        "ac_gedf_2": 1.0 / (1.0 + 10.0 ** values["log10z_c_2"]),
        "f_gedf_2": values["f_gedf_2"],
        "N_ncdm": 1,
        "m_ncdm": 0.06,
        "N_ur": 2.0308,
        "T_cmb": 2.7255,
        "YHe": "BBN",
        "recombination": "HyRec",
        "lensing": "no",
        "output": "tCl",
        "l_max_scalars": 20,
    }
    if full:
        params.update({
            "non_linear": "hmcode",
            "hmcode_version": "2020",
            "lensing": "yes",
            "output": "lCl,tCl,pCl,mPk",
            "l_max_scalars": 9500,
            "delta_l_max": 1800,
            "P_k_max_h/Mpc": 100.0,
            "l_logstep": 1.025,
            "l_linstep": 20,
            "perturbations_sampling_stepsize": 0.05,
            "l_switch_limber": 30.0,
            "hyper_sampling_flat": 32.0,
            "l_max_g": 40,
            "l_max_ur": 35,
            "l_max_pol_g": 60,
            "ur_fluid_approximation": 2,
            "ur_fluid_trigger_tau_over_tau_k": 130.0,
            "radiation_streaming_approximation": 2,
            "radiation_streaming_trigger_tau_over_tau_k": 240.0,
            "hyper_flat_approximation_nu": 7000.0,
            "transfer_neglect_delta_k_S_t0": 0.17,
            "transfer_neglect_delta_k_S_t1": 0.05,
            "transfer_neglect_delta_k_S_t2": 0.17,
            "transfer_neglect_delta_k_S_e": 0.17,
            "accurate_lensing": 1,
            "start_small_k_at_tau_c_over_tau_h": 0.0004,
            "start_large_k_at_tau_h_over_tau_k": 0.05,
            "tight_coupling_trigger_tau_c_over_tau_h": 0.005,
            "tight_coupling_trigger_tau_c_over_tau_k": 0.008,
            "start_sources_at_tau_c_over_tau_h": 0.006,
            "l_max_ncdm": 30,
            "tol_ncdm_synchronous": 1e-6,
            "has_gedf_perturbations": "yes",
        })
    return params


def compute(cosmo, params):
    cosmo.set(params)
    cosmo.compute()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--after-full", action="store_true")
    args = parser.parse_args()
    rng = random.Random(20260713)
    points = [
        class_params(
            {name: draw(rng, ref) for name, ref in REFS.items()},
            full=args.full,
        )
        for _ in range(args.n)
    ]

    if args.after_full:
        first = class_params(
            {name: draw(rng, ref) for name, ref in REFS.items()}, full=True
        )
        second = class_params(
            {name: draw(rng, ref) for name, ref in REFS.items()}, full=False
        )
        fresh = Class()
        compute(fresh, second)
        fresh.struct_cleanup()
        fresh.empty()

        reused = Class()
        compute(reused, first)
        compute(reused, second)
        reused.struct_cleanup()
        reused.empty()
        print("fresh second=OK reused after full=OK")
        return 0

    fresh_results = []
    for params in points:
        cosmo = Class()
        try:
            compute(cosmo, params)
            fresh_results.append("OK")
        except Exception as exc:
            fresh_results.append(f"FAIL {exc}")
        finally:
            cosmo.struct_cleanup()
            cosmo.empty()

    reused_results = []
    cosmo = Class()
    for params in points:
        try:
            compute(cosmo, params)
            reused_results.append("OK")
        except Exception as exc:
            reused_results.append(f"FAIL {exc}")
    cosmo.struct_cleanup()
    cosmo.empty()

    for i, (fresh, reused) in enumerate(zip(fresh_results, reused_results)):
        print(f"{i:03d}: fresh={fresh.splitlines()[0]} reused={reused.splitlines()[0]}")

    fresh_ok = sum(result == "OK" for result in fresh_results)
    reused_ok = sum(result == "OK" for result in reused_results)
    print(f"fresh={fresh_ok}/{len(points)} reused={reused_ok}/{len(points)}")
    return not (fresh_ok == reused_ok == len(points))


if __name__ == "__main__":
    raise SystemExit(main())
