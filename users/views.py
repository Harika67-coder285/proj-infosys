 
import random
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from .models import Freelancer, Recruiter, OTP,Job,Application
from django.conf import settings
import json
# ---------- Pages ----------
def chatbox(request):
    return render(request,"chatbox.html")
def home(request):
    jobs = Job.objects.filter(is_active=True).order_by('-id')[:3]  # latest 3 jobs
    freelancers = Freelancer.objects.all()
    context = {
        "jobs": jobs,
        "freelancers":freelancers,
        "user_logged_in": "user_id" in request.session
    }
    return render(request, "index.html", context)

def browse_page(request):
    recruiter = Recruiter.objects.get(id=request.session["user_id"])
    freelancers = Freelancer.objects.all()

    # Get all contracts for this recruiter
    contracts = Contract.objects.filter(recruiter=recruiter)
    hired_freelancer_ids = contracts.filter(status="accepted").values_list("freelancer_id", flat=True)
    pending_freelancer_ids = contracts.filter(status="pending").values_list("freelancer_id", flat=True)
    print(hired_freelancer_ids,pending_freelancer_ids)
    context = {
        "freelancers": freelancers,
        "hired_freelancer_ids": list(hired_freelancer_ids),
        "pending_freelancer_ids": list(pending_freelancer_ids)
    }
    return render(request, "browse.html", context)

from django.shortcuts import render
from .models import Freelancer

from django.db.models import Q

def browse_freelancers(request):
    freelancers = Freelancer.objects.all()

    # ---------------- FILTER LOGIC ----------------
    skill = request.GET.get("skill")
    experience = request.GET.get("experience")
    location = request.GET.get("location")
    min_rate = request.GET.get("min_rate")
    max_rate = request.GET.get("max_rate")

    if skill:
        freelancers = freelancers.filter(skills__icontains=skill)

    if experience:
        freelancers = freelancers.filter(experience_level__iexact=experience)

    if location:
        freelancers = freelancers.filter(address__icontains=location)

    if min_rate:
        freelancers = freelancers.filter(hourly_rate__gte=min_rate)

    if max_rate:
        freelancers = freelancers.filter(hourly_rate__lte=max_rate)
    # ------------------------------------------------

    # Default values for guests
    hired_freelancer_ids = []
    pending_freelancer_ids = []
    user_logged_in = False

    # Recruiter logic
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if user_id and account_type == "recruiter":
        user_logged_in = True
        recruiter = Recruiter.objects.get(id=user_id)

        contracts = Contract.objects.filter(recruiter=recruiter)
        hired_freelancer_ids = contracts.filter(
            status="accepted"
        ).values_list("freelancer_id", flat=True)

        pending_freelancer_ids = contracts.filter(
            status="pending"
        ).values_list("freelancer_id", flat=True)

    context = {
        "freelancers": freelancers,
        "hired_freelancer_ids": list(hired_freelancer_ids),
        "pending_freelancer_ids": list(pending_freelancer_ids),
        "user_logged_in": user_logged_in,
    }

    return render(request, "browse.html", context)

from django.shortcuts import render
from .models import Job

def how_it_works_page(request):
    jobs = Job.objects.filter(is_active=True).order_by("-created_at")
    return render(request, "howitworks.html", {"jobs": jobs})

from django.shortcuts import render, redirect
from .models import Freelancer, Recruiter

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import Freelancer, Recruiter


def dashboard(request):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or not account_type:
        return redirect("login_page")

    # Fetch user
    if account_type == "freelancer":
        user = Freelancer.objects.get(id=user_id)
    else:
        user = Recruiter.objects.get(id=user_id)
    return render(request, "dashboard.html", {"app_user": user})


def login_page(request): return render(request, "login.html")
def register_page(request): return render(request, "signup.html")

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import random

from .models import Freelancer, Recruiter, OTP


def verify_otp_page(request):
    email = request.GET.get("email")
    return render(request, "verify_otp.html", {"email": email})


def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        entered_otp = request.POST.get("otp")

        otp_record = OTP.objects.filter(email=email).order_by('-created_at').first()
        if not otp_record:
            return JsonResponse({"status": "error", "message": "OTP not found."})

        if timezone.now() > otp_record.created_at + timedelta(minutes=10):
            otp_record.delete()
            return JsonResponse({"status": "error", "message": "OTP expired."})

        if str(otp_record.code) != str(entered_otp):
            return JsonResponse({"status": "error", "message": "Incorrect OTP."})

        if Freelancer.objects.filter(email=email).exists():
            user = Freelancer.objects.get(email=email)
            account_type = "freelancer"
            redirect_url = "complete-profile"
        else:
            user = Recruiter.objects.get(email=email)
            account_type = "recruiter"
            redirect_url = "recruiter-dashboard"

        user.is_active = True
        user.save()

        request.session['user_id'] = user.id
        request.session['account_type'] = account_type
        if account_type=="freelancer":
            request.session['freelancer_id']=user.id
        else:
            request.session['recruiter_id']=user.id
        otp_record.delete()

        return JsonResponse({
            "status": "success",
            "message": "OTP verified successfully!",
            "redirect_url": redirect_url
        })


def resend_otp(request):
    if request.method == "POST":
        try:
            email = request.POST.get("email")

            if not email:
                return JsonResponse({
                    "status": "error",
                    "message": "Email is required."
                })

            otp_code = str(random.randint(100000, 999999))

            # Save OTP
            OTP.objects.create(
                email=email,
                code=otp_code,
                created_at=timezone.now()
            )

            # Send OTP email
            send_mail(
                subject="SkillConnect OTP Verification",
                message=f"Hello ,\nYour OTP for SkillConnect signup is: {otp_code}\nThis is valid for only 30 seconds.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )

            return JsonResponse({
                "status": "success",
                "message": "A new OTP has been sent to your email."
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            })

    return JsonResponse({
        "status": "error",
        "message": "Invalid request."
    })

from django.core.mail import send_mail
import random

# ---------- Register User ----------

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from .models import Freelancer, Recruiter, OTP
from django.core.mail import send_mail
import random
import pdfplumber
import re
from django.http import JsonResponse


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

from users.models import Freelancer, Recruiter, OTP

@csrf_exempt
def register_user(request):
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        account_type = request.POST.get("account_type")
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Freelancer-specific fields
        experience_level = request.POST.get("experience_level")
        resume = request.FILES.get("resume")
        linkedin = request.POST.get("linkedin")
        hourly_rate = request.POST.get("hourly_rate")
        education = request.POST.get("education")
        tech_stack = request.POST.get("tech_stack")
        skills = request.POST.get("skills")
        dob = request.POST.get("dob")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        photo = request.FILES.get("photo")

        # Basic validation
        if not all([account_type, full_name, email, password]):
            return JsonResponse({"status": "error", "message": "Please fill all required fields."})

        if Freelancer.objects.filter(email=email).exists() or Recruiter.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "User with this email already exists."})

        try:
            hashed_password = make_password(password)

            # Create user
            if account_type == "freelancer":
                SERVICE_FEE_PERCENT = 10
                expected_hourly_rate = float(hourly_rate) if hourly_rate else 0
                service_fee = expected_hourly_rate * SERVICE_FEE_PERCENT / 100
                net_hourly_rate = expected_hourly_rate - service_fee

                user = Freelancer.objects.create(
                    full_name=full_name,
                    email=email,
                    password=hashed_password,
                    experience_level=experience_level,
                    resume=resume,
                    linkedin=linkedin,
                    hourly_rate=hourly_rate if hourly_rate else None,
                    education=education,
                    tech_stack=tech_stack,
                    skills=skills,
                    dob=dob if dob else None,
                    phone=phone,
                    address=address,
                    photo=photo,
                    is_active=False
                )
            elif account_type == "recruiter":
               from PIL import Image, ImageDraw, ImageFont, ImageFilter
               from io import BytesIO
               from django.core.files.base import ContentFile
               from django.conf import settings
               import os
               
               # Get initials (first letter only or first+last)
               name_parts = full_name.strip().split()
               if len(name_parts) >= 2:
                   initials = name_parts[0][0] + name_parts[-1][0]
               else:
                   initials = name_parts[0][0]
               initials = initials.upper()
               
               # Image size
               img_size = 300
               
               # Create transparent image
               img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
               draw = ImageDraw.Draw(img)
               
               # Gradient colors (modern look)
               top_color = (241, 196, 15)   # Gold
               bottom_color = (243, 156, 18)
               
               # Create gradient
               for y in range(img_size):
                   ratio = y / img_size
                   r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                   g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                   b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                   draw.line([(0, y), (img_size, y)], fill=(r, g, b, 255))
               
               # Create circular mask
               mask = Image.new("L", (img_size, img_size), 0)
               mask_draw = ImageDraw.Draw(mask)
               mask_draw.ellipse((0, 0, img_size, img_size), fill=255)
               
               # Apply mask (make it a circle)
               circle_img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
               circle_img.paste(img, (0, 0), mask)
               
               # Load font
               font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "Roboto-Regular.ttf")
               
               font_size = 180
               font = ImageFont.truetype(font_path, font_size)
               
               # Resize font if too big
               while True:
                   bbox = font.getbbox(initials)
                   w = bbox[2] - bbox[0]
                   h = bbox[3] - bbox[1]
                   if w < img_size * 0.7 and h < img_size * 0.7:
                       break
                   font_size -= 4
                   font = ImageFont.truetype(font_path, font_size)
               
               # Center text
               x = (img_size - w) / 2
               y = (img_size - h) / 2
               
               text_layer = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
               text_draw = ImageDraw.Draw(text_layer)
               
               # Soft shadow
               text_draw.text((x+4, y+4), initials, font=font, fill=(0, 0, 0, 100))
               text_draw.text((x, y), initials, font=font, fill=(255, 255, 255, 255))
               
               final_img = Image.alpha_composite(circle_img, text_layer)
               
               # Save to Django
               img_io = BytesIO()
               final_img.save(img_io, format="PNG")
               img_content = ContentFile(img_io.getvalue(), f"{email}_avatar.png")
               
               user = Recruiter.objects.create(
                   full_name=full_name,
                   email=email,
                   password=hashed_password,
                   photo=img_content,
                   is_active=False
               )

            


            else:
                return JsonResponse({"status": "error", "message": "Invalid account type."})

            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            OTP.objects.create(email=email, code=otp_code, created_at=timezone.now())

            # Send OTP via AnyMail (Brevo)
            send_mail(
                subject="SkillConnect OTP Verification",
                message=f"Hello {full_name},\nYour OTP for SkillConnect signup is: {otp_code}\nThis is valid for only 30 seconds.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )

            # Return success
            return JsonResponse({"status": "success","email": email})

        except Exception as e:
            # Catch any error (like file upload or email sending)
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request."})


from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import Freelancer, Recruiter

from django.shortcuts import redirect

def logout_user(request):
    request.session.flush()   # clears all session data
    return redirect('login_page')
from django.shortcuts import render, redirect
from .models import Freelancer
from django.core.files.storage import FileSystemStorage


# ---------------- Login ----------------
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import Freelancer, Recruiter

def login_user(request):
    if request.method == "GET":
        return render(request, "login.html")  # Show login page

    # POST
    account_type = request.POST.get("accountType")
    email = request.POST.get("email")
    password = request.POST.get("password")

    if not all([account_type, email, password]):
        return render(request, "login.html", {"error": "Fill all fields."})

    try:
        # Fetch user based on account type
        if account_type == "freelancer":
            user = Freelancer.objects.get(email=email)
            file="freelancer_dashboard"
        elif account_type == "recruiter":
            user = Recruiter.objects.get(email=email)
            file="recruiter_dashboard"
        else:
            return render(request, "login.html", {"error": "Invalid account type."})

        # Check password
        if not check_password(password, user.password):
            return render(request, "login.html", {"error": "Invalid email or password."})

        # Set session
        request.session['user_id'] = user.id
        request.session['user_name'] = getattr(user, 'full_name', '')
        request.session['account_type'] = account_type
        if account_type=="freelancer":
            request.session['freelancer_email'] = user.email
            request.session['freelancer_id']=user.id
        else:
            request.session['recruiter_id']=user.id

        if account_type == "freelancer" and not user.is_active:
            return redirect("complete_profile")  # freelancer profile incomplete
        return redirect(file)  # recruiter or freelancer completed profile

    except (Freelancer.DoesNotExist, Recruiter.DoesNotExist):
        return render(request, "login.html", {"error": "Invalid email or password."})


from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Freelancer

def complete_profile(request):
    """
    Only for freelancers whose profile is incomplete (is_active=False)
    """
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")
    if account_type=="freelancer":
            request.session['freelancer_id']=user_id
            
    else:
            request.session['recruiter_id']=user_id
    if not user_id or account_type != "freelancer":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "Unauthorized. Please login."})
        return redirect("login_page")

    user = Freelancer.objects.get(id=user_id)
    request.session['freelancer_email']=user.email
    if request.method == "POST":
        try:

            # Get form data
            user.job_role = request.POST.get("job_role") or "Freelancer"
            user.experience_level = request.POST.get("experience_level")
            user.resume = request.FILES.get("resume") or user.resume
            user.tech_stack = request.POST.get("tech_stack")
            user.skills = request.POST.get("skills")
            user.education = request.POST.get("education")
            user.hourly_rate = request.POST.get("hourly_rate")
            user.linkedin = request.POST.get("linkedin")
            user.dob = request.POST.get("dob")
            user.phone = request.POST.get("phone")
            user.address = request.POST.get("address")
            user.photo = request.FILES.get("photo") or user.photo

            user.is_active = True  # mark profile as complete
            user.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "success", "message": "Profile updated successfully!"})
            else:
                return redirect("freelancer_dashboard")

        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": str(e)})
            else:
                return render(request, "complete_profile.html", {"user": user, "error": str(e)})

    return render(request, "complete-profile.html", {"user": user})
from django.shortcuts import render, redirect
from .models import Freelancer, Recruiter

def edit_profile(request):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or not account_type:
        return redirect("login_page")

    # Get the user object
    if account_type == "freelancer":
        user = Freelancer.objects.get(id=user_id)
    else:
        user = Recruiter.objects.get(id=user_id)

    if request.method == "POST":
        # Update fields from form submission
        user.full_name = request.POST.get("full_name", user.full_name)
        user.email = request.POST.get("email", user.email)
        if account_type == "freelancer":
            user.experience_level = request.POST.get("experience_level", user.experience_level)
            user.hourly_rate = request.POST.get("hourly_rate", user.hourly_rate)
            user.education = request.POST.get("education", user.education)
            user.tech_stack = request.POST.get("tech_stack", user.tech_stack)
            user.skills = request.POST.get("skills", user.skills)
            user.linkedin = request.POST.get("linkedin", user.linkedin)
            if "photo" in request.FILES:
                user.photo = request.FILES["photo"]
            if "resume" in request.FILES:
                user.resume = request.FILES["resume"]

        # Save changes
        user.save()
        return redirect("freelancer-dashboard")

    return render(request, "edit_profile.html", {"app_user": user, "account_type": account_type})
# users/views.py
from django.shortcuts import render

def my_projects(request):
    return render(request, "my_projects.html")

def client_requests(request):
    return render(request, "client_requests.html")


def settings_page(request):
    return render(request, "settings_page.html")
# users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Freelancer, Recruiter

def edit_profile_picture(request):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or not account_type:
        return redirect("login_page")

    # Get user object
    user = Freelancer.objects.get(id=user_id) if account_type == "freelancer" else Recruiter.objects.get(id=user_id)

    if request.method == "POST" and "photo" in request.FILES:
        user.photo = request.FILES["photo"]
        user.save()
        if account_type=="freelancer":
            return redirect("freelancer-dashboard")
        return redirect("recruiter-dashboard")
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import User  # Assuming your user model is named User

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from .models import Freelancer  # import your freelancer model

def update_profile(request):
    freelancer_id = request.session.get('user_id')  # session key storing logged-in freelancer ID
    if not freelancer_id:
        # Not logged in
        return redirect(f"{reverse('login_page')}?next={request.path}")

    # Get the freelancer object
    try:
        freelancer = Freelancer.objects.get(id=freelancer_id)
    except Freelancer.DoesNotExist:
        return redirect(f"{reverse('login_page')}?next={request.path}")

    if request.method == "POST":
        # Update profile fields
        freelancer.full_name = request.POST.get("full_name", freelancer.full_name)
        freelancer.email = request.POST.get("email", freelancer.email)
        freelancer.experience_level = request.POST.get("experience_level", freelancer.experience_level)
        freelancer.hourly_rate = request.POST.get("hourly_rate", freelancer.hourly_rate)
        freelancer.tech_stack = request.POST.get("tech_stack", freelancer.tech_stack)
        freelancer.skills = request.POST.get("skills", freelancer.skills)
        freelancer.linkedin = request.POST.get("linkedin", freelancer.linkedin)

        # Update profile picture
        if "photo" in request.FILES:
            freelancer.photo = request.FILES["photo"]

        # Update resume
        if "resume" in request.FILES:
            freelancer.resume = request.FILES["resume"]

        # Update password if provided
        password = request.POST.get("password")
        if password:
            freelancer.password = make_password(password)

        freelancer.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("settings_page")

    return render(request, "settings_page.html", {"app_user": freelancer})

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
import os
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure your Gemini API key here
genai_client = genai.Client(api_key=GEMINI_API_KEY)

import time
@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Please type a message!"})

        bot_reply = "Sorry, something went wrong."
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = genai_client.models.generate_content(
                    model="models/gemini-2.5-flash",  # Free, fast model
                    contents=[user_message]
                )
                bot_reply = response.text
                break  # Success, exit retry loop
            except Exception as e:
                if "503" in str(e):
                    bot_reply = "Bot is busy, retrying..."
                    time.sleep(2)  # wait 2 sec before retry
                    continue
                else:
                    bot_reply = f"Error: {str(e)}"
                    break

        return JsonResponse({"reply": bot_reply})
    
    return JsonResponse({"reply": "Invalid request"}, status=400)
def post_job(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["user_id"])

    if request.method == 'POST':
        Job.objects.create(
            recruiter=recruiter,
            title=request.POST['title'],
            skills=request.POST['skills'],
            work_type=request.POST['work_type'],
            duration=request.POST['duration'],
            experience_level=request.POST['experience_level'],
            payment_type=request.POST['payment_type'],
            description=request.POST.get('description', ''),
            document=request.FILES.get('document')  # matches the form field name
        )
        return redirect('my_jobs')

    return render(request, 'post_job.html')

from django.shortcuts import render, redirect, get_object_or_404
from .models import Application

def recruiter_applications(request, job_id):
    applications = Application.objects.filter(job_id=job_id)

    return render(request, "job_applications.html", {
        "applications": applications
    })


def update_application_status(request, app_id, new_status):
    if request.session.get('account_type') != 'recruiter':
        return redirect('login_page')

    application = get_object_or_404(Application, id=app_id)
    application.status = new_status
    application.save()

    # Optional: notify freelancer
    # Notification.objects.create(
    #     freelancer=application.freelancer,
    #     message=f"Your application for '{application.job.title}' is now {new_status}"
    # )

    return redirect('job_applications', job_id=application.job.id)

def applications(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("home")

    return render(request, "applications.html")

from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, Application, Freelancer, Notification

def apply_job(request, job_id):
    # Only freelancers can apply
    if request.session.get('account_type') != 'freelancer':
        return redirect('login_page')

    freelancer = Freelancer.objects.get(id=request.session['user_id'])
    job = get_object_or_404(Job, id=job_id)

    # Prevent duplicate applications
    existing_application = Application.objects.filter(
        job=job,
        freelancer=freelancer
    ).first()

    if existing_application:
        return redirect('jobs_list')

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')

        # Create Application and store only required freelancer info
        application = Application.objects.create(
            job=job,
            freelancer=freelancer,
            cover_letter=cover_letter,
            freelancer_name=freelancer.full_name,
            freelancer_email=freelancer.email,
            freelancer_resume=freelancer.resume  # make sure resume field exists in Freelancer model
        )

        
        return redirect('jobs_list')

    return render(request, 'apply_job_form.html', {'job': job,'freelancer':freelancer})
from django.shortcuts import render, redirect

def jobs_applied(request):
    if request.session.get("account_type") != "freelancer":
        return redirect("login_page")

    freelancer = Freelancer.objects.get(id=request.session["user_id"])

    applications = Application.objects.filter(
        freelancer=freelancer
    ).select_related("job").order_by("-applied_at")

    return render(request, "jobs_applied.html", {
        "applications": applications
    })


def my_jobs(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["user_id"])
    jobs = Job.objects.filter(recruiter=recruiter)

    context = {
        "jobs": jobs,
        "job_count": jobs.count()  # ✅ FIX
    }
    return render(request, "my_jobs.html", context)
from users.models import Job, Application, Freelancer,SavedJob

from django.db.models import Q

from django.db.models import Q

def jobs_list(request):
    jobs = Job.objects.filter(is_active=True)

    applied_job_ids = []
    saved_job_ids = []
    user_logged_in = False

    # 🔍 FILTERS
    q = request.GET.get("q")
    work_type = request.GET.get("work_type")
    experience = request.GET.get("experience")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(skills__icontains=q) |
            Q(description__icontains=q)
        )

    if work_type:
        jobs = jobs.filter(work_type=work_type)

    if experience:
        jobs = jobs.filter(experience_level=experience)

    # 👤 LOGIN CHECK
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if user_id and account_type == "freelancer":
        user_logged_in = True
        freelancer = Freelancer.objects.get(id=user_id)

        applied_job_ids = Application.objects.filter(
            freelancer=freelancer
        ).values_list("job_id", flat=True)

        saved_job_ids = SavedJob.objects.filter(
            freelancer=freelancer
        ).values_list("job_id", flat=True)

    context = {
        "jobs": jobs,
        "applied_job_ids": applied_job_ids,
        "saved_job_ids": saved_job_ids,
        "user_logged_in": user_logged_in,
    }

    return render(request, "jobs_list.html", context)

def job_applications(request, job_id):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter_id = request.session.get("user_id")
    job = Job.objects.get(id=job_id, recruiter_id=recruiter_id)

    applications = Application.objects.filter(job=job)

    return render(request, "job_applications.html", {"job": job, "applications": applications})

from django.shortcuts import render, get_object_or_404, redirect

def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.skills = request.POST.get("skills")
        job.work_type = request.POST.get("work_type")
        job.duration = request.POST.get("duration")
        job.experience_level = request.POST.get("experience_level")
        job.payment_type = request.POST.get("payment_type")
        job.description = request.POST.get("description")
        
        # Handle uploaded file
        if request.FILES.get("document"):
            job.document = request.FILES["document"]
        
        job.save()
        return redirect("my_jobs")  # Redirect to jobs list

    return render(request, "edit_job.html", {"job": job})
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import Job

def delete_job(request, job_id):
    # Only recruiters
    if request.session.get("account_type") != "recruiter":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    recruiter_id = request.session.get("user_id")

    # Get the job
    job = get_object_or_404(Job, id=job_id, recruiter_id=recruiter_id)

    if request.method == "POST":
        job.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

from django.shortcuts import render
from .models import Freelancer

def search_freelancers(request):
    freelancers = Freelancer.objects.filter(is_active=True)

    skill = request.GET.get('skill')
    experience = request.GET.get('experience')
    location = request.GET.get('location')
    hourly_rate = request.GET.get('hourly_rate')

    if skill:
        freelancers = freelancers.filter(skills__icontains=skill)

    if experience:
        freelancers = freelancers.filter(experience_level=experience)

    if location:
        freelancers = freelancers.filter(location__icontains=location)

    if hourly_rate:
        freelancers = freelancers.filter(hourly_rate__lte=hourly_rate)

    context = {
        'freelancers': freelancers
    }
    return render(request, 'search_freelancers.html', context)



def interviews(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("home")

    interviews = Interview.objects.select_related(
        "application",
        "application__freelancer",
        "application__job"
    ).all()

    return render(request, "interviews.html", {
        "interviews": interviews
    })

from .models import Interview

def schedule_interview(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    if request.method == "POST":
        Interview.objects.create(
            application=application,
            interview_date=request.POST.get("date"),
            interview_time=request.POST.get("time"),
            mode=request.POST.get("mode")
        )

        application.status = "interview"
        application.save()

        return redirect("recruiter_applications", job_id=application.job.id)

    return render(request, "schedule_interview.html", {
        "application": application
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Freelancer, Contract, Recruiter
from .models import Notification

from .models import Notification

# views.py
def create_direct_contract(request, freelancer_id):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["user_id"])
    freelancer = Freelancer.objects.get(id=freelancer_id)

    if request.method == "POST":
        contract = Contract.objects.create(
            recruiter=recruiter,
            freelancer=freelancer,
            payment_type=request.POST["payment_type"],
            agreed_amount=request.POST["amount"],
            start_date=request.POST["start_date"],
            status="pending",
            is_active=False
        )

        # 🔔 Notify freelancer
        Notification.objects.create(
            freelancer=freelancer,
            message=f"{recruiter.full_name} sent you a contract offer"
        )

        # Redirect to browse page to refresh the status
        return redirect("contracts")  # instead of 'contracts'

    return render(request, "create_direct_contract.html", {"freelancer": freelancer})
from django.shortcuts import render, redirect
from django.db.models import Count
from .models import Application, Contract, Freelancer

def freelancer_dashboard(request):
    if request.session.get('account_type') != 'freelancer':
        return redirect('login_page')

    freelancer = Freelancer.objects.get(id=request.session['user_id'])

    # Job applications
    applied = Application.objects.filter(freelancer=freelancer).count()
    shortlisted = Application.objects.filter(
        freelancer=freelancer, status='shortlisted'
    ).count()
    interviews = Application.objects.filter(
        freelancer=freelancer, status='interview'
    ).count()
    accepted = Application.objects.filter(
        freelancer=freelancer, status='accepted'
    ).count()
    rejected = Application.objects.filter(
        freelancer=freelancer, status='rejected'
    ).count()

    # Contracts
    active_contracts = Contract.objects.filter(
        freelancer=freelancer, is_active=True
    ).count()

    context = {
        'applied': applied,
        'shortlisted': shortlisted,
        'interviews': interviews,
        'accepted': accepted,
        'rejected': rejected,
        'active_contracts': active_contracts
    }

    return render(request, 'freelancer_dashboard.html', context)

def accept_contract(request, contract_id):
    if request.session.get("account_type") != "freelancer":
        return redirect("login_page")

    contract = Contract.objects.get(id=contract_id)
    contract.status = "accepted"
    contract.is_active = True
    contract.save()

    return redirect("freelancer_contracts")


def reject_contract(request, contract_id):
    if request.session.get("account_type") != "freelancer":
        return redirect("login_page")

    contract = Contract.objects.get(id=contract_id)
    contract.status = "rejected"
    contract.is_active = False
    contract.save()

    return redirect("freelancer_contracts")
def recruiter_contracts(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["user_id"])
    contracts = Contract.objects.filter(recruiter=recruiter)

    return render(request, "contracts.html", {
        "contracts": contracts
    })

def freelancer_contracts(request):
    if request.session.get("account_type") != "freelancer":
        return redirect("login_page")

    freelancer_id = request.session["user_id"]

    contracts = Contract.objects.filter(freelancer_id=freelancer_id)

    return render(request, "freelancer_contracts.html", {
        "contracts": contracts
    })


def contract_action(request, contract_id):
    if request.session.get("account_type") != "freelancer":
        return redirect("login_page")

    contract = Contract.objects.get(id=contract_id)

    action = request.GET.get("action")

    if action == "accept":
        contract.status = "accepted"
        contract.is_active = True
        contract.save()

    elif action == "reject":
        contract.status = "rejected"
        contract.is_active = False
        contract.save()

    return redirect("freelancer_contracts")

def recruiter_dashboard(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    # Get Recruiter object from session
    try:
        recruiter_obj = Recruiter.objects.get(id=request.session["user_id"])
    except Recruiter.DoesNotExist:
        return redirect("login_page")  # or show an error page

    # Jobs posted by this recruiter
    jobs = Job.objects.filter(recruiter=recruiter_obj)
    jobs_count = jobs.count()

    # Applications related to this recruiter's jobs
    applications = Application.objects.filter(job__recruiter=recruiter_obj)

    total_proposals = applications.count()
    pending_proposals = applications.filter(status="applied").count()
    shortlisted = applications.filter(status="shortlisted").count()
    accepted = applications.filter(status="accepted").count()
    rejected = applications.filter(status="rejected").count()

    # Pending contracts (offers sent but not accepted)
    pending_offers = Contract.objects.filter(recruiter=recruiter_obj, status="pending").count()

    context = {
        "jobs_count": jobs_count,
        "total_proposals": total_proposals,
        "pending_proposals": pending_proposals,
        "shortlisted": shortlisted,
        "accepted": accepted,
        "rejected": rejected,
        "pending_offers": pending_offers,
    }

    return render(request, "recruiter_dashboard.html", context)

def reports(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])

    payments = Payment.objects.filter(contract__recruiter=recruiter)

    total_paid = payments.filter(status="paid").aggregate(models.Sum("amount"))["amount__sum"] or 0
    pending = payments.filter(status="pending").aggregate(models.Sum("amount"))["amount__sum"] or 0

    return render(request, "reports.html", {
        "payments": payments,
        "total_paid": total_paid,
        "pending": pending
    })

from django.contrib.auth.decorators import login_required
from .models import Contract

@login_required
def hired_talent(request):
    contracts = Contract.objects.filter(
        recruiter=request.user
    ).select_related('freelancer')

    return render(request, 'hired_talent.html', {
        'contracts': contracts
    })
from django.shortcuts import render, redirect
from .models import Recruiter,Job, Application, Contract

def analysis_dashboard(request):
    # Only allow recruiters
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    # Get Recruiter object from session
    try:
        recruiter_obj = Recruiter.objects.get(id=request.session["user_id"])
    except Recruiter.DoesNotExist:
        return redirect("login_page")  # or show an error page

    # Jobs posted by this recruiter
    jobs = Job.objects.filter(recruiter=recruiter_obj)
    jobs_count = jobs.count()

    # Applications related to this recruiter's jobs
    applications = Application.objects.filter(job__recruiter=recruiter_obj)

    total_proposals = applications.count()
    pending_proposals = applications.filter(status="applied").count()
    shortlisted = applications.filter(status="shortlisted").count()
    accepted = applications.filter(status="accepted").count()
    rejected = applications.filter(status="rejected").count()

    # Pending contracts (offers sent but not accepted)
    pending_offers = Contract.objects.filter(recruiter=recruiter_obj, status="pending").count()

    context = {
        "jobs_count": jobs_count,
        "total_proposals": total_proposals,
        "pending_proposals": pending_proposals,
        "shortlisted": shortlisted,
        "accepted": accepted,
        "rejected": rejected,
        "pending_offers": pending_offers,
    }

    return render(request, "analysis.html", context)

from django.shortcuts import render
from django.db.models import Count
from .models import Job, Application, Recruiter

def recruiter_analysis(request):
    recruiter = Recruiter.objects.get(email=request.session.get("email"))

    jobs = Job.objects.filter(recruiter=recruiter)

    total_jobs = jobs.count()

    total_proposals = Application.objects.filter(job__in=jobs).count()

    pending_proposals = Application.objects.filter(
        job__in=jobs,
        status__in=['applied', 'shortlisted', 'interview']
    ).count()

    accepted_proposals = Application.objects.filter(
        job__in=jobs,
        status='accepted'
    ).count()

    rejected_proposals = Application.objects.filter(
        job__in=jobs,
        status='rejected'
    ).count()

    context = {
        'total_jobs': total_jobs,
        'total_proposals': total_proposals,
        'pending_proposals': pending_proposals,
        'accepted_proposals': accepted_proposals,
        'rejected_proposals': rejected_proposals,
    }

    return render(request, 'recruiter_analysis.html', context)
from django.shortcuts import render, redirect, get_object_or_404
from .models import Message, Recruiter, Freelancer
from django.db.models import Q


from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Payment, Contract


def financial_reports(request, recruiter_id):
    today = timezone.now()
    week_start = today - timedelta(days=7)

    # Weekly summary
    weekly_payments = Payment.objects.filter(
        contract__recruiter_id=recruiter_id,
        paid_on__gte=week_start
    )

    weekly_total_paid = weekly_payments.filter(status='paid').aggregate(
        total=models.Sum('amount')
    )['total'] or 0

    weekly_pending = weekly_payments.filter(status='pending').aggregate(
        total=models.Sum('amount')
    )['total'] or 0

    # Transaction history
    transactions = Payment.objects.filter(
        contract__recruiter_id=recruiter_id
    ).order_by('-paid_on')

    # Overall totals
    total_paid = Payment.objects.filter(
        contract__recruiter_id=recruiter_id,
        status='paid'
    ).aggregate(total=models.Sum('amount'))['total'] or 0

    total_pending = Payment.objects.filter(
        contract__recruiter_id=recruiter_id,
        status='pending'
    ).aggregate(total=models.Sum('amount'))['total'] or 0

    return render(request, "reports.html", {
        "weekly_total_paid": weekly_total_paid,
        "weekly_pending": weekly_pending,
        "transactions": transactions,
        "total_paid": total_paid,
        "total_pending": total_pending
    })
from django.shortcuts import render
from django.db.models import Sum
from .models import Contract, Timesheet


def work_dashboard(request, recruiter_id):
    # Active contracts
    active_contracts = Contract.objects.filter(
        recruiter_id=recruiter_id,
        is_active=True
    )

    # Completed contracts
    completed_contracts = Contract.objects.filter(
        recruiter_id=recruiter_id,
        is_active=False
    )

    return render(request, "work_dashboard.html", {
        "active_contracts": active_contracts,
        "completed_contracts": completed_contracts,
    })

def contracts(request):
    if request.session.get("account_type") != "recruiter":
        return redirect("login_page")

    recruiter = Recruiter.objects.get(id=request.session["user_id"])
    contracts = Contract.objects.filter(recruiter=recruiter)

    return render(request, "contracts.html", {
        "contracts": contracts
    })
def messages(request):
    return render(request, "messages.html")

def contract_timesheets(request, contract_id):
    timesheets = Timesheet.objects.filter(contract_id=contract_id)

    total_hours = timesheets.aggregate(
        total=Sum('hours_worked')
    )['total'] or 0

    return render(request, "timesheets.html", {
        "timesheets": timesheets,
        "total_hours": total_hours
    })
from .models import Message

def chat(request, recruiter_id, freelancer_id):
    messages = Message.objects.filter(
        sender_recruiter_id=recruiter_id,
        receiver_freelancer_id=freelancer_id
    ) | Message.objects.filter(
        sender_freelancer_id=freelancer_id,
        receiver_recruiter_id=recruiter_id
    )

    messages = messages.order_by("created_at")

    if request.method == "POST":
        Message.objects.create(
            sender_recruiter_id=recruiter_id,
            receiver_freelancer_id=freelancer_id,
            message=request.POST.get("message"),
            file=request.FILES.get("file")
        )
        return redirect("chat", recruiter_id=recruiter_id, freelancer_id=freelancer_id)

    return render(request, "chat.html", {
        "messages": messages
    })
from .models import Contract, Freelancer

def freelancer_notifications(request):
    if request.session.get("account_type") == "freelancer":
        freelancer_id = request.session.get("user_id")
        count = Contract.objects.filter(
            freelancer_id=freelancer_id,
            status="pending"
        ).count()
        return {"pending_contracts_count": count}

    return {"pending_contracts_count": 0}
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def toggle_save_job(request, job_id):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or account_type != "freelancer":
        return redirect("login_page")

    freelancer = Freelancer.objects.get(id=user_id)
    job = get_object_or_404(Job, id=job_id)

    saved = SavedJob.objects.filter(freelancer=freelancer, job=job)

    if saved.exists():
        saved.delete()
        messages.info(request, "Job removed from saved")
    else:
        SavedJob.objects.create(freelancer=freelancer, job=job)
        messages.success(request, "Job saved")

    return redirect(request.META.get("HTTP_REFERER", "jobs_list"))
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from django.shortcuts import redirect, get_object_or_404
from .models import SavedJob, Job, Freelancer

def save_job(request, job_id):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or account_type != "freelancer":
        return redirect("login_page")

    freelancer = get_object_or_404(Freelancer, id=user_id)
    job = get_object_or_404(Job, id=job_id)

    saved_job = SavedJob.objects.filter(
        freelancer=freelancer,
        job=job
    ).first()

    if saved_job:
        # 🔥 UNSAVE → DELETE FROM DB
        saved_job.delete()
    else:
        # ⭐ SAVE
        SavedJob.objects.create(
            freelancer=freelancer,
            job=job
        )

    return redirect(request.META.get("HTTP_REFERER", "jobs_list"))
def saved_jobs(request):
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if not user_id or account_type != "freelancer":
        return redirect("login_page")

    freelancer = Freelancer.objects.get(id=user_id)

    saved_jobs = SavedJob.objects.filter(
        freelancer=freelancer
    ).select_related("job")

    applied_job_ids = Application.objects.filter(
        freelancer=freelancer
    ).values_list("job_id", flat=True)

    context = {
        "saved_jobs": saved_jobs,
        "applied_job_ids": applied_job_ids
    }

    return render(request, "saved_jobs.html", context)

def jobs_list(request):
    jobs = Job.objects.filter(is_active=True)

    applied_job_ids = []
    saved_job_ids = []
    user_logged_in = False

    # 🔍 FILTERS
    q = request.GET.get("q")
    work_type = request.GET.get("work_type")
    experience = request.GET.get("experience")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(skills__icontains=q) |
            Q(description__icontains=q)
        )

    if work_type:
        jobs = jobs.filter(work_type=work_type)

    if experience:
        jobs = jobs.filter(experience_level=experience)

    # 👤 LOGIN CHECK
    user_id = request.session.get("user_id")
    account_type = request.session.get("account_type")

    if user_id and account_type == "freelancer":
        user_logged_in = True
        freelancer = Freelancer.objects.get(id=user_id)

        applied_job_ids = Application.objects.filter(
            freelancer=freelancer
        ).values_list("job_id", flat=True)

        saved_job_ids = SavedJob.objects.filter(
            freelancer=freelancer
        ).values_list("job_id", flat=True)

    context = {
        "jobs": jobs,
        "applied_job_ids": applied_job_ids,
        "saved_job_ids": saved_job_ids,
        "user_logged_in": user_logged_in,
    }

    return render(request, "jobs_list.html", context)
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner
from django.shortcuts import render
from .models import Freelancer, Recruiter

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        signer = TimestampSigner()

        user = None
        user_type = None

        try:
            user = Freelancer.objects.get(email=email)
            user_type = "freelancer"
        except Freelancer.DoesNotExist:
            try:
                user = Recruiter.objects.get(email=email)
                user_type = "recruiter"
            except Recruiter.DoesNotExist:
                return render(request, "forgot_password.html", {
                    "error": "Email not registered"
                })

        token = signer.sign(user.id)

        reset_link = request.build_absolute_uri(
            f"/reset-password/{user_type}/{token}/"
        )

        send_mail(
            subject="Reset Your SkillConnect Password",
            message=f"Click the link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        return render(request, "forgot_password.html", {
            "success": "Password reset link sent to your email"
        })

    return render(request, "forgot_password.html")
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from .models import Freelancer, Recruiter

def reset_password(request, user_type, token):
    signer = TimestampSigner()

    try:
        user_id = signer.unsign(token, max_age=900)  # 15 minutes

        if user_type == "freelancer":
            user = Freelancer.objects.get(pk=user_id)
        else:
            user = Recruiter.objects.get(pk=user_id)

    except (BadSignature, SignatureExpired):
        return render(request, "reset_password.html", {
            "error": "Link expired or invalid"
        })

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            return render(request, "reset_password.html", {
                "error": "Passwords do not match"
            })

        # ✅ HASH PASSWORD
        user.password = make_password(password)
        user.save()

        return redirect("login_page")

    return render(request, "reset_password.html")
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Message

from django.shortcuts import render, get_object_or_404
from users.models import Freelancer, Recruiter

def chat_room(request, other_user_id, other_user_type):
    """
    other_user_type: 'freelancer' or 'recruiter'
    """
    if other_user_type == 'freelancer':
        other_user = get_object_or_404(Freelancer, id=other_user_id)
    elif other_user_type == 'recruiter':
        other_user = get_object_or_404(Recruiter, id=other_user_id)
    else:
        return HttpResponse("Invalid user type", status=400)

    return render(request, "chat_room.html", {"other_user": other_user})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from users.models import Message, User

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


from django.http import JsonResponse
from .models import Message
from django.contrib.auth.models import User

def fetch_messages(request, receiver_id):
    user = request.user  # current logged-in user
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return JsonResponse([], safe=False)  # return empty list if no user

    # Fetch messages between current user and receiver
    messages = Message.objects.filter(
        sender=user, receiver=receiver
    ) | Message.objects.filter(
        sender=receiver, receiver=user
    )
    messages = messages.order_by("timestamp")

    # Serialize messages
    data = []
    for msg in messages:
        data.append({
            "sender": msg.sender.username,
            "receiver": msg.receiver.username,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse(data, safe=False)

from django.shortcuts import render
from users.models import Recruiter

def list_recruiters(request):
    # Fetch all active recruiters
    recruiters = Recruiter.objects.all()
    return render(request, "list_recruiters.html", {"recruiters": recruiters})
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Freelancer
from django.shortcuts import render, redirect
from .models import Freelancer
from .forms import FreelancerForm,RecruiterSettingsForm

def freelancer_settings(request):
    # ✅ get logged-in freelancer using session
    email = request.session.get('freelancer_email')

    if not email:
        return redirect('login_page')

    freelancer = Freelancer.objects.get(email=email)

    if request.method == 'POST':
        form = FreelancerForm(
            request.POST,
            request.FILES,
            instance=freelancer   
        )

        if form.is_valid():
            form.save()
            return redirect('freelancer_dashboard')
        else:
            print(form.errors)   # debug

    else:
        form = FreelancerForm(instance=freelancer)

    return render(request, 'settings_page.html', {
        'form': form,
        'freelancer': freelancer
    })
from django.shortcuts import render, redirect
from .models import Recruiter
from .forms import RecruiterSettingsForm

def recruiter_settings(request):
    recruiter_id = request.session.get('recruiter_id')

    if not recruiter_id:
        return redirect('login_page')  # safety

    recruiter = Recruiter.objects.get(id=recruiter_id)

    if request.method == 'POST':
        form = RecruiterSettingsForm(request.POST, instance=recruiter)
        if form.is_valid():
            form.save()
            return redirect('recruiter_dashboard')  # ✅ prevents resubmission
    else:
        form = RecruiterSettingsForm(instance=recruiter)

    return render(request, 'settings2.html', {'form': form})
from .models import Chat, Message
from users.models import Freelancer, Recruiter

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Chat, Message
from users.models import Freelancer, Recruiter

def chat_view(request, freelancer_id, recruiter_id):
    freelancer = get_object_or_404(Freelancer, id=freelancer_id)
    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    chat, created = Chat.objects.get_or_create(
        freelancer=freelancer,
        recruiter=recruiter
    )

    messages = chat.messages.order_by('created_at')

    # 👇 detect who is logged in
    if request.session.get('freelancer_id'):
        current_user_type = 'freelancer'
        current_user_id = request.session.get('freelancer_id')
    else:
        current_user_type = 'recruiter'
        current_user_id = request.session.get('recruiter_id')

    return render(request, 'chat.html', {
        'chat': chat,
        'messages': messages,
        'current_user_type': current_user_type,
        'current_user_id': current_user_id,
        'freelancer_id': freelancer_id,
        'recruiter_id': recruiter_id,
    })

def send_message(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        sender_type = request.POST.get('sender_type')
        sender_id = request.POST.get('sender_id')
        text = request.POST.get('text')

        chat = Chat.objects.get(id=chat_id)

        msg = Message.objects.create(
            chat=chat,
            sender_type=sender_type,
            sender_id=sender_id,
            text=text
        )

        return JsonResponse({
            'status': 'success',
            'message': msg.text,
            'sender_type': msg.sender_type
        })

from .models import Chat
from users.models import Freelancer, Recruiter

def chat_list_view(request):

    if hasattr(request.user, 'freelancer'):
        freelancer = request.user.freelancer

        chats = Chat.objects.filter(
            freelancer=freelancer
        ).select_related('recruiter')

        role = 'freelancer'

    elif hasattr(request.user, 'recruiter'):
        recruiter = request.user.recruiter

        chats = Chat.objects.filter(
            recruiter=recruiter
        ).select_related('freelancer')

        role = 'recruiter'

    return render(request, 'chat_list.html', {
        'chats': chats,
        'role': role
    })
from django.shortcuts import render, redirect, get_object_or_404
from .models import Chat
from users.models import Freelancer

def freelancer_chat_list(request):
    freelancer_id = request.session.get('freelancer_id')

    if not freelancer_id:
        return redirect('login_user')

    freelancer = get_object_or_404(Freelancer, id=freelancer_id)

    chats = Chat.objects.filter(freelancer=freelancer).order_by('-created_at')

    chat_data = []
    for chat in chats:
        last_msg = chat.messages.order_by('-created_at').first()
        chat_data.append({
            'recruiter': chat.recruiter,
            'chat': chat,
            'last_message': last_msg.text if last_msg else ''
        })

    return render(request, 'freelancer_chat_list.html', {
        'chat_data': chat_data,
        'freelancer_id': freelancer_id
    })
from django.shortcuts import render, redirect, get_object_or_404
from users.models import Recruiter
from .models import Chat

from django.shortcuts import render, redirect, get_object_or_404
from users.models import Recruiter
from .models import Chat

def recruiter_chat_list(request):
    recruiter_id = request.session.get('recruiter_id')

    if not recruiter_id:
        return redirect('login_user')

    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    chats = Chat.objects.filter(recruiter=recruiter).order_by('-created_at')

    chat_data = []
    for chat in chats:
        last_msg = chat.messages.order_by('-created_at').first()
        chat_data.append({
            'freelancer': chat.freelancer,
            'chat': chat,
            'last_message': last_msg.text if last_msg else ''
        })

    return render(request, 'recruiter_chat_list.html', {
        'chat_data': chat_data,
        'recruiter_id': recruiter_id
    })
from django.shortcuts import render, redirect, get_object_or_404
from .models import Chat
from users.models import Freelancer, Recruiter

def combined_chat_view(request, chat_id=None):

    # detect logged-in user
    if request.session.get('freelancer_id'):
        current_user_type = 'freelancer'
        current_user_id = request.session.get('freelancer_id')
        chats = Chat.objects.filter(freelancer_id=current_user_id)
    elif request.session.get('recruiter_id'):
        current_user_type = 'recruiter'
        current_user_id = request.session.get('recruiter_id')
        chats = Chat.objects.filter(recruiter_id=current_user_id)
    else:
        return redirect('login_user')

    selected_chat = None
    messages = []

    if chat_id:
        selected_chat = get_object_or_404(Chat, id=chat_id)
        messages = selected_chat.messages.order_by('created_at')

    return render(request, "chats_page.html", {
        "chats": chats,
        "selected_chat": selected_chat,
        "messages": messages,
        "current_user_type": current_user_type,
        "current_user_id": current_user_id
    })
from django.shortcuts import redirect, get_object_or_404
from .models import Chat
from users.models import Freelancer, Recruiter

def start_chat(request, user_id):
    # Freelancer must be logged in
    if request.session.get('account_type')=="freelancer":
        freelancer_id = request.session.get('freelancer_id')
        recruiter_id=user_id
    else:
        recruiter_id=request.session.get('recruiter_id')  
        freelancer_id=user_id  
    
    if not freelancer_id or not recruiter_id:
        return redirect('login_page')

    freelancer = get_object_or_404(Freelancer, id=freelancer_id)
    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    # Create or get chat
    chat, created = Chat.objects.get_or_create(
        freelancer=freelancer,
        recruiter=recruiter
    )

    # Redirect to chat list with selected chat
    return redirect(f"/chats/{chat.id}/")
