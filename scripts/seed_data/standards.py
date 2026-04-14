"""
Official standards seed data (NGSS HS-PS and AP Chemistry CED).

STANDARDS_SEED is a flat list: each row has ``source`` (stored as ``framework`` in DB),
``category``, and ``is_core``. Lesson ↔ standard junction rows are in lesson_standards.py.

NGSS sources:
  "NGSS"       — Disciplinary Core Ideas (HS-PS1-x, HS-PS2-x, HS-PS3-x)
  "NGSS-SEP"   — Science and Engineering Practices
  "NGSS-CCC"   — Crosscutting Concepts

AP source:
  "AP"         — AP Chemistry CED (AP-X.Y codes)
"""

from typing import TypedDict


class StandardSeedRow(TypedDict):
    code: str
    source: str
    title: str
    description: str | None
    category: str | None
    is_core: bool


STANDARDS_SEED: list[StandardSeedRow] = [

    # ══════════════════════════════════════════════════════════════════════
    # NGSS — Disciplinary Core Ideas (HS-PS)
    # Descriptions match the curriculum document exactly.
    # ══════════════════════════════════════════════════════════════════════

    {
        "code": "HS-PS1-1",
        "source": "NGSS",
        "title": "Predict element properties from atomic structure patterns",
        "description": "Use the periodic table as a model to predict the properties of elements based on patterns in atomic structure.",
        "category": "Structure and Properties of Matter",
        "is_core": True,
    },
    {
        "code": "HS-PS1-2",
        "source": "NGSS",
        "title": "Explain chemical reactions — atoms rearrange but are conserved",
        "description": "Construct explanations for how substances react by using evidence that atoms rearrange but are conserved during chemical processes.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "HS-PS1-3",
        "source": "NGSS",
        "title": "Investigate how substance properties change during chemical reactions",
        "description": "Plan and carry out investigations to gather evidence about how the properties of substances change when they undergo chemical reactions.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "HS-PS1-4",
        "source": "NGSS",
        "title": "Model energy absorbed or released during bond changes",
        "description": "Develop models that show how energy is absorbed or released when chemical bonds form or break during reactions.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "HS-PS1-5",
        "source": "NGSS",
        "title": "Explain effects of temperature and concentration on reaction rates",
        "description": "Apply scientific principles to explain how changing conditions (i.e., temperature or concentration) affect reaction rates.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "HS-PS1-7",
        "source": "NGSS",
        "title": "Demonstrate conservation of atoms and mass in chemical reactions",
        "description": "Use mathematical representations to demonstrate that atoms, and therefore mass, are conserved in chemical reactions.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "HS-PS1-8",
        "source": "NGSS",
        "title": "Model nuclear processes — decay, fission, and fusion",
        "description": "Develop models to illustrate nuclear processes, including radioactive decay, fission, and fusion.",
        "category": "Nuclear Processes",
        "is_core": True,
    },
    {
        "code": "HS-PS2-6",
        "source": "NGSS",
        "title": "Molecular structure determines interactions and properties",
        "description": "Communicate scientific information showing how the structure of molecules determines their interactions and resulting properties.",
        "category": "Motion and Stability: Forces and Interactions",
        "is_core": True,
    },
    {
        "code": "HS-PS3-1",
        "source": "NGSS",
        "title": "Model energy changes within a system based on particle interactions",
        "description": "Create computational models to calculate how energy changes within a system based on the motion and interactions of particles.",
        "category": "Energy",
        "is_core": True,
    },
    {
        "code": "HS-PS3-2",
        "source": "NGSS",
        "title": "Model energy transfer between particles or systems",
        "description": "Develop and use models to illustrate how energy is transferred between particles or systems, such as during heating or cooling.",
        "category": "Energy",
        "is_core": True,
    },
    {
        "code": "HS-PS3-3",
        "source": "NGSS",
        "title": "Design energy-transfer systems with real-world constraints",
        "description": "Design or evaluate systems that involve energy transfer, considering constraints such as materials, efficiency, and environmental impact.",
        "category": "Energy",
        "is_core": True,
    },

    # ══════════════════════════════════════════════════════════════════════
    # NGSS — Science and Engineering Practices (SEPs)
    # is_core = False; these are practices, not disciplinary ideas.
    # Only the five SEPs used across this curriculum are seeded.
    # ══════════════════════════════════════════════════════════════════════

    {
        "code": "NGSS-SEP-2",
        "source": "NGSS-SEP",
        "title": "Developing and Using Models",
        "description": "Develop and use models to represent and explain phenomena or to predict outcomes.",
        "category": "Science and Engineering Practices",
        "is_core": False,
    },
    {
        "code": "NGSS-SEP-3",
        "source": "NGSS-SEP",
        "title": "Planning and Carrying Out Investigations",
        "description": "Plan and carry out investigations to produce data for constructing or revising explanations and designing solutions.",
        "category": "Science and Engineering Practices",
        "is_core": False,
    },
    {
        "code": "NGSS-SEP-4",
        "source": "NGSS-SEP",
        "title": "Analyzing and Interpreting Data",
        "description": "Analyze and interpret data to provide evidence for phenomena.",
        "category": "Science and Engineering Practices",
        "is_core": False,
    },
    {
        "code": "NGSS-SEP-5",
        "source": "NGSS-SEP",
        "title": "Using Mathematics and Computational Thinking",
        "description": "Use mathematics and computational thinking to represent and understand phenomena and to solve problems.",
        "category": "Science and Engineering Practices",
        "is_core": False,
    },
    {
        "code": "NGSS-SEP-6",
        "source": "NGSS-SEP",
        "title": "Constructing Explanations and Designing Solutions",
        "description": "Construct explanations and design solutions supported by multiple sources of evidence.",
        "category": "Science and Engineering Practices",
        "is_core": False,
    },

    # ══════════════════════════════════════════════════════════════════════
    # NGSS — Crosscutting Concepts (CCCs)
    # is_core = False; these are lenses, not disciplinary ideas.
    # Only the five CCCs used across this curriculum are seeded.
    # ══════════════════════════════════════════════════════════════════════

    {
        "code": "NGSS-CCC-1",
        "source": "NGSS-CCC",
        "title": "Patterns",
        "description": "Observed patterns in nature guide organization and classification and prompt questions about relationships and causation.",
        "category": "Crosscutting Concepts",
        "is_core": False,
    },
    {
        "code": "NGSS-CCC-3",
        "source": "NGSS-CCC",
        "title": "Scale, Proportion, and Quantity",
        "description": "In considering phenomena, it is critical to recognize what is relevant at different size, time, and energy scales and to recognize proportional relationships.",
        "category": "Crosscutting Concepts",
        "is_core": False,
    },
    {
        "code": "NGSS-CCC-5",
        "source": "NGSS-CCC",
        "title": "Energy and Matter",
        "description": "Tracking energy and matter flows into, out of, and within systems helps one understand the system's behavior.",
        "category": "Crosscutting Concepts",
        "is_core": False,
    },
    {
        "code": "NGSS-CCC-6",
        "source": "NGSS-CCC",
        "title": "Structure and Function",
        "description": "The way an object is shaped or structured determines many of its properties and functions.",
        "category": "Crosscutting Concepts",
        "is_core": False,
    },
    {
        "code": "NGSS-CCC-7",
        "source": "NGSS-CCC",
        "title": "Stability and Change",
        "description": "For both designed and natural systems, conditions that affect stability and factors that control rates of change are critical elements.",
        "category": "Crosscutting Concepts",
        "is_core": False,
    },

    # ══════════════════════════════════════════════════════════════════════
    # AP Chemistry CED (by unit / topic) — unchanged
    # ══════════════════════════════════════════════════════════════════════

    # Unit 1 — Atomic Structure and Properties
    {
        "code": "AP-1.1",
        "source": "AP",
        "title": "Moles and Molar Mass",
        "description": "Calculate quantities of a substance or its relative number of particles using dimensional analysis and the mole concept.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    {
        "code": "AP-1.2",
        "source": "AP",
        "title": "Mass Spectrometry of Elements",
        "description": "Explain the quantitative relationship between the mass spectrum of an element and the masses of the element's isotopes.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    {
        "code": "AP-1.3",
        "source": "AP",
        "title": "Elemental Composition of Pure Substances",
        "description": "Explain the quantitative relationship between the elemental composition by mass and the empirical formula of a pure substance.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    {
        "code": "AP-1.5",
        "source": "AP",
        "title": "Atomic Structure and Electron Configuration",
        "description": "Represent the electron configuration of an element or ions of an element using the Aufbau principle.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    {
        "code": "AP-1.6",
        "source": "AP",
        "title": "Photoelectron Spectroscopy",
        "description": "Explain the relationship between the photoelectron spectrum of an atom or ion and the electron configuration of the species.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    {
        "code": "AP-1.7",
        "source": "AP",
        "title": "Periodic Trends",
        "description": "Explain the relationship between trends in atomic properties of elements and atomic structure and periodicity.",
        "category": "Atomic Structure and Properties",
        "is_core": True,
    },
    # Unit 2 — Molecular and Ionic Compound Structure and Properties
    {
        "code": "AP-2.1",
        "source": "AP",
        "title": "Types of Chemical Bonds",
        "description": "Explain the relationship between the type of bonding and the solid properties based on electronegativity differences.",
        "category": "Molecular and Ionic Compound Structure",
        "is_core": True,
    },
    {
        "code": "AP-2.3",
        "source": "AP",
        "title": "Structure of Ionic Solids",
        "description": "Represent the ionic solid structure using particulate models that show maximizing attractions and minimizing repulsions.",
        "category": "Molecular and Ionic Compound Structure",
        "is_core": True,
    },
    {
        "code": "AP-2.5",
        "source": "AP",
        "title": "Lewis Diagrams",
        "description": "Represent a molecule with a Lewis diagram, showing bonding and nonbonding electron pairs.",
        "category": "Molecular and Ionic Compound Structure",
        "is_core": True,
    },
    {
        "code": "AP-2.6",
        "source": "AP",
        "title": "Resonance and Formal Charge",
        "description": "Represent a molecule with a Lewis diagram that accounts for resonance and calculates formal charge to determine the best structure.",
        "category": "Molecular and Ionic Compound Structure",
        "is_core": True,
    },
    {
        "code": "AP-2.7",
        "source": "AP",
        "title": "VSEPR and Bond Hybridization",
        "description": "Predict the geometry and hybridization (sp, sp2, sp3) of a central atom based on VSEPR theory.",
        "category": "Molecular and Ionic Compound Structure",
        "is_core": True,
    },
    # Unit 3 — Intermolecular Forces and Properties
    {
        "code": "AP-3.1",
        "source": "AP",
        "title": "Intermolecular Forces",
        "description": "Explain the relationship between the chemical structures of molecules and the relative strength of their intermolecular forces.",
        "category": "Intermolecular Forces and Properties",
        "is_core": True,
    },
    {
        "code": "AP-3.4",
        "source": "AP",
        "title": "Ideal Gas Law",
        "description": "Explain the relationship between the macroscopic properties of a sample of gas or mixture of gases using the ideal gas law.",
        "category": "Intermolecular Forces and Properties",
        "is_core": True,
    },
    {
        "code": "AP-3.8",
        "source": "AP",
        "title": "Representations of Solutions",
        "description": "Using particulate models for mixtures, represent interactions between components (solute and solvent).",
        "category": "Intermolecular Forces and Properties",
        "is_core": True,
    },
    {
        "code": "AP-3.13",
        "source": "AP",
        "title": "Beer-Lambert Law",
        "description": "Explain the amount of light absorbed by a solution of molecules or ions in relationship to the concentration, path length, and molar absorptivity.",
        "category": "Intermolecular Forces and Properties",
        "is_core": True,
    },
    # Unit 4 — Chemical Reactions
    {
        "code": "AP-4.2",
        "source": "AP",
        "title": "Net Ionic Equations",
        "description": "Represent changes in matter with a balanced net ionic equation.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "AP-4.5",
        "source": "AP",
        "title": "Stoichiometry",
        "description": "Explain changes in the amounts of reactants and products based on the balanced reaction equation for a chemical process.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "AP-4.6",
        "source": "AP",
        "title": "Introduction to Titration",
        "description": "Identify the equivalence point in a titration based on the amounts of the titrant and analyte.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    {
        "code": "AP-4.9",
        "source": "AP",
        "title": "Oxidation-Reduction (Redox) Reactions",
        "description": "Represent a redox reaction with a balanced equation and identify oxidation states.",
        "category": "Chemical Reactions",
        "is_core": True,
    },
    # Unit 5 — Kinetics
    {
        "code": "AP-5.1",
        "source": "AP",
        "title": "Reaction Rates",
        "description": "Explain the relationship between the rate of a chemical reaction and experimental parameters.",
        "category": "Kinetics",
        "is_core": True,
    },
    {
        "code": "AP-5.2",
        "source": "AP",
        "title": "Introduction to Rate Law",
        "description": "Identify the rate law expression of a chemical reaction using data that show how the concentrations of reactants affect the rate.",
        "category": "Kinetics",
        "is_core": True,
    },
    {
        "code": "AP-5.3",
        "source": "AP",
        "title": "Concentration Changes Over Time",
        "description": "Identify the rate law expression of a chemical reaction using data that show how the concentration of a reactant changes over time (Integrated Rate Laws).",
        "category": "Kinetics",
        "is_core": True,
    },
    {
        "code": "AP-5.5",
        "source": "AP",
        "title": "Collision Model",
        "description": "Explain the relationship between the rate of an elementary reaction and the frequency, energy, and orientation of molecular collisions.",
        "category": "Kinetics",
        "is_core": True,
    },
    {
        "code": "AP-5.8",
        "source": "AP",
        "title": "Reaction Mechanism and Rate Law",
        "description": "Identify the rate law for a reaction from a mechanism in which the first step is rate determining.",
        "category": "Kinetics",
        "is_core": True,
    },
    {
        "code": "AP-5.11",
        "source": "AP",
        "title": "Catalysis",
        "description": "Explain the relationship between the effect of a catalyst on a reaction and changes in the reaction mechanism.",
        "category": "Kinetics",
        "is_core": True,
    },
    # Unit 6 — Thermodynamics
    {
        "code": "AP-6.1",
        "source": "AP",
        "title": "Endothermic and Exothermic Processes",
        "description": "Explain the relationship between experimental observations and energy changes associated with a chemical or physical transformation.",
        "category": "Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-6.4",
        "source": "AP",
        "title": "Heat Capacity and Calorimetry",
        "description": "Calculate the heat q absorbed or released by a system undergoing heating/cooling based on the amount of the substance, heat capacity, and change in temperature.",
        "category": "Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-6.8",
        "source": "AP",
        "title": "Enthalpy of Formation",
        "description": "Calculate the enthalpy change for a chemical or physical process based on the standard enthalpies of formation.",
        "category": "Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-6.9",
        "source": "AP",
        "title": "Hess's Law",
        "description": "Represent a chemical or physical process as a sequence of steps; and calculate the enthalpy change using Hess's Law.",
        "category": "Thermodynamics",
        "is_core": True,
    },
    # Unit 7 — Equilibrium
    {
        "code": "AP-7.2",
        "source": "AP",
        "title": "Direction of Reversible Reactions",
        "description": "Explain the relationship between the direction in which a reversible reaction proceeds and the relative rates of the forward and reverse reactions.",
        "category": "Equilibrium",
        "is_core": True,
    },
    {
        "code": "AP-7.4",
        "source": "AP",
        "title": "Calculating the Equilibrium Constant",
        "description": "Calculate the value of an equilibrium constant, K, from concentration data.",
        "category": "Equilibrium",
        "is_core": True,
    },
    {
        "code": "AP-7.9",
        "source": "AP",
        "title": "Introduction to Le Chatelier's Principle",
        "description": "Identify the response of a system at equilibrium to an external stress, using Le Chatelier's principle.",
        "category": "Equilibrium",
        "is_core": True,
    },
    {
        "code": "AP-7.11",
        "source": "AP",
        "title": "Introduction to Solubility Equilibria",
        "description": "Calculate the solubility of a salt based on the value of Ksp for the salt.",
        "category": "Equilibrium",
        "is_core": True,
    },
    # Unit 8 — Acids and Bases
    {
        "code": "AP-8.1",
        "source": "AP",
        "title": "Introduction to Acids and Bases",
        "description": "Identify acids and bases and explain their behavior in aqueous solutions based on Arrhenius, Brønsted-Lowry, and Lewis definitions.",
        "category": "Acids and Bases",
        "is_core": True,
    },
    {
        "code": "AP-8.2",
        "source": "AP",
        "title": "pH and pOH of Strong Acids and Bases",
        "description": "Calculate pH and pOH based on concentrations of particulate species in a solution of a strong acid or a strong base.",
        "category": "Acids and Bases",
        "is_core": True,
    },
    {
        "code": "AP-8.3",
        "source": "AP",
        "title": "Weak Acid and Base Equilibria",
        "description": "Calculate pH and pOH based on concentrations of particulate species in a solution of a weak acid or a weak base (using Ka and Kb).",
        "category": "Acids and Bases",
        "is_core": True,
    },
    {
        "code": "AP-8.5",
        "source": "AP",
        "title": "Acid-Base Titrations",
        "description": "Explain results from the titration of a mono- or polyprotic acid or base solution, in relation to the properties of the solution and its components.",
        "category": "Acids and Bases",
        "is_core": True,
    },
    {
        "code": "AP-8.8",
        "source": "AP",
        "title": "Properties of Buffers",
        "description": "Explain the relationship between the ability of a buffer to stabilize pH and the reactions that occur when an acid or a base is added to a buffered solution.",
        "category": "Acids and Bases",
        "is_core": True,
    },
    # Unit 9 — Applications of Thermodynamics
    {
        "code": "AP-9.1",
        "source": "AP",
        "title": "Introduction to Entropy",
        "description": "Identify the sign and relative magnitude of the entropy change associated with chemical or physical processes.",
        "category": "Applications of Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-9.3",
        "source": "AP",
        "title": "Gibbs Free Energy and Thermodynamic Favorability",
        "description": "Explain whether a physical or chemical process is thermodynamically favored based on an evaluation of ΔG°.",
        "category": "Applications of Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-9.5",
        "source": "AP",
        "title": "Free Energy and Equilibrium",
        "description": "Explain whether a physical or chemical process is thermodynamically favored based on an evaluation of ΔG° and K.",
        "category": "Applications of Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-9.7",
        "source": "AP",
        "title": "Galvanic (Voltaic) and Electrolytic Cells",
        "description": "Explain the relationship between the physical components of a galvanic or electrolytic cell and the overall operational principles of the cell.",
        "category": "Applications of Thermodynamics",
        "is_core": True,
    },
    {
        "code": "AP-9.8",
        "source": "AP",
        "title": "Cell Potential and Free Energy",
        "description": "Explain the relationship between the standard cell potential of a galvanic or electrolytic cell and the thermodynamic favorability of the overall redox reaction (ΔG° = -nFE°).",
        "category": "Applications of Thermodynamics",
        "is_core": True,
    },
]
