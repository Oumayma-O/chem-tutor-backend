"""Lookup table data: grades, interests, allowed course names."""

GRADES: list[tuple[str, int]] = [
    ("Middle School", 1), ("9th Grade", 2), ("10th Grade", 3),
    ("11th Grade", 4),    ("12th Grade", 5), ("AP / Advanced", 6), ("College", 7),
]

INTERESTS: list[tuple[str, str, str]] = [
    ("sports",  "Sports",       "🏀"),
    ("music",   "Music",        "🎵"),
    ("food",    "Food & Cooking","🍕"),
    ("gaming",  "Gaming",       "🎮"),
    ("art",     "Art & Design", "🎨"),
    ("nature",  "Nature",       "🌿"),
    ("tech",    "Technology",   "💻"),
    ("movies",  "Movies & TV",  "🎬"),
]

KEEP_COURSE_NAMES: set[str] = {"Standard Chemistry", "AP Chemistry"}
