"""Few-shot examples for concise, natural, diagnostic chemistry hints."""

HINT_FEW_SHOTS = """
### FEW-SHOT EXAMPLES (style to imitate) ###

Example 1 (Units — J vs kJ)
Student Answer: "50951"
Correct Answer: "51.0"
Key Rule: 1 kJ = 1000 J
Hint:
Looks like a unit issue.
Activation energy is often reported in kJ/mol — did you convert from J?

---

Example 2 (Arrhenius — direction of effect)
Student Answer: "k increases when Ea increases"
Correct Answer: "k decreases when Ea increases"
Key Rule: $k = A e^{{-E_a/RT}}$
Hint:
Think about the exponential term.
What happens to $e^{{-E_a/RT}}$ when $E_a$ gets larger?

---

Example 3 (Electron configuration — count)
Student Answer: "1s2 2s2 2p6"
Correct Answer: "1s2 2s2 2p5"
Key Rule: $e^- = Z - \\text{{charge}}$
Hint:
Check the total electrons.
Fluorine has 9 — does your configuration match that count?

---

Example 4 (Ions — gaining vs losing electrons)
Student Answer: "14"
Correct Answer: "18"
Key Rule: anion gains electrons: $e^- = p^+ + |\\text{{charge}}|$
Hint:
Focus on the ion charge.
A 2− ion has gained electrons compared to the neutral atom.

---

Example 5 (Stoichiometry — mole ratio)
Student Answer: "120"
Correct Answer: "1.20"
Key Rule: mole ratio from balanced equation
Hint:
You're off by a factor.
Check your mole-to-mole ratio from the balanced equation.

---

Example 6 (Thermochemistry — sign of q)
Student Answer: "q = +250 kJ"
Correct Answer: "q = -250 kJ"
Key Rule: exothermic process → q < 0 for the system
Hint:
Check the sign convention.
Is the system releasing or absorbing heat here?

---

Example 7 (Scientific notation)
Student Answer: "0.00023"
Correct Answer: "$2.3 \\times 10^{{-4}}$"
Key Rule: $a \\times 10^n$ with $1 \\le a < 10$
Hint:
Rewrite in scientific notation.
Make sure the coefficient is between 1 and 10.

---

Example 8 (Significant figures)
Student Answer: "3.2"
Correct Answer: "3.20"
Key Rule: sig figs determined by least precise measurement
Hint:
Your value is right.
Now match the number of significant figures required.

---

Example 9 (Gas constant — unit mismatch)
Student Answer: "0.082"
Correct Answer: "8.31"
Key Rule: R = 8.314 J/(mol·K) or 0.0821 L·atm/(mol·K)
Hint:
Check which gas constant you're using.
Its units must match the rest of the equation.

---

Example 10 (Catalysis — mechanism)
Student Answer: "catalyst increases temperature"
Correct Answer: "catalyst lowers activation energy"
Key Rule: catalyst provides alternative pathway with lower $E_a$
Hint:
Think about the mechanism.
Does a catalyst change temperature or the energy barrier?

---

Example 11 (Isotope notation — reading charge from symbol)
Student Answer: "4-"
Correct Answer: "2-"
Key Rule: charge is shown as a superscript on the upper right of the chemical symbol
Hint:
Look at the small superscript on the upper right of the ion symbol — not the mass number.
That tells you the exact charge.

---
"""
