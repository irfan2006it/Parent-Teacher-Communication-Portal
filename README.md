# Parent–Teacher Communication Portal
**A College Lab Micro Project in Python Flask & MongoDB Atlas**

---

## 1. Project Objective
The **Parent–Teacher Communication Portal** is a lightweight, responsive web application designed for academic institutions to facilitate seamless communication and academic record sharing between parents, teachers, and school administration. 

This project demonstrates core full-stack software development principles required for college lab curriculum and viva evaluation:
- **Python Flask** web framework and routing
- **Flask-Login** session-based user authentication and access control
- **MongoDB Atlas** NoSQL cloud database integration
- **PyMongo** CRUD (Create, Read, Update, Delete) operations
- **Role-Based Access Control (RBAC)** across Admin, Teacher, and Parent roles
- **Bootstrap 5 & Clean UI** for a modern, responsive layout

---

## 2. Key Features

###  Admin Role (`/admin/dashboard`)
- **Executive Analytics:** Overview cards for total students, faculty teachers, and registered parents.
- **Student Management:** Full CRUD (Enrol, View, Edit, Delete) with linkage to parents and class teachers.
- **Teacher Management:** Register and view teaching staff accounts.
- **Parent Management:** Register and view parent accounts linked to enrolled children.

###  Teacher Role (`/teacher/dashboard`)
- **Classroom Roster:** View only students assigned to the logged-in teacher.
- **Daily Attendance Marking:** Record `Present` or `Absent` with date selection and automatic **duplicate-prevention logic** (prevents recording duplicate attendance for the same student on the same date).
- **Marks & Assessment Entry:** Input marks obtained and total marks per subject and exam; calculate percentage automatically; edit and delete mark records.
- **Parent Communication:** View student conversation threads and send direct replies to parent queries.

###  Parent Role (`/parent/dashboard`)
- **Child Information:** Real-time profile details of child and assigned class teacher.
- **Dynamic Attendance Metrics:** Overall attendance percentage dynamically computed from database records (`Total Days`, `Present`, `Absent`).
- **Academic Performance Tracker:** Examination breakdown (`Subject`, `Exam`, `Score`, `Percentage`) with grade indicators.
- **Direct Messaging:** Send questions and feedback directly to the child's class teacher.

---

## 3. Technology Stack

- **Backend:** Python 3, Flask, Flask-Login, PyMongo, python-dotenv, Werkzeug
- **Database:** MongoDB Atlas (Cloud NoSQL)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons

---

## 4. Database Structure (`parent_teacher_portal`)

The project uses five distinct MongoDB collections:
1. `users` — Stores login accounts with hashed passwords and user roles (`admin`, `teacher`, `parent`).
2. `students` — Stores student records (`student_id`, `name`, `class`, `section`, `parent_id`, `teacher_id`).
3. `attendance` — Stores daily attendance records (`student_id`, `date`, `status: Present/Absent`).
4. `marks` — Stores examination scores (`student_id`, `subject`, `exam`, `marks`, `total`).
5. `messages` — Stores direct communication (`sender_id`, `receiver_id`, `student_id`, `message`, `timestamp`, `is_read`).

---

## 5. MongoDB Atlas Setup Guide

To connect the application to your MongoDB Atlas cloud database:

1. **Create an Account:** Visit [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and sign up for a free tier account.
2. **Deploy Free Cluster:** Create a free M0 cluster (e.g. `Cluster0`).
3. **Database User:** Under **Security > Database Access**, create a user (e.g. `portal_user`) and set a secure password.
4. **Network Access:** Under **Security > Network Access**, click **Add IP Address** and choose **Allow Access from Anywhere (`0.0.0.0/0`)** or your current IP.
5. **Get Connection String:** Click **Database > Connect > Drivers > Python (3.6 or later)** and copy the connection URI:
   ```text
   mongodb+srv://<username>:<password>@cluster0.mongodb.net/parent_teacher_portal?retryWrites=true&w=majority
   ```
6. **Update `.env`:** Paste your connection string into `.env`:
   ```env
   MONGO_URI=mongodb+srv://portal_user:YourPassword123@cluster0.mongodb.net/parent_teacher_portal?retryWrites=true&w=majority
   SECRET_KEY=ptportal_college_secret_key_2026
   ```

*(Note: The project includes an intelligent fallback mechanism for local or offline demonstration if the Atlas connection is not configured or internet is unavailable during evaluation).*

---

## 6. Installation & Execution

### Step 1: Open Terminal in the Project Directory
```bash
cd parent_teacher_portal
```

### Step 2: Create and Activate Virtual Environment (Recommended)
**Windows (PowerShell/CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed Sample Demonstration Data
Run the seeding script to populate sample accounts, students, attendance, marks, and messages:
```bash
python seed_database.py
```

### Step 5: Start the Flask Application
```bash
python app.py
```

### Step 6: Access the Application
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 7. Demo Login Credentials (For Viva / Lab Evaluation)

| Role | Email | Password | Quick Features to Test |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@ptportal.com` | `Admin@123` | Add Student, Add Teacher, Add Parent, Assign relations |
| **Teacher** | `teacher@ptportal.com` | `Teacher@123` | Mark Attendance, Add Marks, Reply to Parent Messages |
| **Parent** | `parent@ptportal.com` | `Parent@123` | View Child, Check Attendance %, View Marks %, Send Message |

*(Tip: The login page includes 1-click **Quick Demo Account** buttons to instantly fill credentials during live lab demonstrations!)*

---

## 8. Complete Demonstration Workflow

Follow this step-by-step path to demonstrate the entire application flow:

1. **Admin Workflow:**
   - Log in as Admin (`admin@ptportal.com` / `Admin@123`).
   - Navigate to **Students** > Click **Add New Student** > Register a new student and assign them to `Prof. John Sharma` and `Ramesh Kumar`.
   - Verify the student appears on the list.

2. **Teacher Workflow:**
   - Sign out and log in as Teacher (`teacher@ptportal.com` / `Teacher@123`).
   - Go to **My Students** to view assigned pupils.
   - Go to **Attendance** > Select a student > Mark `Present` for today > Attempt to mark again to show duplicate validation.
   - Go to **Marks** > Add a score (e.g. `Science`, `Internal 1`, `88/100`).

3. **Parent Workflow:**
   - Sign out and log in as Parent (`parent@ptportal.com` / `Parent@123`).
   - View **Dashboard** > Confirm dynamic attendance and marks percentages reflect the updates.
   - Go to **Messages** > Send a message: *"How is Rahul performing in Science?"*.

4. **Teacher Reply:**
   - Sign out and log back in as Teacher (`teacher@ptportal.com` / `Teacher@123`).
   - Open **Messages** > View parent inquiry > Send a reply: *"He is performing excellently!"*.
   - Sign back into Parent to confirm the reply appears in the chat thread.

---

## 9. Security & Best Practices
- **Password Hashing:** Passwords hashed with `werkzeug.security.generate_password_hash` (PBKDF2/SHA256).
- **Access Guarding:** Flask-Login `@login_required` and custom `@role_required` decorators ensure users cannot access unauthorized pages.
- **Environment Isolation:** Secrets and MongoDB URI are loaded via `python-dotenv` from `.env`, which is ignored in `.gitignore`.
