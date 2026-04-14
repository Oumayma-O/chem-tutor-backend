"""
Lesson ↔ standard junction seed data.

Flat list of (lesson_slug, standard_code) pairs. The seed script loads this into
the lesson_standards table. The DB is the source of truth — do not add a
standards field to MASTER_LESSONS; edit this list instead.

Standard definitions live in standards.py (STANDARDS_SEED).

Organization per standard unit (NGSS alignment from curriculum document):
  unit-intro-chem          → N/A core  | SEP-3, SEP-4 | CCC-3, CCC-1
  unit-dimensional-analysis→ N/A core  | SEP-5        | CCC-3
  unit-mole                → PS1-7     | SEP-5        | CCC-5, CCC-3
  unit-atomic-theory       → PS1-1, PS1-8 | SEP-2    | CCC-6
  unit-electrons           → PS1-1     | SEP-2        | CCC-1, CCC-6
  unit-periodic-table      → PS1-1     | SEP-4        | CCC-1
  unit-nomenclature        → PS1-2, PS1-7 | SEP-5, SEP-6 | —
  unit-bonding             → PS1-3, PS2-6 | SEP-2    | CCC-6
  unit-kinetic-theory      → PS3-2, PS1-4 | SEP-2    | CCC-5
  unit-gas-laws            → PS3-1, PS3-2 | SEP-5    | CCC-3
  unit-chemical-reactions  → PS1-2, PS1-7 | SEP-5, SEP-6 | CCC-5
  unit-stoichiometry       → PS1-7     | SEP-5        | CCC-5
  unit-solutions           → PS1-2, PS1-5 | SEP-4    | CCC-5, CCC-6
  unit-thermochem          → PS3-1, PS3-2, PS1-4 | SEP-2, SEP-5 | CCC-5
  unit-nuclear-chem        → PS1-8, PS3-3 | SEP-2   | CCC-5, CCC-7

AP-only lessons retain their AP CED standard mappings.
NGSS standards are not applied to AP-only lessons (no unit-level mapping defined).
"""

LESSON_STANDARDS: list[tuple[str, str]] = [

    # ══════════════════════════════════════════════════════════════════════
    # unit-intro-chem  (N/A core standard)
    # SEP: Planning & Carrying Out Investigations (SEP-3)
    #      Analyzing & Interpreting Data (SEP-4)
    # CCC: Scale, Proportion, and Quantity (CCC-3)
    #      Patterns (CCC-1)
    # ══════════════════════════════════════════════════════════════════════
    ("L-intro-safety",                  "NGSS-SEP-3"),
    ("L-intro-safety",                  "NGSS-SEP-4"),
    ("L-intro-safety",                  "NGSS-CCC-3"),
    ("L-intro-safety",                  "NGSS-CCC-1"),

    ("L-intro-scientific-method",       "NGSS-SEP-3"),
    ("L-intro-scientific-method",       "NGSS-SEP-4"),
    ("L-intro-scientific-method",       "NGSS-CCC-3"),
    ("L-intro-scientific-method",       "NGSS-CCC-1"),

    ("L-intro-classification-matter",   "NGSS-SEP-3"),
    ("L-intro-classification-matter",   "NGSS-SEP-4"),
    ("L-intro-classification-matter",   "NGSS-CCC-3"),
    ("L-intro-classification-matter",   "NGSS-CCC-1"),

    ("L-intro-chem-phys-changes",       "NGSS-SEP-3"),
    ("L-intro-chem-phys-changes",       "NGSS-SEP-4"),
    ("L-intro-chem-phys-changes",       "NGSS-CCC-3"),
    ("L-intro-chem-phys-changes",       "NGSS-CCC-1"),

    ("L-intro-measurement",             "NGSS-SEP-3"),
    ("L-intro-measurement",             "NGSS-SEP-4"),
    ("L-intro-measurement",             "NGSS-CCC-3"),
    ("L-intro-measurement",             "NGSS-CCC-1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-atomic-theory  (PS1-1, PS1-8)
    # SEP: Developing and Using Models (SEP-2)
    # CCC: Structure and Function (CCC-6)
    # ══════════════════════════════════════════════════════════════════════
    ("L-atomic-history",                "HS-PS1-1"),
    ("L-atomic-history",                "HS-PS1-8"),
    ("L-atomic-history",                "NGSS-SEP-2"),
    ("L-atomic-history",                "NGSS-CCC-6"),

    ("L-atomic-structure",              "HS-PS1-1"),
    ("L-atomic-structure",              "HS-PS1-8"),
    ("L-atomic-structure",              "NGSS-SEP-2"),
    ("L-atomic-structure",              "NGSS-CCC-6"),
    ("L-atomic-structure",              "AP-1.5"),

    ("L-atomic-mass",                   "HS-PS1-1"),
    ("L-atomic-mass",                   "HS-PS1-8"),
    ("L-atomic-mass",                   "NGSS-SEP-2"),
    ("L-atomic-mass",                   "NGSS-CCC-6"),
    ("L-atomic-mass",                   "AP-1.2"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-nuclear-chem  (PS1-8 on all; PS3-3 only on reactions lesson)
    # PS3-3 = "design/evaluate systems involving energy transfer, efficiency,
    # environmental impact" — applies to fission/fusion applications, not to
    # introductory radiation types or half-life calculation lessons.
    # SEP: Developing and Using Models (SEP-2)
    # CCC: Energy and Matter (CCC-5), Stability and Change (CCC-7)
    # ══════════════════════════════════════════════════════════════════════
    ("L-nuclear-intro",                 "HS-PS1-8"),
    ("L-nuclear-intro",                 "NGSS-SEP-2"),
    ("L-nuclear-intro",                 "NGSS-CCC-5"),
    ("L-nuclear-intro",                 "NGSS-CCC-7"),

    ("L-nuclear-radioactive-decay",     "HS-PS1-8"),
    ("L-nuclear-radioactive-decay",     "NGSS-SEP-2"),
    ("L-nuclear-radioactive-decay",     "NGSS-CCC-5"),
    ("L-nuclear-radioactive-decay",     "NGSS-CCC-7"),

    ("L-nuclear-reactions",             "HS-PS1-8"),
    ("L-nuclear-reactions",             "HS-PS3-3"),
    ("L-nuclear-reactions",             "NGSS-SEP-2"),
    ("L-nuclear-reactions",             "NGSS-CCC-5"),
    ("L-nuclear-reactions",             "NGSS-CCC-7"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-electrons  (PS1-1)
    # SEP: Developing and Using Models (SEP-2)
    # CCC: Patterns (CCC-1), Structure and Function (CCC-6)
    # ══════════════════════════════════════════════════════════════════════
    ("L-electrons-ions",                "HS-PS1-1"),
    ("L-electrons-ions",                "NGSS-SEP-2"),
    ("L-electrons-ions",                "NGSS-CCC-1"),
    ("L-electrons-ions",                "NGSS-CCC-6"),
    ("L-electrons-ions",                "AP-1.5"),

    ("L-electrons-intro-config",        "HS-PS1-1"),
    ("L-electrons-intro-config",        "NGSS-SEP-2"),
    ("L-electrons-intro-config",        "NGSS-CCC-1"),
    ("L-electrons-intro-config",        "NGSS-CCC-6"),
    ("L-electrons-intro-config",        "AP-1.5"),

    ("L-electrons-config-orbital",      "HS-PS1-1"),
    ("L-electrons-config-orbital",      "NGSS-SEP-2"),
    ("L-electrons-config-orbital",      "NGSS-CCC-1"),
    ("L-electrons-config-orbital",      "NGSS-CCC-6"),
    ("L-electrons-config-orbital",      "AP-1.5"),

    ("L-electrons-noble-gas",           "HS-PS1-1"),
    ("L-electrons-noble-gas",           "NGSS-SEP-2"),
    ("L-electrons-noble-gas",           "NGSS-CCC-1"),
    ("L-electrons-noble-gas",           "NGSS-CCC-6"),
    ("L-electrons-noble-gas",           "AP-1.5"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-periodic-table  (PS1-1)
    # SEP: Analyzing and Interpreting Data (SEP-4)
    # CCC: Patterns (CCC-1)
    # ══════════════════════════════════════════════════════════════════════
    ("L-periodic-history",              "HS-PS1-1"),
    ("L-periodic-history",              "NGSS-SEP-4"),
    ("L-periodic-history",              "NGSS-CCC-1"),

    ("L-periodic-atomic-size",          "HS-PS1-1"),
    ("L-periodic-atomic-size",          "NGSS-SEP-4"),
    ("L-periodic-atomic-size",          "NGSS-CCC-1"),
    ("L-periodic-atomic-size",          "AP-1.7"),

    ("L-periodic-ionization",           "HS-PS1-1"),
    ("L-periodic-ionization",           "NGSS-SEP-4"),
    ("L-periodic-ionization",           "NGSS-CCC-1"),
    ("L-periodic-ionization",           "AP-1.7"),

    ("L-periodic-electronegativity",    "HS-PS1-1"),
    ("L-periodic-electronegativity",    "NGSS-SEP-4"),
    ("L-periodic-electronegativity",    "NGSS-CCC-1"),
    ("L-periodic-electronegativity",    "AP-1.7"),
    ("L-periodic-electronegativity",    "AP-2.1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-bonding  (PS1-3, PS2-6)
    # SEP: Developing and Using Models (SEP-2)
    # CCC: Structure and Function (CCC-6)
    # ══════════════════════════════════════════════════════════════════════
    ("L-bonding-basics",                "HS-PS1-3"),
    ("L-bonding-basics",                "HS-PS2-6"),
    ("L-bonding-basics",                "NGSS-SEP-2"),
    ("L-bonding-basics",                "NGSS-CCC-6"),
    ("L-bonding-basics",                "AP-2.1"),

    ("L-bonding-ionic",                 "HS-PS1-3"),
    ("L-bonding-ionic",                 "HS-PS2-6"),
    ("L-bonding-ionic",                 "NGSS-SEP-2"),
    ("L-bonding-ionic",                 "NGSS-CCC-6"),
    ("L-bonding-ionic",                 "AP-2.3"),

    ("L-bonding-covalent",              "HS-PS1-3"),
    ("L-bonding-covalent",              "HS-PS2-6"),
    ("L-bonding-covalent",              "NGSS-SEP-2"),
    ("L-bonding-covalent",              "NGSS-CCC-6"),
    ("L-bonding-covalent",              "AP-2.5"),

    ("L-bonding-molecular-geometry",    "HS-PS1-3"),
    ("L-bonding-molecular-geometry",    "HS-PS2-6"),
    ("L-bonding-molecular-geometry",    "NGSS-SEP-2"),
    ("L-bonding-molecular-geometry",    "NGSS-CCC-6"),
    ("L-bonding-molecular-geometry",    "AP-2.7"),

    ("L-bonding-polarity",              "HS-PS1-3"),
    ("L-bonding-polarity",              "HS-PS2-6"),
    ("L-bonding-polarity",              "NGSS-SEP-2"),
    ("L-bonding-polarity",              "NGSS-CCC-6"),
    ("L-bonding-polarity",              "AP-2.1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-nomenclature  (PS1-2, PS1-7)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    #      Constructing Explanations (SEP-6)
    # CCC: — (none)
    # ══════════════════════════════════════════════════════════════════════
    ("L-nomenclature-properties",       "HS-PS1-2"),
    ("L-nomenclature-properties",       "HS-PS1-7"),
    ("L-nomenclature-properties",       "NGSS-SEP-5"),
    ("L-nomenclature-properties",       "NGSS-SEP-6"),
    ("L-nomenclature-properties",       "AP-2.1"),

    ("L-nomenclature-name-formula",     "HS-PS1-2"),
    ("L-nomenclature-name-formula",     "HS-PS1-7"),
    ("L-nomenclature-name-formula",     "NGSS-SEP-5"),
    ("L-nomenclature-name-formula",     "NGSS-SEP-6"),

    ("L-nomenclature-formula-name",     "HS-PS1-2"),
    ("L-nomenclature-formula-name",     "HS-PS1-7"),
    ("L-nomenclature-formula-name",     "NGSS-SEP-5"),
    ("L-nomenclature-formula-name",     "NGSS-SEP-6"),

    ("L-nomenclature-acids",            "HS-PS1-2"),
    ("L-nomenclature-acids",            "HS-PS1-7"),
    ("L-nomenclature-acids",            "NGSS-SEP-5"),
    ("L-nomenclature-acids",            "NGSS-SEP-6"),
    ("L-nomenclature-acids",            "AP-2.1"),

    ("L-nomenclature-covalent",         "HS-PS1-2"),
    ("L-nomenclature-covalent",         "HS-PS1-7"),
    ("L-nomenclature-covalent",         "NGSS-SEP-5"),
    ("L-nomenclature-covalent",         "NGSS-SEP-6"),
    ("L-nomenclature-covalent",         "AP-2.1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-dimensional-analysis  (N/A core standard)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    # CCC: Scale, Proportion, and Quantity (CCC-3)
    # ══════════════════════════════════════════════════════════════════════
    ("L-da-intro",                      "NGSS-SEP-5"),
    ("L-da-intro",                      "NGSS-CCC-3"),

    ("L-da-multi-step",                 "NGSS-SEP-5"),
    ("L-da-multi-step",                 "NGSS-CCC-3"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-mole  (PS1-7)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    # CCC: Energy and Matter (CCC-5), Scale, Proportion, and Quantity (CCC-3)
    # ══════════════════════════════════════════════════════════════════════
    ("L-mole-history",                  "HS-PS1-7"),
    ("L-mole-history",                  "NGSS-SEP-5"),
    ("L-mole-history",                  "NGSS-CCC-5"),
    ("L-mole-history",                  "NGSS-CCC-3"),
    ("L-mole-history",                  "AP-1.1"),

    ("L-mole-molar-mass-1step",         "HS-PS1-7"),
    ("L-mole-molar-mass-1step",         "NGSS-SEP-5"),
    ("L-mole-molar-mass-1step",         "NGSS-CCC-5"),
    ("L-mole-molar-mass-1step",         "NGSS-CCC-3"),
    ("L-mole-molar-mass-1step",         "AP-1.1"),

    ("L-mole-molar-mass-2step",         "HS-PS1-7"),
    ("L-mole-molar-mass-2step",         "NGSS-SEP-5"),
    ("L-mole-molar-mass-2step",         "NGSS-CCC-5"),
    ("L-mole-molar-mass-2step",         "NGSS-CCC-3"),
    ("L-mole-molar-mass-2step",         "AP-1.1"),

    ("L-mole-percent-composition",      "HS-PS1-7"),
    ("L-mole-percent-composition",      "NGSS-SEP-5"),
    ("L-mole-percent-composition",      "NGSS-CCC-5"),
    ("L-mole-percent-composition",      "NGSS-CCC-3"),
    ("L-mole-percent-composition",      "AP-1.3"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-chemical-reactions  (PS1-2, PS1-7)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    #      Constructing Explanations (SEP-6)
    # CCC: Energy and Matter (CCC-5)
    # ══════════════════════════════════════════════════════════════════════
    ("L-rxn-equations",                 "HS-PS1-2"),
    ("L-rxn-equations",                 "HS-PS1-7"),
    ("L-rxn-equations",                 "NGSS-SEP-5"),
    ("L-rxn-equations",                 "NGSS-SEP-6"),
    ("L-rxn-equations",                 "NGSS-CCC-5"),

    ("L-rxn-balancing",                 "HS-PS1-2"),
    ("L-rxn-balancing",                 "HS-PS1-7"),
    ("L-rxn-balancing",                 "NGSS-SEP-5"),
    ("L-rxn-balancing",                 "NGSS-SEP-6"),
    ("L-rxn-balancing",                 "NGSS-CCC-5"),

    ("L-rxn-both-skills",               "HS-PS1-2"),
    ("L-rxn-both-skills",               "HS-PS1-7"),
    ("L-rxn-both-skills",               "NGSS-SEP-5"),
    ("L-rxn-both-skills",               "NGSS-SEP-6"),
    ("L-rxn-both-skills",               "NGSS-CCC-5"),

    ("L-rxn-synthesis-decomp",          "HS-PS1-2"),
    ("L-rxn-synthesis-decomp",          "HS-PS1-7"),
    ("L-rxn-synthesis-decomp",          "NGSS-SEP-5"),
    ("L-rxn-synthesis-decomp",          "NGSS-SEP-6"),
    ("L-rxn-synthesis-decomp",          "NGSS-CCC-5"),

    ("L-rxn-single-replacement",        "HS-PS1-2"),
    ("L-rxn-single-replacement",        "HS-PS1-7"),
    ("L-rxn-single-replacement",        "NGSS-SEP-5"),
    ("L-rxn-single-replacement",        "NGSS-SEP-6"),
    ("L-rxn-single-replacement",        "NGSS-CCC-5"),

    ("L-rxn-double-replacement",        "HS-PS1-2"),
    ("L-rxn-double-replacement",        "HS-PS1-7"),
    ("L-rxn-double-replacement",        "NGSS-SEP-5"),
    ("L-rxn-double-replacement",        "NGSS-SEP-6"),
    ("L-rxn-double-replacement",        "NGSS-CCC-5"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-stoichiometry  (PS1-7)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    # CCC: Energy and Matter (CCC-5)
    # ══════════════════════════════════════════════════════════════════════
    ("L-stoich-mole-mole",              "HS-PS1-7"),
    ("L-stoich-mole-mole",              "NGSS-SEP-5"),
    ("L-stoich-mole-mole",              "NGSS-CCC-5"),
    ("L-stoich-mole-mole",              "AP-4.5"),

    ("L-stoich-mass-mass",              "HS-PS1-7"),
    ("L-stoich-mass-mass",              "NGSS-SEP-5"),
    ("L-stoich-mass-mass",              "NGSS-CCC-5"),
    ("L-stoich-mass-mass",              "AP-4.5"),

    ("L-stoich-limiting",               "HS-PS1-7"),
    ("L-stoich-limiting",               "NGSS-SEP-5"),
    ("L-stoich-limiting",               "NGSS-CCC-5"),
    ("L-stoich-limiting",               "AP-4.5"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-solutions  (PS1-2, PS1-5)
    # SEP: Analyzing and Interpreting Data (SEP-4)
    # CCC: Energy and Matter (CCC-5), Structure and Function (CCC-6)
    # ══════════════════════════════════════════════════════════════════════
    ("L-solutions-intro",               "HS-PS1-2"),
    ("L-solutions-intro",               "HS-PS1-5"),
    ("L-solutions-intro",               "NGSS-SEP-4"),
    ("L-solutions-intro",               "NGSS-CCC-5"),
    ("L-solutions-intro",               "NGSS-CCC-6"),

    ("L-solutions-molarity",            "HS-PS1-2"),
    ("L-solutions-molarity",            "HS-PS1-5"),
    ("L-solutions-molarity",            "NGSS-SEP-4"),
    ("L-solutions-molarity",            "NGSS-CCC-5"),
    ("L-solutions-molarity",            "NGSS-CCC-6"),
    ("L-solutions-molarity",            "AP-3.8"),

    ("L-solutions-acids-bases-props",   "HS-PS1-2"),
    ("L-solutions-acids-bases-props",   "HS-PS1-5"),
    ("L-solutions-acids-bases-props",   "NGSS-SEP-4"),
    ("L-solutions-acids-bases-props",   "NGSS-CCC-5"),
    ("L-solutions-acids-bases-props",   "NGSS-CCC-6"),
    ("L-solutions-acids-bases-props",   "AP-8.1"),

    ("L-solutions-acid-base-calc",      "HS-PS1-2"),
    ("L-solutions-acid-base-calc",      "HS-PS1-5"),
    ("L-solutions-acid-base-calc",      "NGSS-SEP-4"),
    ("L-solutions-acid-base-calc",      "NGSS-CCC-5"),
    ("L-solutions-acid-base-calc",      "NGSS-CCC-6"),
    ("L-solutions-acid-base-calc",      "AP-8.2"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-thermochem  (PS3-1, PS3-2, PS1-4)
    # SEP: Developing and Using Models (SEP-2)
    #      Using Mathematics and Computational Thinking (SEP-5)
    # CCC: Energy and Matter (CCC-5)
    # ══════════════════════════════════════════════════════════════════════
    ("L-thermo-intro",                  "HS-PS3-1"),
    ("L-thermo-intro",                  "HS-PS3-2"),
    ("L-thermo-intro",                  "HS-PS1-4"),
    ("L-thermo-intro",                  "NGSS-SEP-2"),
    ("L-thermo-intro",                  "NGSS-SEP-5"),
    ("L-thermo-intro",                  "NGSS-CCC-5"),
    ("L-thermo-intro",                  "AP-6.1"),

    ("L-thermo-calorimetry",            "HS-PS3-1"),
    ("L-thermo-calorimetry",            "HS-PS3-2"),
    ("L-thermo-calorimetry",            "HS-PS1-4"),
    ("L-thermo-calorimetry",            "NGSS-SEP-2"),
    ("L-thermo-calorimetry",            "NGSS-SEP-5"),
    ("L-thermo-calorimetry",            "NGSS-CCC-5"),
    ("L-thermo-calorimetry",            "AP-6.4"),

    ("L-thermo-equations",              "HS-PS3-1"),
    ("L-thermo-equations",              "HS-PS3-2"),
    ("L-thermo-equations",              "HS-PS1-4"),
    ("L-thermo-equations",              "NGSS-SEP-2"),
    ("L-thermo-equations",              "NGSS-SEP-5"),
    ("L-thermo-equations",              "NGSS-CCC-5"),
    ("L-thermo-equations",              "AP-6.8"),
    ("L-thermo-equations",              "AP-6.9"),

    ("L-thermo-heating-curves",         "HS-PS3-1"),
    ("L-thermo-heating-curves",         "HS-PS3-2"),
    ("L-thermo-heating-curves",         "HS-PS1-4"),
    ("L-thermo-heating-curves",         "NGSS-SEP-2"),
    ("L-thermo-heating-curves",         "NGSS-SEP-5"),
    ("L-thermo-heating-curves",         "NGSS-CCC-5"),
    ("L-thermo-heating-curves",         "AP-6.1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-kinetic-theory  (PS3-2, PS1-4)
    # SEP: Developing and Using Models (SEP-2)
    # CCC: Energy and Matter (CCC-5)
    # ══════════════════════════════════════════════════════════════════════
    ("L-kmt-gases",                     "HS-PS3-2"),
    ("L-kmt-gases",                     "HS-PS1-4"),
    ("L-kmt-gases",                     "NGSS-SEP-2"),
    ("L-kmt-gases",                     "NGSS-CCC-5"),
    ("L-kmt-gases",                     "AP-3.4"),

    ("L-kmt-liquids",                   "HS-PS3-2"),
    ("L-kmt-liquids",                   "HS-PS1-4"),
    ("L-kmt-liquids",                   "NGSS-SEP-2"),
    ("L-kmt-liquids",                   "NGSS-CCC-5"),
    ("L-kmt-liquids",                   "AP-3.1"),

    ("L-kmt-solids",                    "HS-PS3-2"),
    ("L-kmt-solids",                    "HS-PS1-4"),
    ("L-kmt-solids",                    "NGSS-SEP-2"),
    ("L-kmt-solids",                    "NGSS-CCC-5"),
    ("L-kmt-solids",                    "AP-3.1"),

    ("L-kmt-phase-diagrams",            "HS-PS3-2"),
    ("L-kmt-phase-diagrams",            "HS-PS1-4"),
    ("L-kmt-phase-diagrams",            "NGSS-SEP-2"),
    ("L-kmt-phase-diagrams",            "NGSS-CCC-5"),
    ("L-kmt-phase-diagrams",            "AP-3.1"),

    # ══════════════════════════════════════════════════════════════════════
    # unit-gas-laws  (PS3-1, PS3-2)
    # SEP: Using Mathematics and Computational Thinking (SEP-5)
    # CCC: Scale, Proportion, and Quantity (CCC-3)
    # ══════════════════════════════════════════════════════════════════════
    ("L-gas-intro",                     "HS-PS3-1"),
    ("L-gas-intro",                     "HS-PS3-2"),
    ("L-gas-intro",                     "NGSS-SEP-5"),
    ("L-gas-intro",                     "NGSS-CCC-3"),
    ("L-gas-intro",                     "AP-3.4"),

    ("L-gas-boyle-charles",             "HS-PS3-1"),
    ("L-gas-boyle-charles",             "HS-PS3-2"),
    ("L-gas-boyle-charles",             "NGSS-SEP-5"),
    ("L-gas-boyle-charles",             "NGSS-CCC-3"),
    ("L-gas-boyle-charles",             "AP-3.4"),

    ("L-gas-gay-lussac-combined",       "HS-PS3-1"),
    ("L-gas-gay-lussac-combined",       "HS-PS3-2"),
    ("L-gas-gay-lussac-combined",       "NGSS-SEP-5"),
    ("L-gas-gay-lussac-combined",       "NGSS-CCC-3"),
    ("L-gas-gay-lussac-combined",       "AP-3.4"),

    ("L-gas-ideal",                     "HS-PS3-1"),
    ("L-gas-ideal",                     "HS-PS3-2"),
    ("L-gas-ideal",                     "NGSS-SEP-5"),
    ("L-gas-ideal",                     "NGSS-CCC-3"),
    ("L-gas-ideal",                     "AP-3.4"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only extensions — Atomic Structure (ap-unit-1)
    # ══════════════════════════════════════════════════════════════════════
    ("L-mass-spectrometry",             "AP-1.2"),
    ("L-pes",                           "AP-1.6"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only extensions — Bonding (ap-unit-2)
    # ══════════════════════════════════════════════════════════════════════
    ("L-bonding-formal-charge",         "AP-2.6"),
    ("L-bonding-hybridization",         "AP-2.7"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only extensions — IMF / Gas (ap-unit-3)
    # ══════════════════════════════════════════════════════════════════════
    ("L-gas-van-der-waals",             "AP-3.4"),
    ("L-solutions-beer-lambert",        "AP-3.13"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only extensions — Chemical Reactions (ap-unit-4)
    # ══════════════════════════════════════════════════════════════════════
    ("L-rxn-net-ionic",                 "AP-4.2"),
    ("L-rxn-redox-titration",           "AP-4.6"),
    ("L-rxn-redox-titration",           "AP-4.9"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only — Kinetics (ap-unit-5)
    # HS-PS1-5 applies: "explain how changing conditions affect reaction rates"
    # ══════════════════════════════════════════════════════════════════════
    ("L-ap-kinetics-rate-laws",         "AP-5.1"),
    ("L-ap-kinetics-rate-laws",         "AP-5.2"),
    ("L-ap-kinetics-rate-laws",         "HS-PS1-5"),

    ("L-kinetics-zero-order",           "AP-5.3"),
    ("L-kinetics-zero-order",           "HS-PS1-5"),

    ("L-kinetics-first-order",          "AP-5.3"),
    ("L-kinetics-first-order",          "HS-PS1-5"),

    ("L-kinetics-second-order",         "AP-5.3"),
    ("L-kinetics-second-order",         "HS-PS1-5"),

    ("L-kinetics-comparison",           "AP-5.3"),
    ("L-kinetics-comparison",           "HS-PS1-5"),

    ("L-ap-kinetics-mechanisms",        "AP-5.8"),

    ("L-ap-kinetics-arrhenius",         "AP-5.5"),
    ("L-ap-kinetics-arrhenius",         "HS-PS1-5"),

    ("L-ap-kinetics-catalysis",         "AP-5.11"),
    ("L-ap-kinetics-catalysis",         "HS-PS1-5"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only extensions — Thermodynamics (ap-unit-6)
    # HS-PS1-4: "models show energy absorbed/released when bonds form or break"
    # ══════════════════════════════════════════════════════════════════════
    ("L-thermo-bond-enthalpies",        "AP-6.8"),
    ("L-thermo-bond-enthalpies",        "HS-PS1-4"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only — Equilibrium (ap-unit-7)
    # ══════════════════════════════════════════════════════════════════════
    ("L-ap-eq-intro-kc",                "AP-7.4"),
    ("L-ap-eq-kp",                      "AP-7.4"),
    ("L-ap-eq-q",                       "AP-7.2"),
    ("L-ap-eq-le-chatelier",            "AP-7.9"),
    ("L-ap-eq-ice",                     "AP-7.4"),
    ("L-ap-eq-ksp",                     "AP-7.11"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only — Acids & Bases (ap-unit-8)
    # ══════════════════════════════════════════════════════════════════════
    ("L-solutions-weak-acids-pt1",      "AP-8.3"),
    ("L-solutions-weak-acids-pt2",      "AP-8.3"),
    ("L-ap-acid-kakb",                  "AP-8.3"),
    ("L-ap-acid-salt-hydrolysis",       "AP-8.3"),
    ("L-ap-acid-buffers",               "AP-8.8"),
    ("L-ap-acid-titration-curves",      "AP-8.5"),
    ("L-ap-acid-polyprotic",            "AP-8.3"),
    ("L-ap-acid-polyprotic",            "AP-8.5"),

    # ══════════════════════════════════════════════════════════════════════
    # AP-only — Applications of Thermodynamics (ap-unit-9)
    # ══════════════════════════════════════════════════════════════════════
    ("L-ap-thermo-entropy",             "AP-9.1"),
    ("L-ap-thermo-gibbs",               "AP-9.3"),
    ("L-ap-thermo-dg-k-e",             "AP-9.5"),
    ("L-ap-thermo-dg-k-e",             "AP-9.8"),
    ("L-ap-electro-galvanic",           "AP-9.7"),
    ("L-ap-electro-nernst",             "AP-9.8"),
    ("L-ap-electro-electrolysis",       "AP-9.7"),
    ("L-ap-electro-faraday",            "AP-9.8"),
]
