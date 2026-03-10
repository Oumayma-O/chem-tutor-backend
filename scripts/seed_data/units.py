"""
Unit definitions and curriculum bridge map.

STANDARD_UNITS — 15 General Chemistry units
AP_UNITS       — 9 College Board AP Chemistry units
UNIT_BRIDGE_MAP — Standard→AP progression hints
"""

STANDARD_UNITS: list[dict] = [
    {
        "id": "unit-intro-chem", "sort_order": 1,
        "title": "Introduction to Chemistry", "icon": "🧪",
        "description": "Lab safety, scientific method, classification of matter, and measurement.",
        "lesson_ids": ["L-intro-safety", "L-intro-scientific-method", "L-intro-classification-matter", "L-intro-chem-phys-changes", "L-intro-measurement"],
    },
    {
        "id": "unit-atomic-theory", "sort_order": 2,
        "title": "Atomic Theory & Structure", "icon": "⚛️",
        "description": "History of atomic theory, atomic structure, and average atomic mass.",
        "lesson_ids": ["L-atomic-history", "L-atomic-structure", "L-atomic-mass"],
    },
    {
        "id": "unit-nuclear-chem", "sort_order": 3,
        "title": "Nuclear Chemistry", "icon": "☢️",
        "description": "Types of radiation, radioactive decay, half-life, and nuclear reactions.",
        "lesson_ids": ["L-nuclear-intro", "L-nuclear-radioactive-decay", "L-nuclear-reactions"],
    },
    {
        "id": "unit-electrons", "sort_order": 4,
        "title": "Electrons & Electron Configurations", "icon": "⚡",
        "description": "Ions, electron configurations, orbital notation, and valence electrons.",
        "lesson_ids": ["L-electrons-ions", "L-electrons-intro-config", "L-electrons-config-orbital", "L-electrons-noble-gas"],
    },
    {
        "id": "unit-periodic-table", "sort_order": 5,
        "title": "The Periodic Table", "icon": "📊",
        "description": "History of the periodic table and periodic trends: atomic size, ionization energy, electronegativity.",
        "lesson_ids": ["L-periodic-history", "L-periodic-atomic-size", "L-periodic-ionization", "L-periodic-electronegativity"],
    },
    {
        "id": "unit-bonding", "sort_order": 6,
        "title": "Chemical Bonding", "icon": "🔗",
        "description": "Ionic bonding, covalent bonding, molecular geometry, and polarity.",
        "lesson_ids": ["L-bonding-basics", "L-bonding-ionic", "L-bonding-covalent", "L-bonding-molecular-geometry", "L-bonding-polarity"],
    },
    {
        "id": "unit-nomenclature", "sort_order": 7,
        "title": "Chemical Nomenclature", "icon": "🏷️",
        "description": "Naming ionic compounds, covalent compounds, and acids.",
        "lesson_ids": ["L-nomenclature-properties", "L-nomenclature-name-formula", "L-nomenclature-formula-name", "L-nomenclature-acids", "L-nomenclature-covalent"],
    },
    {
        "id": "unit-dimensional-analysis", "sort_order": 8,
        "title": "Dimensional Analysis", "icon": "📐",
        "description": "Single-step and multi-step unit conversions using dimensional analysis.",
        "lesson_ids": ["L-da-intro", "L-da-multi-step"],
    },
    {
        "id": "unit-mole", "sort_order": 9,
        "title": "The Mole", "icon": "🐭",
        "description": "Avogadro's number, molar mass conversions, and percent composition.",
        "lesson_ids": ["L-mole-history", "L-mole-molar-mass-1step", "L-mole-molar-mass-2step", "L-mole-percent-composition"],
    },
    {
        "id": "unit-chemical-reactions", "sort_order": 10,
        "title": "Chemical Reactions", "icon": "⚗️",
        "description": "Writing and balancing equations; synthesis, decomposition, and replacement reactions.",
        "lesson_ids": ["L-rxn-equations", "L-rxn-balancing", "L-rxn-both-skills", "L-rxn-synthesis-decomp", "L-rxn-single-replacement", "L-rxn-double-replacement"],
    },
    {
        "id": "unit-stoichiometry", "sort_order": 11,
        "title": "Stoichiometry", "icon": "⚖️",
        "description": "Mole ratios, mass-mass calculations, limiting reactants, and percent yield.",
        "lesson_ids": ["L-stoich-mole-mole", "L-stoich-mass-mass", "L-stoich-limiting"],
    },
    {
        "id": "unit-solutions", "sort_order": 12,
        "title": "Solutions", "icon": "💧",
        "description": "Molarity, acid-base properties, and pH calculations.",
        "lesson_ids": ["L-solutions-intro", "L-solutions-molarity", "L-solutions-acids-bases-props", "L-solutions-acid-base-calc"],
    },
    {
        "id": "unit-thermochem", "sort_order": 13,
        "title": "Thermochemistry", "icon": "🔥",
        "description": "Calorimetry, thermochemical equations, Hess's law, and heating curves.",
        "lesson_ids": ["L-thermo-intro", "L-thermo-calorimetry", "L-thermo-equations", "L-thermo-heating-curves"],
    },
    {
        "id": "unit-kinetic-theory", "sort_order": 14,
        "title": "Kinetic Molecular Theory", "icon": "💨",
        "description": "KMT for gases, liquids, and solids; phase diagrams.",
        "lesson_ids": ["L-kmt-gases", "L-kmt-liquids", "L-kmt-solids", "L-kmt-phase-diagrams"],
    },
    {
        "id": "unit-gas-laws", "sort_order": 15,
        "title": "Gas Laws", "icon": "🎈",
        "description": "Boyle's, Charles', Gay-Lussac's, combined, and ideal gas laws.",
        "lesson_ids": ["L-gas-intro", "L-gas-boyle-charles", "L-gas-gay-lussac-combined", "L-gas-ideal"],
    },
]

AP_UNITS: list[dict] = [
    {
        "id": "ap-unit-1", "sort_order": 1,
        "title": "Atomic Structure & Properties", "icon": "⚛️",
        "description": "Moles, molar mass, atomic structure, electron configurations, mass spectrometry, PES, and periodic trends.",
        "lesson_ids": ["L-mole-molar-mass-1step", "L-mole-molar-mass-2step", "L-mole-percent-composition", "L-atomic-structure", "L-atomic-mass", "L-electrons-intro-config", "L-electrons-config-orbital", "L-electrons-noble-gas", "L-mass-spectrometry", "L-pes", "L-periodic-atomic-size", "L-periodic-ionization", "L-periodic-electronegativity"],
    },
    {
        "id": "ap-unit-2", "sort_order": 2,
        "title": "Molecular & Ionic Compound Structure & Properties", "icon": "🔗",
        "description": "All bond types, molecular geometry, polarity, formal charge, resonance, and hybridization.",
        "lesson_ids": ["L-bonding-basics", "L-bonding-ionic", "L-bonding-covalent", "L-bonding-molecular-geometry", "L-bonding-polarity", "L-bonding-formal-charge", "L-bonding-hybridization"],
    },
    {
        "id": "ap-unit-3", "sort_order": 3,
        "title": "Intermolecular Forces & Properties", "icon": "💧",
        "description": "KMT, phase diagrams, gas laws, real gases, solutions, molarity, and Beer-Lambert law.",
        "lesson_ids": ["L-kmt-gases", "L-kmt-liquids", "L-kmt-solids", "L-kmt-phase-diagrams", "L-gas-boyle-charles", "L-gas-gay-lussac-combined", "L-gas-ideal", "L-gas-van-der-waals", "L-solutions-intro", "L-solutions-molarity", "L-solutions-beer-lambert"],
    },
    {
        "id": "ap-unit-4", "sort_order": 4,
        "title": "Chemical Reactions", "icon": "⚗️",
        "description": "Balancing, reaction types, net ionic equations, redox, stoichiometry, and limiting reactants.",
        "lesson_ids": ["L-rxn-balancing", "L-rxn-synthesis-decomp", "L-rxn-single-replacement", "L-rxn-double-replacement", "L-rxn-net-ionic", "L-rxn-redox-titration", "L-stoich-mole-mole", "L-stoich-mass-mass", "L-stoich-limiting"],
    },
    {
        "id": "ap-unit-5", "sort_order": 5,
        "title": "Kinetics", "icon": "⏱️",
        "description": "Reaction rates, zero/first/second order, comparison, mechanisms, Arrhenius, catalysis.",
        "lesson_ids": ["L-ap-kinetics-rate-laws", "L-kinetics-zero-order", "L-kinetics-first-order", "L-kinetics-second-order", "L-kinetics-comparison", "L-ap-kinetics-mechanisms", "L-ap-kinetics-arrhenius", "L-ap-kinetics-catalysis"],
    },
    {
        "id": "ap-unit-6", "sort_order": 6,
        "title": "Thermodynamics", "icon": "🔥",
        "description": "Thermochemistry, calorimetry, Hess's law, heating curves, and bond enthalpies.",
        "lesson_ids": ["L-thermo-intro", "L-thermo-calorimetry", "L-thermo-equations", "L-thermo-heating-curves", "L-thermo-bond-enthalpies"],
    },
    {
        "id": "ap-unit-7", "sort_order": 7,
        "title": "Equilibrium", "icon": "⚖️",
        "description": "Equilibrium constants Kc and Kp, reaction quotient Q, Le Châtelier's principle, ICE tables, and Ksp.",
        "lesson_ids": ["L-ap-eq-intro-kc", "L-ap-eq-kp", "L-ap-eq-q", "L-ap-eq-le-chatelier", "L-ap-eq-ice", "L-ap-eq-ksp"],
    },
    {
        "id": "ap-unit-8", "sort_order": 8,
        "title": "Acids & Bases", "icon": "🧪",
        "description": "Acid-base properties, pH, weak acids, Ka/Kb, buffers, titration curves, and polyprotic acids.",
        "lesson_ids": ["L-solutions-acids-bases-props", "L-solutions-acid-base-calc", "L-solutions-weak-acids-pt1", "L-solutions-weak-acids-pt2", "L-ap-acid-kakb", "L-ap-acid-salt-hydrolysis", "L-ap-acid-buffers", "L-ap-acid-titration-curves", "L-ap-acid-polyprotic"],
    },
    {
        "id": "ap-unit-9", "sort_order": 9,
        "title": "Applications of Thermodynamics", "icon": "⚡",
        "description": "Entropy, Gibbs free energy, ΔG°/K/E° relationships, galvanic cells, Nernst equation, electrolysis, and Faraday's laws.",
        "lesson_ids": ["L-ap-thermo-entropy", "L-ap-thermo-gibbs", "L-ap-thermo-dg-k-e", "L-ap-electro-galvanic", "L-ap-electro-nernst", "L-ap-electro-electrolysis", "L-ap-electro-faraday"],
    },
]

# Maps Standard units to the AP units they feed into (for bridge UI / progress calc).
UNIT_BRIDGE_MAP: list[dict] = [
    {"standard_unit_id": "unit-atomic-theory",     "leads_into_ap_unit": "ap-unit-1", "bridge_description": "Standard structure provides the 'What'; AP Mass Spec/PES provides the 'How we know'."},
    {"standard_unit_id": "unit-bonding",            "leads_into_ap_unit": "ap-unit-2", "bridge_description": "Standard bonding covers shapes; AP adds electron delocalization and orbital hybridization."},
    {"standard_unit_id": "unit-chemical-reactions", "leads_into_ap_unit": "ap-unit-5", "bridge_description": "You can't study how fast a reaction goes until you know how to balance it."},
    {"standard_unit_id": "unit-stoichiometry",      "leads_into_ap_unit": "ap-unit-7", "bridge_description": "Equilibrium is stoichiometry with a limit."},
    {"standard_unit_id": "unit-electrons",          "leads_into_ap_unit": "ap-unit-9", "bridge_description": "Electron transfer and redox underpin electrochemistry."},
    {"standard_unit_id": "unit-solutions",          "leads_into_ap_unit": "ap-unit-8", "bridge_description": "Moving from basic pH of strong acids to equilibrium-based weak acid chemistry."},
]
