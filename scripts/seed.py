"""
Seed script — Master Lesson Library v2.

Architecture:
  MASTER_LESSONS  — single source of truth, keyed by stable slug
  STANDARD_UNITS  — 15 Standard Chemistry units (non-AP-only lessons)
  AP_UNITS        — 9 College Board AP units (shared + AP-only lessons)
  unit_lessons    — junction table for per-unit lesson ordering

Run after migrations:
  python -m scripts.seed
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.database.models import Course, Grade, Interest, Lesson, Unit, UnitLesson

settings = get_settings()


# ══════════════════════════════════════════════════════════════
# MASTER LESSON LIBRARY
# canonical_unit / canonical_index = mastery-tracking key (stored in DB as chapter_id / topic_index)
# ══════════════════════════════════════════════════════════════

MASTER_LESSONS: dict[str, dict] = {
    # ── Introduction to Chemistry ─────────────────────────────
    "L-intro-safety":                {"title": "Safety",                                    "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify common lab safety rules", "Recognize hazard symbols"],                                   "canonical_unit": "unit-intro-chem", "canonical_index": 0},
    "L-intro-scientific-method":     {"title": "Scientific Method",                         "is_ap_only": False, "key_equations": [],                                          "objectives": ["Describe steps of the scientific method", "Distinguish hypothesis from theory"],                   "canonical_unit": "unit-intro-chem", "canonical_index": 1},
    "L-intro-classification-matter": {"title": "Classification of Matter",                  "is_ap_only": False, "key_equations": [],                                          "objectives": ["Classify matter as element, compound, or mixture", "Distinguish pure substances from mixtures"],   "canonical_unit": "unit-intro-chem", "canonical_index": 2},
    "L-intro-chem-phys-changes":     {"title": "Chemical & Physical Changes",               "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify chemical vs physical changes", "Give examples of each type"],                            "canonical_unit": "unit-intro-chem", "canonical_index": 3},
    "L-intro-measurement":           {"title": "Measurement & Scientific Notation",         "is_ap_only": False, "key_equations": ["1 km = 1000 m", "a × 10ⁿ"],               "objectives": ["Use SI units and metric prefixes", "Express numbers in scientific notation"],                      "canonical_unit": "unit-intro-chem", "canonical_index": 4},

    # ── Atomic Theory & Structure ─────────────────────────────
    "L-atomic-history":              {"title": "History & Basics of Atomic Theory",         "is_ap_only": False, "key_equations": [],                                          "objectives": ["Trace development of the atomic model", "Describe contributions of key scientists"],              "canonical_unit": "unit-atomic-theory", "canonical_index": 0},
    "L-atomic-structure":            {"title": "Atomic Structure",                          "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify protons, neutrons, and electrons", "Use atomic number and mass number"],                 "canonical_unit": "unit-atomic-theory", "canonical_index": 1},
    "L-atomic-mass":                 {"title": "Atomic Mass",                               "is_ap_only": False, "key_equations": ["avg atomic mass = Σ(isotope mass × abundance)"], "objectives": ["Calculate average atomic mass from isotope data"],                                        "canonical_unit": "unit-atomic-theory", "canonical_index": 2},
    "L-mass-spectrometry":           {"title": "Mass Spectrometry",                         "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Interpret mass spectrometry data", "Identify isotopes from m/z peaks"],                           "canonical_unit": "ap-unit-1", "canonical_index": 8},
    "L-pes":                         {"title": "Photoelectron Spectroscopy (PES)",          "is_ap_only": True,  "key_equations": ["IE = hν - KE"],                            "objectives": ["Interpret PES spectra", "Relate PES peaks to electron shell energies"],                          "canonical_unit": "ap-unit-1", "canonical_index": 9},

    # ── Nuclear Chemistry ─────────────────────────────────────
    "L-nuclear-intro":               {"title": "Intro to Nuclear Chemistry",                "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify types of radiation", "Describe nuclear stability"],                                     "canonical_unit": "unit-nuclear-chem", "canonical_index": 0},
    "L-nuclear-radioactive-decay":   {"title": "Radioactive Decay",                        "is_ap_only": False, "key_equations": ["N(t) = N₀e^(-λt)", "t½ = ln2 / λ"],       "objectives": ["Write decay equations", "Calculate half-life and decay rate"],                                    "canonical_unit": "unit-nuclear-chem", "canonical_index": 1},
    "L-nuclear-reactions":           {"title": "Nuclear Reactions",                         "is_ap_only": False, "key_equations": ["E = mc²"],                                 "objectives": ["Balance nuclear equations", "Calculate mass-energy equivalence"],                                "canonical_unit": "unit-nuclear-chem", "canonical_index": 2},

    # ── Electrons & Electron Configurations ──────────────────
    "L-electrons-ions":              {"title": "Ions",                                      "is_ap_only": False, "key_equations": [],                                          "objectives": ["Determine ion charge from electron gain/loss", "Write ion symbols"],                             "canonical_unit": "unit-electrons", "canonical_index": 0},
    "L-electrons-intro-config":      {"title": "Intro to Electron Configurations",          "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain the Aufbau principle", "Write basic electron configurations"],                            "canonical_unit": "unit-electrons", "canonical_index": 1},
    "L-electrons-config-orbital":    {"title": "Electron Configurations & Orbital Notations", "is_ap_only": False, "key_equations": [],                                       "objectives": ["Write full electron configurations", "Draw orbital notation diagrams"],                           "canonical_unit": "unit-electrons", "canonical_index": 2},
    "L-electrons-noble-gas":         {"title": "Noble Gas Abbreviations & Valence Electrons", "is_ap_only": False, "key_equations": [],                                       "objectives": ["Write noble gas shorthand configurations", "Identify valence electrons"],                          "canonical_unit": "unit-electrons", "canonical_index": 3},

    # ── The Periodic Table ────────────────────────────────────
    "L-periodic-history":            {"title": "History of the Periodic Table",             "is_ap_only": False, "key_equations": [],                                          "objectives": ["Describe Mendeleev's contribution", "Explain periodic law"],                                      "canonical_unit": "unit-periodic-table", "canonical_index": 0},
    "L-periodic-atomic-size":        {"title": "Atomic Size",                               "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain trends in atomic radius", "Compare radii across periods and groups"],                     "canonical_unit": "unit-periodic-table", "canonical_index": 1},
    "L-periodic-ionization":         {"title": "Ionization Energy",                         "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain ionization energy trends", "Predict relative ionization energies"],                       "canonical_unit": "unit-periodic-table", "canonical_index": 2},
    "L-periodic-electronegativity":  {"title": "Electronegativity",                         "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain electronegativity trends", "Use electronegativity to predict bond type"],               "canonical_unit": "unit-periodic-table", "canonical_index": 3},

    # ── Chemical Bonding ──────────────────────────────────────
    "L-bonding-basics":              {"title": "Bonding Basics",                            "is_ap_only": False, "key_equations": [],                                          "objectives": ["Describe types of chemical bonds", "Explain why atoms form bonds"],                              "canonical_unit": "unit-bonding", "canonical_index": 0},
    "L-bonding-ionic":               {"title": "Ionic Bonding",                             "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain ionic bond formation", "Draw Lewis dot structures for ionic compounds"],               "canonical_unit": "unit-bonding", "canonical_index": 1},
    "L-bonding-covalent":            {"title": "Covalent Bonding",                          "is_ap_only": False, "key_equations": [],                                          "objectives": ["Explain covalent bond formation", "Draw Lewis structures for molecules"],                        "canonical_unit": "unit-bonding", "canonical_index": 2},
    "L-bonding-molecular-geometry":  {"title": "Molecular Geometry",                        "is_ap_only": False, "key_equations": [],                                          "objectives": ["Apply VSEPR theory", "Predict molecular shapes"],                                                "canonical_unit": "unit-bonding", "canonical_index": 3},
    "L-bonding-polarity":            {"title": "Polarity",                                  "is_ap_only": False, "key_equations": [],                                          "objectives": ["Determine bond polarity", "Predict molecular polarity"],                                         "canonical_unit": "unit-bonding", "canonical_index": 4},
    "L-bonding-formal-charge":       {"title": "Formal Charge & Resonance",                 "is_ap_only": True,  "key_equations": ["FC = V - L - B/2"],                       "objectives": ["Calculate formal charge", "Draw resonance structures"],                                          "canonical_unit": "ap-unit-2", "canonical_index": 5},
    "L-bonding-hybridization":       {"title": "Hybridization",                             "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Explain sp, sp², sp³ hybridization", "Relate hybridization to geometry"],                        "canonical_unit": "ap-unit-2", "canonical_index": 6},

    # ── Chemical Nomenclature ─────────────────────────────────
    "L-nomenclature-properties":     {"title": "Properties of Ionic & Covalent Compounds",  "is_ap_only": False, "key_equations": [],                                          "objectives": ["Compare properties of ionic and covalent compounds"],                                           "canonical_unit": "unit-nomenclature", "canonical_index": 0},
    "L-nomenclature-name-formula":   {"title": "Name → Formula (Ionic)",                    "is_ap_only": False, "key_equations": [],                                          "objectives": ["Write formulas from ionic compound names"],                                                      "canonical_unit": "unit-nomenclature", "canonical_index": 1},
    "L-nomenclature-formula-name":   {"title": "Formula → Name (Ionic)",                    "is_ap_only": False, "key_equations": [],                                          "objectives": ["Name ionic compounds from their formulas"],                                                      "canonical_unit": "unit-nomenclature", "canonical_index": 2},
    "L-nomenclature-acids":          {"title": "Naming Acids",                              "is_ap_only": False, "key_equations": [],                                          "objectives": ["Name binary acids and oxyacids"],                                                               "canonical_unit": "unit-nomenclature", "canonical_index": 3},
    "L-nomenclature-covalent":       {"title": "Naming Covalent Compounds",                 "is_ap_only": False, "key_equations": [],                                          "objectives": ["Use Greek prefixes to name covalent compounds"],                                                 "canonical_unit": "unit-nomenclature", "canonical_index": 4},

    # ── Dimensional Analysis ──────────────────────────────────
    "L-da-intro":                    {"title": "Intro to Dimensional Analysis",             "is_ap_only": False, "key_equations": [],                                          "objectives": ["Set up unit conversion factors", "Solve single-step conversions"],                               "canonical_unit": "unit-dimensional-analysis", "canonical_index": 0},
    "L-da-multi-step":               {"title": "Multi-Step Dimensional Analysis",           "is_ap_only": False, "key_equations": [],                                          "objectives": ["Chain multiple conversion factors", "Solve complex unit conversions"],                            "canonical_unit": "unit-dimensional-analysis", "canonical_index": 1},

    # ── The Mole ──────────────────────────────────────────────
    "L-mole-history":                {"title": "History & Particle Conversions",            "is_ap_only": False, "key_equations": ["1 mol = 6.022 × 10²³ particles"],          "objectives": ["Explain the mole concept", "Convert between moles and particles"],                               "canonical_unit": "unit-mole", "canonical_index": 0},
    "L-mole-molar-mass-1step":       {"title": "Molar Mass (1-Step)",                       "is_ap_only": False, "key_equations": ["n = m / M"],                               "objectives": ["Calculate molar mass of elements", "Convert between moles and grams (1-step)"],                  "canonical_unit": "unit-mole", "canonical_index": 1},
    "L-mole-molar-mass-2step":       {"title": "Molar Mass (2-Step)",                       "is_ap_only": False, "key_equations": ["n = m / M"],                               "objectives": ["Calculate molar mass of compounds", "Convert between grams, moles, and particles"],             "canonical_unit": "unit-mole", "canonical_index": 2},
    "L-mole-percent-composition":    {"title": "Percent Composition",                       "is_ap_only": False, "key_equations": ["% = (part mass / molar mass) × 100"],      "objectives": ["Calculate percent composition by mass", "Determine empirical formula from percent composition"], "canonical_unit": "unit-mole", "canonical_index": 3},

    # ── Chemical Reactions ────────────────────────────────────
    "L-rxn-equations":               {"title": "Word & Formula Equations",                  "is_ap_only": False, "key_equations": [],                                          "objectives": ["Translate word equations to formula equations", "Identify reactants and products"],             "canonical_unit": "unit-chemical-reactions", "canonical_index": 0},
    "L-rxn-balancing":               {"title": "Balancing Chemical Equations",              "is_ap_only": False, "key_equations": [],                                          "objectives": ["Balance chemical equations by inspection", "Apply conservation of mass"],                        "canonical_unit": "unit-chemical-reactions", "canonical_index": 1},
    "L-rxn-both-skills":             {"title": "Both Skills Together",                      "is_ap_only": False, "key_equations": [],                                          "objectives": ["Write and balance equations from word descriptions"],                                            "canonical_unit": "unit-chemical-reactions", "canonical_index": 2},
    "L-rxn-synthesis-decomp":        {"title": "Synthesis & Decomposition",                 "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify synthesis reactions", "Identify decomposition reactions"],                             "canonical_unit": "unit-chemical-reactions", "canonical_index": 3},
    "L-rxn-single-replacement":      {"title": "Single Replacement",                        "is_ap_only": False, "key_equations": [],                                          "objectives": ["Predict single replacement reactions using the activity series"],                               "canonical_unit": "unit-chemical-reactions", "canonical_index": 4},
    "L-rxn-double-replacement":      {"title": "Double Replacement",                        "is_ap_only": False, "key_equations": [],                                          "objectives": ["Predict double replacement reactions", "Identify precipitate formation"],                        "canonical_unit": "unit-chemical-reactions", "canonical_index": 5},
    "L-rxn-net-ionic":               {"title": "Net Ionic Equations",                       "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Write complete and net ionic equations", "Identify spectator ions"],                            "canonical_unit": "ap-unit-4", "canonical_index": 4},
    "L-rxn-redox-titration":         {"title": "Advanced Redox & Intro to Titration",       "is_ap_only": True,  "key_equations": ["oxidation state rules"],                   "objectives": ["Assign oxidation states", "Balance redox equations", "Describe titration"],                     "canonical_unit": "ap-unit-4", "canonical_index": 5},

    # ── Stoichiometry ─────────────────────────────────────────
    "L-stoich-mole-mole":            {"title": "Mole-Mole Calculations",                    "is_ap_only": False, "key_equations": [],                                          "objectives": ["Use mole ratios to convert between reactants and products"],                                    "canonical_unit": "unit-stoichiometry", "canonical_index": 0},
    "L-stoich-mass-mass":            {"title": "Mass-Mass Calculations",                    "is_ap_only": False, "key_equations": [],                                          "objectives": ["Perform gram-to-gram stoichiometry calculations"],                                              "canonical_unit": "unit-stoichiometry", "canonical_index": 1},
    "L-stoich-limiting":             {"title": "Limiting Reactants",                        "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify the limiting reactant", "Calculate theoretical yield and percent yield"],              "canonical_unit": "unit-stoichiometry", "canonical_index": 2},

    # ── Solutions ─────────────────────────────────────────────
    "L-solutions-intro":             {"title": "Intro to Solutions",                        "is_ap_only": False, "key_equations": [],                                          "objectives": ["Define solute, solvent, and solution", "Explain the dissolution process"],                      "canonical_unit": "unit-solutions", "canonical_index": 0},
    "L-solutions-molarity":          {"title": "Molarity",                                  "is_ap_only": False, "key_equations": ["M = n / V"],                               "objectives": ["Calculate molarity of a solution", "Prepare solutions of a given molarity"],                   "canonical_unit": "unit-solutions", "canonical_index": 1},
    "L-solutions-acids-bases-props": {"title": "Acids & Bases Properties",                  "is_ap_only": False, "key_equations": ["pH + pOH = 14"],                           "objectives": ["Describe Arrhenius and Brønsted-Lowry definitions", "Identify conjugate acid-base pairs"],     "canonical_unit": "unit-solutions", "canonical_index": 2},
    "L-solutions-acid-base-calc":    {"title": "Acid-Base Calculations",                    "is_ap_only": False, "key_equations": ["pH = -log[H⁺]"],                          "objectives": ["Calculate pH from [H⁺]", "Interconvert pH, pOH, [H⁺], [OH⁻]"],                              "canonical_unit": "unit-solutions", "canonical_index": 3},
    "L-solutions-beer-lambert":      {"title": "Beer-Lambert Law",                          "is_ap_only": True,  "key_equations": ["A = εlc"],                                 "objectives": ["Apply the Beer-Lambert law", "Determine concentration from absorbance"],                         "canonical_unit": "ap-unit-3", "canonical_index": 10},
    "L-solutions-weak-acids":        {"title": "Weak Acids & Ka",                           "is_ap_only": True,  "key_equations": ["Ka = [H⁺][A⁻] / [HA]"],                  "objectives": ["Calculate pH of weak acid solutions", "Use Ka expressions"],                                   "canonical_unit": "ap-unit-8", "canonical_index": 2},

    # ── Thermochemistry ───────────────────────────────────────
    "L-thermo-intro":                {"title": "Intro to Thermochemistry",                  "is_ap_only": False, "key_equations": [],                                          "objectives": ["Distinguish endothermic and exothermic processes", "Define system and surroundings"],          "canonical_unit": "unit-thermochem", "canonical_index": 0},
    "L-thermo-calorimetry":          {"title": "Calorimetry",                               "is_ap_only": False, "key_equations": ["q = mcΔT"],                                "objectives": ["Perform calorimetry calculations", "Calculate specific heat capacity"],                          "canonical_unit": "unit-thermochem", "canonical_index": 1},
    "L-thermo-equations":            {"title": "Thermochemical Equations",                  "is_ap_only": False, "key_equations": ["Hess's Law"],                              "objectives": ["Write thermochemical equations", "Apply Hess's law"],                                            "canonical_unit": "unit-thermochem", "canonical_index": 2},
    "L-thermo-heating-curves":       {"title": "Heating Curves",                            "is_ap_only": False, "key_equations": ["q = mL"],                                  "objectives": ["Interpret heating/cooling curves", "Calculate heat for phase changes"],                          "canonical_unit": "unit-thermochem", "canonical_index": 3},
    "L-thermo-bond-enthalpies":      {"title": "Bond Enthalpies",                           "is_ap_only": True,  "key_equations": ["ΔH = Σ BE(broken) - Σ BE(formed)"],       "objectives": ["Estimate ΔH using bond enthalpies", "Compare bond strengths"],                                  "canonical_unit": "ap-unit-6", "canonical_index": 4},

    # ── Kinetic Molecular Theory ──────────────────────────────
    "L-kmt-gases":                   {"title": "KMT: Gases",                                "is_ap_only": False, "key_equations": [],                                          "objectives": ["State the postulates of KMT for gases", "Explain pressure and temperature at molecular level"], "canonical_unit": "unit-kinetic-theory", "canonical_index": 0},
    "L-kmt-liquids":                 {"title": "KMT: Liquids",                              "is_ap_only": False, "key_equations": [],                                          "objectives": ["Describe intermolecular forces in liquids", "Explain surface tension and viscosity"],            "canonical_unit": "unit-kinetic-theory", "canonical_index": 1},
    "L-kmt-solids":                  {"title": "KMT: Solids",                               "is_ap_only": False, "key_equations": [],                                          "objectives": ["Classify types of solids", "Compare crystalline and amorphous solids"],                        "canonical_unit": "unit-kinetic-theory", "canonical_index": 2},
    "L-kmt-phase-diagrams":          {"title": "Phase Diagrams",                            "is_ap_only": False, "key_equations": [],                                          "objectives": ["Interpret phase diagrams", "Identify triple point and critical point"],                         "canonical_unit": "unit-kinetic-theory", "canonical_index": 3},

    # ── Gas Laws ──────────────────────────────────────────────
    "L-gas-intro":                   {"title": "Intro to Gas Laws",                         "is_ap_only": False, "key_equations": [],                                          "objectives": ["Identify the four gas variables", "Describe qualitative gas law relationships"],               "canonical_unit": "unit-gas-laws", "canonical_index": 0},
    "L-gas-boyle-charles":           {"title": "Boyle's & Charles' Laws",                   "is_ap_only": False, "key_equations": ["P₁V₁ = P₂V₂", "V₁/T₁ = V₂/T₂"],          "objectives": ["Apply Boyle's law", "Apply Charles' law"],                                                      "canonical_unit": "unit-gas-laws", "canonical_index": 1},
    "L-gas-gay-lussac-combined":     {"title": "Gay-Lussac's & Combined Gas Law",           "is_ap_only": False, "key_equations": ["P₁V₁/T₁ = P₂V₂/T₂"],                     "objectives": ["Apply Gay-Lussac's law", "Use the combined gas law"],                                            "canonical_unit": "unit-gas-laws", "canonical_index": 2},
    "L-gas-ideal":                   {"title": "Ideal Gas Law",                             "is_ap_only": False, "key_equations": ["PV = nRT"],                                "objectives": ["Use the ideal gas law (PV = nRT)", "Solve for any gas variable"],                               "canonical_unit": "unit-gas-laws", "canonical_index": 3},
    "L-gas-van-der-waals":           {"title": "Real Gases & van der Waals Equation",       "is_ap_only": True,  "key_equations": ["(P + an²/V²)(V - nb) = nRT"],             "objectives": ["Explain deviations from ideal behavior", "Apply van der Waals equation"],                      "canonical_unit": "ap-unit-3", "canonical_index": 7},

    # ── AP Unit 5: Kinetics ────────────────────────────────────
    "L-ap-kinetics-rate-laws":       {"title": "Rate Laws & Reaction Rates",                "is_ap_only": True,  "key_equations": ["rate = k[A]ᵐ[B]ⁿ"],                      "objectives": ["Write rate law expressions", "Determine reaction order from experimental data"],               "canonical_unit": "ap-unit-5", "canonical_index": 0},
    "L-ap-kinetics-integrated":      {"title": "Integrated Rate Laws",                      "is_ap_only": True,  "key_equations": ["[A]t = [A]₀ - kt", "ln[A]t = ln[A]₀ - kt", "1/[A]t = 1/[A]₀ + kt"], "objectives": ["Use integrated rate laws (0th, 1st, 2nd order)", "Calculate half-life"], "canonical_unit": "ap-unit-5", "canonical_index": 1},
    "L-ap-kinetics-mechanisms":      {"title": "Reaction Mechanisms",                       "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Identify elementary steps in a mechanism", "Determine rate-determining step"],                 "canonical_unit": "ap-unit-5", "canonical_index": 2},
    "L-ap-kinetics-arrhenius":       {"title": "Arrhenius Equation & Activation Energy",    "is_ap_only": True,  "key_equations": ["k = Ae^(-Ea/RT)"],                        "objectives": ["Apply the Arrhenius equation", "Calculate activation energy from rate data"],                  "canonical_unit": "ap-unit-5", "canonical_index": 3},
    "L-ap-kinetics-catalysis":       {"title": "Catalysis",                                 "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Explain how catalysts affect reaction rate", "Distinguish homogeneous and heterogeneous catalysis"], "canonical_unit": "ap-unit-5", "canonical_index": 4},

    # ── AP Unit 7: Equilibrium ─────────────────────────────────
    "L-ap-eq-intro-kc":              {"title": "Intro to Equilibrium & Kc",                 "is_ap_only": True,  "key_equations": ["Kc = [products]/[reactants]"],             "objectives": ["Write equilibrium constant expressions", "Interpret the magnitude of Kc"],                    "canonical_unit": "ap-unit-7", "canonical_index": 0},
    "L-ap-eq-kp":                    {"title": "Kp and Gas-Phase Equilibria",                "is_ap_only": True,  "key_equations": ["Kp = Kc(RT)^Δn"],                        "objectives": ["Write Kp expressions", "Convert between Kc and Kp"],                                            "canonical_unit": "ap-unit-7", "canonical_index": 1},
    "L-ap-eq-q":                     {"title": "Reaction Quotient Q",                       "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Calculate Q and compare to K", "Predict reaction direction"],                                  "canonical_unit": "ap-unit-7", "canonical_index": 2},
    "L-ap-eq-le-chatelier":          {"title": "Le Châtelier's Principle",                  "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Predict equilibrium shifts from stress", "Apply Le Châtelier's principle"],                   "canonical_unit": "ap-unit-7", "canonical_index": 3},
    "L-ap-eq-ice":                   {"title": "ICE Tables",                                "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Set up ICE tables", "Solve for equilibrium concentrations"],                                   "canonical_unit": "ap-unit-7", "canonical_index": 4},
    "L-ap-eq-ksp":                   {"title": "Solubility Equilibria & Ksp",               "is_ap_only": True,  "key_equations": ["Ksp = [Aᵐ⁺]ᵃ[Bⁿ⁻]ᵇ"],                 "objectives": ["Write Ksp expressions", "Calculate molar solubility from Ksp"],                               "canonical_unit": "ap-unit-7", "canonical_index": 5},

    # ── AP Unit 8: Acids & Bases (AP-only lessons) ────────────
    "L-ap-acid-kakb":                {"title": "Ka, Kb & pKa / pKb",                        "is_ap_only": True,  "key_equations": ["Ka × Kb = Kw", "pKa + pKb = 14"],         "objectives": ["Use Ka and Kb to calculate pH", "Relate acid and base strengths"],                             "canonical_unit": "ap-unit-8", "canonical_index": 3},
    "L-ap-acid-salt-hydrolysis":     {"title": "Salt Hydrolysis & pH",                      "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Predict pH of salt solutions", "Explain hydrolysis of salts"],                                 "canonical_unit": "ap-unit-8", "canonical_index": 4},
    "L-ap-acid-buffers":             {"title": "Buffer Design & Capacity",                  "is_ap_only": True,  "key_equations": ["pH = pKa + log([A⁻]/[HA])"],              "objectives": ["Design a buffer of a given pH", "Calculate buffer pH using Henderson-Hasselbalch"],           "canonical_unit": "ap-unit-8", "canonical_index": 5},
    "L-ap-acid-titration-curves":    {"title": "Titration Curves & Indicators",             "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Interpret strong and weak acid titration curves", "Select appropriate indicators"],            "canonical_unit": "ap-unit-8", "canonical_index": 6},
    "L-ap-acid-polyprotic":          {"title": "Polyprotic Acids",                          "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Calculate pH of polyprotic acid solutions", "Identify dominant species at each pH"],           "canonical_unit": "ap-unit-8", "canonical_index": 7},

    # ── AP Unit 9: Applications of Thermodynamics ─────────────
    "L-ap-thermo-entropy":           {"title": "Entropy & ΔS",                              "is_ap_only": True,  "key_equations": ["ΔS° = Σ S°(products) - Σ S°(reactants)"], "objectives": ["Define entropy and predict sign of ΔS", "Calculate standard entropy change"],                "canonical_unit": "ap-unit-9", "canonical_index": 0},
    "L-ap-thermo-gibbs":             {"title": "Gibbs Free Energy",                         "is_ap_only": True,  "key_equations": ["ΔG = ΔH - TΔS"],                          "objectives": ["Calculate ΔG and predict spontaneity", "Determine temperature dependence of spontaneity"],   "canonical_unit": "ap-unit-9", "canonical_index": 1},
    "L-ap-thermo-dg-k-e":            {"title": "ΔG°, K, and E° Relationships",              "is_ap_only": True,  "key_equations": ["ΔG° = -RT ln K", "ΔG° = -nFE°"],         "objectives": ["Relate ΔG°, K, and E°", "Calculate equilibrium constants from thermodynamic data"],          "canonical_unit": "ap-unit-9", "canonical_index": 2},
    "L-ap-electro-galvanic":         {"title": "Galvanic Cells & Cell Notation",            "is_ap_only": True,  "key_equations": ["E°cell = E°cathode - E°anode"],            "objectives": ["Describe galvanic cell operation", "Write cell notation"],                                     "canonical_unit": "ap-unit-9", "canonical_index": 3},
    "L-ap-electro-nernst":           {"title": "Nernst Equation",                           "is_ap_only": True,  "key_equations": ["E = E° - (RT/nF) ln Q"],                  "objectives": ["Apply the Nernst equation", "Calculate cell potential under non-standard conditions"],       "canonical_unit": "ap-unit-9", "canonical_index": 4},
    "L-ap-electro-electrolysis":     {"title": "Electrolysis",                              "is_ap_only": True,  "key_equations": [],                                          "objectives": ["Describe electrolytic cell operation", "Predict electrolysis products"],                        "canonical_unit": "ap-unit-9", "canonical_index": 5},
    "L-ap-electro-faraday":          {"title": "Faraday's Laws",                            "is_ap_only": True,  "key_equations": ["m = (M × I × t) / (n × F)"],              "objectives": ["Apply Faraday's laws of electrolysis", "Calculate mass deposited from charge"],               "canonical_unit": "ap-unit-9", "canonical_index": 6},
}


# ══════════════════════════════════════════════════════════════
# UNIT DEFINITIONS
# ══════════════════════════════════════════════════════════════

STANDARD_UNITS = [
    {"id": "unit-intro-chem",           "sort_order": 1,  "title": "Introduction to Chemistry",          "icon": "🧪",  "description": "Lab safety, scientific method, classification of matter, and measurement.",                    "lesson_ids": ["L-intro-safety", "L-intro-scientific-method", "L-intro-classification-matter", "L-intro-chem-phys-changes", "L-intro-measurement"]},
    {"id": "unit-atomic-theory",        "sort_order": 2,  "title": "Atomic Theory & Structure",           "icon": "⚛️", "description": "History of atomic theory, atomic structure, and average atomic mass.",                       "lesson_ids": ["L-atomic-history", "L-atomic-structure", "L-atomic-mass"]},
    {"id": "unit-nuclear-chem",         "sort_order": 3,  "title": "Nuclear Chemistry",                   "icon": "☢️", "description": "Types of radiation, radioactive decay, half-life, and nuclear reactions.",                   "lesson_ids": ["L-nuclear-intro", "L-nuclear-radioactive-decay", "L-nuclear-reactions"]},
    {"id": "unit-electrons",            "sort_order": 4,  "title": "Electrons & Electron Configurations", "icon": "⚡", "description": "Ions, electron configurations, orbital notation, and valence electrons.",                    "lesson_ids": ["L-electrons-ions", "L-electrons-intro-config", "L-electrons-config-orbital", "L-electrons-noble-gas"]},
    {"id": "unit-periodic-table",       "sort_order": 5,  "title": "The Periodic Table",                  "icon": "📊", "description": "History of the periodic table and periodic trends: atomic size, ionization energy, electronegativity.", "lesson_ids": ["L-periodic-history", "L-periodic-atomic-size", "L-periodic-ionization", "L-periodic-electronegativity"]},
    {"id": "unit-bonding",              "sort_order": 6,  "title": "Chemical Bonding",                    "icon": "🔗", "description": "Ionic bonding, covalent bonding, molecular geometry, and polarity.",                         "lesson_ids": ["L-bonding-basics", "L-bonding-ionic", "L-bonding-covalent", "L-bonding-molecular-geometry", "L-bonding-polarity"]},
    {"id": "unit-nomenclature",         "sort_order": 7,  "title": "Chemical Nomenclature",               "icon": "🏷️", "description": "Naming ionic compounds, covalent compounds, and acids.",                                    "lesson_ids": ["L-nomenclature-properties", "L-nomenclature-name-formula", "L-nomenclature-formula-name", "L-nomenclature-acids", "L-nomenclature-covalent"]},
    {"id": "unit-dimensional-analysis", "sort_order": 8,  "title": "Dimensional Analysis",                "icon": "📐", "description": "Single-step and multi-step unit conversions using dimensional analysis.",                    "lesson_ids": ["L-da-intro", "L-da-multi-step"]},
    {"id": "unit-mole",                 "sort_order": 9,  "title": "The Mole",                            "icon": "🐭", "description": "Avogadro's number, molar mass conversions, and percent composition.",                       "lesson_ids": ["L-mole-history", "L-mole-molar-mass-1step", "L-mole-molar-mass-2step", "L-mole-percent-composition"]},
    {"id": "unit-chemical-reactions",   "sort_order": 10, "title": "Chemical Reactions",                  "icon": "⚗️", "description": "Writing and balancing equations; synthesis, decomposition, and replacement reactions.",       "lesson_ids": ["L-rxn-equations", "L-rxn-balancing", "L-rxn-both-skills", "L-rxn-synthesis-decomp", "L-rxn-single-replacement", "L-rxn-double-replacement"]},
    {"id": "unit-stoichiometry",        "sort_order": 11, "title": "Stoichiometry",                       "icon": "⚖️", "description": "Mole ratios, mass-mass calculations, limiting reactants, and percent yield.",                "lesson_ids": ["L-stoich-mole-mole", "L-stoich-mass-mass", "L-stoich-limiting"]},
    {"id": "unit-solutions",            "sort_order": 12, "title": "Solutions",                           "icon": "💧", "description": "Molarity, acid-base properties, and pH calculations.",                                      "lesson_ids": ["L-solutions-intro", "L-solutions-molarity", "L-solutions-acids-bases-props", "L-solutions-acid-base-calc"]},
    {"id": "unit-thermochem",           "sort_order": 13, "title": "Thermochemistry",                     "icon": "🔥", "description": "Calorimetry, thermochemical equations, Hess's law, and heating curves.",                     "lesson_ids": ["L-thermo-intro", "L-thermo-calorimetry", "L-thermo-equations", "L-thermo-heating-curves"]},
    {"id": "unit-kinetic-theory",       "sort_order": 14, "title": "Kinetic Molecular Theory",            "icon": "💨", "description": "KMT for gases, liquids, and solids; phase diagrams.",                                      "lesson_ids": ["L-kmt-gases", "L-kmt-liquids", "L-kmt-solids", "L-kmt-phase-diagrams"]},
    {"id": "unit-gas-laws",             "sort_order": 15, "title": "Gas Laws",                            "icon": "🎈", "description": "Boyle's, Charles', Gay-Lussac's, combined, and ideal gas laws.",                             "lesson_ids": ["L-gas-intro", "L-gas-boyle-charles", "L-gas-gay-lussac-combined", "L-gas-ideal"]},
]

AP_UNITS = [
    {"id": "ap-unit-1", "sort_order": 1, "title": "Atomic Structure & Properties",                      "icon": "⚛️", "description": "Moles, molar mass, atomic structure, electron configurations, mass spectrometry, PES, and periodic trends.",              "lesson_ids": ["L-mole-molar-mass-1step", "L-mole-molar-mass-2step", "L-mole-percent-composition", "L-atomic-structure", "L-atomic-mass", "L-electrons-intro-config", "L-electrons-config-orbital", "L-electrons-noble-gas", "L-mass-spectrometry", "L-pes", "L-periodic-atomic-size", "L-periodic-ionization", "L-periodic-electronegativity"]},
    {"id": "ap-unit-2", "sort_order": 2, "title": "Molecular & Ionic Compound Structure & Properties",  "icon": "🔗", "description": "All bond types, molecular geometry, polarity, formal charge, resonance, and hybridization.",                                "lesson_ids": ["L-bonding-basics", "L-bonding-ionic", "L-bonding-covalent", "L-bonding-molecular-geometry", "L-bonding-polarity", "L-bonding-formal-charge", "L-bonding-hybridization"]},
    {"id": "ap-unit-3", "sort_order": 3, "title": "Intermolecular Forces & Properties",                 "icon": "💧", "description": "KMT, phase diagrams, gas laws, real gases, solutions, molarity, and Beer-Lambert law.",                                    "lesson_ids": ["L-kmt-gases", "L-kmt-liquids", "L-kmt-solids", "L-kmt-phase-diagrams", "L-gas-boyle-charles", "L-gas-gay-lussac-combined", "L-gas-ideal", "L-gas-van-der-waals", "L-solutions-intro", "L-solutions-molarity", "L-solutions-beer-lambert"]},
    {"id": "ap-unit-4", "sort_order": 4, "title": "Chemical Reactions",                                 "icon": "⚗️", "description": "Balancing, reaction types, net ionic equations, redox, stoichiometry, and limiting reactants.",                             "lesson_ids": ["L-rxn-balancing", "L-rxn-synthesis-decomp", "L-rxn-single-replacement", "L-rxn-double-replacement", "L-rxn-net-ionic", "L-rxn-redox-titration", "L-stoich-mole-mole", "L-stoich-mass-mass", "L-stoich-limiting"]},
    {"id": "ap-unit-5", "sort_order": 5, "title": "Kinetics",                                           "icon": "⏱️", "description": "Rate laws, integrated rate laws, reaction mechanisms, Arrhenius equation, and catalysis.",                                  "lesson_ids": ["L-ap-kinetics-rate-laws", "L-ap-kinetics-integrated", "L-ap-kinetics-mechanisms", "L-ap-kinetics-arrhenius", "L-ap-kinetics-catalysis"]},
    {"id": "ap-unit-6", "sort_order": 6, "title": "Thermodynamics",                                     "icon": "🔥", "description": "Thermochemistry, calorimetry, Hess's law, heating curves, and bond enthalpies.",                                          "lesson_ids": ["L-thermo-intro", "L-thermo-calorimetry", "L-thermo-equations", "L-thermo-heating-curves", "L-thermo-bond-enthalpies"]},
    {"id": "ap-unit-7", "sort_order": 7, "title": "Equilibrium",                                        "icon": "⚖️", "description": "Equilibrium constants Kc and Kp, reaction quotient Q, Le Châtelier's principle, ICE tables, and Ksp.",                   "lesson_ids": ["L-ap-eq-intro-kc", "L-ap-eq-kp", "L-ap-eq-q", "L-ap-eq-le-chatelier", "L-ap-eq-ice", "L-ap-eq-ksp"]},
    {"id": "ap-unit-8", "sort_order": 8, "title": "Acids & Bases",                                      "icon": "🧪", "description": "Acid-base properties, pH, weak acids, Ka/Kb, buffers, titration curves, and polyprotic acids.",                            "lesson_ids": ["L-solutions-acids-bases-props", "L-solutions-acid-base-calc", "L-solutions-weak-acids", "L-ap-acid-kakb", "L-ap-acid-salt-hydrolysis", "L-ap-acid-buffers", "L-ap-acid-titration-curves", "L-ap-acid-polyprotic"]},
    {"id": "ap-unit-9", "sort_order": 9, "title": "Applications of Thermodynamics",                     "icon": "⚡", "description": "Entropy, Gibbs free energy, ΔG°/K/E° relationships, galvanic cells, Nernst equation, electrolysis, and Faraday's laws.",  "lesson_ids": ["L-ap-thermo-entropy", "L-ap-thermo-gibbs", "L-ap-thermo-dg-k-e", "L-ap-electro-galvanic", "L-ap-electro-nernst", "L-ap-electro-electrolysis", "L-ap-electro-faraday"]},
]

GRADES = [
    ("Middle School", 1), ("9th Grade", 2), ("10th Grade", 3),
    ("11th Grade", 4),    ("12th Grade", 5), ("AP / Advanced", 6), ("College", 7),
]

INTERESTS = [
    ("sports", "Sports", "🏀"), ("music", "Music", "🎵"),
    ("food", "Food & Cooking", "🍕"), ("gaming", "Gaming", "🎮"),
    ("art", "Art & Design", "🎨"), ("nature", "Nature", "🌿"),
    ("tech", "Technology", "💻"), ("movies", "Movies & TV", "🎬"),
]

KEEP_UNIT_IDS = {u["id"] for u in STANDARD_UNITS} | {u["id"] for u in AP_UNITS}
KEEP_COURSE_NAMES = {"Standard Chemistry", "AP Chemistry"}


# ══════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ══════════════════════════════════════════════════════════════

async def seed(session: AsyncSession) -> None:
    print("\n─── Lookup tables ───")

    for name, sort in GRADES:
        if not await session.scalar(select(Grade).where(Grade.name == name)):
            session.add(Grade(name=name, sort_order=sort))
            print(f"  + Grade: {name}")
    await session.flush()

    for name, sort in [("Standard Chemistry", 1), ("AP Chemistry", 2)]:
        if not await session.scalar(select(Course).where(Course.name == name)):
            session.add(Course(name=name, sort_order=sort))
            print(f"  + Course: {name}")
    await session.flush()

    for slug, label, icon in INTERESTS:
        if not await session.scalar(select(Interest).where(Interest.slug == slug)):
            session.add(Interest(slug=slug, label=label, icon=icon))
            print(f"  + Interest: {label}")
    await session.flush()

    # Remove stale courses
    for c in (await session.scalars(select(Course))).all():
        if c.name not in KEEP_COURSE_NAMES:
            print(f"  ✗ Removing stale course: {c.name}")
            await session.delete(c)
    await session.flush()

    std_course = await session.scalar(select(Course).where(Course.name == "Standard Chemistry"))
    ap_course  = await session.scalar(select(Course).where(Course.name == "AP Chemistry"))

    # ── Remove stale units ────────────────────────────────────
    for unit in (await session.scalars(select(Unit))).all():
        if unit.id not in KEEP_UNIT_IDS:
            print(f"  ✗ Removing stale unit: {unit.id}")
            await session.execute(text(f"DELETE FROM units WHERE id = '{unit.id}'"))
    await session.flush()

    # ── Upsert all units (bare, no lesson links yet) ──────────
    print("\n─── Upserting units ───")
    await _upsert_units_bare(session, STANDARD_UNITS, std_course.id)
    await _upsert_units_bare(session, AP_UNITS, ap_course.id)

    # ── Master lesson library (units must exist first) ────────
    print("\n─── Master lesson library ───")

    # Delete legacy lessons via raw SQL (CASCADE handles topic_standards children)
    result = await session.execute(
        text("DELETE FROM lessons WHERE slug LIKE 'L-legacy-%'")
    )
    deleted = result.rowcount
    if deleted:
        print(f"  ✗ Deleted {deleted} legacy lessons")
    await session.flush()

    slug_to_lesson_id: dict[str, int] = {}

    for slug, data in MASTER_LESSONS.items():
        lesson = await session.scalar(select(Lesson).where(Lesson.slug == slug))
        if lesson is None:
            lesson = Lesson(
                slug=slug,
                title=data["title"],
                description="",
                is_ap_only=data["is_ap_only"],
                key_equations=data["key_equations"],
                objectives=data["objectives"],
                unit_id=data["canonical_unit"],
                lesson_index=data["canonical_index"],
                is_active=True,
            )
            session.add(lesson)
            await session.flush()
            print(f"  + {slug}")
        else:
            lesson.title = data["title"]
            lesson.is_ap_only = data["is_ap_only"]
            lesson.key_equations = data["key_equations"]
            lesson.objectives = data["objectives"]
        slug_to_lesson_id[slug] = lesson.id

    await session.flush()

    # ── Seed unit_lessons junction ────────────────────────────
    print("\n─── Standard Chemistry unit_lessons ───")
    await _seed_unit_lessons(session, STANDARD_UNITS, slug_to_lesson_id)

    print("\n─── AP Chemistry unit_lessons ───")
    await _seed_unit_lessons(session, AP_UNITS, slug_to_lesson_id)

    print("\n✅  Seed complete!")


async def _upsert_units_bare(
    session: AsyncSession,
    unit_defs: list[dict],
    course_id: int,
) -> None:
    """Create or update units without touching unit_lessons."""
    for u in unit_defs:
        unit = await session.get(Unit, u["id"])
        if unit is None:
            unit = Unit(
                id=u["id"],
                title=u["title"],
                description=u.get("description", ""),
                icon=u.get("icon"),
                sort_order=u["sort_order"],
                course_id=course_id,
                is_active=True,
                is_coming_soon=False,
            )
            session.add(unit)
            await session.flush()
            print(f"  + {u['id']}: {u['title']}")
        else:
            unit.title = u["title"]
            unit.description = u.get("description", unit.description)
            unit.icon = u.get("icon", unit.icon)
            unit.sort_order = u["sort_order"]
            unit.course_id = course_id
    await session.flush()


async def _seed_unit_lessons(
    session: AsyncSession,
    unit_defs: list[dict],
    slug_to_lesson_id: dict[str, int],
) -> None:
    """Clear and re-seed unit_lessons junction rows."""
    for u in unit_defs:
        await session.execute(delete(UnitLesson).where(UnitLesson.unit_id == u["id"]))
        lesson_ids = u.get("lesson_ids", [])
        for order, slug in enumerate(lesson_ids):
            lid = slug_to_lesson_id.get(slug)
            if lid is None:
                print(f"  ⚠  Unknown slug in {u['id']}: {slug}")
                continue
            session.add(UnitLesson(unit_id=u["id"], lesson_id=lid, lesson_order=order))
        await session.flush()
        print(f"  {u['id']}: {len(lesson_ids)} lessons")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    # Ensure columns exist (idempotent, runs before ORM)
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS slug VARCHAR(100)"))
        await conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS is_ap_only BOOLEAN NOT NULL DEFAULT FALSE"))
        await conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS objectives JSONB DEFAULT '[]'"))
        # Backfill slugs for any un-slugged rows so NOT NULL constraint doesn't break
        await conn.execute(text("UPDATE lessons SET slug = 'L-legacy-' || id::text WHERE slug IS NULL"))
        await conn.execute(text("ALTER TABLE lessons ALTER COLUMN slug SET NOT NULL"))

    await engine.dispose()

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
