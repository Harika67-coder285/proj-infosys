# SkillConnect 🚀

> **Live Demo:** [https://proj-infosys.onrender.com](https://proj-infosys.onrender.com)

SkillConnect is a comprehensive web platform designed to bridge the gap between freelancers and recruiters. It facilitates seamless skill matching, job posting, and application management, empowering users to connect and collaborate effectively.

## ✨ Features

- **User Roles:** Dedicated dashboards for **Freelancers** and **Recruiters**.
- **Job Management:**
  - Recruiters can post, edit, and manage job listings.
  - Freelancers can browse, filter, and apply for jobs.
- **Smart Matching:** Skill-based matching to connect the right talent with the right opportunities.
- **AI Integration:** Powered by **Google Gemini** for enhanced features (e.g., content generation, recommendations).
- **Application Tracking:** Track the status of job applications in real-time.
- **Modern UI:** Built with **HTML,CSS and JS** for a responsive and visually appealing experience.
- **Secure Authentication:** CSRF-based authentication for secure access.

## 🛠️ Tech Stack

### Frontend
- **HTML** (Structured Markup Language)
- **CSS** (Styling)

### Backend
- **Django** & **Django REST Framework**
- **Simple CSRF** (Authentication)
- **SQLite** Production Database / Dev
- **WhiteNoise** (Static File Serving)
- **Google Generative AI SDK**

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
- Python 3.12+
- Django

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---


*Verified Live Deployment:* [https://proj-infosys.onrender.com](https://proj-infosys.onrender.com)
