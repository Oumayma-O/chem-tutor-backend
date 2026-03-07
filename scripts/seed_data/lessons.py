"""
Master Lesson Library — single source of truth for all lessons.

Each key is the stable slug used as Lesson.slug in the DB.
canonical_unit / canonical_index define the primary (unit_id, lesson_index) stored
on the Lesson row. Lessons shared across units are linked via unit_lessons junction.
"""

MASTER_LESSONS: dict[str, dict] = {

    # ══════════════════════════════════════════════════════
    # unit-intro-chem  (Introduction to Chemistry)
    # ══════════════════════════════════════════════════════

    "L-intro-safety": {
        "title": "Safety",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Always wear safety goggles and appropriate protective equipment",
            "Never eat or drink in the laboratory",
            "Know the location of safety equipment (eyewash, fire extinguisher, safety shower)",
            "Dispose of chemicals according to lab instructions",
        ],
        "misconceptions": [
            "Lab coats or goggles are only needed for 'dangerous' chemicals",
            "A lab fire can be put out with water (not always true for chemical fires)",
            "Smelling a chemical directly is the best way to identify it (wafting is required)",
        ],
        "objectives": [
            "Identify common lab safety rules",
            "Recognize hazard symbols",
        ],
        "canonical_unit": "unit-intro-chem",
        "canonical_index": 0,
    },

    "L-intro-scientific-method": {
        "title": "Scientific Method",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Observation leads to a question",
            "A hypothesis must be testable and falsifiable",
            "Experiments must include controlled variables",
            "Results must be reproducible",
        ],
        "misconceptions": [
            "A 'Theory' is just a guess (in science, it is a well-supported explanation)",
            "Experiments must prove the hypothesis right to be successful",
            "The scientific method is a rigid, linear set of steps",
        ],
        "objectives": [
            "Describe steps of the scientific method",
            "Distinguish hypothesis from theory",
        ],
        "canonical_unit": "unit-intro-chem",
        "canonical_index": 1,
    },

    "L-intro-classification-matter": {
        "title": "Classification of Matter",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Elements consist of only one type of atom",
            "Compounds contain two or more elements chemically bonded",
            "Mixtures contain substances physically combined",
            "Mixtures can be homogeneous or heterogeneous",
        ],
        "misconceptions": [
            "A compound is just a mixture of elements",
            "Heterogeneous mixtures are always visible to the naked eye",
            "Pure water is the same as tap water (tap water is a mixture)",
        ],
        "objectives": [
            "Classify matter as element, compound, or mixture",
            "Distinguish pure substances from mixtures",
        ],
        "canonical_unit": "unit-intro-chem",
        "canonical_index": 2,
    },

    "L-intro-chem-phys-changes": {
        "title": "Chemical & Physical Changes",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Physical changes alter form but not chemical composition",
            "Chemical changes produce new substances",
            "Indicators of chemical change include gas formation, precipitate, color change, or heat release",
        ],
        "misconceptions": [
            "Boiling water is a chemical change because gas is formed",
            "Dissolving sugar is a chemical change",
            "Mass is lost during a chemical reaction if a gas escapes",
        ],
        "objectives": [
            "Identify chemical vs physical changes",
            "Give examples of each type",
        ],
        "canonical_unit": "unit-intro-chem",
        "canonical_index": 3,
    },

    "L-intro-measurement": {
        "title": "Measurement & Scientific Notation",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "value × 10^n",
            "density = mass / volume",
        ],
        "key_rules": [
            "SI units are the standard measurement system in science",
            "Metric prefixes represent powers of ten",
            "Measurements must include units",
            "Significant figures reflect measurement precision",
        ],
        "misconceptions": [
            "Scientific notation can only be used for very large numbers",
            "Zeros are never significant",
            "Density depends on the amount of substance (it is an intensive property)",
        ],
        "objectives": [
            "Use SI units and metric prefixes",
            "Express numbers in scientific notation",
            "Perform unit conversions",
            "Calculate density",
        ],
        "canonical_unit": "unit-intro-chem",
        "canonical_index": 4,
    },

    # ══════════════════════════════════════════════════════
    # unit-atomic-theory  (Atomic Theory & Structure)
    # ══════════════════════════════════════════════════════

    "L-atomic-history": {
        "title": "History & Basics of Atomic Theory",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Dalton proposed atoms as indivisible particles",
            "Thomson discovered the electron via cathode ray tube",
            "Rutherford discovered the nucleus via gold foil experiment",
            "Bohr proposed quantized electron energy levels",
        ],
        "misconceptions": [
            "Electrons orbit the nucleus like planets (Bohr model vs. Quantum model)",
            "The atom is mostly solid matter",
            "Scientific models never change",
        ],
        "objectives": [
            "Trace development of the atomic model",
            "Describe contributions of key scientists",
        ],
        "canonical_unit": "unit-atomic-theory",
        "canonical_index": 0,
    },

    "L-atomic-structure": {
        "title": "Atomic Structure",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "Mass Number (A) = Z + n",
            "Charge = protons - electrons",
        ],
        "key_rules": [
            "Atomic number (Z) defines the element",
            "Protons and neutrons reside in the nucleus",
            "Electrons reside in the electron cloud",
        ],
        "misconceptions": [
            "Atomic mass equals mass number",
            "Protons and electrons have the same mass",
            "Neutrons have a charge",
        ],
        "objectives": [
            "Identify protons, neutrons, and electrons",
            "Determine particle counts",
        ],
        "canonical_unit": "unit-atomic-theory",
        "canonical_index": 1,
    },

    "L-atomic-mass": {
        "title": "Atomic Mass",
        "blueprint": "solver",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "Avg Atomic Mass = Σ(Isotope Mass × Fractional Abundance)",
        ],
        "key_rules": [
            "Abundance must be converted from percentage to decimal",
            "Isotopes of an element have different numbers of neutrons",
        ],
        "misconceptions": [
            "The atomic mass on the periodic table is the mass of a single atom",
            "All isotopes of an element exist in equal amounts (50/50)",
            "Isotopes have different chemical properties",
        ],
        "objectives": [
            "Calculate average atomic mass",
            "Interpret isotope data",
        ],
        "canonical_unit": "unit-atomic-theory",
        "canonical_index": 2,
    },

    # ══════════════════════════════════════════════════════
    # unit-nuclear-chem  (Nuclear Chemistry)
    # ══════════════════════════════════════════════════════

    "L-nuclear-intro": {
        "title": "Introduction to Nuclear Chemistry",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Distinguish nuclear reactions from chemical reactions",
            "Identify types of radiation (alpha, beta, gamma)",
        ],
        "canonical_unit": "unit-nuclear-chem",
        "canonical_index": 0,
    },

    "L-nuclear-radioactive-decay": {
        "title": "Radioactive Decay & Half-Life",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "t½ = 0.693 / k",
            "N = N₀ × (1/2)^(t / t½)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Calculate remaining quantity after radioactive decay",
            "Solve half-life problems",
        ],
        "canonical_unit": "unit-nuclear-chem",
        "canonical_index": 1,
    },

    "L-nuclear-reactions": {
        "title": "Nuclear Reactions",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "E = mc²",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write balanced nuclear equations",
            "Compare fission and fusion",
        ],
        "canonical_unit": "unit-nuclear-chem",
        "canonical_index": 2,
    },

    # ══════════════════════════════════════════════════════
    # unit-electrons  (Electrons & Electron Configurations)
    # ══════════════════════════════════════════════════════

    "L-electrons-ions": {
        "title": "Ions",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Cations are positive (lose electrons)",
            "Anions are negative (gain electrons)",
            "Metals tend to form cations; nonmetals tend to form anions",
        ],
        "misconceptions": [
            "A positive charge means protons were added",
            "Ions are the same as isotopes",
            "Anions are smaller than their parent atoms (anions are actually larger)",
        ],
        "objectives": [
            "Determine ion charge from electron gain/loss",
            "Write ion symbols",
        ],
        "canonical_unit": "unit-electrons",
        "canonical_index": 0,
    },

    "L-electrons-intro-config": {
        "title": "Intro to Electron Configurations",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Aufbau Principle: Electrons fill lowest energy levels first",
            "Pauli Exclusion Principle: Max 2 electrons per orbital with opposite spins",
            "Hund's Rule: Electrons fill degenerate orbitals singly before pairing",
        ],
        "misconceptions": [
            "Energy levels fill in a simple 1, 2, 3, 4 numerical order (4s before 3d)",
            "Electrons move in circular paths",
            "Shells can hold an infinite number of electrons",
        ],
        "objectives": [
            "Explain the Aufbau principle",
            "Write basic electron configurations",
        ],
        "canonical_unit": "unit-electrons",
        "canonical_index": 1,
    },

    "L-electrons-config-orbital": {
        "title": "Electron Configurations & Orbital Notations",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "The block (s, p, d, f) indicates the subshell type",
            "The coefficient is the principal energy level",
            "Orbital diagrams use arrows to represent spin",
        ],
        "misconceptions": [
            "Subshells like 2p have only one orbital",
            "Arrows in orbital diagrams are just decoration",
            "Transition metals always lose 'd' electrons first",
        ],
        "objectives": [
            "Write full electron configurations",
            "Draw orbital notation diagrams",
        ],
        "canonical_unit": "unit-electrons",
        "canonical_index": 2,
    },

    "L-electrons-noble-gas": {
        "title": "Noble Gas Abbreviations & Valence Electrons",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write noble gas abbreviated electron configurations",
            "Identify valence electrons from configurations",
        ],
        "canonical_unit": "unit-electrons",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-periodic-table  (The Periodic Table)
    # ══════════════════════════════════════════════════════

    "L-periodic-history": {
        "title": "History of the Periodic Table",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Describe Mendeleev's contributions to the periodic table",
            "Explain how elements are organized by atomic number",
        ],
        "canonical_unit": "unit-periodic-table",
        "canonical_index": 0,
    },

    "L-periodic-atomic-size": {
        "title": "Atomic Size",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Atomic radius increases down a group (more shells)",
            "Atomic radius decreases across a period (higher effective nuclear charge, Zeff)",
        ],
        "misconceptions": [
            "Atoms get larger across a period because they have more particles",
            "Effective nuclear charge (Zeff) is the same as total nuclear charge",
            "Cations are larger than their neutral atoms",
        ],
        "objectives": [
            "Explain trends in atomic radius",
            "Compare radii across periods and groups",
        ],
        "canonical_unit": "unit-periodic-table",
        "canonical_index": 1,
    },

    "L-periodic-ionization": {
        "title": "Ionization Energy",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Ionization energy increases across a period",
            "Ionization energy decreases down a group",
            "Successive ionization energies (IE1, IE2...) increase drastically once a core shell is reached",
        ],
        "misconceptions": [
            "Ionization energy is the energy released when an electron is added",
            "Removing a second electron is always easier than the first",
            "Stable atoms (like noble gases) have zero ionization energy",
        ],
        "objectives": [
            "Explain ionization energy trends",
            "Predict relative ionization energies",
        ],
        "canonical_unit": "unit-periodic-table",
        "canonical_index": 2,
    },

    "L-periodic-electronegativity": {
        "title": "Electronegativity",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Describe electronegativity trends across the periodic table",
            "Use electronegativity differences to predict bond polarity",
        ],
        "canonical_unit": "unit-periodic-table",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-bonding  (Chemical Bonding)
    # ══════════════════════════════════════════════════════

    "L-bonding-basics": {
        "title": "Bonding Basics",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Bonding lowers the potential energy of the system",
            "Bond breaking is endothermic; bond formation is exothermic",
            "Valence electrons drive chemical bonding",
        ],
        "misconceptions": [
            "Atoms 'want' to be happy with 8 electrons (atoms have no desires; it's about energetics)",
            "Bonds are physical 'sticks' between atoms",
            "Only one type of bond can exist in a compound",
        ],
        "objectives": [
            "Describe types of chemical bonds",
            "Explain why atoms form bonds",
        ],
        "canonical_unit": "unit-bonding",
        "canonical_index": 0,
    },

    "L-bonding-ionic": {
        "title": "Ionic Bonding",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "Lattice Energy ∝ (q₁q₂ / r)",
        ],
        "key_rules": [
            "Involves transfer of electrons from metal to nonmetal",
            "Ionic solids form crystal lattices, not discrete molecules",
            "High melting and boiling points due to strong electrostatic forces",
        ],
        "misconceptions": [
            "Ionic compounds exist as individual molecules (e.g., a single 'NaCl')",
            "Ionic bonds are weak because they dissolve in water",
            "Lattice energy only depends on the size of the ions",
        ],
        "objectives": [
            "Explain ionic bond formation",
            "Draw Lewis dot structures for ionic compounds",
        ],
        "canonical_unit": "unit-bonding",
        "canonical_index": 1,
    },

    "L-bonding-covalent": {
        "title": "Covalent Bonding",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Involves sharing of electron pairs between nonmetals",
            "Single, double, and triple bonds have different lengths and strengths",
            "Lewis structures represent the arrangement of valence electrons",
        ],
        "misconceptions": [
            "Covalent bonds are always stronger than ionic bonds",
            "Electrons are always shared equally in a covalent bond",
            "Double bonds are exactly twice as strong as single bonds",
        ],
        "objectives": [
            "Explain covalent bond formation",
            "Draw Lewis structures for molecules",
        ],
        "canonical_unit": "unit-bonding",
        "canonical_index": 2,
    },

    "L-bonding-molecular-geometry": {
        "title": "Molecular Geometry",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "VSEPR theory: Electron domains repel and stay as far apart as possible",
            "Lone pairs take up more space than bonding pairs",
            "Geometry is determined by the total number of electron domains around the central atom",
        ],
        "misconceptions": [
            "Molecular shape and electron geometry are the same thing",
            "Bent molecules like water are linear (180°)",
            "Non-bonding (lone) pairs do not affect bond angles",
        ],
        "objectives": [
            "Apply VSEPR theory",
            "Predict molecular shapes",
        ],
        "canonical_unit": "unit-bonding",
        "canonical_index": 3,
    },

    "L-bonding-polarity": {
        "title": "Polarity",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Determine bond polarity using electronegativity",
            "Predict molecular polarity from geometry",
        ],
        "canonical_unit": "unit-bonding",
        "canonical_index": 4,
    },

    # ══════════════════════════════════════════════════════
    # unit-nomenclature  (Chemical Nomenclature)
    # ══════════════════════════════════════════════════════

    "L-nomenclature-properties": {
        "title": "Properties of Ionic & Covalent Compounds",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Compare physical properties of ionic vs covalent compounds",
            "Relate bonding type to melting point and conductivity",
        ],
        "canonical_unit": "unit-nomenclature",
        "canonical_index": 0,
    },

    "L-nomenclature-name-formula": {
        "title": "Name to Formula (Ionic)",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Convert ionic compound names to chemical formulas",
            "Use polyatomic ion charges correctly",
        ],
        "canonical_unit": "unit-nomenclature",
        "canonical_index": 1,
    },

    "L-nomenclature-formula-name": {
        "title": "Formula to Name (Ionic)",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Convert ionic compound formulas to systematic names",
            "Apply Roman numeral notation for transition metals",
        ],
        "canonical_unit": "unit-nomenclature",
        "canonical_index": 2,
    },

    "L-nomenclature-acids": {
        "title": "Naming Acids",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Name binary acids (hydro-/ic acid)",
            "Name oxyacids using -ous/-ic acid endings",
        ],
        "canonical_unit": "unit-nomenclature",
        "canonical_index": 3,
    },

    "L-nomenclature-covalent": {
        "title": "Naming Covalent Compounds",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Name binary covalent compounds using Greek prefixes",
            "Write formulas from covalent compound names",
        ],
        "canonical_unit": "unit-nomenclature",
        "canonical_index": 4,
    },

    # ══════════════════════════════════════════════════════
    # unit-dimensional-analysis  (Dimensional Analysis)
    # ══════════════════════════════════════════════════════

    "L-da-intro": {
        "title": "Intro to Dimensional Analysis",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "Known Value × (Desired Unit / Known Unit) = Result",
        ],
        "key_rules": [
            "Units must cancel out diagonally",
            "Conversion factors are ratios equal to 1",
            "The 'K' (Known) and 'U' (Unknown) method helps organize the problem",
        ],
        "misconceptions": [
            "Dimensional analysis is just for science; it can't be used for money or time",
            "You can just multiply by any number as long as the units are there",
            "The number in the denominator is always 1",
        ],
        "objectives": [
            "Set up unit conversion factors",
            "Solve single-step conversions",
        ],
        "canonical_unit": "unit-dimensional-analysis",
        "canonical_index": 0,
    },

    "L-da-multi-step": {
        "title": "Multi-Step Dimensional Analysis",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Chain multiple conversion factors in a single setup",
            "Convert between non-adjacent units using intermediate steps",
        ],
        "canonical_unit": "unit-dimensional-analysis",
        "canonical_index": 1,
    },

    # ══════════════════════════════════════════════════════
    # unit-mole  (The Mole)
    # ══════════════════════════════════════════════════════

    "L-mole-history": {
        "title": "History & Particle Conversions",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "N = n × Nₐ  (Nₐ = 6.022 × 10²³ mol⁻¹)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Explain the origin of Avogadro's number",
            "Convert between moles and number of particles",
        ],
        "canonical_unit": "unit-mole",
        "canonical_index": 0,
    },

    "L-mole-molar-mass-1step": {
        "title": "Molar Mass (1-Step)",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "n = m / M",
        ],
        "key_rules": [
            "Molar mass is found by summing atomic masses from the periodic table",
            "Units for molar mass are g/mol",
            "One mole of any element contains 6.022 × 10²³ atoms",
        ],
        "misconceptions": [
            "One mole of Lead weighs the same as one mole of Helium",
            "The molar mass of a diatomic gas (like O₂) is just the atomic mass of O",
            "Moles and molecules are the same thing",
        ],
        "objectives": [
            "Calculate molar mass of elements",
            "Convert between moles and grams (1-step)",
        ],
        "canonical_unit": "unit-mole",
        "canonical_index": 1,
    },

    "L-mole-molar-mass-2step": {
        "title": "Molar Mass (2-Step)",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "n = m / M",
            "N = n × Nₐ",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Calculate molar mass of compounds",
            "Convert between grams, moles, and particles in two steps",
        ],
        "canonical_unit": "unit-mole",
        "canonical_index": 2,
    },

    "L-mole-percent-composition": {
        "title": "Percent Composition",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "% Element = (Mass of Element / Total Molar Mass) × 100",
        ],
        "key_rules": [
            "Percentages must sum to 100%",
            "Empirical formulas are the simplest whole-number ratio of atoms",
        ],
        "misconceptions": [
            "Percent composition depends on the amount of sample",
            "The empirical formula is always the same as the molecular formula",
            "Percentage by mass is the same as percentage by atom count",
        ],
        "objectives": [
            "Calculate percent composition by mass",
            "Determine empirical formula from percent composition",
        ],
        "canonical_unit": "unit-mole",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-chemical-reactions  (Chemical Reactions)
    # ══════════════════════════════════════════════════════

    "L-rxn-equations": {
        "title": "Word & Formula Equations",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Convert word equations to formula equations",
            "Include state symbols (s, l, g, aq) in chemical equations",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 0,
    },

    "L-rxn-balancing": {
        "title": "Balancing Chemical Equations",
        "blueprint": "architect",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [
            "Law of Conservation of Mass: Mass cannot be created or destroyed",
            "Only coefficients can be changed, never subscripts",
            "The number of atoms for each element must be equal on both sides",
        ],
        "misconceptions": [
            "Changing a subscript is a valid way to balance an equation",
            "Equations represent what 'can' happen, not what 'must' happen",
            "The arrow means 'equals' (it means 'yields' or 'reacts to form')",
        ],
        "objectives": [
            "Balance chemical equations by inspection",
            "Apply conservation of mass",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 1,
    },

    "L-rxn-both-skills": {
        "title": "Word Equations & Balancing Together",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Translate word equations and balance them in a combined workflow",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 2,
    },

    "L-rxn-synthesis-decomp": {
        "title": "Synthesis & Decomposition Reactions",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Identify and write synthesis reactions (A + B → AB)",
            "Identify and write decomposition reactions (AB → A + B)",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 3,
    },

    "L-rxn-single-replacement": {
        "title": "Single Replacement Reactions",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Predict products of single replacement reactions using the activity series",
            "Determine if a reaction will occur",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 4,
    },

    "L-rxn-double-replacement": {
        "title": "Double Replacement Reactions",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Predict products of double replacement reactions",
            "Identify precipitate formation using solubility rules",
        ],
        "canonical_unit": "unit-chemical-reactions",
        "canonical_index": 5,
    },

    # ══════════════════════════════════════════════════════
    # unit-stoichiometry  (Stoichiometry)
    # ══════════════════════════════════════════════════════

    "L-stoich-mole-mole": {
        "title": "Mole-Mole Calculations",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "Moles A × (coeff B / coeff A) = Moles B",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Use mole ratios from balanced equations",
            "Convert moles of reactant to moles of product",
        ],
        "canonical_unit": "unit-stoichiometry",
        "canonical_index": 0,
    },

    "L-stoich-mass-mass": {
        "title": "Mass-Mass Calculations",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "Mass A → Moles A → Moles B → Mass B",
        ],
        "key_rules": [
            "The mole ratio comes from the coefficients of the balanced equation",
            "You cannot convert directly from grams of A to grams of B",
            "Standard stoichiometry assumes 100% yield",
        ],
        "misconceptions": [
            "Grams of A / Grams B = Coefficient A / Coefficient B",
            "Stoichiometry only applies to the products",
            "Balanced equations show mass ratios",
        ],
        "objectives": [
            "Perform gram-to-gram stoichiometry calculations",
        ],
        "canonical_unit": "unit-stoichiometry",
        "canonical_index": 1,
    },

    "L-stoich-limiting": {
        "title": "Limiting Reactants",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "% Yield = (Actual / Theoretical) × 100",
        ],
        "key_rules": [
            "The limiting reactant is completely consumed and determines the yield",
            "The excess reactant has leftover amount",
            "Theoretical yield is the maximum possible product formed",
        ],
        "misconceptions": [
            "The reactant with the smallest mass is always the limiting reactant",
            "Reaction stops when the excess reactant runs out",
            "Actual yield can be higher than theoretical yield (implies contamination or error)",
        ],
        "objectives": [
            "Identify the limiting reactant",
            "Calculate theoretical yield and percent yield",
        ],
        "canonical_unit": "unit-stoichiometry",
        "canonical_index": 2,
    },

    # ══════════════════════════════════════════════════════
    # unit-solutions  (Solutions)
    # ══════════════════════════════════════════════════════

    "L-solutions-intro": {
        "title": "Introduction to Solutions",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Define solute, solvent, and solution",
            "Describe factors affecting solubility",
        ],
        "canonical_unit": "unit-solutions",
        "canonical_index": 0,
    },

    "L-solutions-molarity": {
        "title": "Molarity",
        "blueprint": "solver",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "M = n / V",
            "M₁V₁ = M₂V₂ (Dilution)",
        ],
        "key_rules": [
            "Volume must be in Liters",
            "Molarity measures concentration, not total amount of solute",
            "Dilution adds solvent, but the moles of solute remain constant",
        ],
        "misconceptions": [
            "Molarity is the same as moles",
            "Adding water to a solution increases the molarity",
            "1.0 M NaCl is the same as 1.0 M glucose in terms of particle concentration (colligative properties)",
        ],
        "objectives": [
            "Calculate molarity of a solution",
            "Prepare solutions of a given molarity",
        ],
        "canonical_unit": "unit-solutions",
        "canonical_index": 1,
    },

    "L-solutions-acids-bases-props": {
        "title": "Acids & Bases Properties",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Identify Arrhenius, Brønsted-Lowry, and Lewis acid/base definitions",
            "Distinguish strong acids/bases from weak acids/bases",
        ],
        "canonical_unit": "unit-solutions",
        "canonical_index": 2,
    },

    "L-solutions-acid-base-calc": {
        "title": "Acid-Base Calculations",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "pH = −log[H⁺]",
            "pOH = −log[OH⁻]",
            "pH + pOH = 14",
            "[H⁺][OH⁻] = 1.0 × 10⁻¹⁴",
        ],
        "key_rules": [
            "A pH < 7 is acidic; pH > 7 is basic",
            "Each pH unit represents a 10-fold change in concentration",
            "Strong acids/bases ionize completely",
        ],
        "misconceptions": [
            "A pH of 0 means there are no H⁺ ions",
            "Weak acids have a high pH and strong acids have a low pH always (depends on concentration)",
            "Neutral solutions have no H⁺ or OH⁻ ions",
        ],
        "objectives": [
            "Calculate pH from [H⁺]",
            "Interconvert pH, pOH, [H⁺], [OH⁻]",
        ],
        "canonical_unit": "unit-solutions",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-thermochem  (Thermochemistry)
    # ══════════════════════════════════════════════════════

    "L-thermo-intro": {
        "title": "Introduction to Thermochemistry",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Define system, surroundings, and universe",
            "Distinguish endothermic from exothermic processes",
        ],
        "canonical_unit": "unit-thermochem",
        "canonical_index": 0,
    },

    "L-thermo-calorimetry": {
        "title": "Calorimetry",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "q = mcΔT",
            "q_sys = −q_surr",
        ],
        "key_rules": [
            "Specific heat (c) is the heat needed to raise 1g by 1°C",
            "Energy is conserved: heat lost by the system is gained by the surroundings",
            "ΔT is Final Temperature - Initial Temperature",
        ],
        "misconceptions": [
            "Temperature and heat are the same thing",
            "A negative q means the substance got colder (it means heat was released)",
            "Specific heat depends on the mass of the sample",
        ],
        "objectives": [
            "Perform calorimetry calculations",
            "Calculate specific heat capacity",
        ],
        "canonical_unit": "unit-thermochem",
        "canonical_index": 1,
    },

    "L-thermo-equations": {
        "title": "Thermochemical Equations",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "ΔH°rxn = Σ ΔH°f(products) − Σ ΔH°f(reactants)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write thermochemical equations with ΔH values",
            "Apply Hess's law to calculate ΔH for a reaction",
        ],
        "canonical_unit": "unit-thermochem",
        "canonical_index": 2,
    },

    "L-thermo-heating-curves": {
        "title": "Heating Curves",
        "blueprint": "detective",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "q = mcΔT  (for temperature changes)",
            "q = n × ΔH  (for phase changes)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Interpret a heating/cooling curve",
            "Calculate total heat for a multi-step temperature + phase change process",
        ],
        "canonical_unit": "unit-thermochem",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-kinetic-theory  (Kinetic Molecular Theory)
    # ══════════════════════════════════════════════════════

    "L-kmt-gases": {
        "title": "KMT: Gases",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "State the postulates of KMT for gases",
            "Relate temperature to average kinetic energy of gas particles",
        ],
        "canonical_unit": "unit-kinetic-theory",
        "canonical_index": 0,
    },

    "L-kmt-liquids": {
        "title": "KMT: Liquids",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Describe intermolecular forces in liquids",
            "Explain surface tension and viscosity using KMT",
        ],
        "canonical_unit": "unit-kinetic-theory",
        "canonical_index": 1,
    },

    "L-kmt-solids": {
        "title": "KMT: Solids",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Compare crystalline and amorphous solids",
            "Relate solid properties to particle arrangement",
        ],
        "canonical_unit": "unit-kinetic-theory",
        "canonical_index": 2,
    },

    "L-kmt-phase-diagrams": {
        "title": "Phase Diagrams",
        "blueprint": "detective",
        "required_tools": [],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Interpret a phase diagram",
            "Identify triple point and critical point",
        ],
        "canonical_unit": "unit-kinetic-theory",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # unit-gas-laws  (Gas Laws)
    # ══════════════════════════════════════════════════════

    "L-gas-intro": {
        "title": "Introduction to Gas Laws",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Define pressure, volume, temperature, and amount for gases",
            "Convert between pressure units (atm, kPa, mmHg)",
        ],
        "canonical_unit": "unit-gas-laws",
        "canonical_index": 0,
    },

    "L-gas-boyle-charles": {
        "title": "Boyle's Law & Charles' Law",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "P₁V₁ = P₂V₂  (Boyle's Law)",
            "V₁/T₁ = V₂/T₂  (Charles' Law)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Apply Boyle's Law (constant T and n)",
            "Apply Charles' Law (constant P and n)",
        ],
        "canonical_unit": "unit-gas-laws",
        "canonical_index": 1,
    },

    "L-gas-gay-lussac-combined": {
        "title": "Gay-Lussac's Law & Combined Gas Law",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": False,
        "key_equations": [
            "P₁/T₁ = P₂/T₂  (Gay-Lussac's Law)",
            "P₁V₁/T₁ = P₂V₂/T₂  (Combined Gas Law)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Apply Gay-Lussac's Law (constant V and n)",
            "Use the combined gas law for problems with two variables changing",
        ],
        "canonical_unit": "unit-gas-laws",
        "canonical_index": 2,
    },

    "L-gas-ideal": {
        "title": "Ideal Gas Law",
        "blueprint": "solver",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": False,
        "key_equations": [
            "PV = nRT",
        ],
        "key_rules": [
            "Temperature must be in Kelvin",
            "Pressure and Volume units must match the R constant used",
            "Ideal gases have no intermolecular forces and zero particle volume",
        ],
        "misconceptions": [
            "The 'R' constant is the same for all units",
            "Gas particles stop moving at 0°C",
            "Real gases behave ideally at very high pressures",
        ],
        "objectives": [
            "Use the ideal gas law (PV = nRT)",
            "Solve for any gas variable",
        ],
        "canonical_unit": "unit-gas-laws",
        "canonical_index": 3,
    },

    # ══════════════════════════════════════════════════════
    # AP EXTENSIONS — Atomic Structure (ap-unit-1)
    # ══════════════════════════════════════════════════════

    "L-mass-spectrometry": {
        "title": "Mass Spectrometry",
        "blueprint": "detective",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [
            "Each peak on a mass spectrum represents an isotope",
            "The x-axis represents mass-to-charge ratio (m/z)",
            "Relative peak height indicates relative abundance",
        ],
        "misconceptions": [
            "The number of peaks equals the number of protons",
            "Small peaks are just 'errors' (they are often rare isotopes)",
            "Mass spec can determine the exact shape of a molecule alone",
        ],
        "objectives": [
            "Interpret mass spectra",
            "Identify isotopes",
        ],
        "extension_of": "L-atomic-mass",
        "canonical_unit": "unit-atomic-theory",
        "canonical_index": 3,
    },

    "L-pes": {
        "title": "Photoelectron Spectroscopy (PES)",
        "blueprint": "detective",
        "required_tools": ['periodic_table'],
        "is_ap_only": True,
        "key_equations": [
            "Binding Energy = hν − Kinetic Energy",
        ],
        "key_rules": [
            "PES peaks correspond to specific subshells",
            "Peak height is proportional to the number of electrons in that subshell",
            "Peaks further to the left (higher binding energy) are closer to the nucleus",
        ],
        "misconceptions": [
            "Binding energy is the same as the charge of the nucleus",
            "The x-axis always increases from left to right (PES often goes from high to low)",
            "Inner shell electrons have low binding energy",
        ],
        "objectives": [
            "Interpret PES spectra",
            "Relate peaks to electron shells",
        ],
        "extension_of": "L-electrons-config-orbital",
        "canonical_unit": "unit-electrons",
        "canonical_index": 4,
    },

    # ══════════════════════════════════════════════════════
    # AP EXTENSIONS — Bonding (ap-unit-2)
    # ══════════════════════════════════════════════════════

    "L-bonding-formal-charge": {
        "title": "Formal Charge & Resonance",
        "blueprint": "architect",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [
            "FC = V − L − B/2",
        ],
        "key_rules": [
            "Formal charge helps determine the most stable Lewis structure",
            "The sum of formal charges must equal the overall charge of the species",
            "Resonance structures represent electron delocalization",
        ],
        "misconceptions": [
            "Molecules 'flip' back and forth between resonance structures",
            "A formal charge of zero is impossible for an ion",
            "Resonance makes a molecule less stable",
        ],
        "objectives": [
            "Calculate formal charge",
            "Draw resonance structures",
        ],
        "extension_of": "L-bonding-covalent",
        "canonical_unit": "unit-bonding",
        "canonical_index": 5,
    },

    "L-bonding-hybridization": {
        "title": "Hybridization",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [
            "Atomic orbitals mix to form new hybrid orbitals for bonding",
            "sp = 2 domains (linear), sp² = 3 domains (trigonal planar), sp³ = 4 domains (tetrahedral)",
            "Sigma (σ) bonds are formed by head-on overlap; Pi (π) bonds by side-to-side overlap",
        ],
        "misconceptions": [
            "All bonds are hybrid orbitals",
            "A double bond consists of two sigma bonds",
            "Hybridization occurs in isolated atoms",
        ],
        "objectives": [
            "Explain sp, sp², sp³ hybridization",
            "Relate hybridization to geometry",
        ],
        "extension_of": "L-bonding-molecular-geometry",
        "canonical_unit": "unit-bonding",
        "canonical_index": 6,
    },

    # ══════════════════════════════════════════════════════
    # AP EXTENSIONS — Intermolecular Forces (ap-unit-3)
    # ══════════════════════════════════════════════════════

    "L-gas-van-der-waals": {
        "title": "Real Gases & van der Waals Equation",
        "blueprint": "lawyer",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "(P + a(n/V)²)(V − nb) = nRT",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Explain deviations of real gases from ideal behavior",
            "Apply the van der Waals equation",
        ],
        "extension_of": "L-gas-ideal",
        "canonical_unit": "ap-unit-3",
        "canonical_index": 7,
    },

    "L-solutions-beer-lambert": {
        "title": "Beer-Lambert Law",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "A = εbc",
        ],
        "key_rules": [
            "Absorbance is directly proportional to concentration",
            "Path length and molar absorptivity are usually constant",
            "The wavelength used should be the one where the substance absorbs most strongly",
        ],
        "misconceptions": [
            "A darker solution has lower absorbance",
            "Absorbance is the same as transmittance",
            "Beer's Law works at very high concentrations (it becomes non-linear)",
        ],
        "objectives": [
            "Apply the Beer-Lambert law",
            "Determine concentration from absorbance",
        ],
        "canonical_unit": "ap-unit-3",
        "canonical_index": 10,
    },

    # ══════════════════════════════════════════════════════
    # AP EXTENSIONS — Chemical Reactions (ap-unit-4)
    # ══════════════════════════════════════════════════════

    "L-rxn-net-ionic": {
        "title": "Net Ionic Equations",
        "blueprint": "architect",
        "required_tools": ['periodic_table'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [
            "Strong electrolytes must be written as separate ions in aqueous solution",
            "Spectator ions appear unchanged on both sides and are removed",
            "Solids, liquids, and gases are never split into ions",
        ],
        "misconceptions": [
            "Insoluble precipitates are split into ions",
            "Spectator ions disappear from the reaction entirely (they remain in the beaker)",
            "All ionic compounds are strong electrolytes",
        ],
        "objectives": [
            "Write complete and net ionic equations",
            "Identify spectator ions",
        ],
        "canonical_unit": "ap-unit-4",
        "canonical_index": 4,
    },

    "L-rxn-redox-titration": {
        "title": "Redox Reactions & Titration",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Assign oxidation states and identify oxidizing/reducing agents",
            "Perform redox titration calculations",
        ],
        "canonical_unit": "ap-unit-4",
        "canonical_index": 5,
    },

    # ══════════════════════════════════════════════════════
    # AP — Kinetics (ap-unit-5)
    # ══════════════════════════════════════════════════════

    "L-ap-kinetics-rate-laws": {
        "title": "Reaction Rates & Rate Laws",
        "blueprint": "detective",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "rate = k[A]^m[B]^n",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write rate law expressions from experimental data",
            "Determine overall reaction order",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 0,
    },

    "L-kinetics-zero-order": {
        "title": "Zero-Order Reactions",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "[A]t = −kt + [A]₀",
            "t½ = [A]₀ / (2k)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Apply zero-order integrated rate law",
            "Recognize a zero-order plot ([A] vs time is linear)",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 1,
    },

    "L-kinetics-first-order": {
        "title": "First-Order Reactions",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "ln[A]t = −kt + ln[A]₀",
            "t½ = 0.693 / k",
        ],
        "key_rules": [
            "A plot of ln[A] vs time is linear for first-order reactions",
            "The half-life of a first-order reaction is independent of initial concentration",
            "The rate is directly proportional to the concentration of one reactant",
        ],
        "misconceptions": [
            "Half-life gets shorter as the reaction proceeds",
            "Rate constants (k) are the same for all temperatures",
            "The units of k for first-order are M/s (they are 1/s)",
        ],
        "extension_of": "L-ap-kinetics-rate-laws",
        "has_simulation": True,
        "objectives": [
            "Apply first-order integrated rate law",
            "Calculate half-life",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 2,
    },

    "L-kinetics-second-order": {
        "title": "Second-Order Reactions",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "1/[A]t = kt + 1/[A]₀",
            "t½ = 1 / (k[A]₀)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Apply second-order integrated rate law",
            "Recognize a second-order plot (1/[A] vs time is linear)",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 3,
    },

    "L-kinetics-comparison": {
        "title": "Comparing Reaction Orders",
        "blueprint": "detective",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Distinguish zero-, first-, and second-order reactions from graphs",
            "Select the correct integrated rate law given experimental data",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 4,
    },

    "L-ap-kinetics-mechanisms": {
        "title": "Reaction Mechanisms",
        "blueprint": "architect",
        "required_tools": [],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Identify elementary steps and the rate-determining step",
            "Derive a rate law from a proposed mechanism",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 5,
    },

    "L-ap-kinetics-arrhenius": {
        "title": "Arrhenius Equation & Activation Energy",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "k = A × e^(−Ea / RT)",
            "ln(k₂/k₁) = (Ea/R)(1/T₁ − 1/T₂)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Use the Arrhenius equation to relate rate constant, temperature, and activation energy",
            "Calculate Ea from experimental k values at two temperatures",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 6,
    },

    "L-ap-kinetics-catalysis": {
        "title": "Catalysis",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Explain how catalysts lower activation energy",
            "Distinguish homogeneous from heterogeneous catalysis",
        ],
        "canonical_unit": "ap-unit-5",
        "canonical_index": 7,
    },

    # ══════════════════════════════════════════════════════
    # AP — Thermodynamics (ap-unit-6)
    # ══════════════════════════════════════════════════════

    "L-thermo-bond-enthalpies": {
        "title": "Bond Enthalpies",
        "blueprint": "solver",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [
            "ΔH ≈ Σ(bonds broken) − Σ(bonds formed)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Estimate ΔH using average bond enthalpies",
            "Explain why bond enthalpy estimates are approximations",
        ],
        "canonical_unit": "ap-unit-6",
        "canonical_index": 4,
    },

    # ══════════════════════════════════════════════════════
    # AP — Equilibrium (ap-unit-7)
    # ══════════════════════════════════════════════════════

    "L-ap-eq-intro-kc": {
        "title": "Introduction to Equilibrium & Kc",
        "blueprint": "architect",
        "required_tools": [],
        "is_ap_only": True,
        "key_equations": [
            "Kc = [products]^coeff / [reactants]^coeff",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write equilibrium constant expressions (Kc)",
            "Interpret the magnitude of K",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 0,
    },

    "L-ap-eq-kp": {
        "title": "Kp and the Relationship Between Kp and Kc",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "Kp = Kc(RT)^Δn",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write Kp expressions for gas-phase equilibria",
            "Convert between Kp and Kc",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 1,
    },

    "L-ap-eq-q": {
        "title": "Reaction Quotient Q",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Calculate Q and compare it to K",
            "Predict the direction of equilibrium shift",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 2,
    },

    "L-ap-eq-le-chatelier": {
        "title": "Le Châtelier's Principle",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [
            "Systems at equilibrium shift to counteract stress",
            "Adding a reactant shifts equilibrium toward products",
            "Increasing pressure shifts equilibrium toward the side with fewer gas moles",
            "Only temperature changes the value of the equilibrium constant (K)",
        ],
        "misconceptions": [
            "Adding a catalyst shifts the equilibrium",
            "Equilibrium means the concentrations of reactants and products are equal",
            "Changing volume shifts the equilibrium for all reactions (only if Δn_gas ≠ 0)",
        ],
        "objectives": [
            "Predict equilibrium shifts from stress",
            "Apply Le Châtelier's principle",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 3,
    },

    "L-ap-eq-ice": {
        "title": "ICE Tables",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Set up and solve ICE tables to find equilibrium concentrations",
            "Apply the small-x approximation when appropriate",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 4,
    },

    "L-ap-eq-ksp": {
        "title": "Solubility Equilibria & Ksp",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "Ksp = [cation]^a [anion]^b",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write Ksp expressions for slightly soluble salts",
            "Calculate molar solubility from Ksp",
        ],
        "canonical_unit": "ap-unit-7",
        "canonical_index": 5,
    },

    # ══════════════════════════════════════════════════════
    # AP — Acids & Bases (ap-unit-8)
    # ══════════════════════════════════════════════════════

    "L-solutions-weak-acids": {
        "title": "Weak Acids & Percent Ionization",
        "blueprint": "recipe",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "Ka = [H⁺][A⁻] / [HA]",
            "% ionization = ([H⁺]eq / [HA]₀) × 100",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write Ka expressions for weak acids",
            "Calculate pH of weak acid solutions using ICE",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 2,
    },

    "L-ap-acid-kakb": {
        "title": "Ka, Kb, and Conjugate Pairs",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "Ka × Kb = Kw = 1.0 × 10⁻¹⁴",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Relate Ka and Kb for conjugate acid-base pairs",
            "Calculate Kb from Ka and vice versa",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 3,
    },

    "L-ap-acid-salt-hydrolysis": {
        "title": "Salt Hydrolysis",
        "blueprint": "lawyer",
        "required_tools": ['periodic_table'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Predict whether a salt solution is acidic, basic, or neutral",
            "Calculate pH of a salt solution",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 4,
    },

    "L-ap-acid-buffers": {
        "title": "Buffers: Design & Simulation",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "pH = pKa + log([A⁻]/[HA])",
        ],
        "key_rules": [
            "Buffers consist of a weak acid and its conjugate base",
            "They resist changes in pH when small amounts of acid/base are added",
            "Optimal buffering occurs when pH ≈ pKa",
        ],
        "misconceptions": [
            "Buffers can neutralize any amount of added acid",
            "A buffer's pH never changes",
            "You can make a buffer using a strong acid and its conjugate",
        ],
        "extension_of": "L-solutions-acids-bases-props",
        "has_simulation": True,
        "objectives": [
            "Design a buffer of a given pH",
            "Calculate buffer pH using Henderson-Hasselbalch",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 5,
    },

    "L-ap-acid-titration-curves": {
        "title": "Acid-Base Titration Curves",
        "blueprint": "detective",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Interpret strong acid–strong base and weak acid–strong base titration curves",
            "Identify the equivalence point and half-equivalence point",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 6,
    },

    "L-ap-acid-polyprotic": {
        "title": "Polyprotic Acids",
        "blueprint": "detective",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Write stepwise ionization equations for polyprotic acids",
            "Explain why Ka1 >> Ka2 >> Ka3",
        ],
        "canonical_unit": "ap-unit-8",
        "canonical_index": 7,
    },

    # ══════════════════════════════════════════════════════
    # AP — Applications of Thermodynamics (ap-unit-9)
    # ══════════════════════════════════════════════════════

    "L-ap-thermo-entropy": {
        "title": "Entropy & the Second Law",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "ΔS°rxn = Σ S°(products) − Σ S°(reactants)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Define entropy and predict the sign of ΔS",
            "State the second law of thermodynamics",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 0,
    },

    "L-ap-thermo-gibbs": {
        "title": "Gibbs Free Energy",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "ΔG = ΔH − TΔS",
            "ΔG° = −RT ln K",
        ],
        "key_rules": [
            "ΔG < 0 indicates a thermodynamically favored (spontaneous) process",
            "ΔG = 0 indicates the system is at equilibrium",
            "Standard conditions (°) are 1 atm and 298 K",
        ],
        "misconceptions": [
            "Spontaneous reactions happen instantly (spontaneity is not kinetics)",
            "Exothermic reactions are always spontaneous",
            "ΔG is the same as ΔG°",
        ],
        "objectives": [
            "Calculate ΔG and predict spontaneity",
            "Determine temperature dependence of spontaneity",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 1,
    },

    "L-ap-thermo-dg-k-e": {
        "title": "Relationships Between ΔG°, K, and E°",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "ΔG° = −RT ln K",
            "ΔG° = −nFE°",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 2,
    },

    "L-ap-electro-galvanic": {
        "title": "Galvanic Cells & Cell Notation",
        "blueprint": "architect",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [
            "E°cell = E°red(cathode) − E°red(anode)",
        ],
        "key_rules": [
            "Oxidation occurs at the Anode (An Ox); Reduction at the Cathode (Red Cat)",
            "Electrons flow from anode to cathode through the wire",
            "Salt bridge maintains electrical neutrality by allowing ion flow",
        ],
        "misconceptions": [
            "Electrons flow through the salt bridge",
            "The anode is always the negative electrode in all cells",
            "Standard reduction potentials depend on the coefficients in the balanced equation",
        ],
        "objectives": [
            "Describe galvanic cell operation",
            "Write cell notation",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 3,
    },

    "L-ap-electro-nernst": {
        "title": "Nernst Equation",
        "blueprint": "solver",
        "required_tools": ['calculator'],
        "is_ap_only": True,
        "key_equations": [
            "E = E° − (RT/nF) ln Q",
            "E = E° − (0.0592/n) log Q  (at 298 K)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Apply the Nernst equation to calculate cell potential under non-standard conditions",
            "Predict cell potential as the reaction proceeds",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 4,
    },

    "L-ap-electro-electrolysis": {
        "title": "Electrolysis",
        "blueprint": "lawyer",
        "required_tools": [],
        "is_ap_only": True,
        "key_equations": [],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Describe how electrolysis uses electrical energy to drive non-spontaneous reactions",
            "Identify the products of electrolysis of molten and aqueous solutions",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 5,
    },

    "L-ap-electro-faraday": {
        "title": "Faraday's Law",
        "blueprint": "recipe",
        "required_tools": ['calculator', 'periodic_table'],
        "is_ap_only": True,
        "key_equations": [
            "m = (M × I × t) / (n × F)",
        ],
        "key_rules": [],
        "misconceptions": [],
        "objectives": [
            "Calculate mass deposited or volume of gas produced during electrolysis",
            "Apply Faraday's constant (F = 96,485 C/mol)",
        ],
        "canonical_unit": "ap-unit-9",
        "canonical_index": 6,
    },
}
