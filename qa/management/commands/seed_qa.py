"""
Seed NIAT Q&A with curated questions and answers.
Usage: python manage.py seed_qa
Creates a seed user (niat_seed) if needed, then inserts all Q&As.
Questions marked is_faq=True appear on the homepage; faq_order controls their order.
"""
import uuid
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from qa.models import Question, Answer

User = get_user_model()

# FAQ order for homepage: only these 8 get is_faq=True and faq_order 1-8
FAQ_TITLES_ORDER = [
    "What exactly is NIAT and who runs it?",
    "Does NIAT give a degree? Will it be valid for government jobs or higher studies abroad?",
    "How is NIAT different from a regular B.Tech college?",
    "What is the total fee for the B.Tech program at NIAT?",
    "Are there scholarships available at NIAT?",
    "How are placements at NIAT? What companies come for hiring?",
    "What specializations can I choose in the B.Tech program?",
    "Is NIAT recognized by NASSCOM and the government?",
]

SEED_DATA = [
    # --- ABOUT NIAT ---
    {
        "category": "About NIAT",
        "title": "What exactly is NIAT and who runs it?",
        "answer": "NIAT stands for NxtWave Institute of Advanced Technologies. It's an initiative by NxtWave, founded by alumni of IIT Bombay, IIT Kharagpur, and IIIT Hyderabad — specifically Sashank Gujjula, Anupam Pedarla, and Rahul Attuluri. NIAT isn't a university itself — instead, it designs an industry-ready upskilling curriculum that runs inside UGC-recognised and AICTE-approved partner universities. So you get a valid B.Tech degree from the university, but your actual learning is powered by NIAT's curriculum and mentors. Think of NIAT as the \"engine\" and the university as the \"car.\"",
    },
    {
        "category": "About NIAT",
        "title": "Does NIAT give a degree? Will it be valid for government jobs or higher studies abroad?",
        "answer": "Yes, but the degree is awarded by the partner university, not NIAT itself. NIAT explicitly states it is not a university and does not award degrees on its own. The B.Tech you receive is from the collaborating UGC-recognised or AICTE-approved university, which makes it fully valid for government jobs and higher studies abroad. Always double-check which specific university you're being admitted to and confirm their accreditation before joining.",
    },
    {
        "category": "About NIAT",
        "title": "How is NIAT different from a regular B.Tech college?",
        "answer": "The biggest difference is the curriculum approach. Regular engineering colleges still run theory-heavy syllabi that haven't kept up with the industry. NIAT's skill map is built from feedback from 3,000+ companies and is updated every semester. From day one, you're writing code, building projects, and participating in hackathons — not sitting through long theory lectures. You also get mentors from companies like Microsoft, Google, and Amazon, plus masterclasses from CEOs and CXOs. That said, the on-campus experience (hostel, college culture, sports) still depends on which partner university you're assigned to.",
    },
    {
        "category": "About NIAT",
        "title": "In which states and cities does NIAT operate?",
        "answer": "As of 2025, NIAT has a presence across 8 states: Telangana, Andhra Pradesh, Tamil Nadu, Karnataka, Maharashtra, Rajasthan, Delhi NCR, and Uttar Pradesh. Cities include Hyderabad, Bangalore, Chennai, Pune, Vijayawada, Guntur, Greater Noida, and more. Each city has one or more partner universities. During the counselling process, you'll be recommended a university based on your NAT score, preferences, and seat availability.",
    },
    # --- ADMISSION & ELIGIBILITY ---
    {
        "category": "Admission & Eligibility",
        "title": "What is the eligibility criteria to apply for NIAT?",
        "answer": "You need to have completed Class 12 (or be currently appearing) with Physics, Chemistry, and Mathematics as core subjects and a minimum of 50% aggregate marks. After that, you take the NxtWave Assessment Test (NAT). Students with 85%+ aggregate in Class 12 can directly qualify the primary round. The NAT is an online exam of 90 minutes with 81 questions covering Psychometric Tests, Critical Thinking, and Mathematics — it's testing your potential, not your existing coding knowledge. A one-on-one counselling session follows the test.",
    },
    {
        "category": "Admission & Eligibility",
        "title": "What is the NAT exam and how should I prepare for it?",
        "answer": "NAT (NxtWave Assessment Test) is NIAT's entrance exam. It has 81 questions across three sections: Psychometric Tests (your personality and mindset), Critical Thinking (logic and reasoning), and Mathematics (Class 10–12 level). There's no negative marking as far as students have reported. You don't need to know programming to crack it. Focus on logical reasoning, basic maths, and be honest in the psychometric section — it's assessing your learning aptitude and attitude, not just scores. After clearing NAT, you'll have a one-on-one counselling session where the team recommends a university that fits your preferences and goals.",
    },
    {
        "category": "Admission & Eligibility",
        "title": "Is admission guaranteed after I clear the NAT?",
        "answer": "No, clearing NAT is not a guarantee of admission. The final admission is solely at the discretion of the partner university, following UGC and AICTE norms. NIAT's counselling team recommends a university based on your score and preferences, but the university makes the final call. Make sure you meet the university's own eligibility criteria and submit all required documents on time.",
    },
    {
        "category": "Admission & Eligibility",
        "title": "Can I choose which city or university I want to join?",
        "answer": "You can express your preferences during the one-on-one counselling session after your NAT. The NIAT team will recommend a university from among their partner institutions based on your score, preferences, and seat availability. You can communicate your city preference, but the final allocation depends on seats and fit. It's a good idea to research the specific partner universities in your preferred city before your counselling session so you can ask informed questions.",
    },
    # --- FEES & SCHOLARSHIPS ---
    {
        "category": "Fees & Scholarships",
        "title": "What is the total fee for the B.Tech program at NIAT?",
        "answer": "The fees vary by location and partner university. Here's a rough breakdown based on what's publicly available: Hyderabad campuses range between ₹12–16 lakhs total for 4 years. Bangalore is around ₹14 lakhs total (approximately ₹3.5 lakhs/year). Vijayawada is on the lower end at around ₹10 lakhs total (approximately ₹2.5 lakhs/year). Tamil Nadu and Pune are in the ₹12–14 lakh range. These figures include tuition and course fees — confirm the exact breakdown including hostel, transport, and exam fees during your counselling session, as they can add up.",
    },
    {
        "category": "Fees & Scholarships",
        "title": "Are there scholarships available at NIAT?",
        "answer": "Yes. NIAT offers merit-based scholarships, including up to 100% scholarship for the first year based on academic performance and NAT scores. If you have a strong Class 12 record and perform well in the NAT, you have a real shot at a scholarship. Details are discussed during the counselling session. Don't assume the scholarship will continue automatically — ask specifically about renewal criteria for subsequent years.",
    },
    {
        "category": "Fees & Scholarships",
        "title": "What is the hostel fee at NIAT campuses?",
        "answer": "Hostel facilities are typically provided through private hostels partnered with the university, not directly by NIAT. At the Tamil Nadu campus, for example: a 4-occupancy room costs ₹10,500/month, ₹60,000 for 6 months, or ₹1,08,000 for a year. A 2-occupancy room costs ₹12,500/month, ₹70,000 for 6 months, or ₹1,30,000 for a year. Hostels generally include 24/7 Wi-Fi, CCTV, meals, and some have AC options and gyms. Fees will differ by campus, so ask specifically during counselling.",
    },
    # --- PLACEMENTS & INTERNSHIPS ---
    {
        "category": "Placements & Internships",
        "title": "How are placements at NIAT? What companies come for hiring?",
        "answer": "NIAT has a network of 3,000+ companies — ranging from fast-growing startups to Fortune 500 giants. Companies in their recruiter network include Amazon, Microsoft, Google, Accenture, Infosys, TCS, Deloitte, Wipro, Capgemini, Goldman Sachs, Oracle, Cognizant, HDFC Bank, and Samsung, among many others. That said, since NIAT was founded in 2023, detailed placement statistics for graduating batches are still emerging. The institute is transparent about this — their website states that \"enrollment in NIAT itself does not assure a job or internship\" and placement outcomes depend heavily on your own skills and effort. Students report getting paid internships by their second year, which is a positive signal.",
    },
    {
        "category": "Placements & Internships",
        "title": "When can I expect to get my first internship at NIAT?",
        "answer": "Based on what current students share, many are landing paid internships by their 1st or 2nd year. NIAT's curriculum is structured so you're building real-world projects from semester one, which makes your profile strong early on. NIAT provides mock interviews, Problem of the Day (POTD), mock test series, and dedicated placement prep. The goal the NIAT team sets for students is to crack a tech internship within 1–2 years of joining. That's realistic if you stay consistent with the coding practice and project work.",
    },
    {
        "category": "Placements & Internships",
        "title": "Does NIAT guarantee placement after graduation?",
        "answer": "No, NIAT does not guarantee placement. They clearly state this on their official website. What they offer is placement support — a strong recruiter network, career guidance, interview preparation, and a placement team that actively connects students with companies. Your placement outcome ultimately depends on the skills you build, your consistency, and your performance in interviews. Think of NIAT as giving you the best runway — you still have to take off yourself.",
    },
    # --- CURRICULUM & LEARNING ---
    {
        "category": "Curriculum & Learning",
        "title": "What specializations can I choose in the B.Tech program?",
        "answer": "NIAT offers B.Tech in Computer Science Engineering (CSE) with three main specialization tracks: Artificial Intelligence (AI), Machine Learning (ML), and Data Science. Some campuses also offer Full Stack Development as a track. The core curriculum covers programming fundamentals, MERN stack development, core CS concepts, and then goes deep into your chosen specialization. The curriculum is updated every semester based on industry feedback, so what you learn stays relevant.",
    },
    {
        "category": "Curriculum & Learning",
        "title": "Is the learning at NIAT really practical or is it just marketing?",
        "answer": "From what multiple students consistently report, the practical focus is genuine. Classes are structured around real-world projects, coding exercises, and hackathons rather than theory lectures. You start coding real projects from day one. The campus doesn't feel like a traditional college classroom — students often describe it as a \"work environment.\" You'll also have Industry 5.0 clubs for AI, Robotics, Drones, and Autonomous Vehicles. That said, the quality of your experience will depend significantly on your own initiative and the specific mentors at your campus.",
    },
    {
        "category": "Curriculum & Learning",
        "title": "Who are the mentors and faculty at NIAT?",
        "answer": "NIAT's world-class mentors are industry professionals from companies like Microsoft, Google, Amazon, and IITs. The institute also hosts masterclasses by CEOs and CXOs from leading companies. For the academic side, faculty at the partner universities handle your university coursework. The blend means you get industry-relevant training from practitioners alongside formal academic instruction. Students generally rate the mentors highly for being approachable and focused on real-world skills.",
    },
    {
        "category": "Curriculum & Learning",
        "title": "How often is the curriculum updated?",
        "answer": "NIAT claims to update its skill map every semester based on continuous feedback from 3,000+ companies and students. This is one of their core differentiators — they call it India's first \"real-time adaptive curriculum.\" In practice, this means new tools, languages, and frameworks that become industry-relevant get incorporated into what you learn. This is significantly better than traditional colleges where the syllabus can be 5–10 years outdated.",
    },
    # --- CAMPUS LIFE & INFRASTRUCTURE ---
    {
        "category": "Campus Life & Infrastructure",
        "title": "What is the campus infrastructure like at NIAT?",
        "answer": "Campuses are modern and well-equipped. Students report wide classrooms with smartboards and high-speed Wi-Fi, well-equipped coding labs with the latest software tools, a cafeteria on the floor, indoor games, and clean washrooms. Because NIAT operates inside partner university campuses, you also have access to the university's library, sports complex, and other facilities. One thing to note: some campuses are located in tech parks or financial districts surrounded by tech companies, which means less open outdoor space compared to a traditional sprawling college campus.",
    },
    {
        "category": "Campus Life & Infrastructure",
        "title": "Is the NIAT campus safe? What about safety for female students?",
        "answer": "NIAT has stated that its campuses maintain strict safety protocols. There are grievance committees and discipline committees conducting 24/7 surveillance both inside and outside the campus. Hostels are separate for boys and girls. CCTV is installed across hostels and campus areas. The campuses are located in established areas (often tech districts), which adds another layer of security. As with any institution, it's wise to visit the specific campus you're considering and speak with current students directly.",
    },
    {
        "category": "Campus Life & Infrastructure",
        "title": "How many holidays and breaks do students get at NIAT?",
        "answer": "This is one point where students have flagged a drawback — NIAT has fewer holidays compared to traditional colleges. The program is intensive and keeps students occupied throughout the year. If you're someone who values long semester breaks, NIAT's schedule may feel demanding. The trade-off is that the focused learning environment builds skills faster. Plan your personal time and family visits accordingly.",
    },
    # --- GENERAL QUERIES ---
    {
        "category": "General",
        "title": "Is NIAT recognized by NASSCOM and the government?",
        "answer": "Yes. NIAT is recognized by NASSCOM (National Association of Software and Service Companies), the National Skill Development Corporation (NSDC), and Startup India. The founders were featured in Forbes India 30 Under 30 in 2024. NIAT has also signed an MoU with AICTE to offer courses on the NEAT platform, signed an MoU with NSDC for the SkillUp India 4.0 initiative, and their CEO was invited to the World Economic Forum's Annual Meeting 2025. These are strong credibility signals for an institute founded in 2023.",
    },
    {
        "category": "General",
        "title": "Is NIAT worth it compared to a regular private engineering college?",
        "answer": "If your goal is a software job at a good tech company, NIAT is likely the better choice over an average private engineering college with an outdated syllabus. The industry-aligned curriculum, practical projects, coding culture, and recruiter network are genuine advantages. However, if you're comparing to a top NIT, BITS, or IIT, the brand value and alumni network of those institutions still carry more weight. NIAT is strongest for students from tier-2/3 cities who want a structured, industry-ready path into tech without cracking JEE Advanced. Weigh your options based on your goals, the specific partner university, and the fee you're comfortable with.",
    },
    {
        "category": "General",
        "title": "Can I transfer out of NIAT's program to another college after the first year?",
        "answer": "Technically, since your admission is with the partner university (not NIAT directly), any transfer would follow that university's policies and UGC regulations for lateral transfers. NIAT's upskilling program is embedded into the B.Tech curriculum, so transferring to a college without that program means you'd lose access to NIAT's resources. It's not impossible, but it's complicated. Think carefully before joining rather than banking on a transfer later.",
    },
]


def make_slug_unique(title: str) -> str:
    base = (slugify(title) or "question")[:300]
    slug = base
    while Question.objects.filter(slug=slug).exists():
        slug = f"{base}-{uuid.uuid4().hex[:8]}"
    return slug


class Command(BaseCommand):
    help = "Seed Q&A with NIAT questions and answers. Creates niat_seed user if needed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing questions (and answers) created by the seed user before seeding.",
        )

    def handle(self, *args, **options):
        # Get or create seed user (verified senior so answers are valid)
        seed_user, created = User.objects.get_or_create(
            username="niat_seed",
            defaults={
                "email": "seed@niat.local",
                "role": "senior",
                "is_verified_senior": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if created:
            seed_user.set_unusable_password()
            seed_user.save()
            self.stdout.write(self.style.SUCCESS("Created seed user: niat_seed (verified senior)"))

        if options["clear"]:
            deleted, _ = Question.objects.filter(author=seed_user).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing question(s) from seed user."))

        faq_order_map = {t: i + 1 for i, t in enumerate(FAQ_TITLES_ORDER)}
        created_count = 0
        skipped = 0

        for item in SEED_DATA:
            title = item["title"]
            if Question.objects.filter(author=seed_user, title=title).exists():
                skipped += 1
                continue
            slug = make_slug_unique(title)
            if Question.objects.filter(slug=slug).exists():
                skipped += 1
                continue

            is_faq = title in faq_order_map
            faq_order = faq_order_map.get(title, 0)

            q = Question.objects.create(
                author=seed_user,
                title=title,
                slug=slug,
                body="",
                is_answered=True,
                is_faq=is_faq,
                faq_order=faq_order,
            )
            Answer.objects.create(
                question=q,
                author=seed_user,
                body=item["answer"].strip(),
            )
            created_count += 1
            self.stdout.write(f"  [{item['category']}] {title[:60]}...")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} Q&As, skipped {skipped}."))
