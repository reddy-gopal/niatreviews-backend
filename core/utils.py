import re

from rest_framework import serializers


def validate_password_strength(value):
    password = value or ""
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise serializers.ValidationError("Password must include at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise serializers.ValidationError("Password must include at least one digit.")
    
    return password
