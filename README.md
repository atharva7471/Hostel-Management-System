# HostelOS - Smarter Hostel Management

HostelOS is a comprehensive, modern hostel management system designed with a premium SaaS-style UI and built with FastAPI and MongoDB. It provides dual workflows for both **Students** (residents) and **Management**, streamlining hostel operations from student onboarding to room allocation, fee collection, complaints, and maintenance.

## Features

- **Authentication System**: Role-based access control (Student vs Management) using JWT stored in `localStorage`.
- **Student Onboarding Flow**: 
  - Students register and complete their profile preferences.
  - Management reviews, requests changes, approves, and dynamically allocates available rooms and beds.
- **Hostel Identity Generation**: Automatically generates official `Resident IDs` and dynamic Identity Cards for verified residents.
- **Fees & Payments**: Management can generate fee records, and students can view their payment statuses. Dashboard shows collected, pending, and overdue metrics.
- **Complaints & Maintenance**: 
  - Students can raise complaints and maintenance requests categorized by severity.
  - Management can track, assign, and resolve these requests.
- **Notifications & Announcements**: Centralized announcement broadcast system and dynamic notification system for specific actions (e.g., room allocated, complaint updated).
- **Modern UI**: Fully responsive frontend built with Vanilla JS, HTML, and Tailwind CSS. Features dark mode, rich micro-interactions, and Lucide icons.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB (Motor Async Driver)
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (via CDN)
- **Icons**: Lucide Icons

## Prerequisites

- Python 3.10+
- MongoDB instance (Local or Atlas)
- Node.js (optional, if you want a local static server using `npx`, though Python's `http.server` works perfectly)

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository_url>
cd Hostel-Management-System
```

### 2. Backend Setup
Create a virtual environment and install the dependencies:
```bash
python -m venv venv
venv\Scripts\activate  # On macOS/Linux use `source venv/bin/activate`
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your configuration details:
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=hostel_db
SECRET_KEY=your_super_secret_jwt_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 4. Running the Backend
From the root directory, start the FastAPI Uvicorn server:
```bash
uvicorn backend.main:app --reload
```
The API will be available at `http://localhost:8000`. You can view the auto-generated Swagger UI docs at `http://localhost:8000/docs`.

### 5. Running the Frontend
In a new terminal window, navigate to the `frontend` folder and serve the static files:
```bash
cd frontend
python -m http.server 3000
```
Then open your browser and navigate to `http://localhost:3000`.

## Default Credentials
When starting with an empty database, you can use the register page to create a student.
For a management account, you can create a user directly in the database with the role `"MANAGEMENT"`.

## Project Structure
- `/backend`: Contains all FastAPI logic, models (Pydantic), and database connections.
  - `/routes`: Specific API routers (students, hostels, rooms, auth, etc.)
- `/frontend`: Contains all static HTML, JS, and CSS files.
  - `/student`: Pages specifically for the student dashboard and features.
  - `/management`: Pages strictly for management operations.
  - `/js`: Reusable frontend scripts (API fetching, auth verification, etc.)

## License
MIT License
