"""
Seed script — populate all lookup tables and full chemistry curriculum.

Run once after migrations:
  python -m scripts.seed

Idempotent: get-or-create patterns; safe to run multiple times.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database.models import (
    Chapter,
    Course,
    Grade,
    Interest,
    Standard,
    Topic,
    TopicStandard,
)

settings = get_settings()


# ── Curriculum Data ───────────────────────────────────────────────────────────
# Each chapter: (id, title, description, icon, gradient, course_name, sort_order, is_coming_soon, topics, standards)
# Each topic: (index, title, description, key_equations, standard_codes)

CURRICULUM = [
    {
        "id": "atomic-structure",
        "title": "Atomic Structure",
        "description": "Atoms, subatomic particles, electron configurations, and periodic trends.",
        "icon": "⚛️",
        "gradient": "linear-gradient(135deg, #4f46e5 0%, #818cf8 100%)",
        "course": "Intro Chemistry",
        "sort_order": 1,
        "is_coming_soon": False,
        "topics": [
            (0, "Atomic Models",
             "Historical and modern models of the atom from Dalton to quantum mechanics.",
             ["Z = protons", "A = Z + N", "e⁻ = protons (neutral atom)"],
             ["NGSS MS-PS1-1", "CA Chem 1a"]),
            (1, "Subatomic Particles",
             "Properties and locations of protons, neutrons, and electrons.",
             ["mass number A = p⁺ + n⁰", "atomic number Z = p⁺"],
             ["NGSS MS-PS1-1"]),
            (2, "Electron Configuration",
             "Orbital notation, electron configurations, and quantum numbers.",
             ["1s² 2s² 2p⁶ 3s² 3p⁶ 4s²...", "max electrons per shell = 2n²"],
             ["CA Chem 1a"]),
            (3, "Periodic Trends",
             "Atomic radius, ionization energy, electronegativity, and electron affinity across the periodic table.",
             ["IE increases across period", "atomic radius decreases across period"],
             ["NGSS MS-PS1-1", "CA Chem 1a"]),
        ],
    },
    {
        "id": "stoichiometry",
        "title": "Stoichiometry",
        "description": "Mole conversions, limiting reagents, and percent yield calculations.",
        "icon": "⚖️",
        "gradient": "linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)",
        "course": "High School Chemistry",
        "sort_order": 2,
        "is_coming_soon": True,
        "topics": [
            (0, "Mole Ratios",
             "Use balanced equations to convert between moles of reactants and products.",
             ["mol A / mol B = coeff A / coeff B"],
             ["NGSS HS-PS1-7", "CA Chem 3a"]),
            (1, "Limiting Reagents",
             "Identify the limiting reagent and calculate maximum product yield.",
             ["mol product = mol limiting × (coeff product / coeff limiting)"],
             ["NGSS HS-PS1-7"]),
            (2, "Percent Yield",
             "Calculate theoretical yield and compare to actual experimental yield.",
             ["% yield = (actual / theoretical) × 100"],
             ["CA Chem 3a"]),
            (3, "Mole-Mass Conversions",
             "Convert between mass, moles, particles, and volume of gases at STP.",
             ["n = m / M", "1 mol = 6.022×10²³ particles", "1 mol gas = 22.4 L at STP"],
             ["NGSS HS-PS1-7", "CA Chem 3a"]),
        ],
    },
    {
        "id": "thermodynamics",
        "title": "Thermodynamics",
        "description": "Enthalpy, entropy, Gibbs free energy, and calorimetry.",
        "icon": "🔥",
        "gradient": "linear-gradient(135deg, #ef4444 0%, #f97316 100%)",
        "course": "AP Chemistry",
        "sort_order": 3,
        "is_coming_soon": True,
        "topics": [
            (0, "Enthalpy",
             "Heat flow in chemical reactions; exothermic and endothermic processes.",
             ["ΔH = H_products − H_reactants", "ΔH < 0 → exothermic", "ΔH > 0 → endothermic"],
             ["NGSS HS-PS3-1", "CA Chem 7a"]),
            (1, "Hess's Law",
             "Calculate reaction enthalpy by combining known enthalpy changes.",
             ["ΔH_rxn = Σ ΔH_f(products) − Σ ΔH_f(reactants)"],
             ["NGSS HS-PS3-1"]),
            (2, "Calorimetry",
             "Measure heat transfer using constant-pressure and constant-volume calorimeters.",
             ["q = mcΔT", "q_rxn = −q_calorimeter", "c_water = 4.184 J/g·°C"],
             ["CA Chem 7a"]),
            (3, "Gibbs Free Energy",
             "Predict spontaneity of reactions using enthalpy, entropy, and temperature.",
             ["ΔG = ΔH − TΔS", "ΔG < 0 → spontaneous", "ΔG = 0 → equilibrium"],
             ["NGSS HS-PS3-1", "CA Chem 7a"]),
        ],
    },
    {
        "id": "chemical-kinetics",
        "title": "Chemical Kinetics",
        "description": "Reaction rates, rate laws, integrated rate equations, and mechanisms.",
        "icon": "⚡",
        "gradient": "linear-gradient(135deg, #667eea 0%, #f6d365 100%)",
        "course": "AP Chemistry",
        "sort_order": 4,
        "is_coming_soon": False,
        "topics": [
            (0, "Zero-Order Kinetics",
             "Reactions whose rate is independent of reactant concentration.",
             ["[A]t = [A]₀ − kt", "t₁/₂ = [A]₀ / 2k", "Rate = k"],
             ["NGSS HS-PS1-5", "CA Chem 8a"]),
            (1, "First-Order Kinetics",
             "Reactions whose rate depends linearly on one reactant concentration.",
             ["ln[A]t = ln[A]₀ − kt", "t₁/₂ = ln2 / k", "Rate = k[A]"],
             ["NGSS HS-PS1-5", "CA Chem 8a"]),
            (2, "Second-Order Kinetics",
             "Reactions whose rate depends on the square of reactant concentration.",
             ["1/[A]t = 1/[A]₀ + kt", "t₁/₂ = 1/(k[A]₀)", "Rate = k[A]²"],
             ["NGSS HS-PS1-5"]),
            (3, "Rate Laws",
             "Determine rate law from experimental data and calculate rate constants.",
             ["Rate = k[A]^m[B]^n", "overall order = m + n"],
             ["NGSS HS-PS1-5", "CA Chem 8a"]),
        ],
    },
    {
        "id": "chemical-equilibrium",
        "title": "Chemical Equilibrium",
        "description": "Equilibrium constants, Le Chatelier's principle, and ICE tables.",
        "icon": "⚖️",
        "gradient": "linear-gradient(135deg, #0891b2 0%, #06b6d4 100%)",
        "course": "High School Chemistry",
        "sort_order": 5,
        "is_coming_soon": True,
        "topics": [
            (0, "Keq Expressions",
             "Write equilibrium constant expressions for homogeneous and heterogeneous reactions.",
             ["Keq = [products]^coeff / [reactants]^coeff", "Kp = Kc(RT)^Δn"],
             ["NGSS HS-PS1-6", "AP 4.A"]),
            (1, "Le Chatelier's Principle",
             "Predict how a system at equilibrium responds to changes in concentration, pressure, or temperature.",
             ["Q < K → shift right", "Q > K → shift left"],
             ["NGSS HS-PS1-6"]),
            (2, "ICE Tables",
             "Use Initial-Change-Equilibrium tables to solve for equilibrium concentrations.",
             ["K = (Ce + x)^a / (Ci − x)^b"],
             ["NGSS HS-PS1-6", "AP 4.A"]),
            (3, "Solubility Product (Ksp)",
             "Calculate solubility of sparingly soluble salts and predict precipitation.",
             ["Ksp = [A^m+]^m[B^n-]^n", "Q > Ksp → precipitate forms"],
             ["AP 4.A"]),
        ],
    },
    {
        "id": "acids-and-bases",
        "title": "Acids & Bases",
        "description": "pH calculations, buffer systems, and titration curves.",
        "icon": "🧪",
        "gradient": "linear-gradient(135deg, #059669 0%, #34d399 100%)",
        "course": "High School Chemistry",
        "sort_order": 6,
        "is_coming_soon": True,
        "topics": [
            (0, "pH & pOH",
             "Calculate pH, pOH, [H⁺], and [OH⁻] for strong and weak acids and bases.",
             ["pH = −log[H⁺]", "pOH = −log[OH⁻]", "pH + pOH = 14", "Ka × Kb = Kw"],
             ["NGSS HS-PS1-2", "CA Chem 5a"]),
            (1, "Buffer Solutions",
             "Understand how buffers resist pH change; apply Henderson-Hasselbalch equation.",
             ["pH = pKa + log([A⁻]/[HA])", "buffer capacity ↑ with concentration"],
             ["AP 6.A"]),
            (2, "Titrations",
             "Determine unknown concentrations from acid-base titration data and curves.",
             ["n_acid = n_base at equivalence", "mol = M × V", "pH at eq. pt. depends on salt"],
             ["NGSS HS-PS1-2", "CA Chem 5a"]),
            (3, "Acid-Base Theories",
             "Compare Arrhenius, Brønsted-Lowry, and Lewis definitions of acids and bases.",
             ["conjugate acid-base pairs differ by H⁺", "Lewis acid accepts e⁻ pair"],
             ["AP 6.A"]),
        ],
    },
]

# ── Standards master list (code → framework, description) ────────────────────
STANDARDS = {
    "NGSS MS-PS1-1": ("NGSS",  "Develop models to describe the atomic composition of simple molecules and extended structures."),
    "NGSS HS-PS1-2": ("NGSS",  "Construct and revise an explanation for the outcome of a simple chemical reaction based on the outermost electron states of atoms."),
    "NGSS HS-PS1-5": ("NGSS",  "Apply scientific principles and evidence to explain how the rate of a chemical reaction changes with conditions."),
    "NGSS HS-PS1-6": ("NGSS",  "Refine the design of a chemical system by specifying a change in conditions that would shift a reaction toward products."),
    "NGSS HS-PS1-7": ("NGSS",  "Use mathematical representations to support the claim that atoms, and therefore mass, are conserved during a chemical reaction."),
    "NGSS HS-PS3-1": ("NGSS",  "Create a computational model to calculate the change in the energy of one component in a system when the change in energy of the other component(s) and energy flows in and out of the system are known."),
    "CA Chem 1a":    ("CA",    "Students know the nucleus of the atom is much smaller than the atom yet contains most of its mass."),
    "CA Chem 3a":    ("CA",    "Students know how to describe chemical reactions by writing balanced equations."),
    "CA Chem 5a":    ("CA",    "Students know the observable properties of acids, bases, and salt solutions."),
    "CA Chem 7a":    ("CA",    "Students know how to describe temperature and heat flow in terms of the motion of molecules."),
    "CA Chem 8a":    ("CA",    "Students know the rate of reaction is the decrease in concentration of reactants or the increase in concentration of products with time."),
    "AP 4.A":        ("AP",    "Explain changes in concentrations of reactants and products based on the equilibrium constant for a reaction."),
    "AP 6.A":        ("AP",    "Explain the relationship between the strength of an acid or base and the structure of the molecule or ion."),
}


async def get_or_create_grade(session: AsyncSession, name: str, sort_order: int) -> Grade:
    existing = (await session.execute(select(Grade).where(Grade.name == name))).scalar_one_or_none()
    if existing:
        return existing
    g = Grade(name=name, sort_order=sort_order)
    session.add(g)
    await session.flush()
    return g


async def get_or_create_course(session: AsyncSession, name: str, sort_order: int, grade_id: int | None = None) -> Course:
    existing = (await session.execute(select(Course).where(Course.name == name))).scalar_one_or_none()
    if existing:
        return existing
    c = Course(name=name, grade_id=grade_id, sort_order=sort_order)
    session.add(c)
    await session.flush()
    return c


async def get_or_create_standard(session: AsyncSession, code: str, framework: str, description: str) -> Standard:
    existing = (await session.execute(select(Standard).where(Standard.code == code))).scalar_one_or_none()
    if existing:
        return existing
    s = Standard(code=code, framework=framework, description=description)
    session.add(s)
    await session.flush()
    return s


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure all tables exist (idempotent)
    print("Creating tables if not exist...")
    import app.infrastructure.database.models  # noqa: F401 — register all ORM models
    from app.infrastructure.database.connection import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ tables ready\n")

    async with SessionFactory() as session:

        # ── Grades ────────────────────────────────────────────
        print("Seeding grades...")
        grade_hs = await get_or_create_grade(session, "High School", 2)
        grade_ap = await get_or_create_grade(session, "AP / Advanced", 3)
        # Keep legacy grades for backward compat
        await get_or_create_grade(session, "Middle School", 1)
        await get_or_create_grade(session, "High School (9–10)", 2)
        await get_or_create_grade(session, "High School (11–12)", 3)
        print("  ✓ grades")

        # ── Courses (match frontend filter tabs exactly) ───────
        print("Seeding courses...")
        course_map: dict[str, Course] = {}
        course_map["Intro Chemistry"]      = await get_or_create_course(session, "Intro Chemistry",      1, grade_hs.id)
        course_map["High School Chemistry"] = await get_or_create_course(session, "High School Chemistry", 2, grade_hs.id)
        course_map["AP Chemistry"]         = await get_or_create_course(session, "AP Chemistry",         3, grade_ap.id)
        await get_or_create_course(session, "Not sure", 4)
        print("  ✓ courses")

        # ── Interests ─────────────────────────────────────────
        print("Seeding interests...")
        interests_data = [
            ("sports",   "Sports",            "🏀", 1),
            ("music",    "Music",             "🎵", 2),
            ("food",     "Food & Cooking",    "🍕", 3),
            ("tech",     "Technology",        "💻", 4),
            ("nature",   "Nature",            "🌿", 5),
            ("gaming",   "Gaming",            "🎮", 6),
            ("art",      "Art & Design",      "🎨", 7),
            ("health",   "Health & Medicine", "💊", 8),
            ("dance",    "Dance",             "💃", 9),
            ("movies",   "Movies & TV",       "🎬", 10),
        ]
        from app.infrastructure.database.models import Interest
        for slug, label, icon, order in interests_data:
            existing = (await session.execute(select(Interest).where(Interest.slug == slug))).scalar_one_or_none()
            if existing is None:
                session.add(Interest(slug=slug, label=label, icon=icon, sort_order=order))
        await session.flush()
        print(f"  ✓ {len(interests_data)} interests")

        # ── Standards ─────────────────────────────────────────
        print("Seeding standards...")
        std_map: dict[str, Standard] = {}
        for code, (framework, desc) in STANDARDS.items():
            std_map[code] = await get_or_create_standard(session, code, framework, desc)
        print(f"  ✓ {len(std_map)} standards")

        # ── Chapters + Topics ─────────────────────────────────
        print("Seeding chapters and topics...")
        for ch_data in CURRICULUM:
            chapter_id = ch_data["id"]
            course = course_map[ch_data["course"]]

            existing = (await session.execute(select(Chapter).where(Chapter.id == chapter_id))).scalar_one_or_none()
            if existing is not None:
                # Update course/sort linkage in case it changed
                existing.course_id = course.id
                existing.sort_order = ch_data["sort_order"]
                existing.is_coming_soon = ch_data["is_coming_soon"]
                await session.flush()
                print(f"  → updated chapter: {chapter_id}")
            else:
                chapter = Chapter(
                    id=chapter_id,
                    title=ch_data["title"],
                    description=ch_data["description"],
                    icon=ch_data["icon"],
                    gradient=ch_data["gradient"],
                    course_id=course.id,
                    sort_order=ch_data["sort_order"],
                    is_active=True,
                    is_coming_soon=ch_data["is_coming_soon"],
                )
                session.add(chapter)
                await session.flush()
                print(f"  ✓ created chapter: {chapter_id}")

            # Topics — upsert by (chapter_id, topic_index)
            for (idx, title, desc, equations, std_codes) in ch_data["topics"]:
                existing_topic = (await session.execute(
                    select(Topic).where(Topic.chapter_id == chapter_id, Topic.topic_index == idx)
                )).scalar_one_or_none()

                if existing_topic is None:
                    topic = Topic(
                        chapter_id=chapter_id,
                        title=title,
                        description=desc,
                        topic_index=idx,
                        key_equations=equations,
                        sort_order=idx,
                        is_active=True,
                    )
                    session.add(topic)
                    await session.flush()
                else:
                    topic = existing_topic
                    topic.title = title
                    topic.description = desc
                    topic.key_equations = equations
                    await session.flush()

                # Attach standards (skip if already linked)
                for code in std_codes:
                    if code not in std_map:
                        continue
                    already_linked = (await session.execute(
                        select(TopicStandard).where(
                            TopicStandard.topic_id == topic.id,
                            TopicStandard.standard_id == std_map[code].id,
                        )
                    )).scalar_one_or_none()
                    if already_linked is None:
                        session.add(TopicStandard(topic_id=topic.id, standard_id=std_map[code].id))

            await session.flush()
            print(f"    ✓ {len(ch_data['topics'])} topics for {chapter_id}")

        await session.commit()
        print("\n✅  Seed complete!")
        print(f"   {len(CURRICULUM)} chapters · {sum(len(c['topics']) for c in CURRICULUM)} topics · {len(STANDARDS)} standards")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
