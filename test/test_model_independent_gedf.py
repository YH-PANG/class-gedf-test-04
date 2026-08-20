import numpy as np
from classy import Class


PARAMS = {
    "H0": 67.4,
    "omega_b": 0.0224,
    "omega_cdm": 0.120,
    "A_s": 2.1e-9,
    "n_s": 0.965,
    "tau_reio": 0.054,
    "N_ur": 2.0328,
    "N_ncdm": 1,
    "m_ncdm": 0.06,
    "f_gedf": 0.03,
    "use_model_independent_gedf": "yes",
    "wi_gedf": -0.9,
    "wf_gedf": 0.0,
    "zi_gedf": 5000.0,
    "zf_gedf": 500.0,
    "gedf_node_count": 3,
    "gedf_node_z": "3000.0, 1800.0, 900.0",
    "gedf_node_w": "-0.2, 0.3333333333333333, 0.1",
    "gedf_pchip_tension": 0.0,
    "has_gedf_perturbations": "yes",
    "set_const_cs2": "yes",
    "cs2_gedf": 1.0,
    "output": "mPk",
    "P_k_max_1/Mpc": 1.0,
    "z_pk": "0,1",
    "k_output_values": 0.1,
}


def main():
    model = Class()
    model.set(PARAMS)
    model.compute()
    background = model.get_background()
    z = background["z"]
    w = background["(.)w_gedf"]
    rho = background["(.)rho_gedf"]
    rho_tot = background["(.)rho_tot"]

    control_z = np.array([5000.0, 3000.0, 1800.0, 900.0, 500.0])
    control_w = np.array([-0.9, -0.2, 1.0 / 3.0, 0.1, 0.0])
    # CLASS returns background rows from high redshift to z=0, while
    # numpy.interp expects an increasing abscissa.
    recovered_w = np.interp(control_z, z[::-1], w[::-1])
    assert np.max(np.abs(recovered_w - control_w)) < 3.0e-4
    fraction_at_zi = np.interp(5000.0, z[::-1], (rho / rho_tot)[::-1])
    assert abs(fraction_at_zi - 0.03) < 3.0e-5
    assert np.all(np.isfinite(w)) and np.all(np.isfinite(rho))

    scalar = model.get_perturbations()["scalar"][0]
    perturbation_fields = [
        "delta_gedf", "delta_rho_gedf", "rho_plus_p_theta_gedf",
        "delta_p_gedf", "ca2_gedf_output", "u_gedf",
    ]
    for field in perturbation_fields:
        assert np.all(np.isfinite(scalar[field])), field

    print("max control-point |dw|:", np.max(np.abs(recovered_w - control_w)))
    print("f_gedf(zi):", fraction_at_zi)
    print("perturbation samples:", len(scalar["a"]))
    print("all reconstructed GEDF background and perturbation checks passed")
    model.struct_cleanup()
    model.empty()


if __name__ == "__main__":
    main()
