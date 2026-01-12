from django.core.management.base import BaseCommand
from users.models import User, Freelancer, Recruiter,Job,Application
from django.contrib.auth.hashers import make_password
import random
from datetime import date

class Command(BaseCommand):
    help = "Seed demo data safely (no duplicates)"

    def handle(self, *args, **kwargs):

        # ---------------- FREELANCERS ----------------
        if Freelancer.objects.exists():
            self.stdout.write("⚠ Freelancers already exist. Skipping freelancer creation.")
        else:
            for i in range(1, 21):
                email = f"freelancer{i}@skillconnect.demo"

                user = User.objects.create(
                    full_name=f"Freelancer {i}",
                    email=email,
                    password=make_password("password123"),
                    account_type="freelancer",
                    is_verified=True
                )

                Freelancer.objects.create(
                    full_name=user.full_name,
                    email=email,
                    password=user.password,
                    job_role=random.choice(["Web Developer", "UI Designer", "Python Developer"]),
                    experience_level=random.choice(["fresher", "experienced", "expert"]),
                    hourly_rate=random.randint(10, 50),
                    education="B.Tech Computer Science",
                    tech_stack="HTML, CSS, JavaScript, Django",
                    skills="Frontend, Backend, APIs",
                    location=random.choice(["Hyderabad", "Bangalore", "Chennai"]),
                    dob=date(2001, 5, 15),
                    phone=f"90000000{i:02d}",
                    address="India",
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS("✔ Freelancers created"))

        # ---------------- RECRUITERS ----------------
        if Recruiter.objects.exists():
            self.stdout.write("⚠ Recruiters already exist. Skipping recruiter creation.")
        else:
            for i in range(1, 11):
                email = f"recruiter{i}@skillconnect.demo"

                User.objects.create(
                    full_name=f"Recruiter {i}",
                    email=email,
                    password=make_password("password123"),
                    account_type="recruiter",
                    is_verified=True
                )

                Recruiter.objects.create(
                    full_name=f"Recruiter {i}",
                    email=email,
                    password=make_password("password123"),
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS("✔ Recruiters created"))

        # ---------------- JOBS ----------------
        recruiters = Recruiter.objects.all()

        if not recruiters.exists():
            self.stdout.write("❌ No recruiters found. Jobs not created.")
            return


        job_titles = [
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "Python Developer",
            "React Developer",
            "UI/UX Designer"
        ]

        skills_list = [
            "HTML, CSS, JavaScript",
            "Python, Django, REST",
            "React, Node.js",
            "SQL, MongoDB",
            "Bootstrap, Tailwind"
        ]
        if not Job.objects.exists():
            for recruiter in recruiters:
                for _ in range(random.randint(2, 4)):
                    Job.objects.create(
                        recruiter=recruiter,
                        title=random.choice(job_titles),
                        skills=random.choice(skills_list),
                        work_type=random.choice(["short", "long"]),
                        duration=random.choice(["1 month", "3 months", "6 months"]),
                        experience_level=random.choice(["fresher", "experienced"]),
                        payment_type=random.choice(["hourly", "fixed"]),
                        description="Demo job created for academic project.",
                        is_active=True
                    )

            self.stdout.write(self.style.SUCCESS("✔ Jobs created successfully"))
        # ---------------- APPLICATIONS ----------------


        freelancers = list(Freelancer.objects.all())

        for job in Job.objects.all():
            num_applications = random.randint(3, 5)
            applied_freelancers = random.sample(freelancers, min(num_applications, len(freelancers)))

            for freelancer in applied_freelancers:
                Application.objects.create(
                    job=job,
                    freelancer=freelancer,
                    cover_letter=f"Hi, I am {freelancer.full_name} and I am interested in this job."
                )

        self.stdout.write(self.style.SUCCESS("✔ Applications created successfully"))
