from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone
class User(models.Model):
    ACCOUNT_TYPES = (
        ('freelancer', 'Freelancer'),
        ('recruiter', 'Recruiter'),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

# models.py
from django.db import models
from django.db import models

class Freelancer(models.Model):
    # Basic Info
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    # Freelancer Details
    job_role = models.CharField(
    max_length=255,
    default="Freelancer"
)

    experience_level = models.CharField(
        max_length=20,
        choices=[('fresher', 'Fresher'), ('experienced', 'Experienced'), ('expert', 'Expert')],
        blank=True,
        null=True
    )
    
    resume = models.FileField(upload_to='freelancer_resumes/', blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    education = models.CharField(max_length=255, blank=True, null=True)
    tech_stack = models.CharField(max_length=255, blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True, null=True)

    # 🔥 REQUIRED FOR SEARCH BY LOCATION
    location = models.CharField(max_length=100, blank=True, null=True)

    # Personal Info
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='freelancer_photos/', blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

class Recruiter(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    photo = models.ImageField(upload_to="recruiter_photos/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

class OTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
# jobs/models.py
from django.db import models
from users.models import User


class Job(models.Model):
    WORK_TYPE_CHOICES = [
        ("short", "Short-term"),
        ("long", "Long-term"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("fresher", "Fresher"),
        ("experienced", "Experienced"),
    ]

    PAYMENT_TYPE_CHOICES = [
        ("hourly", "Hourly"),
        ("fixed", "Fixed"),
    ]

    recruiter = models.ForeignKey(
        Recruiter,
        on_delete=models.CASCADE,
        related_name="posted_jobs"
    )
    title = models.CharField(max_length=200)
    skills = models.CharField(max_length=255, blank=True, default="")
    work_type = models.CharField(max_length=10, choices=WORK_TYPE_CHOICES, default="short")
    duration = models.CharField(max_length=50, blank=True, null=True)  # e.g., "3 months"
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default="fresher")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default="fixed")
    description = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to="job_documents/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    resume = models.FileField(upload_to="job_applications/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.freelancer.full_name} → {self.job.title}"
class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    freelancer = models.ForeignKey('Freelancer', on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied'
    )

    # --- Extra fields to store freelancer info for recruiter view ---
    freelancer_name = models.CharField(max_length=200, default="")
    freelancer_email = models.EmailField(default="")
    freelancer_resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Populate extra fields from freelancer profile automatically
        if self.freelancer:
            self.freelancer_name = self.freelancer.full_name
            self.freelancer_email = self.freelancer.email
            if self.freelancer.resume:
                self.freelancer_resume = self.freelancer.resume
        super(Application, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.freelancer_name} -> {self.job.title}"

class Contract(models.Model):
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    agreed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed')],
        default='pending'
    )
    is_active = models.BooleanField(default=False)

class Timesheet(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
class Interview(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    interview_date = models.DateField()
    interview_time = models.TimeField()
    mode = models.CharField(max_length=50, choices=[
        ('call','Call'),
        ('video','Video'),
        ('in_person','In Person')
    ])
class Message(models.Model):
    sender_recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, null=True, blank=True)
    sender_freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, null=True, blank=True)
    receiver_recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='received_recruiter', null=True, blank=True)
    receiver_freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, related_name='received_freelancer', null=True, blank=True)

    message = models.TextField()
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
class Payment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('paid','Paid'),
        ('pending','Pending')
    ])
class Notification(models.Model):
    freelancer = models.ForeignKey(
        Freelancer,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.freelancer.full_name}"
class SavedJob(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('freelancer', 'job')

    def __str__(self):
        return f"{self.freelancer} saved {self.job.title}"

from django.db import models
from users.models import Freelancer, Recruiter

class Chat(models.Model):
    freelancer = models.ForeignKey(
        Freelancer,
        on_delete=models.CASCADE
    )
    recruiter = models.ForeignKey(
        Recruiter,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('freelancer', 'recruiter')

    def __str__(self):
        return f"Chat {self.freelancer.id} ↔ {self.recruiter.id}"
    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender_type = models.CharField(
        max_length=10,
        choices=[('freelancer', 'Freelancer'), ('recruiter', 'Recruiter')]
    )
    sender_id = models.IntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_type}: {self.text[:20]}"
