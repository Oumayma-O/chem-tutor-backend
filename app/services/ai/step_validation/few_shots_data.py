"""
Raw calibration-example strings for the LLM equivalence grader.

Each block is a category-labelled set of STUDENT / CANONICAL / VERDICT triples.
Imported by few_shots.py — do not add logic here.
"""

COMPOUND = """
[CATEGORY: multi-segment answers separated by semicolons]

STUDENT:   "ΔG° = -65600 J/mol; K = 3.15e11"
CANONICAL: "ΔG° = -65.6 kJ/mol; K = 3.15 × 10^11"
VERDICT:   CORRECT – ΔG° uses J/mol instead of kJ/mol but value scales correctly; K notation matches

STUDENT:   "rate = k[A]^2[B]; 3"
CANONICAL: "rate = k[A]^2[B]; overall order = 3"
VERDICT:   CORRECT – "3" is a valid shorthand for the overall order

STUDENT:   "k[X][Y]^2; 3rd order"
CANONICAL: "k[X][Y]^2; overall order = 3"
VERDICT:   CORRECT – "3rd order" conveys the same meaning as "overall order = 3"

STUDENT:   "ΔG° = -65.6 kJ/mol"
CANONICAL: "ΔG° = -65.6 kJ/mol; K = 3.15 × 10^11"
VERDICT:   WRONG – feedback: "Also include the equilibrium constant K."

STUDENT:   "rate = k[A]^2[B]; overall order = 4"
CANONICAL: "rate = k[A]^2[B]; overall order = 3"
VERDICT:   WRONG – feedback: "Recount the sum of the exponents in your rate law."

STUDENT:   "k[NO]^2[H2]; 2nd order"
CANONICAL: "k[NO][H2]^2; 3rd order"
VERDICT:   WRONG – feedback: "Exponents are on the wrong reactants and the overall order is incorrect."

STUDENT:   "k[NO][H2]^2; 3"
CANONICAL: "k[NO][H2]^2; overall order = 3"
VERDICT:   CORRECT – both segments match (rate law correct; "3" equals "overall order = 3")
"""

RATE_LAW = """
[CATEGORY: rate law and kinetics expressions]

STUDENT:   "k[A]^2 * [B]"
CANONICAL: "k[A]^2[B]"
VERDICT:   CORRECT – explicit multiplication sign; same expression

STUDENT:   "k[B][A]^2"
CANONICAL: "k[A]^2[B]"
VERDICT:   CORRECT – multiplication is commutative for rate law terms

STUDENT:   "Rate = k[A][B]"
CANONICAL: "k[A][B]"
VERDICT:   CORRECT – including "Rate =" prefix is acceptable extra context

STUDENT:   "k[A]^2[B]^0"
CANONICAL: "k[A]^2"
VERDICT:   CORRECT – raising B to the zero is equivalent to omitting it

STUDENT:   "k[NO]^2[H2]"
CANONICAL: "k[NO][H2]^2"
VERDICT:   WRONG – feedback: "Check which reactant carries second-order dependence."

STUDENT:   "k[A]^2"
CANONICAL: "k[A]^2[B]"
VERDICT:   WRONG – feedback: "Your rate law is missing one reactant."

STUDENT:   "k[A]^3[B]"
CANONICAL: "k[A]^2[B]"
VERDICT:   WRONG – feedback: "The order with respect to A is incorrect."

STUDENT:   "k[A]^2 / [B]"
CANONICAL: "k[A]^2[B]"
VERDICT:   WRONG – feedback: "B should appear in the numerator, not the denominator."

STUDENT:   "k[P]^2[Q]"
CANONICAL: "k[P][Q]^2"
VERDICT:   WRONG – feedback: "The exponents are assigned to the wrong reactants."
"""

EQUATION = """
[CATEGORY: balanced chemical equations]

STUDENT:   "4Al + 3O2 → 2Al2O3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   CORRECT

STUDENT:   "3O2 + 4Al → 2Al2O3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   CORRECT – reactant order does not change the equation's validity

STUDENT:   "2H2 + O2 → 2H2O"
CANONICAL: "2H2 + O2 → 2H2O"
VERDICT:   CORRECT

STUDENT:   "N2 + 3H2 → 2NH3"
CANONICAL: "N2 + 3H2 → 2NH3"
VERDICT:   CORRECT

STUDENT:   "2Al + 3O2 → 2Al2O3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   WRONG – feedback: "The coefficient for Al is incorrect — rebalance aluminum atoms."

STUDENT:   "4Al + 3O2 → Al2O3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   WRONG – feedback: "The product coefficient is missing — balance oxygen and aluminum."

STUDENT:   "4Al + O2 → 2Al2O3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   WRONG – feedback: "The coefficient for O2 is incorrect — oxygen atoms are not balanced."

STUDENT:   "4Al + 3O2 → 2AlO3"
CANONICAL: "4Al + 3O2 → 2Al2O3"
VERDICT:   WRONG – feedback: "The product formula is wrong — check the aluminum oxide formula."
"""

NUMERIC = """
[CATEGORY: single numeric values with or without units]

STUDENT:   "3.44 g"
CANONICAL: "3.44 g"
VERDICT:   CORRECT

STUDENT:   "121 * 10^-3 kg"
CANONICAL: "121 g"
VERDICT:   CORRECT – 121 × 10⁻³ kg = 0.121 kg = 121 g; SI unit conversion is valid

STUDENT:   "50 . 10^-3 kg"
CANONICAL: "50.0 g"
VERDICT:   CORRECT – spaced dot is a multiplication symbol; 50 × 10⁻³ kg = 0.050 kg = 50.0 g

STUDENT:   "50 . 10^3 g"
CANONICAL: "50.0 g"
VERDICT:   WRONG – feedback: "Check your power of ten — 50 × 10³ g is 50 000 g, not 50 g."

STUDENT:   "6.5 * 10^3 J/mol"
CANONICAL: "6500 J/mol"
VERDICT:   CORRECT – scientific notation; 6.5 × 10³ = 6500

STUDENT:   "6500 J/mol"
CANONICAL: "6.5 * 10^3 J/mol"
VERDICT:   CORRECT – expanded form equals the scientific notation value

STUDENT:   "48800 J/mol"
CANONICAL: "48.8 kJ/mol"
VERDICT:   CORRECT – equivalent SI prefix; value scales correctly

STUDENT:   "0.0250 M"
CANONICAL: "0.025 M"
VERDICT:   CORRECT – trailing zero; numerically identical

STUDENT:   "1.37 × 10^-3"
CANONICAL: "1.4 × 10^-3"
VERDICT:   CORRECT – within rounding tolerance of the stated significant figures

STUDENT:   "2.85 × 10^4 J/mol"
CANONICAL: "28.5 kJ/mol"
VERDICT:   CORRECT – equivalent SI prefix

STUDENT:   "1080 s"
CANONICAL: "1080"
VERDICT:   CORRECT – including the expected unit is acceptable when the value is correct

STUDENT:   "3.5 g"
CANONICAL: "3.44 g"
VERDICT:   WRONG – feedback: "Your value is slightly off — revisit the calculation."

STUDENT:   "-3.44 g"
CANONICAL: "3.44 g"
VERDICT:   WRONG – feedback: "Check the sign — deposited mass should be positive."

STUDENT:   "3.44 × 10^10"
CANONICAL: "3.44 × 10^11"
VERDICT:   WRONG – feedback: "Recheck your exponent — the answer is off by a factor of 10."

STUDENT:   "3.44 mol"
CANONICAL: "3.44 g"
VERDICT:   WRONG – feedback: "The unit is wrong — the answer should be in grams, not moles."

STUDENT:   "65.6 kJ/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   WRONG – feedback: "Check the sign — this reaction releases energy, so ΔG° is negative."

STUDENT:   "121 * 10^-3 g"
CANONICAL: "121 g"
VERDICT:   WRONG – feedback: "The unit is correct but check your power-of-ten — 10⁻³ g is not 1 g."
"""

EXPRESSION = """
[CATEGORY: algebraic or arithmetic expressions — calculation setups]

STUDENT:   "-(2)(96485)(0.34)"
CANONICAL: "-2 * 96485 * 0.34"
VERDICT:   CORRECT – parenthesized implied multiplication; same expression

STUDENT:   "(107.87 * 1080 * 2.85) / 96485"
CANONICAL: "(107.87 * 2.85 * 1080) / (1 * 96485)"
VERDICT:   CORRECT – multiplication is commutative; dividing by 1 is trivial

STUDENT:   "ln(k2/k1) = (Ea/R)(1/T1 - 1/T2)"
CANONICAL: "ln(k2/k1) = (Ea/R)(1/T1 - 1/T2)"
VERDICT:   CORRECT

STUDENT:   "-nFE"
CANONICAL: "-n * F * E"
VERDICT:   CORRECT – implicit multiplication is standard notation

STUDENT:   "(8.314 * 298) / (2 * 96485)"
CANONICAL: "RT / (nF)"
VERDICT:   CORRECT – fully substituted numeric form of the symbolic expression

STUDENT:   "-2 * 96485 * 0.35"
CANONICAL: "-2 * 96485 * 0.34"
VERDICT:   WRONG – feedback: "One substituted value is incorrect — recheck E°."

STUDENT:   "(107.87 * 2.85) / 96485"
CANONICAL: "(107.87 * 2.85 * 1080) / (1 * 96485)"
VERDICT:   WRONG – feedback: "The time factor is missing from the numerator."

STUDENT:   "2 * 96485 * 0.34"
CANONICAL: "-2 * 96485 * 0.34"
VERDICT:   WRONG – feedback: "The expression is missing the negative sign."
"""

EQUILIBRIUM = """
[CATEGORY: equilibrium expressions — Kc, Kp, Ksp, Q, ICE]

STUDENT:   "Kc = [C]^2 / ([A][B])"
CANONICAL: "Kc = [C]^2/([A][B])"
VERDICT:   CORRECT – spacing only

STUDENT:   "[C]^2 / ([A][B])"
CANONICAL: "Kc = [C]^2/([A][B])"
VERDICT:   CORRECT – omitting the "Kc =" prefix is acceptable shorthand

STUDENT:   "[Ag+]^2[CrO4^2-]"
CANONICAL: "[Ag+]^2[CrO4^2-]"
VERDICT:   CORRECT

STUDENT:   "x = 0.025 M"
CANONICAL: "0.025"
VERDICT:   CORRECT – variable label and unit are extra context; numeric value matches

STUDENT:   "[NH3]^2 / ([N2][H2]^3)"
CANONICAL: "[NH3]^2/([N2][H2]^3)"
VERDICT:   CORRECT – spacing only

STUDENT:   "[A][B] / [C]^2"
CANONICAL: "[C]^2 / ([A][B])"
VERDICT:   WRONG – feedback: "Your expression is inverted — products go in the numerator."

STUDENT:   "[C] / ([A][B])"
CANONICAL: "[C]^2/([A][B])"
VERDICT:   WRONG – feedback: "Check the exponent on C — use the stoichiometric coefficient."

STUDENT:   "[Ag+][CrO4^2-]"
CANONICAL: "[Ag+]^2[CrO4^2-]"
VERDICT:   WRONG – feedback: "The exponent on Ag⁺ is missing — use its stoichiometric coefficient."

STUDENT:   "Kc = [C]^2 * [A][B]"
CANONICAL: "Kc = [C]^2/([A][B])"
VERDICT:   WRONG – feedback: "Reactants belong in the denominator, not the numerator."
"""

CONFIG = """
[CATEGORY: electron configurations]

STUDENT:   "[Ar] 4s2 3d10 4p4"
CANONICAL: "[Ar] 4s^2 3d^10 4p^4"
VERDICT:   CORRECT – plain-text superscripts are equivalent to caret notation

STUDENT:   "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p4"
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   CORRECT – full configuration is equivalent to the noble-gas abbreviated form

STUDENT:   "[Ar] 4s2 3d10 4p4 "
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   CORRECT – trailing whitespace is irrelevant

STUDENT:   "[Kr] 5s2 4d10 5p6"
CANONICAL: "[Kr] 5s2 4d10 5p6"
VERDICT:   CORRECT

STUDENT:   "[Ar] 4s2 3d10 4p5"
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   WRONG – feedback: "The electron count in the 4p subshell is off by one."

STUDENT:   "[Ne] 4s2 3d10 4p4"
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   WRONG – feedback: "The noble gas core is incorrect — use the right preceding noble gas."

STUDENT:   "[Ar] 4s2 4p4"
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   WRONG – feedback: "You are missing the filled 3d subshell."

STUDENT:   "[Ar] 4s1 3d10 4p4"
CANONICAL: "[Ar] 4s2 3d10 4p4"
VERDICT:   WRONG – feedback: "The 4s subshell is not fully filled — recount the electrons."
"""

THERMODYNAMIC = """
[CATEGORY: thermodynamic quantities — ΔG°, ΔH°, ΔS°, K relationships]

STUDENT:   "-65600 J/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   CORRECT – equivalent SI prefix; value scales correctly

STUDENT:   "ΔG° = -65.6 kJ/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   CORRECT – including the variable label is fine

STUDENT:   "-65.61 kJ/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   CORRECT – within rounding tolerance

STUDENT:   "spontaneous"
CANONICAL: "negative"
VERDICT:   CORRECT – both correctly describe the sign of ΔG° for a spontaneous process

STUDENT:   "-65.6 kJ"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   WRONG – feedback: "Include the per-mole denominator in your unit."

STUDENT:   "+65.6 kJ/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   WRONG – feedback: "Check the sign — a spontaneous reaction has negative ΔG°."

STUDENT:   "-6.56 kJ/mol"
CANONICAL: "-65.6 kJ/mol"
VERDICT:   WRONG – feedback: "Recheck your calculation — the magnitude is off by a factor of 10."

STUDENT:   "3.15 × 10^10"
CANONICAL: "3.15 × 10^11"
VERDICT:   WRONG – feedback: "Recheck your exponent for K — you are off by a factor of 10."

STUDENT:   "non-spontaneous"
CANONICAL: "negative"
VERDICT:   WRONG – feedback: "A negative ΔG° means the reaction IS spontaneous as written."
"""

GENERAL = """
[CATEGORY: general — ordinal, identifier, and short-answer steps]

STUDENT:   "3"
CANONICAL: "3rd order"
VERDICT:   CORRECT – numeric shorthand for an ordinal is acceptable

STUDENT:   "2nd order"
CANONICAL: "second order"
VERDICT:   CORRECT – ordinal notation variants are equivalent

STUDENT:   "second order in NO"
CANONICAL: "2"
VERDICT:   CORRECT – worded form correctly states the numeric order

STUDENT:   "1080 s"
CANONICAL: "1080"
VERDICT:   CORRECT – adding the expected unit to a bare number is acceptable

STUDENT:   "product-favored"
CANONICAL: "K > 1"
VERDICT:   CORRECT – correct conceptual statement of the same fact

STUDENT:   "4"
CANONICAL: "3rd order"
VERDICT:   WRONG – feedback: "Recount the sum of the individual reaction orders."

STUDENT:   "zero order"
CANONICAL: "2"
VERDICT:   WRONG – feedback: "The reaction order does not match the experimental data."

STUDENT:   "K > 1"
CANONICAL: "K < 1"
VERDICT:   WRONG – feedback: "Recheck the direction the equilibrium favours."
"""
