"""
Strict physical-quantity registry for problem generation and step validation.

Maps variable keys (multi_input JSON field names) to a physical quantity; each quantity has an
expected Pint dimensionality. Adding a new quantity only requires extending ``VARIABLE_KEY_TO_QUANTITY``
and ``QUANTITY_SPECS`` — checkers and prompts consume this single source of truth.

Variable keys are aligned with domains in ``scripts/seed_data/lessons.py`` (gas laws, electrochemistry,
thermochemistry, kinetics, measurement). Prefer explicit keys (e.g. ``r_gas``, ``e_cell``) over
ambiguous single letters.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from app.utils.math_eval import _get_pint_registry, _unit_token_to_pint_expression, normalise_unit_string


class PhysicalQuantityId(StrEnum):
    """Coarse quantity classes (dimension-level); extend as new problem types appear."""

    MOLAR_ENERGY = "molar_energy"  # J/mol, kJ/mol — Ea, ΔH°, ΔG° per mole
    ENERGY = "energy"  # J, kJ, cal — heat q, work, etc.
    MOLAR_MASS = "molar_mass"  # g/mol
    MASS = "mass"  # g, kg, ...
    # J/(mol·K) — molar Cp/Cv and ideal gas constant R share this dimension
    MOLAR_HEAT_CAPACITY = "molar_heat_capacity"
    SPECIFIC_HEAT_CAPACITY = "specific_heat_capacity"  # J/(g·K) — calorimetry (lessons: thermochem)
    TEMPERATURE = "temperature"  # K, °C
    MOLARITY = "molarity"  # M, mM, ...
    RATE_CONSTANT = "rate_constant"  # s^-1, M/s, ...
    PRESSURE = "pressure"
    VOLUME = "volume"  # L, mL — gas laws / solutions (lessons: gas laws, stoichiometry)
    DENSITY = "density"  # g/mL, g/cm³ — intro measurement, DA
    ELECTRIC_POTENTIAL = "electric_potential"  # V — electrochemistry (lessons: ΔG°/E°cell)
    ELECTRIC_CURRENT = "electric_current"  # A — electrolysis
    CHARGE_PER_MOLE = "charge_per_mole"  # C/mol — Faraday F
    DIMENSIONLESS = "dimensionless"


@dataclass(frozen=True)
class PhysicalQuantitySpec:
    """Human-readable metadata + Pint reference string for dimensionality equality."""

    id: PhysicalQuantityId
    pint_reference: str
    generator_allowed_units_line: str
    wrong_dimension_hint: str


QUANTITY_SPECS: dict[PhysicalQuantityId, PhysicalQuantitySpec] = {
    PhysicalQuantityId.MOLAR_ENERGY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.MOLAR_ENERGY,
        pint_reference="joule/mole",
        generator_allowed_units_line=(
            "Molar energy (activation energy $E_a$, $\\Delta H$, $\\Delta G$, etc.): **only** "
            "`J/mol` or `kJ/mol` — never bare `J` or `kJ` (those are not per-mole)."
        ),
        wrong_dimension_hint=(
            "This quantity is a molar energy: use J/mol or kJ/mol, not J or kJ alone."
        ),
    ),
    PhysicalQuantityId.ENERGY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.ENERGY,
        pint_reference="joule",
        generator_allowed_units_line="Energy (heat q, work): `J`, `kJ`, `cal`, `kcal` as appropriate.",
        wrong_dimension_hint="Check that your energy unit matches the quantity (e.g. J or kJ for heat).",
    ),
    PhysicalQuantityId.MOLAR_MASS: PhysicalQuantitySpec(
        id=PhysicalQuantityId.MOLAR_MASS,
        pint_reference="gram/mole",
        generator_allowed_units_line="Molar mass: `g/mol` (or `kg/mol` if appropriate).",
        wrong_dimension_hint="Molar mass must include per mole (e.g. g/mol).",
    ),
    PhysicalQuantityId.MASS: PhysicalQuantitySpec(
        id=PhysicalQuantityId.MASS,
        pint_reference="gram",
        generator_allowed_units_line="Mass: `g`, `kg`, `mg`, …",
        wrong_dimension_hint="Check your mass unit (g, kg, …).",
    ),
    PhysicalQuantityId.MOLAR_HEAT_CAPACITY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
        pint_reference="joule/(mole*kelvin)",
        generator_allowed_units_line=(
            "Molar quantity in J/(mol·K): molar heat capacity $C_p$, or gas constant $R$ — "
            "same dimensions; use `J/(mol·K)` (not J/K or bare J)."
        ),
        wrong_dimension_hint="Use J/(mol·K) (molar heat capacity or gas constant R).",
    ),
    PhysicalQuantityId.SPECIFIC_HEAT_CAPACITY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.SPECIFIC_HEAT_CAPACITY,
        pint_reference="joule/(gram*kelvin)",
        generator_allowed_units_line="Specific heat: `J/(g·K)` or `J/(g·°C)` (magnitude) — not J/mol.",
        wrong_dimension_hint="Specific heat uses per gram (e.g. J/(g·K)), not per mole.",
    ),
    PhysicalQuantityId.TEMPERATURE: PhysicalQuantitySpec(
        id=PhysicalQuantityId.TEMPERATURE,
        pint_reference="kelvin",
        generator_allowed_units_line="Temperature: `K` (or `°C`/`°F` if the problem states it).",
        wrong_dimension_hint="Check your temperature unit.",
    ),
    PhysicalQuantityId.MOLARITY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.MOLARITY,
        pint_reference="mole/liter",
        generator_allowed_units_line="Concentration: `M`, `mM`, `μM`, … as appropriate.",
        wrong_dimension_hint="Check your concentration unit.",
    ),
    PhysicalQuantityId.RATE_CONSTANT: PhysicalQuantitySpec(
        id=PhysicalQuantityId.RATE_CONSTANT,
        pint_reference="1/second",
        generator_allowed_units_line=(
            "Rate constant: choose units consistent with the rate law (order sets the dimensions)."
        ),
        wrong_dimension_hint="Check that your rate constant unit matches the reaction order.",
    ),
    PhysicalQuantityId.PRESSURE: PhysicalQuantitySpec(
        id=PhysicalQuantityId.PRESSURE,
        pint_reference="pascal",
        generator_allowed_units_line="Pressure: `atm`, `kPa`, `mmHg`, `torr`, `bar`, …",
        wrong_dimension_hint="Check your pressure unit.",
    ),
    PhysicalQuantityId.VOLUME: PhysicalQuantitySpec(
        id=PhysicalQuantityId.VOLUME,
        pint_reference="liter",
        generator_allowed_units_line="Volume: `L`, `mL`, `cm³` as appropriate to the problem.",
        wrong_dimension_hint="Check your volume unit (L, mL, …).",
    ),
    PhysicalQuantityId.DENSITY: PhysicalQuantitySpec(
        id=PhysicalQuantityId.DENSITY,
        pint_reference="gram/milliliter",
        generator_allowed_units_line="Density: `g/mL`, `g/cm³`, `kg/L` — match the statement’s units.",
        wrong_dimension_hint="Density is mass per volume (e.g. g/mL).",
    ),
    PhysicalQuantityId.ELECTRIC_POTENTIAL: PhysicalQuantitySpec(
        id=PhysicalQuantityId.ELECTRIC_POTENTIAL,
        pint_reference="volt",
        generator_allowed_units_line="Cell or electrode potential: `V` (volts) — e.g. $E^\\circ_{\\text{cell}}$, $E_{\\text{cell}}$.",
        wrong_dimension_hint="Potential must be in volts (V).",
    ),
    PhysicalQuantityId.ELECTRIC_CURRENT: PhysicalQuantitySpec(
        id=PhysicalQuantityId.ELECTRIC_CURRENT,
        pint_reference="ampere",
        generator_allowed_units_line="Current: `A` (amperes).",
        wrong_dimension_hint="Current must be in amperes (A).",
    ),
    PhysicalQuantityId.CHARGE_PER_MOLE: PhysicalQuantitySpec(
        id=PhysicalQuantityId.CHARGE_PER_MOLE,
        pint_reference="coulomb/mole",
        generator_allowed_units_line="Charge per mole (Faraday): `C/mol`.",
        wrong_dimension_hint="Use charge per mole (e.g. C/mol) for Faraday-type constants.",
    ),
    PhysicalQuantityId.DIMENSIONLESS: PhysicalQuantitySpec(
        id=PhysicalQuantityId.DIMENSIONLESS,
        pint_reference="dimensionless",
        generator_allowed_units_line='Unitless quantities: use "" for unit when none applies.',
        wrong_dimension_hint="This value should be dimensionless.",
    ),
}


# Multi_input JSON keys (normalized) → quantity. Covers variables implied by
# ``scripts/seed_data/lessons.py`` domains (gas laws, electrochemistry, thermochem, etc.).
VARIABLE_KEY_TO_QUANTITY: dict[str, PhysicalQuantityId] = {
    # Activation / thermo (molar): Arrhenius, ΔH°, ΔG°, ΔU°
    "ea": PhysicalQuantityId.MOLAR_ENERGY,
    "e_a": PhysicalQuantityId.MOLAR_ENERGY,
    "activationenergy": PhysicalQuantityId.MOLAR_ENERGY,
    "activation_energy": PhysicalQuantityId.MOLAR_ENERGY,
    "deltah": PhysicalQuantityId.MOLAR_ENERGY,
    "delta_h": PhysicalQuantityId.MOLAR_ENERGY,
    "deltag": PhysicalQuantityId.MOLAR_ENERGY,
    "delta_g": PhysicalQuantityId.MOLAR_ENERGY,
    "dg": PhysicalQuantityId.MOLAR_ENERGY,
    "dh": PhysicalQuantityId.MOLAR_ENERGY,
    "deltau": PhysicalQuantityId.MOLAR_ENERGY,
    "delta_u": PhysicalQuantityId.MOLAR_ENERGY,
    "deltah0": PhysicalQuantityId.MOLAR_ENERGY,
    "deltag0": PhysicalQuantityId.MOLAR_ENERGY,
    "deltahrxn": PhysicalQuantityId.MOLAR_ENERGY,
    "deltagrxn": PhysicalQuantityId.MOLAR_ENERGY,
    # Heat (extensive): coffee-cup calorimetry, q
    "q": PhysicalQuantityId.ENERGY,
    "heat": PhysicalQuantityId.ENERGY,
    "work": PhysicalQuantityId.ENERGY,
    "w": PhysicalQuantityId.ENERGY,
    # Mass / molar mass: mole lesson, stoichiometry
    "m": PhysicalQuantityId.MASS,
    "mass": PhysicalQuantityId.MASS,
    "mm": PhysicalQuantityId.MOLAR_MASS,
    "molar_mass": PhysicalQuantityId.MOLAR_MASS,
    "mw": PhysicalQuantityId.MOLAR_MASS,
    # Gas constant R (same dimension as molar Cp): J/(mol·K) — avoid bare "r" (radius ambiguity)
    "r_gas": PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
    "rgas": PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
    # Molar heat capacity
    "cp": PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
    "molar_cp": PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
    "molarheatcapacity": PhysicalQuantityId.MOLAR_HEAT_CAPACITY,
    # Specific heat (thermochem)
    "csp": PhysicalQuantityId.SPECIFIC_HEAT_CAPACITY,
    "specific_heat": PhysicalQuantityId.SPECIFIC_HEAT_CAPACITY,
    "specificheat": PhysicalQuantityId.SPECIFIC_HEAT_CAPACITY,
    # Temperature: Arrhenius, gas law
    "t1": PhysicalQuantityId.TEMPERATURE,
    "t2": PhysicalQuantityId.TEMPERATURE,
    "temp": PhysicalQuantityId.TEMPERATURE,
    # Concentration
    "concentration": PhysicalQuantityId.MOLARITY,
    # Gas laws / stoichiometry volume
    "volume": PhysicalQuantityId.VOLUME,
    "vol": PhysicalQuantityId.VOLUME,
    # Density (measurement, DA)
    "density": PhysicalQuantityId.DENSITY,
    "rho": PhysicalQuantityId.DENSITY,
    # Electrochemistry: E°cell, electrolysis
    "ecell": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e_cell": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e0": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e_cathode": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e_anode": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e_red": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "e_ox": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "voltage": PhysicalQuantityId.ELECTRIC_POTENTIAL,
    "current": PhysicalQuantityId.ELECTRIC_CURRENT,
    "faraday": PhysicalQuantityId.CHARGE_PER_MOLE,
    "faraday_constant": PhysicalQuantityId.CHARGE_PER_MOLE,
    "f_const": PhysicalQuantityId.CHARGE_PER_MOLE,
    # Pressure (avoid bare "p")
    "p1": PhysicalQuantityId.PRESSURE,
    "p2": PhysicalQuantityId.PRESSURE,
}


def normalize_variable_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (key or "").lower())


def quantity_for_variable_key(key: str) -> PhysicalQuantityId | None:
    """Return the strict physical quantity for a multi_input field key, or None if unknown."""
    nk = normalize_variable_key(key)
    if nk in VARIABLE_KEY_TO_QUANTITY:
        return VARIABLE_KEY_TO_QUANTITY[nk]
    if nk.startswith("ea") or "activation" in nk:
        return PhysicalQuantityId.MOLAR_ENERGY
    if nk.startswith("delta") and ("h" in nk or "g" in nk or "u" in nk):
        return PhysicalQuantityId.MOLAR_ENERGY
    return None


@lru_cache(maxsize=len(PhysicalQuantityId))
def expected_dimensionality(qty: PhysicalQuantityId):
    spec = QUANTITY_SPECS[qty]
    ureg = _get_pint_registry()
    return ureg(spec.pint_reference).dimensionality


# Normalised unit substring → Pint expression string (compound and single-token chem units).
_UNIT_TO_PINT_EXPR: dict[str, str] = {
    "j": "joule",
    "kj": "kilojoule",
    "cal": "calorie",
    "kcal": "kilocalorie",
    "ev": "electron_volt",
    "j/mol": "joule/mole",
    "kj/mol": "kilojoule/mole",
    "cal/mol": "calorie/mole",
    "g/mol": "gram/mole",
    "kg/mol": "kilogram/mole",
    "j/(mol*k)": "joule/(mole*kelvin)",
    "j/mol*k": "joule/mole/kelvin",
    "j/(mol·k)": "joule/(mole*kelvin)",
    "m/s": "meter/second",
    "m/s^2": "meter/second**2",
    "m/s**2": "meter/second**2",
    "g": "gram",
    "kg": "kilogram",
    "mg": "milligram",
    "mol": "mole",
    "k": "kelvin",
    "meter": "meter",
    "s": "second",
    "s^-1": "1/second",
    "s**-1": "1/second",
    "atm": "atmosphere",
    "kpa": "kilopascal",
    "pa": "pascal",
    "mmhg": "mercury_mm",
    "torr": "torr",
    "bar": "bar",
    "l": "liter",
    "ml": "milliliter",
    "liter": "liter",
    "volt": "volt",
    "v": "volt",
    "ampere": "ampere",
    "g/ml": "gram/milliliter",
    "g/cm3": "gram/centimeter**3",
    "g/cm^3": "gram/centimeter**3",
    "c/mol": "coulomb/mole",
    "j/g/k": "joule/gram/kelvin",
    "j/(g*k)": "joule/gram/kelvin",
}


def quantity_from_value_and_unit(value: float, unit_str: str):
    """
    Build a Pint quantity from a numeric magnitude and a chemistry unit string.

    Resolution order matches ``unit_dimensionality``: registry compound map, then
    ``math_eval._unit_token_to_pint_expression``, then raw Pint parsing.
    """
    if not unit_str or not str(unit_str).strip():
        return None
    raw = str(unit_str).strip()
    key = normalise_unit_string(raw).replace(" ", "")
    if not key:
        return None
    expr = _UNIT_TO_PINT_EXPR.get(key)
    if expr is None:
        expr = _unit_token_to_pint_expression(raw)
    ureg = _get_pint_registry()
    if expr:
        try:
            return ureg.Quantity(value, expr)
        except Exception:
            pass
    try:
        return ureg.Quantity(value, raw)
    except Exception:
        try:
            return ureg.Quantity(value, key.replace("/", " / "))
        except Exception:
            return None


def unit_dimensionality(unit_str: str) -> dict | None:
    """
    Map a student/canonical unit string to Pint dimensionality, or None if unknown.

    Uses normalise_unit_string + a compound-unit table + Pint parsing.
    """
    q = quantity_from_value_and_unit(1.0, unit_str)
    return None if q is None else q.dimensionality


def unit_matches_quantity(unit_str: str, qty: PhysicalQuantityId) -> bool:
    """True if the unit string's dimensionality matches the registry quantity."""
    if qty == PhysicalQuantityId.DIMENSIONLESS:
        d = unit_dimensionality(unit_str)
        if d is None:
            return not str(unit_str).strip()
        return d == expected_dimensionality(PhysicalQuantityId.DIMENSIONLESS)
    d = unit_dimensionality(unit_str)
    if d is None:
        return False
    return d == expected_dimensionality(qty)


def build_generator_registry_prompt_block() -> str:
    """Inject into problem-generation prompts: quantity-first unit rules (no generic Energy list)."""
    lines = [
        "### PHYSICAL QUANTITY REGISTRY (MANDATORY) ###",
        "For every `inputFields` row you MUST assign a physical quantity by choosing the variable label",
        "and unit together. Do NOT pick units from a vague category like “Energy: J, kJ”.",
        "Match the variable to exactly one line below; the `unit` MUST be drawn **only** from that line.",
        "",
    ]
    for spec in QUANTITY_SPECS.values():
        lines.append(f"- **{spec.id.value}**: {spec.generator_allowed_units_line}")
    lines.append("")
    lines.append(
        "If you introduce a new named variable not covered above, choose the closest quantity line "
        "and a unit with the correct dimensions (e.g. Newton-meters vs joules for energy)."
    )
    return "\n".join(lines)
