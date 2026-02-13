"""
Choice constants for Senior Onboarding Review (mandatory for approved seniors on main app).
"""

FACULTY_SUPPORT_CHOICES = [
    ("very_helpful", "Very helpful"),
    ("average", "Average"),
    ("not_supportive", "Not supportive"),
]

LEARNING_BALANCE_CHOICES = [
    ("practical_focused", "Practical focused"),
    ("balanced", "Balanced"),
    ("too_theoretical", "Too theoretical"),
]

PLACEMENT_REALITY_CHOICES = [
    ("very_promising", "Very promising"),
    ("decent_needs_improvement", "Decent, needs improvement"),
    ("not_as_expected", "Not as expected"),
]

EXPERIENCE_FEEL_CHOICES = [
    ("positive", "Positive"),
    ("mixed", "Mixed"),
    ("stressful", "Stressful"),
]

FINAL_RECOMMENDATION_CHOICES = [
    ("yes_definitely", "Yes, definitely"),
    ("yes_serious_students_only", "Yes, serious students only"),
    ("no_better_options", "No, better options elsewhere"),
]

FACULTY_SUPPORT_VALUES = [c[0] for c in FACULTY_SUPPORT_CHOICES]
LEARNING_BALANCE_VALUES = [c[0] for c in LEARNING_BALANCE_CHOICES]
PLACEMENT_REALITY_VALUES = [c[0] for c in PLACEMENT_REALITY_CHOICES]
EXPERIENCE_FEEL_VALUES = [c[0] for c in EXPERIENCE_FEEL_CHOICES]
FINAL_RECOMMENDATION_VALUES = [c[0] for c in FINAL_RECOMMENDATION_CHOICES]

ONBOARDING_TEXT_MIN_LENGTH = 20
RATING_MIN = 1
RATING_MAX = 5
