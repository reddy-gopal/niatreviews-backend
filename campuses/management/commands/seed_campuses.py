"""
Seed campus directory. Idempotent: uses slug as unique key (upsert).
Run: python manage.py seed_campuses
"""
from django.core.management.base import BaseCommand
from campuses.models import Campus

CAMPUSES = [
    {"name": "Sushant University", "short_name": "Sushant", "location": "Gurgaon", "state": "Haryana", "slug": "niat-sushant-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/HGpTIuSSGmP7aDusPo8tdGRqLC8.png"},
    {"name": "Chaitanya Deemed to be University", "short_name": "Chaitanya", "location": "Hyderabad", "state": "Telangana", "slug": "niat-chaitanya-university", "is_deemed": True, "image_url": "https://framerusercontent.com/images/ULono8yMkd2GZtFh5JjEPH64A.jpg"},
    {"name": "S-VYASA University School of Advanced Studies", "short_name": "S-VYASA", "location": "Bengaluru", "state": "Karnataka", "slug": "niat-s-vyasa-university", "is_deemed": True, "image_url": "https://framerusercontent.com/images/iorBiDrSAGPkIhSlJVUZFkcQI.jpg"},
    {"name": "Noida International University", "short_name": "NIU", "location": "Noida", "state": "Uttar Pradesh", "slug": "niat-noida-international-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/iciqIKyIg81iQzKb5fdeYYDY7A.jpg"},
    {"name": "AMET University", "short_name": "AMET", "location": "Chennai", "state": "Tamil Nadu", "slug": "niat-amet-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/cN3LZE0YoN2StUkQ22CGTfBl7Q.jpg"},
    {"name": "Yenepoya University", "short_name": "Yenepoya", "location": "Mangalore", "state": "Karnataka", "slug": "niat-yenepoya-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/tKVIeYoI0P0n4OPmW5iomK1wA7U.webp"},
    {"name": "Ajeenkya DY Patil University", "short_name": "ADYPU", "location": "Pune", "state": "Maharashtra", "slug": "niat-ajeenkya-dy-patil-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/rrWqy4ED43cM4QocQwlEBosQE.jpeg"},
    {"name": "Sanjay Ghodawat University", "short_name": "SGU", "location": "Kolhapur", "state": "Maharashtra", "slug": "niat-sanjay-ghodawat-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/3q50B22om8o7NUUizLvSwanmuk.png"},
    {"name": "Vivekananda Global University", "short_name": "VGU", "location": "Jaipur", "state": "Rajasthan", "slug": "niat-vivekananda-global-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/kCjPLnr5YW9RR101nFkyC3pSaIQ.jpg"},
    {"name": "NRI University", "short_name": "NRI", "location": "Vijayawada", "state": "Andhra Pradesh", "slug": "niat-nri-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/qrMhb0N7s9127bYZvWO2cgjkAz8.webp"},
    {"name": "St. Peter's Institute of Higher Education and Research", "short_name": "SPIHER", "location": "Bangalore", "state": "Karnataka", "slug": "niat-spiher", "is_deemed": False, "image_url": "https://framerusercontent.com/images/e7oYXpGwiPUSp7kJ1lhK2xlpq70.webp"},
    {"name": "B. S. Abdur Rahman Crescent Institute of Science & Technology", "short_name": "Crescent", "location": "Chennai", "state": "Tamil Nadu", "slug": "niat-bs-abdur-rahman-crescent", "is_deemed": True, "image_url": "https://framerusercontent.com/images/lyGh93hcRTWQPO66lHdp3ra4c.jpg"},
    {"name": "Annamacharya University", "short_name": "Annamacharya", "location": "Kadapa", "state": "Andhra Pradesh", "slug": "niat-annamacharya-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/Ncf6LafzUnbz1LljcPCl1XYx9w.jpg"},
    {"name": "St. Mary's University", "short_name": "St. Mary's", "location": "Hyderabad", "state": "Telangana", "slug": "niat-st-marys-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/Hy5HYIJd21W5KuSuSNi3z8kBHrQ.png"},
    {"name": "Sandip University", "short_name": "Sandip", "location": "Nashik", "state": "Maharashtra", "slug": "niat-sandip-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/UlGKrLkX5zFs9zbsNJeO3hlT7s.png"},
    {"name": "Nadimpalli Satyanarayana Raju Institute of Technology", "short_name": "NSRIT", "location": "Visakhapatnam", "state": "Andhra Pradesh", "slug": "niat-nsrit", "is_deemed": False, "image_url": "https://framerusercontent.com/images/SLiDsXueZRhV0ppgDtJEkdi7Fbg.jpg"},
    {"name": "Scope Global Skills University", "short_name": "SGSU", "location": "Bhopal", "state": "Madhya Pradesh", "slug": "niat-scope-global-skills-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/jwQu0g5yG5fE0tCVjLDgmXEeFY.png"},
    {"name": "Alard University", "short_name": "Alard", "location": "Pune", "state": "Maharashtra", "slug": "niat-alard-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/DQcP9sJHF0jhxaTxv1TEpyk9g0.webp"},
    {"name": "Joy University", "short_name": "Joy", "location": "Tirunelveli", "state": "Tamil Nadu", "slug": "niat-joy-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/iRZXThhVL2LY5nhy3iPbLGgcEk.webp"},
    {"name": "BEST Innovation University", "short_name": "BEST", "location": "Anantapur", "state": "Andhra Pradesh", "slug": "niat-best-innovation-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/0toNpv71sfSADRLfyGUm8w2kHW0.webp"},
    {"name": "Takshashila University", "short_name": "Takshashila", "location": "Pondicherry", "state": "Tamil Nadu", "slug": "niat-takshashila-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/ZcVZbx8PmDdzWPRKDsddEKUHKs.png"},
    {"name": "Chalapathi Institute of Technology", "short_name": "CIT", "location": "Guntur", "state": "Andhra Pradesh", "slug": "niat-chalapathi-institute-of-technology", "is_deemed": False, "image_url": "https://framerusercontent.com/images/fKwM4bLan1ZSmk5wUzMF8qK1Q.png"},
    {"name": "Sanskriti University", "short_name": "Sanskriti", "location": "Mathura", "state": "Uttar Pradesh", "slug": "niat-sanskriti-university", "is_deemed": False, "image_url": "https://framerusercontent.com/images/FkrHCUbelmw5FBEf1sJss10Mp8.jpeg"},
    {"name": "Chalapathi Institute of Engineering and Technology", "short_name": "CIET", "location": "Guntur", "state": "Andhra Pradesh", "slug": "niat-chalapathi-institute-of-engineering-and-technology", "is_deemed": False, "image_url": "https://framerusercontent.com/images/SY74r4lGNweRx1CkeowWS7FeajI.jpg"},
    {"name": "Aurora Deemed University", "short_name": "Aurora", "location": "Hyderabad", "state": "Telangana", "slug": "niat-aurora-deemed-university", "is_deemed": True, "image_url": "https://framerusercontent.com/images/1KJ4DMV1ETo66OqZHdWL95SqoMY.jpg"},
    {"name": "Malla Reddy Vishwavidyapeeth", "short_name": "MRV", "location": "Hyderabad", "state": "Telangana", "slug": "niat-malla-reddy-vishwavidyapeeth", "is_deemed": True, "image_url": "https://framerusercontent.com/images/s77kagrrPsZfnrhDxsaXxrAsK0.png"},
    {"name": "Aurora Deemed University", "short_name": "Aurora", "location": "Hyderabad", "state": "Telangana", "slug": "niat-aurora-deemed-university-2", "is_deemed": True, "image_url": "https://framerusercontent.com/images/1KJ4DMV1ETo66OqZHdWL95SqoMY.jpg"},
]


class Command(BaseCommand):
    help = "Seed campus directory (idempotent by slug)."

    def handle(self, *args, **options):
        for c in CAMPUSES:
            Campus.objects.update_or_create(
                slug=c["slug"],
                defaults={
                    "name": c["name"],
                    "short_name": c.get("short_name"),
                    "location": c["location"],
                    "state": c["state"],
                    "image_url": c["image_url"],
                    "is_deemed": c["is_deemed"],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Upserted {len(CAMPUSES)} campuses."))
