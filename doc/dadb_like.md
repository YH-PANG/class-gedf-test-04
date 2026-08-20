# Phenomenological DADB-like component

This branch adds a late-time interacting dark-sector component alongside the
existing independent EDF/GEDF early-dark-energy implementation. It does not
replace, rename, or reuse GEDF. The standard `omega_cdm` input remains today's
total CDM density and is split into uncoupled and coupled populations by
`dadb_F_d`; changing the recombination density in a fit should be done by
varying `omega_cdm` itself.

The background implements the notebook mass ratio `M(a)`, its analytic
logarithmic derivative `q(a)`, and the physical conservation equations

    d rho_d/d ln(a) + 3 rho_d = q rho_d,
    d rho_X/d ln(a) + 3(1+w_X) rho_X = -q rho_d.

`rho_X(1)` is the spatial-flatness residual after enabled standard species and
the existing EDF/GEDF densities are included. Its early value is obtained from
an integrating-factor quadrature and then evolved forward with the normal
CLASS background integrator. Negative physical `rho_X` is rejected unless the
explicit diagnostic-only `dadb_allow_negative_rho_X=yes` override is supplied.

The background columns `rho_dadb_X` and `rho_dadb_eff` must not be confused.
The former is physical intrinsic dark energy. The latter is only the
constant-mass bookkeeping quantity

    rho_dadb_eff = rho_X + F_d rho_c0 a^-3 (M-1).

Accordingly `DADB w_eff = w_X rho_X/rho_dadb_eff` is a diagnostic. CLASS emits
NaN on the non-positive effective-density branch and when cancellation makes
the denominator numerically ill-conditioned; this is not a physical
background singularity. Plotting code should additionally select finite
values, as in the reference notebook.

## Perturbation closure and limitations

Only synchronous gauge is supported. Uncoupled CDM remains present
(`0 <= dadb_F_d < 1`) and fixes the usual synchronous gauge. Coupled CDM is a
separate pressureless perturbation species satisfying

    delta_d' = -theta_d-h'/2,
    theta_d' = -Hconf(1+q) theta_d.

Thus positive `q` adds damping and negative `q` reduces damping. The intrinsic
X component is kept smooth: the background transfer is energy conserving, but
this perturbation prescription is phenomenological and is not a covariant
interacting-fluid completion.

`dadb_perturbation_mode=drag_only` applies only the equations above.
`qs_yukawa` adds the notebook's attractive algebraic force, including its
transition window, Yukawa scale, and a smooth `k^2/(k^2+Hconf^2)` subhorizon
window. In CLASS sign conventions the extra Euler source is
`-3 a^2 rho_d mu5 delta_d/2`; together with `delta_dot=-theta/Hconf` this gives
the desired positive term in the subhorizon growth equation. This closure is
not a covariant realization of a microscopic DADB scalar and should not be
used to infer horizon-scale scalar dynamics.

The fifth force is attractive for non-negative `dadb_beta5`, vanishes exactly
at `beta5=0`, and is absent when both mass-transition amplitudes vanish. The
provided example uses `drag_only`; switch modes explicitly when comparing the
optional fifth-force result.

## Inputs

The defaults when enabled are those in `examples/dadb_like.ini`. The global
default is `dadb_like=no`, which preserves pre-change CLASS/GEDF behavior.
`dadb_F_d=0` is treated as the exact disabled limit. The fully degenerate
`Delta_e=Delta_l=epsilon_X=0` case is likewise reduced exactly to the original
constant-mass CDM plus Lambda representation. Transition powers must be
positive, transition redshifts greater than -1, the mass must remain finite
and positive, and Newtonian gauge is rejected.
