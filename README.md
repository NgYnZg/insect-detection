# Durian Farm Dashboard

A web-based dashboard for monitoring IoT devices and pest detection in a durian farm, built with Django.

---

## 🚀 Project Overview

The Durian Farm Dashboard is a full-stack web application designed to help farm managers monitor IoT devices, track pest detections, and manage device data efficiently. It provides real-time insights, device management, and user authentication in a modern, responsive interface.

---

## ✨ Features

- **User Authentication**: Secure login, registration, and profile management
- **IoT Device Management**: Add, edit, view, and soft-delete devices
- **Pest Detection Logs**: View detection logs with pest type, confidence, and timestamps
- **Image Log Management**: View images captured by devices
- **Daily Logs Chart**: Interactive line graph of daily detection activity (last 30 days)
- **Responsive UI**: Clean, mobile-friendly design using Bootstrap 4
- **Admin Panel**: Django admin for advanced management
- **Permissions**: Role-based access for device management

---

## 🗂️ Project Structure

```
durian_farm_dashboard/
├── dashboard/           # Main app: views, templates, URLs, device & user management
├── detection/           # Detection logic, models, pest types, image handling
├── durian_farm/         # Project settings, root URLs
├── media/               # Uploaded images and files (served at /media/)
├── Models/              # ML models for pest detection (YOLO)
├── manage.py            # Django management script
└── README.md            # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd durian_farm_dashboard
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Configure Database**
- Default: PostgreSQL (see `durian_farm/settings.py`)
- Update DB credentials as needed

### 4. **Apply Migrations**
```bash
python manage.py migrate
```

### 5. **Create Superuser (Admin)**
```bash
python manage.py createsuperuser
```

### 6. **Run the Development Server**
```bash
python manage.py runserver
```

### 7. **Access the Dashboard**
- Open [http://localhost:8000/](http://localhost:8000/) in your browser

---

## 🧑‍💻 Usage

- **Login/Register**: Access via the login page
- **Dashboard**: View device stats, daily logs chart, and recent detections
- **Devices**: Add, edit, view, or delete IoT devices
- **Device Detail**: See device info, ID, and image logs
- **Detect Insect**: Upload images for pest detection (integrates with ML models)
- **Profile**: Update user info and change password
- **Admin**: Advanced management at `/admin/`

---

## 📊 Data & Media
- **Media files** (images, uploads) are stored in `/media/` and served at `/media/`
- **Device images** are stored in `/media/devices/`
- **Static files** (CSS, JS, logos) are served from `/static/`

---

## 🛡️ Security & Best Practices
- CSRF protection enabled on all forms
- User passwords securely hashed
- Permissions enforced for device management
- Media and static files separated

---

## 📁 Key Files & Directories
- `dashboard/views.py` — Main business logic and views
- `dashboard/templates/` — All HTML templates
- `dashboard/urls.py` — App URL routing
- `detection/models.py` — Device, Image, PestType, Detection models
- `media/` — Uploaded images and files
- `Models/` — ML models for pest detection

---

## 🙏 Credits
- Built with [Django](https://www.djangoproject.com/)
- UI: [Bootstrap 4](https://getbootstrap.com/)
- Charts: [Chart.js](https://www.chartjs.org/)
- Icons: [Font Awesome](https://fontawesome.com/)

---

## 📬 Contact
For questions, suggestions, or contributions, please open an issue or contact the maintainer. 