"""
Lesson ↔ standard junction seed data.

Flat list of (lesson_slug, standard_code) pairs. The seed script loads this into
the lesson_standards table. The DB is the source of truth — do not add a
standards field to MASTER_LESSONS; edit this list instead.

Standard definitions live in standards.py (STANDARDS_SEED).
"""

LESSON_STANDARDS: list[tuple[str, str]] = [

    # ── Introduction to Chemistry ──────────────────────────────────────
    ("L-intro-classification-matter",   "HS-PS1-3"),
    ("L-intro-chem-phys-changes",       "HS-PS1-2"),
    ("L-intro-measurement",             "HS-PS1-7"),

    # ── Atomic Theory ─────────────────────────────────────────────────
    ("L-atomic-history",                "HS-PS1-1"),
    ("L-atomic-structure",              "HS-PS1-1"),
    ("L-atomic-structure",              "AP-1.5"),
    ("L-atomic-mass",                   "AP-1.2"),

    # ── Nuclear Chemistry ─────────────────────────────────────────────
    ("L-nuclear-intro",                 "HS-PS1-8"),
    ("L-nuclear-radioactive-decay",     "HS-PS1-8"),
    ("L-nuclear-reactions",             "HS-PS1-8"),

    # ── Electrons & Configurations ────────────────────────────────────
    ("L-electrons-ions",                "HS-PS1-1"),
    ("L-electrons-ions",                "AP-1.5"),
    ("L-electrons-intro-config",        "HS-PS1-1"),
    ("L-electrons-intro-config",        "AP-1.5"),
    ("L-electrons-config-orbital",      "HS-PS1-1"),
    ("L-electrons-config-orbital",      "AP-1.5"),
    ("L-electrons-noble-gas",           "AP-1.5"),

    # ── Periodic Table ────────────────────────────────────────────────
    ("L-periodic-history",              "HS-PS1-1"),
    ("L-periodic-atomic-size",          "HS-PS1-1"),
    ("L-periodic-atomic-size",          "AP-1.7"),
    ("L-periodic-ionization",           "HS-PS1-1"),
    ("L-periodic-ionization",           "AP-1.7"),
    ("L-periodic-electronegativity",    "HS-PS1-1"),
    ("L-periodic-electronegativity",    "AP-1.7"),
    ("L-periodic-electronegativity",    "AP-2.1"),

    # ── Chemical Bonding ──────────────────────────────────────────────
    ("L-bonding-basics",                "HS-PS1-1"),
    ("L-bonding-basics",                "AP-2.1"),
    ("L-bonding-ionic",                 "AP-2.3"),
    ("L-bonding-covalent",              "AP-2.5"),
    ("L-bonding-molecular-geometry",    "AP-2.7"),
    ("L-bonding-polarity",              "AP-2.1"),

    # ── Nomenclature ──────────────────────────────────────────────────
    ("L-nomenclature-properties",       "HS-PS1-3"),
    ("L-nomenclature-properties",       "AP-2.1"),
    ("L-nomenclature-name-formula",     "HS-PS1-2"),
    ("L-nomenclature-formula-name",     "HS-PS1-2"),
    ("L-nomenclature-acids",            "AP-2.1"),
    ("L-nomenclature-covalent",         "AP-2.1"),

    # ── Dimensional Analysis ──────────────────────────────────────────
    ("L-da-intro",                      "HS-PS1-7"),
    ("L-da-multi-step",                 "HS-PS1-7"),

    # ── The Mole ──────────────────────────────────────────────────────
    ("L-mole-history",                  "AP-1.1"),
    ("L-mole-molar-mass-1step",         "AP-1.1"),
    ("L-mole-molar-mass-2step",         "AP-1.1"),
    ("L-mole-percent-composition",      "AP-1.3"),

    # ── Chemical Reactions ────────────────────────────────────────────
    ("L-rxn-equations",                 "HS-PS1-2"),
    ("L-rxn-balancing",                 "HS-PS1-7"),
    ("L-rxn-both-skills",               "HS-PS1-7"),
    ("L-rxn-both-skills",               "HS-PS1-2"),
    ("L-rxn-synthesis-decomp",          "HS-PS1-2"),
    ("L-rxn-single-replacement",        "HS-PS1-2"),
    ("L-rxn-double-replacement",        "HS-PS1-2"),

    # ── Stoichiometry ─────────────────────────────────────────────────
    ("L-stoich-mole-mole",              "HS-PS1-7"),
    ("L-stoich-mole-mole",              "AP-4.5"),
    ("L-stoich-mass-mass",              "HS-PS1-7"),
    ("L-stoich-mass-mass",              "AP-4.5"),
    ("L-stoich-limiting",               "HS-PS1-7"),
    ("L-stoich-limiting",               "AP-4.5"),

    # ── Solutions ─────────────────────────────────────────────────────
    ("L-solutions-intro",               "HS-PS1-3"),
    ("L-solutions-molarity",            "AP-3.8"),
    ("L-solutions-acids-bases-props",   "AP-8.1"),
    ("L-solutions-acid-base-calc",      "AP-8.2"),

    # ── Thermochemistry ───────────────────────────────────────────────
    ("L-thermo-intro",                  "HS-PS3-4"),
    ("L-thermo-intro",                  "AP-6.1"),
    ("L-thermo-calorimetry",            "AP-6.4"),
    ("L-thermo-equations",              "AP-6.8"),
    ("L-thermo-equations",              "AP-6.9"),
    ("L-thermo-heating-curves",         "AP-6.1"),

    # ── KMT & Gas Laws ────────────────────────────────────────────────
    ("L-kmt-gases",                     "AP-3.4"),
    ("L-kmt-liquids",                   "AP-3.1"),
    ("L-kmt-solids",                    "AP-3.1"),
    ("L-kmt-phase-diagrams",            "AP-3.1"),
    ("L-gas-intro",                     "AP-3.4"),
    ("L-gas-boyle-charles",             "AP-3.4"),
    ("L-gas-gay-lussac-combined",       "AP-3.4"),
    ("L-gas-ideal",                     "AP-3.4"),

    # ── AP: Atomic Structure Extensions ──────────────────────────────
    ("L-mass-spectrometry",             "AP-1.2"),
    ("L-pes",                           "AP-1.6"),

    # ── AP: Bonding Extensions ───────────────────────────────────────
    ("L-bonding-formal-charge",         "AP-2.6"),
    ("L-bonding-hybridization",         "AP-2.7"),

    # ── AP: IMF / Gas Extensions ─────────────────────────────────────
    ("L-gas-van-der-waals",             "AP-3.4"),
    ("L-solutions-beer-lambert",        "AP-3.13"),

    # ── AP: Chemical Reactions ────────────────────────────────────────
    ("L-rxn-net-ionic",                 "AP-4.2"),
    ("L-rxn-redox-titration",           "AP-4.6"),
    ("L-rxn-redox-titration",           "AP-4.9"),

    # ── AP: Kinetics ──────────────────────────────────────────────────
    ("L-ap-kinetics-rate-laws",         "AP-5.1"),
    ("L-ap-kinetics-rate-laws",         "AP-5.2"),
    ("L-kinetics-zero-order",           "AP-5.3"),
    ("L-kinetics-zero-order",           "HS-PS1-5"),
    ("L-kinetics-first-order",          "AP-5.3"),
    ("L-kinetics-first-order",          "HS-PS1-5"),
    ("L-kinetics-second-order",         "AP-5.3"),
    ("L-kinetics-second-order",         "HS-PS1-5"),
    ("L-kinetics-comparison",           "AP-5.3"),
    ("L-ap-kinetics-mechanisms",        "AP-5.8"),
    ("L-ap-kinetics-arrhenius",         "AP-5.5"),
    ("L-ap-kinetics-arrhenius",         "HS-PS1-5"),
    ("L-ap-kinetics-catalysis",         "AP-5.11"),
    ("L-ap-kinetics-catalysis",         "HS-PS1-5"),

    # ── AP: Thermodynamics (Unit 6 extensions) ────────────────────────
    ("L-thermo-bond-enthalpies",        "AP-6.8"),
    ("L-thermo-bond-enthalpies",        "HS-PS1-4"),

    # ── AP: Equilibrium ───────────────────────────────────────────────
    ("L-ap-eq-intro-kc",                "AP-7.4"),
    ("L-ap-eq-kp",                      "AP-7.4"),
    ("L-ap-eq-q",                       "AP-7.2"),
    ("L-ap-eq-le-chatelier",            "AP-7.9"),
    ("L-ap-eq-le-chatelier",            "HS-PS1-6"),
    ("L-ap-eq-ice",                     "AP-7.4"),
    ("L-ap-eq-ksp",                     "AP-7.11"),

    # ── AP: Acids & Bases ─────────────────────────────────────────────
    ("L-solutions-weak-acids-pt1",      "AP-8.3"),
    ("L-solutions-weak-acids-pt2",      "AP-8.3"),
    ("L-ap-acid-kakb",                  "AP-8.3"),
    ("L-ap-acid-salt-hydrolysis",       "AP-8.3"),
    ("L-ap-acid-buffers",               "AP-8.8"),
    ("L-ap-acid-titration-curves",      "AP-8.5"),
    ("L-ap-acid-polyprotic",            "AP-8.3"),
    ("L-ap-acid-polyprotic",            "AP-8.5"),

    # ── AP: Applications of Thermodynamics ───────────────────────────
    ("L-ap-thermo-entropy",             "AP-9.1"),
    ("L-ap-thermo-gibbs",               "AP-9.3"),
    ("L-ap-thermo-dg-k-e",             "AP-9.5"),
    ("L-ap-thermo-dg-k-e",             "AP-9.8"),
    ("L-ap-electro-galvanic",           "AP-9.7"),
    ("L-ap-electro-nernst",             "AP-9.8"),
    ("L-ap-electro-electrolysis",       "AP-9.7"),
    ("L-ap-electro-faraday",            "AP-9.8"),
]
