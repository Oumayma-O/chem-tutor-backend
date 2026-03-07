"""Phase groupings for Standard Chemistry and AP Chemistry."""

STANDARD_PHASES: list[dict] = [
    {
        "name": "Phase 1: The Basics",
        "description": "Foundational tools: measurement, dimensional analysis, and the mole.",
        "sort_order": 0, "color": "#6366f1",
        "units": [("unit-intro-chem", 0), ("unit-dimensional-analysis", 1), ("unit-mole", 2)],
    },
    {
        "name": "Phase 2: Atomic Level",
        "description": "Atomic theory, electron configurations, and periodic trends.",
        "sort_order": 1, "color": "#8b5cf6",
        "units": [("unit-atomic-theory", 0), ("unit-electrons", 1), ("unit-periodic-table", 2)],
    },
    {
        "name": "Phase 3: Building Molecules",
        "description": "Nomenclature, chemical bonding, KMT, and gas laws.",
        "sort_order": 2, "color": "#f59e0b",
        "units": [("unit-nomenclature", 0), ("unit-bonding", 1), ("unit-kinetic-theory", 2), ("unit-gas-laws", 3)],
    },
    {
        "name": "Phase 4: The Core Reactions",
        "description": "Reaction types, stoichiometry, and solutions.",
        "sort_order": 3, "color": "#ef4444",
        "units": [("unit-chemical-reactions", 0), ("unit-stoichiometry", 1), ("unit-solutions", 2)],
    },
    {
        "name": "Phase 5: Energy & Advanced",
        "description": "Thermochemistry and nuclear chemistry.",
        "sort_order": 4, "color": "#10b981",
        "units": [("unit-thermochem", 0), ("unit-nuclear-chem", 1)],
    },
]

AP_PHASES: list[dict] = [
    {
        "name": "Phase 1: Foundations of Matter",
        "description": "Atomic structure, compound structure, mass spec, PES, hybridization.",
        "sort_order": 0, "color": "#6366f1",
        "units": [("ap-unit-1", 0), ("ap-unit-2", 1)],
    },
    {
        "name": "Phase 2: States & Interactions",
        "description": "Intermolecular forces, gas laws, real gases, Beer's law, net ionic eqs.",
        "sort_order": 1, "color": "#8b5cf6",
        "units": [("ap-unit-3", 0), ("ap-unit-4", 1)],
    },
    {
        "name": "Phase 3: Reaction Dynamics",
        "description": "Rate laws, mechanisms, calorimetry, Hess's law, bond enthalpies.",
        "sort_order": 2, "color": "#f59e0b",
        "units": [("ap-unit-5", 0), ("ap-unit-6", 1)],
    },
    {
        "name": "Phase 4: Chemical Equilibrium",
        "description": "Ksp, Le Chatelier, buffers, titrations, polyprotic acids.",
        "sort_order": 3, "color": "#ef4444",
        "units": [("ap-unit-7", 0), ("ap-unit-8", 1)],
    },
    {
        "name": "Phase 5: Entropy & Electrons",
        "description": "Gibbs free energy, galvanic/electrolytic cells, Faraday's laws.",
        "sort_order": 4, "color": "#10b981",
        "units": [("ap-unit-9", 0)],
    },
]
