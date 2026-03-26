"""
Curated reference card data for pre-seeding Lesson.reference_card_json.

Each entry validates against ReferenceCardOutput:
  {lesson, unit_id, lesson_index, steps: [{label, content}]}

Seeded idempotently — skips any lesson that already has a card.

Index key: (unit_id, lesson_index)
"""

REFERENCE_CARDS: list[dict] = [
    # ─── AP UNIT 1 — Atomic Structure & Properties ──────────────────────────
    {
        "lesson": "Molar Mass (1-Step)",
        "unit_id": "ap-unit-1",
        "lesson_index": 0,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify starting unit and target unit"},
            {"label": "Conversion Factors", "content": "Find molar mass ($M$) on the periodic table"},
            {"label": "Dimensional Setup",  "content": "Multiply to cancel starting units ($n = m/M$)"},
            {"label": "Calculate",          "content": "Perform the unrounded arithmetic"},
            {"label": "Answer",             "content": "Round to starting sig figs and attach units"},
        ],
    },
    {
        "lesson": "Molar Mass (2-Step)",
        "unit_id": "ap-unit-1",
        "lesson_index": 1,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify conversion path: $\\text{Mass} \\leftrightarrow \\text{Moles} \\leftrightarrow \\text{Particles}$"},
            {"label": "Conversion Factors", "content": "Identify $M$ ($\\text{g/mol}$) and $N_A$ ($6.022 \\times 10^{23}$)"},
            {"label": "Dimensional Setup",  "content": "Chain the two factors so middle units cancel"},
            {"label": "Calculate",          "content": "Multiply across the top, divide by the bottom"},
            {"label": "Answer",             "content": "Report with correct units and sig figs"},
        ],
    },
    {
        "lesson": "Percent Composition",
        "unit_id": "ap-unit-1",
        "lesson_index": 2,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify the target element and the whole compound"},
            {"label": "Conversion Factors", "content": "Calculate total molar mass of the compound"},
            {"label": "Dimensional Setup",  "content": "Set up: $\\frac{\\text{Mass of Element}}{\\text{Total Mass}} \\times 100$"},
            {"label": "Calculate",          "content": "Divide the part by the whole, then multiply by $100$"},
            {"label": "Answer",             "content": "Report percentage with a $\\%$ sign"},
        ],
    },
    {
        "lesson": "Atomic Structure",
        "unit_id": "ap-unit-1",
        "lesson_index": 3,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify Atomic Number ($Z$) and Mass Number ($A$)"},
            {"label": "Draft",             "content": "Protons $= Z$; Neutrons $= A - Z$"},
            {"label": "Refine",            "content": "Electrons $= \\text{Protons} - \\text{Charge}$"},
            {"label": "Final Answer",      "content": "List the final count of protons, neutrons, electrons"},
        ],
    },
    {
        "lesson": "Atomic Mass",
        "unit_id": "ap-unit-1",
        "lesson_index": 4,
        "steps": [
            {"label": "Equation",   "content": "$\\text{Avg Mass} = \\Sigma (\\text{Mass}_i \\times \\text{Abundance}_i)$"},
            {"label": "Knowns",     "content": "Convert percentage abundances to decimal fractions"},
            {"label": "Substitute", "content": "Multiply each isotope's mass by its decimal abundance"},
            {"label": "Calculate",  "content": "Add the resulting products together"},
            {"label": "Answer",     "content": "Report the weighted average in $\\text{amu}$"},
        ],
    },
    {
        "lesson": "Intro to Electron Configurations",
        "unit_id": "ap-unit-1",
        "lesson_index": 5,
        "steps": [
            {"label": "Inventory / Rules", "content": "Find total electrons; recall $s=2, p=6, d=10, f=14$"},
            {"label": "Draft",             "content": "Apply Aufbau: fill lowest energy orbitals first ($1s, 2s, 2p...$)"},
            {"label": "Refine",            "content": "Apply Pauli: max $2$ electrons per orbital"},
            {"label": "Final Answer",      "content": "Write the full sequence (e.g., $1s^2 2s^2 2p^6$)"},
        ],
    },
    {
        "lesson": "Electron Configurations & Orbital Notations",
        "unit_id": "ap-unit-1",
        "lesson_index": 6,
        "steps": [
            {"label": "Inventory / Rules", "content": "Count total electrons to be placed"},
            {"label": "Draft",             "content": "Write out the subshells in increasing energy order"},
            {"label": "Refine",            "content": "Apply Hund's Rule: fill degenerate orbitals singly first"},
            {"label": "Final Answer",      "content": "Draw up/down arrows or write the final notation"},
        ],
    },
    {
        "lesson": "Noble Gas Abbreviations & Valence Electrons",
        "unit_id": "ap-unit-1",
        "lesson_index": 7,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify the noble gas in the row directly above"},
            {"label": "Draft",             "content": "Place the noble gas symbol in brackets: e.g., $[\\mathrm{Ar}]$"},
            {"label": "Refine",            "content": "Add remaining electrons to outer $s, p, d$ subshells"},
            {"label": "Final Answer",      "content": "Valence electrons = electrons in the highest $n$ level"},
        ],
    },
    {
        "lesson": "Mass Spectrometry",
        "unit_id": "ap-unit-1",
        "lesson_index": 8,
        "steps": [
            {"label": "Data Extraction", "content": "Record the $m/z$ value and height for each peak"},
            {"label": "Feature ID",      "content": "Convert relative peak heights into percentage abundances"},
            {"label": "Apply Concept",   "content": "Calculate the weighted average atomic mass"},
            {"label": "Conclusion",      "content": "Match the average mass to an element on the periodic table"},
        ],
    },
    {
        "lesson": "Photoelectron Spectroscopy (PES)",
        "unit_id": "ap-unit-1",
        "lesson_index": 9,
        "steps": [
            {"label": "Data Extraction", "content": "Identify peaks from highest to lowest binding energy"},
            {"label": "Feature ID",      "content": "Higher binding energy = electrons closer to the nucleus ($1s$)"},
            {"label": "Apply Concept",   "content": "Peak height is proportional to the number of electrons"},
            {"label": "Conclusion",      "content": "Map peaks to subshells ($1s, 2s, 2p$) and identify the element"},
        ],
    },
    {
        "lesson": "Atomic Size",
        "unit_id": "ap-unit-1",
        "lesson_index": 10,
        "steps": [
            {"label": "Concept ID",       "content": "Radius depends on occupied shells ($n$) and $Z_{\\text{eff}}$"},
            {"label": "Relation",         "content": "Compare the number of shells and proton count"},
            {"label": "Evidence / Claim", "content": "More shells = larger. Higher $Z_{\\text{eff}}$ = smaller"},
            {"label": "Conclusion",       "content": "State which atom has the larger or smaller radius"},
        ],
    },
    {
        "lesson": "Ionization Energy",
        "unit_id": "ap-unit-1",
        "lesson_index": 11,
        "steps": [
            {"label": "Concept ID",       "content": "Energy required to remove an outermost electron"},
            {"label": "Relation",         "content": "Compare distance from nucleus and shielding effects"},
            {"label": "Evidence / Claim", "content": "Higher $Z_{\\text{eff}}$ holds electrons tighter (harder to remove)"},
            {"label": "Conclusion",       "content": "State which atom has the higher ionization energy"},
        ],
    },
    {
        "lesson": "Electronegativity",
        "unit_id": "ap-unit-1",
        "lesson_index": 12,
        "steps": [
            {"label": "Concept ID",       "content": "Ability of an atom to attract shared bonding electrons"},
            {"label": "Relation",         "content": "Compare atomic radii and effective nuclear charge ($Z_{\\text{eff}}$)"},
            {"label": "Evidence / Claim", "content": "Smaller atoms with high $Z_{\\text{eff}}$ attract electrons strongly"},
            {"label": "Conclusion",       "content": "Fluorine is the most electronegative element"},
        ],
    },

    # ─── AP UNIT 5 — Kinetics ────────────────────────────────────────────────
    {
        "lesson": "Zero-Order Reactions",
        "unit_id": "ap-unit-5",
        "lesson_index": 1,
        "steps": [
            {"label": "Equation",   "content": "$[\\mathrm{A}]_t = -kt + [\\mathrm{A}]_0$ ; $t_{1/2} = \\frac{[\\mathrm{A}]_0}{2k}$"},
            {"label": "Knowns",     "content": "Identify $[\\mathrm{A}]_0$, $[\\mathrm{A}]_t$, $t$, or $k$ from prompt"},
            {"label": "Substitute", "content": "Plug knowns into the integrated rate law or half-life equation"},
            {"label": "Calculate",  "content": "Solve algebraically for the unknown variable"},
            {"label": "Answer",     "content": "Report value with correct units and sig figs"},
        ],
    },
    {
        "lesson": "First-Order Reactions",
        "unit_id": "ap-unit-5",
        "lesson_index": 2,
        "steps": [
            {"label": "Equation",   "content": "$\\ln[\\mathrm{A}]_t = -kt + \\ln[\\mathrm{A}]_0$ ; $t_{1/2} = \\frac{0.693}{k}$"},
            {"label": "Knowns",     "content": "Identify $[\\mathrm{A}]_0$, $[\\mathrm{A}]_t$, $t$, or $k$"},
            {"label": "Substitute", "content": "Insert knowns into the appropriate first-order equation"},
            {"label": "Calculate",  "content": "Solve using algebra (use $e^x$ to remove $\\ln$ if needed)"},
            {"label": "Answer",     "content": "Report $k$, $t$, or concentration with units"},
        ],
    },
    {
        "lesson": "Second-Order Reactions",
        "unit_id": "ap-unit-5",
        "lesson_index": 3,
        "steps": [
            {"label": "Equation",   "content": "$\\frac{1}{[\\mathrm{A}]_t} = kt + \\frac{1}{[\\mathrm{A}]_0}$ ; $t_{1/2} = \\frac{1}{k[\\mathrm{A}]_0}$"},
            {"label": "Knowns",     "content": "Identify $[\\mathrm{A}]_0$, $[\\mathrm{A}]_t$, $t$, or $k$"},
            {"label": "Substitute", "content": "Place knowns into the needed second-order equation"},
            {"label": "Calculate",  "content": "Solve algebraically for the unknown variable"},
            {"label": "Answer",     "content": "Report $k$, $t$, or concentration with units"},
        ],
    },
    {
        "lesson": "Comparing Reaction Orders",
        "unit_id": "ap-unit-5",
        "lesson_index": 4,
        "steps": [
            {"label": "Data Extraction", "content": "Record concentration changes and corresponding time data"},
            {"label": "Feature ID",      "content": "Calculate $[\\mathrm{A}]$, $\\ln[\\mathrm{A}]$, and $1/[\\mathrm{A}]$ values"},
            {"label": "Apply Concept",   "content": "Test which plot (vs time) yields a straight line"},
            {"label": "Conclusion",      "content": "Zero order = $[\\mathrm{A}]$, First = $\\ln[\\mathrm{A}]$, Second = $1/[\\mathrm{A}]$"},
        ],
    },
    {
        "lesson": "Reaction Mechanisms",
        "unit_id": "ap-unit-5",
        "lesson_index": 5,
        "steps": [
            {"label": "Inventory / Rules", "content": "List elementary steps. Identify intermediates and catalysts"},
            {"label": "Draft",             "content": "Add steps to verify they yield the overall reaction"},
            {"label": "Refine",            "content": "Write the rate law based entirely on the slow step"},
            {"label": "Final Answer",      "content": "Substitute intermediates out of the rate law if necessary"},
        ],
    },
    {
        "lesson": "Arrhenius Equation & Activation Energy",
        "unit_id": "ap-unit-5",
        "lesson_index": 6,
        "steps": [
            {"label": "Equation",   "content": "$k = A e^{-E_a/RT}$ or $\\ln\\left(\\frac{k_2}{k_1}\\right) = \\frac{E_a}{R}\\left(\\frac{1}{T_1} - \\frac{1}{T_2}\\right)$"},
            {"label": "Knowns",     "content": "Identify $k_1$, $k_2$, $T_1$, $T_2$, or $E_a$"},
            {"label": "Substitute", "content": "Insert known variables into the matching equation"},
            {"label": "Calculate",  "content": "Solve algebraically; ensure $R = 8.314 \\text{ J/(mol}\\cdot\\text{K)}$"},
            {"label": "Answer",     "content": "Report $E_a$ or $k$ with correct units"},
        ],
    },
    {
        "lesson": "Catalysis",
        "unit_id": "ap-unit-5",
        "lesson_index": 7,
        "steps": [
            {"label": "Concept ID",       "content": "Catalysts lower Activation Energy ($E_a$) via an alternate pathway"},
            {"label": "Relation",         "content": "Lower $E_a$ increases the frequency of successful collisions"},
            {"label": "Evidence / Claim", "content": "Catalyst speeds up both forward and reverse reactions equally"},
            {"label": "Conclusion",       "content": "Reaction rate increases, but overall $\\Delta H$ and equilibrium remain unchanged"},
        ],
    },

    # ─── AP UNIT 2 — Molecular & Ionic Compound Structure & Properties ────────
    {
        "lesson": "Bonding Basics",
        "unit_id": "ap-unit-2",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Identify bond type: ionic, covalent, or metallic"},
            {"label": "Relation",         "content": "Compare electronegativity differences ($\\Delta\\text{EN}$) between atoms"},
            {"label": "Evidence / Claim", "content": "Large $\\Delta\\text{EN}$ transfers $e^{-}$; small $\\Delta\\text{EN}$ shares $e^{-}$"},
            {"label": "Conclusion",       "content": "State the bond type and expected physical properties"},
        ],
    },
    {
        "lesson": "Ionic Bonding",
        "unit_id": "ap-unit-2",
        "lesson_index": 1,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify interacting ions and their respective charges"},
            {"label": "Draft",             "content": "Use Coulomb's Law: $F \\propto \\frac{q_1 q_2}{r^2}$"},
            {"label": "Refine",            "content": "Higher charges ($q$) and smaller radii ($r$) increase force"},
            {"label": "Final Answer",      "content": "Predict bond strength and lattice stability"},
        ],
    },
    {
        "lesson": "Covalent Bonding",
        "unit_id": "ap-unit-2",
        "lesson_index": 2,
        "steps": [
            {"label": "Inventory / Rules", "content": "Count total valence electrons for all atoms"},
            {"label": "Draft",             "content": "Place least electronegative atom in center; draw single bonds"},
            {"label": "Refine",            "content": "Complete outer octets first, then the central atom"},
            {"label": "Final Answer",      "content": "Create double/triple bonds if central octet is incomplete"},
        ],
    },
    {
        "lesson": "Molecular Geometry",
        "unit_id": "ap-unit-2",
        "lesson_index": 3,
        "steps": [
            {"label": "Inventory / Rules", "content": "Draw the valid Lewis structure for the molecule"},
            {"label": "Draft",             "content": "Count electron domains (bonds + lone pairs) on central atom"},
            {"label": "Refine",            "content": "Apply VSEPR: electron domains repel to maximize distance"},
            {"label": "Final Answer",      "content": "Name the 3D molecular shape (ignoring lone pairs)"},
        ],
    },
    {
        "lesson": "Polarity",
        "unit_id": "ap-unit-2",
        "lesson_index": 4,
        "steps": [
            {"label": "Concept ID",       "content": "Determine if individual bonds are polar ($\\Delta\\text{EN} > 0.4$)"},
            {"label": "Relation",         "content": "Determine the 3D molecular geometry via VSEPR"},
            {"label": "Evidence / Claim", "content": "Symmetrical shapes cancel dipoles; asymmetrical shapes do not"},
            {"label": "Conclusion",       "content": "State if the overall molecule is polar or nonpolar"},
        ],
    },
    {
        "lesson": "Formal Charge & Resonance",
        "unit_id": "ap-unit-2",
        "lesson_index": 5,
        "steps": [
            {"label": "Inventory / Rules", "content": "Draw all possible valid Lewis structures (Resonance)"},
            {"label": "Draft",             "content": "Calculate: $\\text{FC} = \\text{Valence} - \\text{Dots} - \\text{Lines}$"},
            {"label": "Refine",            "content": "Best structure minimizes $\\text{FC}$ closer to $0$"},
            {"label": "Final Answer",      "content": "Negative $\\text{FC}$ must reside on the most electronegative atom"},
        ],
    },
    {
        "lesson": "Hybridization",
        "unit_id": "ap-unit-2",
        "lesson_index": 6,
        "steps": [
            {"label": "Inventory / Rules", "content": "Draw the Lewis structure"},
            {"label": "Draft",             "content": "Count electron domains ($\\sigma$ bonds + lone pairs) on central atom"},
            {"label": "Refine",            "content": "$2 = sp$, $3 = sp^2$, $4 = sp^3$ hybridization"},
            {"label": "Final Answer",      "content": "State hybridization and relate it to electron geometry"},
        ],
    },

    # ─── AP UNIT 3 — Intermolecular Forces & Properties ─────────────────────
    {
        "lesson": "KMT: Gases",
        "unit_id": "ap-unit-3",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "KMT assumes ideal gas particles have no volume or IMFs"},
            {"label": "Relation",         "content": "Particle collisions create pressure ($P$)"},
            {"label": "Evidence / Claim", "content": "Higher temperature ($T$) means greater average kinetic energy"},
            {"label": "Conclusion",       "content": "Predict macroscopic gas behavior from particle motion"},
        ],
    },
    {
        "lesson": "KMT: Liquids",
        "unit_id": "ap-unit-3",
        "lesson_index": 1,
        "steps": [
            {"label": "Concept ID",       "content": "Liquid particles stay close due to intermolecular forces (IMFs)"},
            {"label": "Relation",         "content": "Balance kinetic energy and IMF attractions"},
            {"label": "Evidence / Claim", "content": "Stronger IMFs limit motion, increasing viscosity and surface tension"},
            {"label": "Conclusion",       "content": "Relate liquid properties to particle mobility"},
        ],
    },
    {
        "lesson": "KMT: Solids",
        "unit_id": "ap-unit-3",
        "lesson_index": 2,
        "steps": [
            {"label": "Concept ID",       "content": "Particles vibrate in fixed, closely packed positions"},
            {"label": "Relation",         "content": "Strong attractions overpower kinetic energy"},
            {"label": "Evidence / Claim", "content": "Low kinetic energy prevents translational motion"},
            {"label": "Conclusion",       "content": "Solids maintain a definite shape and volume"},
        ],
    },
    {
        "lesson": "Phase Diagrams",
        "unit_id": "ap-unit-3",
        "lesson_index": 3,
        "steps": [
            {"label": "Data Extraction", "content": "Read $P$ and $T$ axes; identify regions and boundary curves"},
            {"label": "Feature ID",      "content": "Locate the solid, liquid, and gas phases"},
            {"label": "Apply Concept",   "content": "Identify the triple point and critical point"},
            {"label": "Conclusion",      "content": "State the phase present or transition occurring at specific conditions"},
        ],
    },
    {
        "lesson": "Boyle's Law & Charles' Law",
        "unit_id": "ap-unit-3",
        "lesson_index": 4,
        "steps": [
            {"label": "Equation",   "content": "$P_1 V_1 = P_2 V_2$ or $\\frac{V_1}{T_1} = \\frac{V_2}{T_2}$"},
            {"label": "Knowns",     "content": "Identify the changing and constant variables"},
            {"label": "Substitute", "content": "Insert given values; ensure $T$ is in Kelvin"},
            {"label": "Calculate",  "content": "Isolate the unknown variable algebraically"},
            {"label": "Answer",     "content": "Report pressure, volume, or temperature with units"},
        ],
    },
    {
        "lesson": "Gay-Lussac's Law & Combined Gas Law",
        "unit_id": "ap-unit-3",
        "lesson_index": 5,
        "steps": [
            {"label": "Equation",   "content": "$\\frac{P_1}{T_1} = \\frac{P_2}{T_2}$ or $\\frac{P_1 V_1}{T_1} = \\frac{P_2 V_2}{T_2}$"},
            {"label": "Knowns",     "content": "List known initial and final states"},
            {"label": "Substitute", "content": "Insert values; temperatures MUST be in Kelvin"},
            {"label": "Calculate",  "content": "Cross-multiply and isolate the target variable"},
            {"label": "Answer",     "content": "Report the final value with correct units"},
        ],
    },
    {
        "lesson": "Ideal Gas Law",
        "unit_id": "ap-unit-3",
        "lesson_index": 6,
        "steps": [
            {"label": "Equation",   "content": "$PV = nRT$"},
            {"label": "Knowns",     "content": "Identify $P$, $V$, $n$, $T$, and select matching $R$"},
            {"label": "Substitute", "content": "Convert units to match $R$ (e.g., $T$ to Kelvin, $V$ to Liters)"},
            {"label": "Calculate",  "content": "Rearrange $PV = nRT$ and solve for the unknown"},
            {"label": "Answer",     "content": "Report the value with appropriate gas-law units"},
        ],
    },
    {
        "lesson": "Real Gases & van der Waals Equation",
        "unit_id": "ap-unit-3",
        "lesson_index": 7,
        "steps": [
            {"label": "Concept ID",       "content": "Real gases deviate from ideal behavior"},
            {"label": "Relation",         "content": "Use $(P + a(n/V)^2)(V - nb) = nRT$"},
            {"label": "Evidence / Claim", "content": "$a$ corrects for IMFs; $b$ corrects for particle volume"},
            {"label": "Conclusion",       "content": "Deviations are greatest at high $P$ or low $T$"},
        ],
    },
    {
        "lesson": "Introduction to Solutions",
        "unit_id": "ap-unit-3",
        "lesson_index": 8,
        "steps": [
            {"label": "Concept ID",       "content": "A solution is a homogeneous mixture"},
            {"label": "Relation",         "content": "Identify the solute (dissolved) and solvent (dissolver)"},
            {"label": "Evidence / Claim", "content": "Like dissolves like (polar dissolves polar)"},
            {"label": "Conclusion",       "content": "State if a solution will form based on IMFs"},
        ],
    },
    {
        "lesson": "Molarity",
        "unit_id": "ap-unit-3",
        "lesson_index": 9,
        "steps": [
            {"label": "Equation",   "content": "$M = \\frac{n}{V}$ or $M_1 V_1 = M_2 V_2$"},
            {"label": "Knowns",     "content": "Identify moles ($n$), volume ($V$), or dilution variables"},
            {"label": "Substitute", "content": "Insert values; ensure volume is in Liters for $M = n/V$"},
            {"label": "Calculate",  "content": "Solve algebraically for the unknown"},
            {"label": "Answer",     "content": "Report concentration in $\\text{M}$ or requested unit"},
        ],
    },
    {
        "lesson": "Beer-Lambert Law",
        "unit_id": "ap-unit-3",
        "lesson_index": 10,
        "steps": [
            {"label": "Equation",   "content": "$A = \\varepsilon b c$"},
            {"label": "Knowns",     "content": "Identify Absorbance ($A$), absorptivity ($\\varepsilon$), path ($b$), concentration ($c$)"},
            {"label": "Substitute", "content": "Rearrange for the unknown variable"},
            {"label": "Calculate",  "content": "Solve, keeping track of unit cancellation"},
            {"label": "Answer",     "content": "Report the unknown with correct units"},
        ],
    },

    # ─── AP UNIT 4 — Chemical Reactions ─────────────────────────────────────
    {
        "lesson": "Balancing Chemical Equations",
        "unit_id": "ap-unit-4",
        "lesson_index": 0,
        "steps": [
            {"label": "Inventory / Rules", "content": "Count atoms of each element on both sides"},
            {"label": "Draft",             "content": "Change coefficients only, NEVER change subscripts"},
            {"label": "Refine",            "content": "Balance elements appearing once on each side first"},
            {"label": "Final Answer",      "content": "Verify all atoms balance; reduce to smallest whole numbers"},
        ],
    },
    {
        "lesson": "Synthesis & Decomposition Reactions",
        "unit_id": "ap-unit-4",
        "lesson_index": 1,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify reactant/product patterns"},
            {"label": "Draft",             "content": "Synthesis: $\\mathrm{A + B \\rightarrow AB}$"},
            {"label": "Refine",            "content": "Decomposition: $\\mathrm{AB \\rightarrow A + B}$"},
            {"label": "Final Answer",      "content": "Balance coefficients and verify atom counts"},
        ],
    },
    {
        "lesson": "Single Replacement Reactions",
        "unit_id": "ap-unit-4",
        "lesson_index": 2,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify the free element and the compound"},
            {"label": "Draft",             "content": "Use the Activity Series to check if reaction occurs"},
            {"label": "Refine",            "content": "Write: $\\mathrm{A + BC \\rightarrow AC + B}$"},
            {"label": "Final Answer",      "content": "Balance products and ensure correct ionic charges"},
        ],
    },
    {
        "lesson": "Double Replacement Reactions",
        "unit_id": "ap-unit-4",
        "lesson_index": 3,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify the two aqueous ionic compounds"},
            {"label": "Draft",             "content": "Swap cations: $\\mathrm{AB + CD \\rightarrow AD + CB}$"},
            {"label": "Refine",            "content": "Check solubility rules for precipitate, gas, or water"},
            {"label": "Final Answer",      "content": "Balance coefficients and cross-charges for products"},
        ],
    },
    {
        "lesson": "Net Ionic Equations",
        "unit_id": "ap-unit-4",
        "lesson_index": 4,
        "steps": [
            {"label": "Inventory / Rules", "content": "Identify states: $(aq)$, $(s)$, $(l)$, $(g)$"},
            {"label": "Draft",             "content": "Split ONLY strong aqueous electrolytes into ions"},
            {"label": "Refine",            "content": "Cross out spectator ions appearing on both sides"},
            {"label": "Final Answer",      "content": "Write remaining species; verify mass and charge balance"},
        ],
    },
    {
        "lesson": "Redox Reactions & Titration",
        "unit_id": "ap-unit-4",
        "lesson_index": 5,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify analyte, titrant, and overall balanced reaction"},
            {"label": "Conversion Factors", "content": "Find molarity ($M = n/V$) and the stoichiometric mole ratio"},
            {"label": "Dimensional Setup",  "content": "Chain: $V_{\\text{titrant}} \\rightarrow n_{\\text{titrant}} \\rightarrow n_{\\text{analyte}} \\rightarrow \\text{Target}$"},
            {"label": "Calculate",          "content": "Multiply factors across, ensuring units cancel"},
            {"label": "Answer",             "content": "Report final concentration or mass with units"},
        ],
    },
    {
        "lesson": "Mole-Mole Calculations",
        "unit_id": "ap-unit-4",
        "lesson_index": 6,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify the given moles and the target substance"},
            {"label": "Conversion Factors", "content": "Find the mole ratio from the balanced equation"},
            {"label": "Dimensional Setup",  "content": "Set $\\frac{\\text{moles target}}{\\text{moles given}}$ so given units cancel"},
            {"label": "Calculate",          "content": "Multiply given moles by the ratio fraction"},
            {"label": "Answer",             "content": "State final moles with correct sig figs"},
        ],
    },
    {
        "lesson": "Mass-Mass Calculations",
        "unit_id": "ap-unit-4",
        "lesson_index": 7,
        "steps": [
            {"label": "Goal / Setup",       "content": "Map: $\\text{Mass A} \\rightarrow \\text{Moles A} \\rightarrow \\text{Moles B} \\rightarrow \\text{Mass B}$"},
            {"label": "Conversion Factors", "content": "Find molar masses and the equation mole ratio"},
            {"label": "Dimensional Setup",  "content": "Chain all three factors so units cancel diagonally"},
            {"label": "Calculate",          "content": "Multiply numerators, divide by denominators"},
            {"label": "Answer",             "content": "Report target mass in grams"},
        ],
    },
    {
        "lesson": "Limiting Reactants",
        "unit_id": "ap-unit-4",
        "lesson_index": 8,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify given amounts of BOTH reactants"},
            {"label": "Conversion Factors", "content": "Convert each reactant to moles of the same product"},
            {"label": "Dimensional Setup",  "content": "Compare the two theoretical product yields"},
            {"label": "Calculate",          "content": "The reactant that makes LESS product is limiting"},
            {"label": "Answer",             "content": "Calculate $\\% \\text{ Yield} = \\frac{\\text{Actual}}{\\text{Theoretical}} \\times 100$ if asked"},
        ],
    },

    # ─── AP UNIT 6 — Thermodynamics ──────────────────────────────────────────
    {
        "lesson": "Introduction to Thermochemistry",
        "unit_id": "ap-unit-6",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Identify the system (reaction) and surroundings (water/air)"},
            {"label": "Relation",         "content": "Observe the temperature change of the surroundings"},
            {"label": "Evidence / Claim", "content": "If surroundings warm up, the system released heat"},
            {"label": "Conclusion",       "content": "Classify as endothermic ($+q$) or exothermic ($-q$)"},
        ],
    },
    {
        "lesson": "Calorimetry",
        "unit_id": "ap-unit-6",
        "lesson_index": 1,
        "steps": [
            {"label": "Equation",   "content": "$q = mc\\Delta T$ and $q_{\\text{sys}} = -q_{\\text{surr}}$"},
            {"label": "Knowns",     "content": "Identify mass, specific heat ($c$), and $\\Delta T$ ($T_f - T_i$)"},
            {"label": "Substitute", "content": "Calculate $q_{\\text{surr}}$ (the water) first"},
            {"label": "Calculate",  "content": "Apply $q_{\\text{sys}} = -q_{\\text{surr}}$ to find reaction heat"},
            {"label": "Answer",     "content": "Report heat in Joules or kJ with the correct sign"},
        ],
    },
    {
        "lesson": "Thermochemical Equations",
        "unit_id": "ap-unit-6",
        "lesson_index": 2,
        "steps": [
            {"label": "Goal / Setup",       "content": "Relate given moles to the balanced equation's $\\Delta H$"},
            {"label": "Conversion Factors", "content": "Use ratio: $\\frac{\\Delta H}{\\text{moles from balanced equation}}$"},
            {"label": "Dimensional Setup",  "content": "Multiply given amount by the enthalpy conversion factor"},
            {"label": "Calculate",          "content": "Perform the calculation, keeping the sign of $\\Delta H$"},
            {"label": "Answer",             "content": "Report the total heat exchanged with correct units"},
        ],
    },
    {
        "lesson": "Heating Curves",
        "unit_id": "ap-unit-6",
        "lesson_index": 3,
        "steps": [
            {"label": "Data Extraction", "content": "Identify temperature changes (slopes) and phase changes (plateaus)"},
            {"label": "Feature ID",      "content": "Slopes use $q = mc\\Delta T$; Plateaus use $q = n\\Delta H$"},
            {"label": "Apply Concept",   "content": "Calculate the heat ($q$) required for each specific segment"},
            {"label": "Conclusion",      "content": "Sum the segment heats to find total energy required"},
        ],
    },
    {
        "lesson": "Bond Enthalpies",
        "unit_id": "ap-unit-6",
        "lesson_index": 4,
        "steps": [
            {"label": "Equation",   "content": "$\\Delta H \\approx \\sum(\\text{bonds broken}) - \\sum(\\text{bonds formed})$"},
            {"label": "Knowns",     "content": "Draw Lewis structures to count all bonds"},
            {"label": "Substitute", "content": "Insert bond enthalpy values for reactants (broken) and products (formed)"},
            {"label": "Calculate",  "content": "Sum the broken bonds, sum the formed bonds, then subtract"},
            {"label": "Answer",     "content": "Report $\\Delta H$ in $\\text{kJ/mol}$"},
        ],
    },

    # ─── AP UNIT 7 — Equilibrium ─────────────────────────────────────────────
    {
        "lesson": "Introduction to Equilibrium & Kc",
        "unit_id": "ap-unit-7",
        "lesson_index": 0,
        "steps": [
            {"label": "Inventory / Rules", "content": "Write balanced equation and identify phases ($aq$, $g$, $l$, $s$)"},
            {"label": "Draft",             "content": "Set $K_c = \\frac{[\\text{products}]^{\\text{coeff}}}{[\\text{reactants}]^{\\text{coeff}}}$"},
            {"label": "Refine",            "content": "Exclude all pure solids ($s$) and liquids ($l$)"},
            {"label": "Final Answer",      "content": "Ensure exponents match the balanced coefficients exactly"},
        ],
    },

    # ─── AP UNIT 8 — Acids & Bases ───────────────────────────────────────────
    {
        "lesson": "Acids & Bases Properties",
        "unit_id": "ap-unit-8",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Acids donate $\\mathrm{H^+}$; bases accept $\\mathrm{H^+}$ (Brønsted-Lowry)"},
            {"label": "Relation",         "content": "Identify the reactant that loses an $\\mathrm{H^+}$"},
            {"label": "Evidence / Claim", "content": "The species formed after loss is the conjugate base"},
            {"label": "Conclusion",       "content": "State the acid, base, and their conjugate pairs"},
        ],
    },
    {
        "lesson": "Acid-Base Calculations",
        "unit_id": "ap-unit-8",
        "lesson_index": 1,
        "steps": [
            {"label": "Equation",   "content": "$\\mathrm{pH} = -\\log[\\mathrm{H^+}]$, $\\mathrm{pH} + \\mathrm{pOH} = 14$"},
            {"label": "Knowns",     "content": "Identify given $\\mathrm{pH}$, $\\mathrm{pOH}$, $[\\mathrm{H^+}]$, or $[\\mathrm{OH^-}]$"},
            {"label": "Substitute", "content": "Use $10^{-\\mathrm{pH}}$ or $10^{-\\mathrm{pOH}}$ to reverse logs if needed"},
            {"label": "Calculate",  "content": "Perform calculations (remember $K_w = 1.0 \\times 10^{-14}$)"},
            {"label": "Answer",     "content": "Report the final value with correct sig figs"},
        ],
    },
    {
        "lesson": "Weak Acids (Part 1): Concepts & Ka",
        "unit_id": "ap-unit-8",
        "lesson_index": 2,
        "steps": [
            {"label": "Concept ID",       "content": "Weak acids only partially ionize in water"},
            {"label": "Relation",         "content": "Use $K_a = \\frac{[\\mathrm{H^+}][\\mathrm{A^-}]}{[\\mathrm{HA}]}$"},
            {"label": "Evidence / Claim", "content": "Larger $K_a$ means more products and a stronger acid"},
            {"label": "Conclusion",       "content": "Compare acid strengths based on their $K_a$ values"},
        ],
    },
    {
        "lesson": "Weak Acids (Part 2): ICE Table Calculations",
        "unit_id": "ap-unit-8",
        "lesson_index": 3,
        "steps": [
            {"label": "Goal / Setup",       "content": "Set up ICE table for $\\mathrm{HA} \\rightleftharpoons \\mathrm{H^+} + \\mathrm{A^-}$"},
            {"label": "Conversion Factors", "content": "Define changes as $-x$, $+x$, and $+x$"},
            {"label": "Dimensional Setup",  "content": "Substitute into $K_a = \\frac{x^2}{[\\mathrm{HA}]_0 - x}$"},
            {"label": "Calculate",          "content": "Assume $x$ is small to simplify, then solve for $x$"},
            {"label": "Answer",             "content": "Use $x$ as $[\\mathrm{H^+}]$ to find $\\mathrm{pH}$ or $\\%$ ionization"},
        ],
    },
    {
        "lesson": "Ka, Kb, and Conjugate Pairs",
        "unit_id": "ap-unit-8",
        "lesson_index": 4,
        "steps": [
            {"label": "Equation",   "content": "$K_a \\times K_b = K_w = 1.0 \\times 10^{-14}$"},
            {"label": "Knowns",     "content": "Identify the given $K_a$ or $K_b$ for the conjugate pair"},
            {"label": "Substitute", "content": "Insert values into $K_b = \\frac{K_w}{K_a}$ or vice versa"},
            {"label": "Calculate",  "content": "Divide $1.0 \\times 10^{-14}$ by the given constant"},
            {"label": "Answer",     "content": "Report the missing equilibrium constant"},
        ],
    },
    {
        "lesson": "Salt Hydrolysis",
        "unit_id": "ap-unit-8",
        "lesson_index": 5,
        "steps": [
            {"label": "Concept ID",       "content": "Split the salt into its cation and anion"},
            {"label": "Relation",         "content": "Determine the parent acid and base for each ion"},
            {"label": "Evidence / Claim", "content": "Conjugates of weak acids/bases will react with water"},
            {"label": "Conclusion",       "content": "Predict if the resulting solution is acidic, basic, or neutral"},
        ],
    },
    {
        "lesson": "Buffers: Design & Simulation",
        "unit_id": "ap-unit-8",
        "lesson_index": 6,
        "steps": [
            {"label": "Equation",   "content": "$\\mathrm{pH} = \\mathrm{p}K_a + \\log\\left(\\frac{[\\mathrm{A^-}]}{[\\mathrm{HA}]}\\right)$"},
            {"label": "Knowns",     "content": "Identify target $\\mathrm{pH}$, acid $\\mathrm{p}K_a$, and base/acid ratio"},
            {"label": "Substitute", "content": "Insert values into the Henderson-Hasselbalch equation"},
            {"label": "Calculate",  "content": "Solve for the required ratio of $[\\mathrm{A^-}]$ to $[\\mathrm{HA}]$"},
            {"label": "Answer",     "content": "State the ratio or amounts needed to create the buffer"},
        ],
    },
    {
        "lesson": "Acid-Base Titration Curves",
        "unit_id": "ap-unit-8",
        "lesson_index": 7,
        "steps": [
            {"label": "Data Extraction", "content": "Locate the equivalence point (steepest vertical drop/rise)"},
            {"label": "Feature ID",      "content": "Read the $\\mathrm{pH}$ exactly at the equivalence point"},
            {"label": "Apply Concept",   "content": "If $\\mathrm{pH} = 7$, strong/strong. If $\\mathrm{pH} > 7$, weak acid/strong base."},
            {"label": "Conclusion",      "content": "Determine the identity or concentration of the analyte"},
        ],
    },
    {
        "lesson": "Polyprotic Acids",
        "unit_id": "ap-unit-8",
        "lesson_index": 8,
        "steps": [
            {"label": "Data Extraction", "content": "Identify the polyprotic acid (e.g., $\\mathrm{H_3PO_4}$ or $\\mathrm{H_2SO_4}$)"},
            {"label": "Feature ID",      "content": "List the sequential $K_{a1}$, $K_{a2}$, etc. values"},
            {"label": "Apply Concept",   "content": "Recognize that $K_{a1} \\gg K_{a2}$ (first proton is easiest to remove)"},
            {"label": "Conclusion",      "content": "Assume $K_{a1}$ dictates the entire $\\mathrm{pH}$ of the solution"},
        ],
    },

    # ─── Standard: Intro to Chemistry ────────────────────────────────────────
    {
        "lesson": "Safety",
        "unit_id": "unit-intro-chem",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Identify the primary hazard and the broken rule"},
            {"label": "Relation",         "content": "Name the specific safety equipment required"},
            {"label": "Evidence / Claim", "content": "State the standard procedure for using this equipment"},
            {"label": "Conclusion",       "content": "What is the very next action? (e.g., tell the teacher)"},
        ],
    },
    {
        "lesson": "Scientific Method",
        "unit_id": "unit-intro-chem",
        "lesson_index": 1,
        "steps": [
            {"label": "Data Extraction", "content": "List observations, measurements, and given facts"},
            {"label": "Feature ID",      "content": "Identify independent, dependent, and controlled variables"},
            {"label": "Apply Concept",   "content": "Formulate a testable hypothesis (If... then...)"},
            {"label": "Conclusion",      "content": "Compare results to hypothesis; revise if needed"},
        ],
    },
    {
        "lesson": "Classification of Matter",
        "unit_id": "unit-intro-chem",
        "lesson_index": 2,
        "steps": [
            {"label": "Data Extraction", "content": "List observable properties and composition clues"},
            {"label": "Feature ID",      "content": "Decide: pure substance or mixture?"},
            {"label": "Apply Concept",   "content": "Can it be physically or chemically separated?"},
            {"label": "Conclusion",      "content": "Classify as element, compound, homogeneous, or heterogeneous"},
        ],
    },
    {
        "lesson": "Chemical & Physical Changes",
        "unit_id": "unit-intro-chem",
        "lesson_index": 3,
        "steps": [
            {"label": "Concept ID",       "content": "Did the actual chemical formula change?"},
            {"label": "Relation",         "content": "Look for color change, gas, heat, or precipitate"},
            {"label": "Evidence / Claim", "content": "New substance = chemical; Same substance = physical"},
            {"label": "Conclusion",       "content": "Classify the change based on the evidence"},
        ],
    },
    {
        "lesson": "Measurement & Scientific Notation",
        "unit_id": "unit-intro-chem",
        "lesson_index": 4,
        "steps": [
            {"label": "Goal / Setup",       "content": "Identify given value and target unit/format"},
            {"label": "Conversion Factors", "content": "Use metric prefixes or $D = \\frac{m}{V}$"},
            {"label": "Dimensional Setup",  "content": "Set up math: $a \\times 10^n$ (where $1 \\leq a < 10$)"},
            {"label": "Calculate",          "content": "Move decimal: Left = positive $n$, Right = negative $n$"},
            {"label": "Answer",             "content": "State final value with correct sig figs and unit"},
        ],
    },

    # ─── Standard: Periodic Table ────────────────────────────────────────────
    {
        "lesson": "History of the Periodic Table",
        "unit_id": "unit-periodic-table",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Identify the scientist (e.g., Mendeleev vs Moseley)"},
            {"label": "Relation",         "content": "Did they sort by Atomic Mass or Atomic Number?"},
            {"label": "Evidence / Claim", "content": "Elements in the same column share chemical properties"},
            {"label": "Conclusion",       "content": "State how the modern table resolves historical flaws"},
        ],
    },

    # ─── Standard: Atomic Theory ─────────────────────────────────────────────
    {
        "lesson": "History & Basics of Atomic Theory",
        "unit_id": "unit-atomic-theory",
        "lesson_index": 0,
        "steps": [
            {"label": "Concept ID",       "content": "Identify the scientist (e.g., Dalton, Thomson, Rutherford, Bohr)"},
            {"label": "Relation",         "content": "Name their specific experiment (e.g., Gold Foil, Cathode Ray)"},
            {"label": "Evidence / Claim", "content": "State the physical observation made during the experiment"},
            {"label": "Conclusion",       "content": "Conclude what subatomic particle or structure was discovered"},
        ],
    },
]
