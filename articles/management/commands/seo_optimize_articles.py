import json
import time
import os
import re
from django.core.management.base import BaseCommand
from articles.models import Article
from campuses.models import Campus
import anthropic


# ---------------------------------------------
# KEYWORDS TO EXCLUDE
# ---------------------------------------------

EXCLUDE_PATTERNS = [
    'fee', 'fees', 'curriculum', 'syllabus', 'course', 'niat exam',
    'cost', 'price', 'admission', 'registration' , 'niat mock test', 'niat application'
]

# Keep keyword intent tightly aligned with article context.
IRRELEVANT_INTENT_PATTERNS = [
    'placement', 'placements', 'package', 'highest package', 'average package',
    'ranking', 'nirf', 'salary', 'portal', 'login',
    'interview', 'interview questions',
    'eligibility', 'internship',
    'scholarship', 'scholarships',
    'review', 'reviews',
    'how to join', 'join niat', 'join niat college',
]

GENERIC_ALLOWED_KEYWORDS = {
    'niat', 'niat india', 'niat campus', 'niat college', 'niat colleges',
    'nxtwave', 'niat nxtwave',
    'next wave institute of advanced technology',
    'nxtwave institute of advanced technology',
    'nxtwave institute of advanced technologies',
}

TARGET_MAX_KEYWORDS = 30


# ---------------------------------------------
# MASTER KEYWORD LIST
# Claude can ONLY pick from this list.
# Any keyword not in this set is dropped after Claude responds.
# ---------------------------------------------

ALL_KEYWORDS = [
    "niat",
    "niat college",
    "niat hyderabad",
    "niat india",
    "niat full form",
    "niat exam",
    "nxtwave institute of advanced technologies",
    "niat college chennai",
    "niat bangalore",
    "niat entrance exam",
    "niatindia",
    "niat college in bangalore",
    "niat entrance exam date 2026",
    "niat nxtwave",
    "niat website",
    "niat exam date",
    "next wave institute of advanced technology",
    "niat university",
    "niat exam application",
    "niat pune",
    "niat registration",
    "niat application",
    "nait",
    "niat exam date 2026",
    "niat.india",
    "niat login",
    "what is niat",
    "niat exam syllabus",
    "niat campus",
    "niat chennai",
    "niat college hyderabad",
    "www.niat india.com",
    "nxtwave institute of advanced technologies: niat",
    "niat delhi",
    "niat application form",
    "nxtwave institute of advanced technology",
    "niat mock test",
    "niat official website",
    "niat nat exam",
    "niat nat exam date 2026",
    "niat engineering college",
    "nxtwave",
    "niatindia.com",
    "niat vijayawada",
    "nxtwave school of technology",
    "nextwave institute of advanced technology",
    "nait india",
    "niat india.com",
    "niat highest package",
    "niat collaborated colleges",
    "niat application form 2026",
    "nat exam",
    "niat campuses in india",
    "nextwave institute of advanced technologies",
    "next wave institute of technology",
    "niat noida",
    "niat placements",
    "niat jaipur",
    "niat college entrance exam",
    "niat college chennai location",
    "niat branches",
    "nait exam",
    "niat course",
    "niat syllabus",
    "niat college pune",
    "niat hyderabad campus location",
    "nait college india",
    "niat college branches",
    "nxtwave niat",
    "nxtwave college",
    "nxtwave institute of technology",
    "niat result",
    "niat college bangalore",
    "niat colleges",
    "niat last date to apply 2026",
    "niat test",
    "niat helpline number",
    "nextwave college",
    "niat application form 2026 last date",
    "nextwave institute of advance technology",
    "niat form",
    "https www niatindia com",
    "niat mangalore",
    "niat campuses",
    "niat nat exam date 2025",
    "nxtwave institute of advanced technologies: niat photos",
    "nxtwave assessment test",
    "niat admission process",
    "niat next wave",
    "niat slot booking",
    "nat college",
    "niat contact number",
    "nxtwave of innovation in advanced technologies: niat nanakramguda",
    "niat scholarship",
    "niat hyderabad entrance exam",
    "next wave of innovation in advanced technology",
    "nxt wave institute of advanced technologies",
    "niat institute",
    "nat exam niat",
    "nxtwave institute of advanced technologies (niat)",
    "niat entrance exam date 2026 phase 2",
    "nat exam for niat",
    "niat bangalore campus",
    "niat entrance exam syllabus",
    "nxtwave institute of advanced technologies niat",
    "niat internship",
    "niatindia com",
    "niat bangalore college",
    "niat brochure",
    "niat logo",
    "niat colleges in india",
    "niat vizag",
    "niat sample paper",
    "niat nirf ranking",
    "niat courses",
    "niat registration last date",
    "n i a t",
    "niat collaboration college",
    "next wave college",
    "niat vijayawada campus",
    "niat chennai campus",
    "niat registration 2026",
    "niat admission",
    "nxtwave of innovation in advanced technologies",
    "what is niat exam",
    "niat kolhapur",
    "nxtwave assessment test (nat)",
    "niat nat",
    "nxtwave exam",
    "when is niat entrance exam 2026",
    "niat college placement",
    "niat college vijayawada",
    "niat noida international university",
    "niat exam date 2025",
    "niat phase 2 exam date",
    "niat 2026",
    "niat pondicherry",
    "niat crescent college",
    "next wave institute of advanced technology fees",
    "niat branches in india",
    "next wave engineering college",
    "niat hyderabad gachibowli",
    "niat application last date",
    "aurora deemed university",
    "about niat college",
    "niat coupon code 2026",
    "nxt wave institute of technology",
    "niat entrance exam 2026",
    "next wave advanced technology",
    "niat scholarship details",
    "niat guntur",
    "niat collage",
    "niat hyd",
    "niat visakhapatnam",
    "niat institute of technology",
    "niat college courses",
    "niat exam application last date",
    "nxtwave admission test",
    "niat average package cse",
    "nat entrance exam",
    "niat question paper",
    "nxtwave entrance exam",
    "nxt wave",
    "niat college admission process",
    "nextwave university",
    "niat exam information",
    "niat coupon code",
    "niat college in bangalore location",
    "niat college noida",
    "niat academy",
    "next wave school of technology",
    "nait college in bangalore",
    "nxtwave college hyderabad",
    "niat main campus",
    "nxtwave institute of advanced technologies chennai",
    "niat student login",
    "niat tamil nadu",
    "nxt wave college",
    "niat india college",
    "niat online courses",
    "niat collaborated with which university",
    "niat tirupati",
    "niat hyderabad campus",
    "next wave university",
    "niat full form in nxtwave",
    "niat delhi campus",
    "niat exam 2026",
    "niat bhopal",
    "niat meaning",
    "niat chaitanya deemed to be university",
    "niat program",
    "nextwave",
    "nxtwave bangalore",
    "niat means",
    "nat application",
    "niat photos",
    "nait exam date 2026",
    "niat jaipur fees",
    "niat founders",
    "niat details",
    "niat registration date",
    "niat hyderabad entrance exam date",
    "niat in chennai",
    "nxt wave institute of advanced technology",
    "niat exam link",
    "niat syllabus pdf",
    "niat exam pattern",
    "nxtwave institute of advanced technologies fees",
    "apply niatindia com",
    "niat college in chennai",
    "niat college delhi",
    "niat interview",
    "niat amet university",
    "niat average package",
    "how to get admission in niat",
    "niat gachibowli",
    "niat course details",
    "niat college list",
    "niat btech",
    "niat kya hai",
    "nxtwave institute of advanced technologies bangalore",
    "niat interview questions",
    "niat university branches",
    "niat portal login",
    "niat portal",
    "niat exam registration",
    "amet university",
    "grit niat",
    "niat placement percentage",
    "next wave institute of advanced technology hyderabad",
    "nxtwave college fees",
    "nxtwave institute",
    "niat eligibility",
    "next wave college hyderabad",
    "niat chevella",
    "niat malla reddy university",
    "niat yenepoya university bangalore",
    "niat sharda university",
    "niat app",
    "nxtwave institute of advanced technologies pune",
    "nxtwave institute of advance technology",
    "nxtwave institute of advanced technologies: niat reviews",
    "niat location",
    "niat exam details",
    "niat college in hyderabad",
    "nat exam for niat college",
    "niat entrance exam date",
    "niat university bangalore",
    "niat noida fees",
    "niat vijayawada address",
    "niat application last date 2026",
    "niat hyderabad admission process",
    "niat tie up colleges",
    "niat phase 2",
    "next wave hyderabad",
    "niat college highest package",
    "niat clg",
    "niat packages",
    "niat nanakramguda hyderabad",
    "nextwave institute hyderabad",
    "nat application form 2026",
    "next wave institute of advanced technology pune",
    "nxtwave institute of advanced technology fees",
    "niat maharashtra",
    "nait application",
    "niat exam model paper",
    "niat in tamil nadu",
    "niat apply",
    "nextwave institute of technology",
    "nextwave institute of advanced technologies hyderabad",
    "noida international university",
    "nait college",
    "niat pune average package",
    "niat btech fees",
    "niat ranking in india",
    "niat in hyderabad",
    "niat meaning in tamil",
    "next wave institute of technology bangalore",
    "niat college nirf ranking",
    "niat placement",
    "niat college in vizag",
    "niat courses offered",
    "niat hyderabad courses",
    "niat colleges in bangalore",
    "niat bootcamp",
    "niat college details",
    "nait college in india",
    "nxt college",
    "nxtwave engineering college",
    "niat next wave institute of advanced technology",
    "nat niat",
    "nsrit",
    "nxtwave hyderabad",
    "niat pune campus",
    "niat established year",
    "niat college full form",
    "niat exam registration date 2026",
    "niat login portal",
    "nxtwave login",
    "sanjay ghodawat university kolhapur",
    "nxtwave pune",
    "niat college pune fees",
    "nxtwave vijayawada",
    "niat hyderabad location",
    "niat information",
    "niat college mangalore",
    "niat college in karnataka",
    "nat colleges",
    "niat nxtwave institute of advanced technologies",
    "niat campus hyderabad",
    "next way institute of advanced technology",
    "niat nat exam syllabus",
    "niat college campus",
    "niat exam india",
    "niat engineering college bangalore",
    "niat campus bangalore",
    "niat entrance exam application last date",
    "niat malla reddy",
    "niat hyderabad branches",
    "niat university chennai",
    "niat career",
    "chaitanya deemed to be university",
    "niat hyderabad fees for 4 years btech",
    "niat highest package 2025",
    "niat learning portal",
    "new gen colleges in india",
    "niat vijayawada fee structure",
    "niat campus in india",
    "niat best campus",
    "annamacharya university collaborating with niat - rajampet",
    "niat hyderabad placements",
    "niat college information",
    "niat exam last date to apply",
    "niat branches in hyderabad",
    "nxtwave institute of advanced technologies, hyderabad",
    "niat college exam date",
    "niat s vyasa university",
    "niat college location in india",
    "niat andhra pradesh",
    "niat college branches in india",
    "niat chennai college",
    "what is niat application",
    "niat logo download",
    "nxtwave institute of advanced technology bangalore",
    "niat is affiliated to which university",
    "niat top colleges",
    "niat company",
    "nextwave engineering college",
    "niat mumbai",
    "s vyasa niat",
    "niat bengaluru",
    "niat certification",
    "niat grit",
    "where is niat college located",
    "next wave institute",
    "full form of niat",
    "niat is government or private",
    "niat college in india",
    "my niat app",
    "nat universities",
    "niat founder",
    "niat placement rate",
    "when was niat established",
    "niat aurora",
    "niat application form 2025 last date",
    "niat hyderabad college",
    "niat cdu",
    "niat pune college",
    "nxtwave registration",
    "next wave engineering college hyderabad",
    "nxt wave university",
    "what is mean by niat",
    "niat qualification",
    "niat joy university",
    "niat college chennai location map",
    "niat noida international university fees",
    "annamacharya university",
    "aurora university hyderabad",
    "sgu kolhapur",
    "new age colleges in india",
    "niat cse average package",
    "niat pune highest package",
    "niat started in which year",
    "niat mangalore fees",
    "niat college in bangalore address",
    "where is niat college",
    "niat chennai location",
    "nxtwave jaipur",
    "niat in bangalore",
    "niat engineering college hyderabad",
    "is niat a university",
    "niat gachibowli hyderabad",
    "niat university vijayawada",
    "how many niat colleges in india",
    "niat colleges in hyderabad",
    "niat exam coupon code",
    "how to join niat",
    "niat cdu campus",
    "nxtwave institute of advanced technologies courses",
    "next wave university hyderabad",
    "niat exams",
    "niat exam login",
    "sanjay ghodawat university",
    "takshashila university chennai",
    "niat reviews",
    "nat exam india",
    "what is nat exam",
    "niat college in bangalore highest package",
    "nita exam",
    "nextwave technologies",
    "nextwave institute",
    "niat college india",
    "niat full form in computer",
    "nxtwave noida",
    "nxtwave exam pattern",
    "niat nirf ranking 2025",
    "nxtwave institute of advanced technologies hyderabad",
    "niat vijayawada highest package",
    "niat college chennai placement",
    "niat students",
    "niat exam uses",
    "nat application form",
    "niat bhubaneswar",
    "nxtwave of innovation in advanced technologies: niat",
    "services offered by niat",
    "nat exam application",
    "niat college bangalore location",
    "niat institute hyderabad",
    "niat ranking",
    "niat admission last date",
    "niat is college or university",
    "takshashila university",
    "adypu",
    "chaitanya (deemed to be university)",
    "next wave",
    "nxtwave courses",
    "is niat a good college",
    "aurora deemed to be university",
    "nri university vijayawada",
    "niat college average package",
    "niat is good or bad",
    "niat is fake or real",
    "about niat exam",
    "nait login",
    "niat college jaipur",
    "niat delhi average package",
    "niat bangalore fee structure",
    "nat application form 2025",
    "niat college is government or private",
    "niat course fees",
    "niat delhi btech cse fees",
    "niat college hyderabad location",
    "niat college packages",
    "nxt wave courses",
    "niat address",
    "how to join niat college",
    "niat near me",
    "nxt wave institute",
    "niat hyderabad (chevella campus)",
    "niat logo png",
    "niat college in bangalore campus",
    "niat bits hyderabad",
    "amet",
    "chaitanya deemed to be university hyderabad",
    "joy university",
    "amet university chennai",
    "chaitanya deemed university hyderabad",
    "b.s abdur rahman university",
    "aurora deemed university, bhongir",
    "next wave login",
    "niat computer education",
    "b. s. abdur rahman crescent institute of science and technology",
    "nextwave courses list",
    "nita college",
    "niat highest package cse",
    "aurora deemed university hyderabad",
    "niat is best or not",
    "niat college placement percentage",
    "nxtwave noida office",
    "nxtwave technologies",
    "new wave institute of technology",
    "new gen colleges",
    "nat exam for engineering",
    "new age colleges",
    "niat main branch",
    "niat hyderabad address",
    "niat college location",
    "niat hyderabad established year",
    "niat ceo",
    "niat bangalore location",
    "coupon code for niat",
    "niat india fees",
    "niat college government or private",
    "nait registration",
    "niat scholarship exam",
    "nat exam college",
    "nat slots",
    "vgu jaipur",
    "chaitanya university hyderabad",
    "bs abdur rahman university",
    "thakshila university chennai",
    "nri college vijayawada",
    "st mary's rehabilitation university",
    "malla reddy vishwavidyapeeth",
    "st marys rehabilitation university",
    "nat registration",
    "is niat a good college for btech",
    "svyasa school of advanced studies",
    "niat ccbp",
    "chaitanya university hyderabad location",
    "next wave institute hyderabad",
    "niat is private or government",
    "nat form",
    "niat jaipur campus",
    "niat college in maharashtra",
    "nxtwave app download",
    "what is nat exam in india",
    "niat exam full form",
    "niat college in bangalore reviews",
    "nxtwave official website",
    "does niat provide btech degree",
    "niat x ajeenkya dy patil university - pune",
    "niat exam fee",
    "highest package in niat hyderabad",
    "nxtwave free courses",
    "niat private or government",
    "st mary's rehabilitation university location",
    "nat india",
    "is niat a college",
    "what is niat?",
    "niat kolhapur fees",
    "ai bootcamp",
    "ai bootcamp for students",
    "how to get into niat",
    "nxtwave online courses",
    "niat mrv",
    "niat abbreviation",
    "nat exam date 2026",
    "niat college in bangalore location map",
    "niatian",
    "nxtwave university hyderabad",
    "niat university fees",
    "chaitanya university",
    "noida university",
    "nxtwave chennai",
    "ciet guntur",
    "aurora university hyderabad uppal",
    "amet university full form",
    "st mary rehabilitation university",
    "nextwave login",
    "bs abdur rahman",
    "niay",
    "nxt wave login",
    "aurora deemed university photos",
    "nadimpalli satyanarayana raju institute of technology",
    "amet chennai",
    "nat academy",
    "b.s. abdur rahman crescent institute of science and technology",
    "smru hyderabad",
    "st. mary's rehabilitation university",
    "aurora university bhongir",
    "aurora university, hyderabad",
    "annamayya university",
    "nri engineering college vijayawada",
    "aurora deemed to be university hyderabad",
    "nri vijayawada",
    "niu noida",
    "adypu pune",
    "nadimpalli satyanarayana raju",
    "nextwave courses fees",
    "niat college review",
    "nat test",
    "nxt wave technologies",
    "niat college is good or bad",
    "niat jaipur average package cse",
    "takshila university chennai",
    "nai t",
    "niat review",
    "niat meaning in english",
    "institute of advanced technology",
    "cdu hyderabad location",
    "sanjay ghodawat college of engineering kolhapur",
    "shreyas pandey",
    "nxtwave bangalore address",
    "nxt wave chennai",
    "ajinkya dy patil university",
    "nxtwave website",
    "nxtwave institute of advanced technologies reviews",
    "next way",
    "na t",
    "st peter's institute of higher education and research bangalore",
    "aurora deemed university uppal",
    "nxtwave vijayawada address",
    "where is niat",
    "b. s. abdur rahman",
    "nait university",
    "s vyasa school of advanced studies",
    "best university anantapur",
    "niat college where is it located",
    "aurora deemed university, bhongir photos",
    "niat college btech fees",
    "niat hyderabad highest package cse",
    "next wave nanakramguda",
    "nxtwave bangalore office",
    "vivekananda global university jaipur address",
    "nri college in vijayawada",
    "what is nat application",
    "sanjay university",
    "nxtwave disruptive technologies",
    "nat registration 2026",
    "niit hyderabad gachibowli",
    "niat government or private",
    "what is nat exam india",
    "nait college fees",
    "niat in english",
    "nait portal",
    "malla reddy vidyapeeth",
    "abdul rahman college chennai",
    "open ai niat",
    "nxtwave disruptive technologies private limited",
    "niat anantapur experience center",
    "nri btech college vijayawada",
    "ghodawat university kolhapur",
    "s vyasa university bangalore",
    "chaitanya deemed to be university hyderabad address",
    "nxtwave data science course",
    "nxtwave institute of advanced technologies: niat by owner",
    "nxtwave india",
    "b.s. abdur rahman crescent institute of science & technology",
    "nat exam registration",
    "nat exam registration 2026",
    "crescent university chennai address",
    "nat exam in india",
    "national advanced technical training institute",
    "ccbp full form",
    "vgu jaipur campus area",
    "malla reddy university",
    "niat college is best or not",
    "niat avg package",
]

# Build a lowercase set for O(1) lookup during validation
MASTER_KEYWORD_SET = {kw.lower().strip() for kw in ALL_KEYWORDS}


# ---------------------------------------------
# PRELOAD ALL CAMPUSES ONCE
# Tokenization rules:
#   location : e.g. "Noida" -> 'noida'
#   state    : e.g. "Uttar Pradesh" -> 'uttar pradesh' + individual words
#   name     : full lowercased campus name
#   short_name: lowercased short name
# ---------------------------------------------

def preload_campuses():
    campus_map = {}

    for c in Campus.objects.all():
        location_token = (c.location or '').lower().strip()
        state_token = (c.state or '').lower().strip()
        name_token = (c.name or '').lower().strip()
        short_name_token = (c.short_name or '').lower().strip()

        tokens = set()
        if location_token:
            tokens.add(location_token)
        if state_token:
            tokens.add(state_token)
            for word in state_token.split():
                if len(word) > 2:
                    tokens.add(word)
        if name_token:
            tokens.add(name_token)
        if short_name_token:
            tokens.add(short_name_token)

        campus_map[c.id] = {
            'name': name_token,
            'short_name': short_name_token,
            'location': location_token,
            'state': state_token,
            'slug': (c.slug or '').lower().strip(),
            'tokens': tokens,
        }

    return campus_map


def get_campus_data(article, campus_map):
    if article.campus_id_id and article.campus_id_id in campus_map:
        return campus_map[article.campus_id_id]
    return None


def get_all_location_tokens(campus_map):
    all_tokens = set()
    for data in campus_map.values():
        if data['location']:
            all_tokens.add(data['location'])
    return all_tokens


# ---------------------------------------------
# FILTER OUT BAD KEYWORDS (fee, syllabus etc.)
# ---------------------------------------------

def filter_exclude_keywords(keywords):
    return [
        kw for kw in keywords
        if not any(
            pat.lower() in (kw or '').lower()
            for pat in EXCLUDE_PATTERNS
        )
    ]


def _keyword_token_set(text):
    return {
        t for t in re.findall(r'[a-z0-9]+', (text or '').lower())
        if len(t) > 2
    }


def filter_seed_keywords(keywords, article, campus_data):
    """
    First-pass keyword gate:
    keep only NIAT/NxtWave brand terms and campus/location-aligned terms.
    """
    campus_tokens = set()
    if campus_data:
        campus_tokens = set(campus_data['tokens'])
        if campus_data.get('name'):
            campus_tokens.update(_keyword_token_set(campus_data['name']))
        if campus_data.get('location'):
            campus_tokens.update(_keyword_token_set(campus_data['location']))
        if campus_data.get('state'):
            campus_tokens.update(_keyword_token_set(campus_data['state']))
    else:
        campus_tokens = _keyword_token_set(article.campus_name)

    seed_terms = {
        'niat', 'nxtwave', 'nextwave', 'next', 'wave',
        'campus', 'college', 'colleges', 'university', 'location',
    }
    seed_terms.update(campus_tokens)

    filtered = []
    for kw in keywords:
        kw_lower = (kw or '').lower().strip()
        if not kw_lower:
            continue
        kw_tokens = _keyword_token_set(kw_lower)
        if kw_tokens.intersection(seed_terms):
            filtered.append(kw)

    return filtered


# ---------------------------------------------
# FILTER OUT WRONG-PLACE KEYWORDS
# Drops keywords that contain another campus's city.
# ---------------------------------------------

def filter_place_keywords(keywords, campus_data, all_location_tokens):
    if not campus_data:
        return keywords

    own_location = campus_data['location']

    filtered = []
    for kw in keywords:
        kw_lower = kw.lower()
        other_place_found = any(
            place in kw_lower
            for place in all_location_tokens
            if place != own_location
        )
        if not other_place_found:
            filtered.append(kw)

    return filtered


def filter_context_relevant_keywords(keywords, article, campus_data):
    campus_tokens = set(campus_data['tokens']) if campus_data else set()
    title_tokens = _keyword_token_set(article.title)
    category_tokens = _keyword_token_set((article.category or '').replace('-', ' '))

    # Add a small body context signal to avoid keeping broad brand-only terms.
    body_preview = ''
    if article.body:
        body_preview = re.sub(r'<[^>]+>', ' ', article.body)
        body_preview = re.sub(r'\s+', ' ', body_preview).strip()[:700]
    body_tokens = _keyword_token_set(body_preview)

    context_tokens = campus_tokens | title_tokens | category_tokens | body_tokens

    filtered = []
    for kw in keywords:
        kw_lower = (kw or '').lower().strip()
        if not kw_lower:
            continue

        if any(pat in kw_lower for pat in IRRELEVANT_INTENT_PATTERNS):
            continue

        if kw_lower in GENERIC_ALLOWED_KEYWORDS:
            filtered.append(kw)
            continue

        kw_tokens = _keyword_token_set(kw_lower)
        if kw_tokens and kw_tokens.intersection(context_tokens):
            filtered.append(kw)

    return filtered


def build_final_keywords(mandatory, validated_keywords):
    final_keywords = []
    seen = set()

    for kw in (mandatory + validated_keywords):
        kw_norm = (kw or '').lower().strip()
        if not kw_norm or kw_norm in seen:
            continue
        seen.add(kw_norm)
        final_keywords.append(kw)

    return final_keywords[:TARGET_MAX_KEYWORDS]


# ---------------------------------------------
# STRICT POST-VALIDATION
# Drops any keyword Claude returned that is not
# exactly in the master list. No exceptions.
# ---------------------------------------------

def validate_keywords_against_master(keywords):
    return [
        kw for kw in keywords
        if kw.lower().strip() in MASTER_KEYWORD_SET
    ]


# ---------------------------------------------
# SMART KEYWORD SCORING
# Scores keywords from master list against article context.
# ---------------------------------------------

def get_keywords_for_article(article, campus_data) -> list:
    campus_tokens = campus_data['tokens'] if campus_data else set()
    campus_location = campus_data['location'] if campus_data else ''
    campus_name = campus_data['name'] if campus_data else (article.campus_name or '').lower()

    category = (article.category or '').lower()
    title = (article.title or '').lower()
    title_words = [w for w in title.split() if len(w) > 2]

    scored = []

    for kw in ALL_KEYWORDS:
        kw_lower = kw.lower()
        score = 0

        if campus_name and campus_name in kw_lower:
            score += 6
        if campus_location and campus_location in kw_lower:
            score += 5
        if any(token in kw_lower for token in campus_tokens):
            score += 3
        if category and category.replace('-', ' ') in kw_lower:
            score += 3
        if any(word in kw_lower for word in title_words):
            score += 2
        if 'niat' in kw_lower:
            score += 2
        if len(kw.split()) >= 3:
            score += 1

        if score > 0:
            scored.append((kw, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [kw for kw, _ in scored]


# ---------------------------------------------
# BUILD MANDATORY KEYWORDS
# Only adds keywords that exist in the master list.
# ---------------------------------------------

def build_mandatory_keywords(article, campus_data):
    mandatory = []

    if not campus_data:
        campus_name_str = (article.campus_name or '').lower().strip()
        if campus_name_str:
            candidate = f"niat {campus_name_str}"
            if candidate in MASTER_KEYWORD_SET:
                mandatory.append(candidate)
        return mandatory

    location = campus_data['location']
    name = campus_data['name']
    state = campus_data['state']

    candidates = []
    if location:
        candidates.append(location)
        candidates.append(f"niat {location}")
    if name:
        candidates.append(f"niat {name}")
    if state:
        candidates.append(state)

    for c in candidates:
        if c.lower().strip() in MASTER_KEYWORD_SET:
            mandatory.append(c)

    return mandatory


# ---------------------------------------------
# TITLE SEO CHECK
# ---------------------------------------------

def is_title_seo_ready(title):
    if not title:
        return False
    words = title.strip().split()
    if len(words) < 4 or len(words) > 15:
        return False
    if title == title.upper():
        return False
    return True


# ---------------------------------------------
# SLUG BUILDER
# Built in Python from meta_title.
# Strips campus name and location so they never appear in URL.
# ---------------------------------------------

def build_seo_slug(title, campus_data, campus_name_str):
    slug = title.lower()

    if campus_name_str:
        slug = slug.replace(campus_name_str.lower().strip(), '')
    if campus_data:
        if campus_data['location']:
            slug = slug.replace(campus_data['location'], '')
        if campus_data['name']:
            slug = slug.replace(campus_data['name'], '')

    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug).strip('-')

    return slug[:70]


# ---------------------------------------------
# COMMAND
# ---------------------------------------------

class Command(BaseCommand):
    help = 'SEO generation using full article and keyword set'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--article-id', type=str)
        parser.add_argument('--overwrite', action='store_true')
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            self.stdout.write(self.style.ERROR('ANTHROPIC_API_KEY missing'))
            return

        client = anthropic.Anthropic(api_key=api_key)

        campus_map = preload_campuses()
        all_location_tokens = get_all_location_tokens(campus_map)

        if options['article_id']:
            articles = Article.objects.filter(
                id=options['article_id'],
                status='published',
            ).select_related('campus_id')
        else:
            articles = Article.objects.filter(
                status='published',
                is_global_guide=False,
                campus_id__isnull=False,
            ).select_related('campus_id')

        total = articles.count()
        success = skipped = errors = processed_count = 0
        limit = options['limit']

        self.stdout.write(f'Found {total} articles\n')

        for article in articles:

            if processed_count >= limit:
                break

            if not options['overwrite'] and article.meta_title:
                skipped += 1
                continue

            try:
                campus_data = get_campus_data(article, campus_map)

                # Score and filter keywords before sending to Claude
                keywords = get_keywords_for_article(article, campus_data)
                keywords = filter_seed_keywords(keywords, article, campus_data)
                keywords = filter_exclude_keywords(keywords)
                keywords = filter_place_keywords(keywords, campus_data, all_location_tokens)

                result = self.generate_seo_with_retry(client, article, keywords, campus_data)

                # Strict post-validation: drop anything Claude invented
                raw_keywords = result.get('meta_keywords', [])
                validated_keywords = validate_keywords_against_master(raw_keywords)
                base_for_slug = result.get('meta_title') or result.get('title') or article.title
                clean_slug = build_seo_slug(base_for_slug, campus_data, article.campus_name)

                # Mandatory first, then Claude picks (Claude is the final relevance selector).
                mandatory = build_mandatory_keywords(article, campus_data)
                final_keywords = build_final_keywords(
                    mandatory=mandatory,
                    validated_keywords=validated_keywords,
                )

                if options['dry_run']:
                    campus_info = (
                        f"{campus_data['name']} / {campus_data['location']}"
                        if campus_data else article.campus_name
                    )
                    self.stdout.write(f"""
CAMPUS INFO : {campus_info}
TITLE       : {result['title']}
SLUG        : {clean_slug}
META TITLE  : {result['meta_title']}
META DESC   : {result['meta_description']}
KEYWORDS    : {", ".join(final_keywords)}
""")
                else:
                    if (
                        result.get('title') and
                        result['title'].lower().strip() != article.title.lower().strip()
                    ):
                        article.title = result['title']

                    article.slug = clean_slug
                    article.meta_title = result['meta_title']
                    article.meta_description = result['meta_description']
                    article.meta_keywords = final_keywords

                    if result.get('first_paragraph') and article.body:
                        article.body = self.replace_first_paragraph(
                            article.body,
                            result['first_paragraph']
                        )

                    article.save()

                success += 1
                processed_count += 1
                time.sleep(0.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"{article.id} | {article.title} | {str(e)}"))
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {success} success | {skipped} skipped | {errors} errors"
        ))


    # ---------------------------------------------
    # RETRY
    # ---------------------------------------------

    def generate_seo_with_retry(self, client, article, keywords, campus_data, max_retries=3):
        delay = 5

        for attempt in range(max_retries):
            try:
                return self.generate_seo(client, article, keywords, campus_data)

            except anthropic.RateLimitError:
                time.sleep(delay)
                delay *= 2

            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)


    # ---------------------------------------------
    # CORE SEO
    # ---------------------------------------------

    def generate_seo(self, client, article, keywords, campus_data):

        body_content = ''
        if article.body:
            body_content = re.sub(r'<[^>]+>', '', article.body)
            body_content = re.sub(r'\s+', ' ', body_content).strip()

        keywords_str = '\n'.join(f'- {kw}' for kw in keywords)

        title_instruction = (
            "The current title looks good. Keep it as-is unless it is clearly vague or too short."
            if is_title_seo_ready(article.title)
            else "The current title needs improvement. Rewrite it to be clear and SEO-optimized."
        )

        if campus_data:
            campus_context = (
                f"Campus Name : {campus_data['name']}\n"
                f"Campus City : {campus_data['location']}\n"
                f"Campus State: {campus_data['state']}"
            )
        else:
            campus_context = f"Campus Name: {article.campus_name}"

        system_prompt = """You are an expert SEO strategist for a student-focused education platform.
Return ONLY valid JSON. No explanation. No markdown. No extra text."""

        user_prompt = f"""Optimise this student-written article for Google ranking.

{campus_context}
CATEGORY: {article.category}
TITLE: {article.title}

FULL ARTICLE:
{body_content}

AVAILABLE KEYWORDS TO CHOOSE FROM:
{keywords_str}

TITLE INSTRUCTION: {title_instruction}

KEYWORD SELECTION CONTEXT:
- AVAILABLE KEYWORDS are already pre-filtered by NIAT/NxtWave brand, campus identity, and campus location signals.
- The list intentionally includes NIAT/NxtWave brand phrases (for example "next wave institute of advanced technology").
- Choose only article-relevant intent keywords from this filtered list.

STRICT RULES:
1. Title: Keep student tone and voice. Only rewrite if vague or too short. Max 60 characters.
2. Slug: Return empty string. Slug is generated separately.
3. Meta title: 50 to 60 characters. Include primary keyword naturally.
4. Meta description: 150 to 160 characters. Natural language. Include 1 to 2 keywords.
5. Keywords: You MUST pick ONLY from the AVAILABLE KEYWORDS list above.
   Do NOT create, invent, or add any keyword not present in the list.
   Do NOT rephrase or modify any keyword from the list.
   Copy each keyword exactly as written in the list.
   Select 20 to 30 keywords most relevant to the article content, campus city, and category.
   Prioritise keywords about campus/location/college identity and student experience in this article.
   Drop irrelevant institutional/process intent (example: scholarship, login/portal, placement, ranking) unless clearly central to the article.
   Avoid generic exam/joining/application intent unless the article clearly discusses that intent.
   Do NOT pick keywords for cities or campuses not related to this article.
6. First paragraph: Rewrite to include primary keyword naturally. Keep student tone. No stuffing.

RETURN JSON:

{{
  "title": "",
  "slug": "",
  "meta_title": "",
  "meta_description": "",
  "meta_keywords": [],
  "first_paragraph": ""
}}"""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = message.content[0].text.strip()

        if '```' in raw:
            raw = re.sub(r'```[a-z]*', '', raw).replace('```', '').strip()

        result = json.loads(raw)

        return result


    # ---------------------------------------------
    # HELPERS
    # ---------------------------------------------

    def replace_first_paragraph(self, body, new_para):
        return re.sub(
            r'<p[^>]*>.*?</p>',
            f'<p>{new_para}</p>',
            body,
            count=1,
            flags=re.DOTALL
        )