import os
from datetime import datetime
from functools import wraps
from bson import ObjectId
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, abort, jsonify
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# 1. Load Environment Configuration
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'college_micro_project_ptportal_secret_key_2026')

# 2. Database Connection (MongoDB Atlas)
MONGO_URI = os.getenv('MONGO_URI', '').strip()
DATABASE_NAME = 'parent_teacher_portal'

def init_mongo_connection():
    """Establish connection to MongoDB Atlas with fallback for offline environments."""
    if MONGO_URI and not MONGO_URI.startswith('your_mongodb_atlas') and 'username:password@cluster.mongodb.net' not in MONGO_URI:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=12000)
            # Test connection
            client.admin.command('ping')
            print("Connected successfully to MongoDB Atlas!")
            return client[DATABASE_NAME]
        except Exception as e:
            print(f"Notice: MongoDB Atlas connection failed ({e}). Falling back to local/in-memory database.")
    
    # Check if local MongoDB is running
    try:
        local_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        local_client.admin.command('ping')
        print("Connected to local MongoDB instance!")
        return local_client[DATABASE_NAME]
    except Exception:
        # Fallback to mongomock for safe local lab demonstrations without external dependencies
        print("Using in-memory MongoDB mock database for offline demonstration.")
        import mongomock
        mock_client = mongomock.MongoClient()
        return mock_client[DATABASE_NAME]

db = init_mongo_connection()

# Database Collections
users_col = db['users']
students_col = db['students']
attendance_col = db['attendance']
marks_col = db['marks']
messages_col = db['messages']

# Ensure unique index for duplicate prevention
try:
    attendance_col.create_index([("student_id", 1), ("date", 1)], unique=True)
except Exception:
    pass

# Auto-seed demo data if database is empty (e.g., mongomock or initial setup)
try:
    if users_col.count_documents({}) == 0:
        import seed_database
        seed_database.seed(db, users_col, students_col, attendance_col, marks_col, messages_col)
except Exception as e:
    print(f"Auto-seed notice: {e}")

# 3. Flask-Login Authentication Setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.name = user_doc.get('name', '')
        self.email = user_doc.get('email', '')
        self.role = user_doc.get('role', '')

@login_manager.user_loader
def load_user(user_id):
    try:
        doc = users_col.find_one({"_id": ObjectId(user_id)})
        if doc:
            return User(doc)
    except Exception:
        pass
    return None

def role_required(*allowed_roles):
    """Decorator to enforce role-based access control."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash("Unauthorized access: Your role is not permitted for this page.", "danger")
                if current_user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif current_user.role == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
                elif current_user.role == 'parent':
                    return redirect(url_for('parent_dashboard'))
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------
# AUTHENTICATION & ROOT ROUTES
# ---------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user_doc = users_col.find_one({"email": email})
        if user_doc and check_password_hash(user_doc.get('password', ''), password):
            user_obj = User(user_doc)
            login_user(user_obj)
            flash(f"Welcome back, {user_obj.name}!", "success")
            if user_obj.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user_obj.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user_obj.role == 'parent':
                return redirect(url_for('parent_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))


# ---------------------------------------------------------
# ADMIN DASHBOARD & MANAGEMENT ROUTES
# ---------------------------------------------------------

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    total_students = students_col.count_documents({})
    total_teachers = users_col.count_documents({"role": "teacher"})
    total_parents = users_col.count_documents({"role": "parent"})

    # Fetch recent students with parent and teacher names populated
    students = list(students_col.find().sort('_id', -1).limit(5))
    for s in students:
        if s.get('parent_id'):
            p = users_col.find_one({"_id": ObjectId(s['parent_id'])})
            s['parent_name'] = p.get('name') if p else None
        if s.get('teacher_id'):
            t = users_col.find_one({"_id": ObjectId(s['teacher_id'])})
            s['teacher_name'] = t.get('name') if t else None

    return render_template(
        'admin/dashboard.html',
        active_page='admin_dashboard',
        total_students=total_students,
        total_teachers=total_teachers,
        total_parents=total_parents,
        students=students
    )

@app.route('/admin/students')
@login_required
@role_required('admin')
def admin_students():
    students = list(students_col.find().sort('name', 1))
    for s in students:
        if s.get('parent_id'):
            p = users_col.find_one({"_id": ObjectId(s['parent_id'])})
            s['parent_name'] = p.get('name') if p else None
        if s.get('teacher_id'):
            t = users_col.find_one({"_id": ObjectId(s['teacher_id'])})
            s['teacher_name'] = t.get('name') if t else None

    return render_template('admin/students.html', active_page='admin_students', students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        student_id = request.form.get('student_id', '').strip().upper()
        class_name = request.form.get('class', '').strip()
        section = request.form.get('section', '').strip().upper()
        parent_id = request.form.get('parent_id', '').strip()
        teacher_id = request.form.get('teacher_id', '').strip()

        if not name or not student_id or not class_name or not section:
            flash("All mandatory fields must be filled out.", "danger")
            return redirect(url_for('admin_add_student'))

        # Check unique student ID
        if students_col.find_one({"student_id": student_id}):
            flash(f"Student ID '{student_id}' is already registered.", "danger")
            return redirect(url_for('admin_add_student'))

        student_doc = {
            "name": name,
            "student_id": student_id,
            "class": class_name,
            "section": section,
            "parent_id": parent_id if parent_id else None,
            "teacher_id": teacher_id if teacher_id else None
        }
        students_col.insert_one(student_doc)
        flash(f"Student '{name}' ({student_id}) enrolled successfully!", "success")
        return redirect(url_for('admin_students'))

    parents = list(users_col.find({"role": "parent"}).sort('name', 1))
    teachers = list(users_col.find({"role": "teacher"}).sort('name', 1))
    return render_template('admin/add_student.html', active_page='admin_students', parents=parents, teachers=teachers)

@app.route('/admin/students/edit/<student_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_student(student_id):
    student = students_col.find_one({"_id": ObjectId(student_id)})
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for('admin_students'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        new_student_id = request.form.get('student_id', '').strip().upper()
        class_name = request.form.get('class', '').strip()
        section = request.form.get('section', '').strip().upper()
        parent_id = request.form.get('parent_id', '').strip()
        teacher_id = request.form.get('teacher_id', '').strip()

        # Check uniqueness if ID was changed
        existing = students_col.find_one({"student_id": new_student_id, "_id": {"$ne": ObjectId(student_id)}})
        if existing:
            flash(f"Student ID '{new_student_id}' already in use by another record.", "danger")
            return redirect(url_for('admin_edit_student', student_id=student_id))

        students_col.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {
                "name": name,
                "student_id": new_student_id,
                "class": class_name,
                "section": section,
                "parent_id": parent_id if parent_id else None,
                "teacher_id": teacher_id if teacher_id else None
            }}
        )
        flash(f"Updated record for '{name}' successfully.", "success")
        return redirect(url_for('admin_students'))

    parents = list(users_col.find({"role": "parent"}).sort('name', 1))
    teachers = list(users_col.find({"role": "teacher"}).sort('name', 1))
    return render_template('admin/edit_student.html', active_page='admin_students', student=student, parents=parents, teachers=teachers)

@app.route('/admin/students/delete/<student_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_student(student_id):
    student = students_col.find_one({"_id": ObjectId(student_id)})
    if student:
        students_col.delete_one({"_id": ObjectId(student_id)})
        # Delete related attendance & marks
        attendance_col.delete_many({"student_id": student.get('student_id')})
        marks_col.delete_many({"student_id": student.get('student_id')})
        messages_col.delete_many({"student_id": student.get('student_id')})
        flash(f"Student record '{student.get('name')}' removed.", "info")
    return redirect(url_for('admin_students'))

@app.route('/admin/teachers')
@login_required
@role_required('admin')
def admin_teachers():
    teachers = list(users_col.find({"role": "teacher"}).sort('name', 1))
    for t in teachers:
        t['student_count'] = students_col.count_documents({"teacher_id": str(t['_id'])})
    return render_template('admin/teachers.html', active_page='admin_teachers', teachers=teachers)

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_teacher():
    if request.method == 'GET':
        return redirect(url_for('admin_teachers'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash("Please provide all teacher fields.", "danger")
        return redirect(url_for('admin_teachers'))

    if users_col.find_one({"email": email}):
        flash(f"Email '{email}' is already registered.", "danger")
        return redirect(url_for('admin_teachers'))

    users_col.insert_one({
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": "teacher"
    })
    flash(f"Teacher account for '{name}' created successfully.", "success")
    return redirect(url_for('admin_teachers'))

@app.route('/admin/teachers/delete/<teacher_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_teacher(teacher_id):
    users_col.delete_one({"_id": ObjectId(teacher_id), "role": "teacher"})
    # Unassign teacher from any student
    students_col.update_many({"teacher_id": teacher_id}, {"$set": {"teacher_id": None}})
    flash("Teacher removed and unlinked from classes.", "info")
    return redirect(url_for('admin_teachers'))

@app.route('/admin/parents')
@login_required
@role_required('admin')
def admin_parents():
    parents = list(users_col.find({"role": "parent"}).sort('name', 1))
    for p in parents:
        p['child_count'] = students_col.count_documents({"parent_id": str(p['_id'])})
    return render_template('admin/parents.html', active_page='admin_parents', parents=parents)

@app.route('/admin/parents/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_parent():
    if request.method == 'GET':
        return redirect(url_for('admin_parents'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash("Please provide all parent details.", "danger")
        return redirect(url_for('admin_parents'))

    if users_col.find_one({"email": email}):
        flash(f"Email '{email}' is already registered.", "danger")
        return redirect(url_for('admin_parents'))

    users_col.insert_one({
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": "parent"
    })
    flash(f"Parent account for '{name}' created successfully.", "success")
    return redirect(url_for('admin_parents'))

@app.route('/admin/parents/delete/<parent_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_parent(parent_id):
    users_col.delete_one({"_id": ObjectId(parent_id), "role": "parent"})
    students_col.update_many({"parent_id": parent_id}, {"$set": {"parent_id": None}})
    flash("Parent removed and unlinked from students.", "info")
    return redirect(url_for('admin_parents'))


# ---------------------------------------------------------
# TEACHER DASHBOARD & ACTIONS
# ---------------------------------------------------------

@app.route('/teacher/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    teacher_id_str = str(current_user.id)
    students = list(students_col.find({"teacher_id": teacher_id_str}))
    student_ids = [s.get('student_id') for s in students]

    # Populate parent names
    for s in students:
        if s.get('parent_id'):
            p = users_col.find_one({"_id": ObjectId(s['parent_id'])})
            s['parent_name'] = p.get('name') if p else None

    # Today's attendance count for teacher's students
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_att_count = attendance_col.count_documents({
        "student_id": {"$in": student_ids},
        "date": today_str
    }) if student_ids else 0

    # Total messages involving teacher
    total_messages_count = messages_col.count_documents({
        "$or": [
            {"receiver_id": teacher_id_str},
            {"sender_id": teacher_id_str}
        ]
    })

    # Recent incoming messages
    recent_messages = list(messages_col.find({"receiver_id": teacher_id_str}).sort('_id', -1).limit(5))
    for m in recent_messages:
        sender = users_col.find_one({"_id": ObjectId(m['sender_id'])})
        m['sender_name'] = sender.get('name') if sender else 'Parent'
        s = students_col.find_one({"student_id": m.get('student_id')})
        m['student_name'] = s.get('name') if s else m.get('student_id')

    unread_count = messages_col.count_documents({"receiver_id": teacher_id_str, "is_read": False})

    return render_template(
        'teacher/dashboard.html',
        active_page='teacher_dashboard',
        assigned_students_count=len(students),
        today_attendance_count=today_att_count,
        total_messages_count=total_messages_count,
        students=students,
        recent_messages=recent_messages,
        unread_count=unread_count
    )

@app.route('/teacher/students')
@login_required
@role_required('teacher')
def teacher_students():
    teacher_id_str = str(current_user.id)
    students = list(students_col.find({"teacher_id": teacher_id_str}).sort('name', 1))
    for s in students:
        if s.get('parent_id'):
            p = users_col.find_one({"_id": ObjectId(s['parent_id'])})
            if p:
                s['parent_name'] = p.get('name')
                s['parent_email'] = p.get('email')

    unread_count = messages_col.count_documents({"receiver_id": teacher_id_str, "is_read": False})
    return render_template('teacher/students.html', active_page='teacher_students', students=students, unread_count=unread_count)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_attendance():
    teacher_id_str = str(current_user.id)
    students = list(students_col.find({"teacher_id": teacher_id_str}).sort('name', 1))
    student_ids = [s.get('student_id') for s in students]

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        date_val = request.form.get('date', '').strip()
        status_val = request.form.get('status', 'Present').strip()

        # Validate that student belongs to teacher
        if student_id not in student_ids:
            flash("Unauthorized: Student not assigned to your supervision.", "danger")
            return redirect(url_for('teacher_attendance'))

        if status_val not in ['Present', 'Absent']:
            flash("Invalid status. Allowed values: Present or Absent.", "danger")
            return redirect(url_for('teacher_attendance'))

        # Check duplicate attendance for the same student on the same date
        existing = attendance_col.find_one({"student_id": student_id, "date": date_val})
        if existing:
            flash(f"Duplicate entry! Attendance for student {student_id} on {date_val} is already recorded as '{existing.get('status')}'.", "warning")
            return redirect(url_for('teacher_attendance'))

        # Insert new record
        attendance_col.insert_one({
            "student_id": student_id,
            "date": date_val,
            "status": status_val
        })
        flash(f"Attendance recorded: {student_id} marked as {status_val} on {date_val}.", "success")
        return redirect(url_for('teacher_attendance'))

    # Fetch recent attendance records for teacher's students
    records = list(attendance_col.find({"student_id": {"$in": student_ids}}).sort('date', -1).limit(50))
    for r in records:
        s = next((item for item in students if item['student_id'] == r['student_id']), None)
        r['student_name'] = s.get('name') if s else r['student_id']

    today_date = datetime.now().strftime('%Y-%m-%d')
    unread_count = messages_col.count_documents({"receiver_id": teacher_id_str, "is_read": False})

    return render_template(
        'teacher/attendance.html',
        active_page='teacher_attendance',
        students=students,
        attendance_records=records,
        today_date=today_date,
        unread_count=unread_count
    )

@app.route('/teacher/marks', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_marks():
    teacher_id_str = str(current_user.id)
    students = list(students_col.find({"teacher_id": teacher_id_str}).sort('name', 1))
    student_ids = [s.get('student_id') for s in students]

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        subject = request.form.get('subject', '').strip()
        exam = request.form.get('exam', '').strip()
        try:
            marks_val = float(request.form.get('marks', 0))
            total_val = float(request.form.get('total', 100))
        except ValueError:
            flash("Please enter valid numeric values for marks.", "danger")
            return redirect(url_for('teacher_marks'))

        if student_id not in student_ids:
            flash("Unauthorized student selection.", "danger")
            return redirect(url_for('teacher_marks'))

        marks_col.insert_one({
            "student_id": student_id,
            "subject": subject,
            "exam": exam,
            "marks": marks_val,
            "total": total_val
        })
        flash(f"Marks added successfully for {student_id} ({subject} - {marks_val}/{total_val}).", "success")
        return redirect(url_for('teacher_marks'))

    # Fetch marks list
    marks_list = list(marks_col.find({"student_id": {"$in": student_ids}}).sort('_id', -1))
    for m in marks_list:
        s = next((item for item in students if item['student_id'] == m['student_id']), None)
        m['student_name'] = s.get('name') if s else m['student_id']

    unread_count = messages_col.count_documents({"receiver_id": teacher_id_str, "is_read": False})

    return render_template(
        'teacher/marks.html',
        active_page='teacher_marks',
        students=students,
        marks_list=marks_list,
        unread_count=unread_count
    )

@app.route('/teacher/marks/edit/<mark_id>', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_edit_marks(mark_id):
    subject = request.form.get('subject', '').strip()
    exam = request.form.get('exam', '').strip()
    try:
        marks_val = float(request.form.get('marks', 0))
        total_val = float(request.form.get('total', 100))
    except ValueError:
        flash("Invalid marks format.", "danger")
        return redirect(url_for('teacher_marks'))

    marks_col.update_one(
        {"_id": ObjectId(mark_id)},
        {"$set": {
            "subject": subject,
            "exam": exam,
            "marks": marks_val,
            "total": total_val
        }}
    )
    flash("Marks record updated.", "success")
    return redirect(url_for('teacher_marks'))

@app.route('/teacher/marks/delete/<mark_id>', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_delete_marks(mark_id):
    marks_col.delete_one({"_id": ObjectId(mark_id)})
    flash("Marks entry removed.", "info")
    return redirect(url_for('teacher_marks'))

@app.route('/teacher/messages')
@login_required
@role_required('teacher')
def teacher_messages():
    teacher_id_str = str(current_user.id)
    students = list(students_col.find({"teacher_id": teacher_id_str}).sort('name', 1))

    threads = []
    for s in students:
        if s.get('parent_id'):
            p = users_col.find_one({"_id": ObjectId(s['parent_id'])})
            unread = messages_col.count_documents({
                "receiver_id": teacher_id_str,
                "student_id": s['student_id'],
                "is_read": False
            })
            threads.append({
                "student_id": s['student_id'],
                "student_name": s['name'],
                "student_class": s['class'],
                "student_section": s['section'],
                "parent_id": s['parent_id'],
                "parent_name": p.get('name') if p else 'Parent',
                "parent_email": p.get('email') if p else '',
                "unread_count": unread
            })

    # Pick active student conversation
    active_student_id = request.args.get('student_id')
    if not active_student_id and threads:
        active_student_id = threads[0]['student_id']

    current_thread = None
    messages = []
    if active_student_id:
        current_thread = next((t for t in threads if t['student_id'] == active_student_id), None)
        if current_thread:
            # Mark incoming messages as read
            messages_col.update_many(
                {
                    "receiver_id": teacher_id_str,
                    "student_id": active_student_id,
                    "is_read": False
                },
                {"$set": {"is_read": True}}
            )
            # Fetch message history
            messages = list(messages_col.find({"student_id": active_student_id}).sort('timestamp', 1))

    total_unread = messages_col.count_documents({"receiver_id": teacher_id_str, "is_read": False})

    return render_template(
        'teacher/messages.html',
        active_page='teacher_messages',
        threads=threads,
        active_student_id=active_student_id,
        current_thread=current_thread,
        messages=messages,
        unread_count=total_unread
    )

@app.route('/teacher/messages/send', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_send_message():
    teacher_id_str = str(current_user.id)
    student_id = request.form.get('student_id', '').strip()
    receiver_id = request.form.get('receiver_id', '').strip()
    message_text = request.form.get('message', '').strip()

    if student_id and receiver_id and message_text:
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        messages_col.insert_one({
            "sender_id": teacher_id_str,
            "receiver_id": receiver_id,
            "student_id": student_id,
            "message": message_text,
            "timestamp": timestamp_str,
            "is_read": False
        })
        flash("Reply sent to parent.", "success")
    return redirect(url_for('teacher_messages', student_id=student_id))


# ---------------------------------------------------------
# PARENT DASHBOARD & ACTIONS
# ---------------------------------------------------------

@app.route('/parent/dashboard')
@login_required
@role_required('parent')
def parent_dashboard():
    parent_id_str = str(current_user.id)
    # Find child linked to parent
    child = students_col.find_one({"parent_id": parent_id_str})

    attendance_pct = 0.0
    total_days = 0
    present_days = 0
    average_marks_pct = 0.0
    marks_count = 0
    recent_marks = []
    teacher = None
    unread_messages = 0

    if child:
        stu_id = child.get('student_id')

        # Attendance calculation
        total_days = attendance_col.count_documents({"student_id": stu_id})
        present_days = attendance_col.count_documents({"student_id": stu_id, "status": "Present"})
        if total_days > 0:
            attendance_pct = round((present_days / total_days) * 100, 1)

        # Marks calculation
        marks_docs = list(marks_col.find({"student_id": stu_id}))
        marks_count = len(marks_docs)
        if marks_docs:
            total_earned = sum(m.get('marks', 0) for m in marks_docs)
            total_possible = sum(m.get('total', 100) for m in marks_docs)
            if total_possible > 0:
                average_marks_pct = round((total_earned / total_possible) * 100, 1)
        recent_marks = marks_docs[-5:]

        # Teacher info
        if child.get('teacher_id'):
            teacher = users_col.find_one({"_id": ObjectId(child['teacher_id'])})

        # Unread messages from teacher
        unread_messages = messages_col.count_documents({
            "receiver_id": parent_id_str,
            "student_id": stu_id,
            "is_read": False
        })

    return render_template(
        'parent/dashboard.html',
        active_page='parent_dashboard',
        child=child,
        attendance_pct=attendance_pct,
        total_days=total_days,
        present_days=present_days,
        average_marks_pct=average_marks_pct,
        marks_count=marks_count,
        recent_marks=recent_marks,
        teacher=teacher,
        unread_messages=unread_messages,
        unread_count=unread_messages
    )

@app.route('/parent/child')
@login_required
@role_required('parent')
def parent_child():
    parent_id_str = str(current_user.id)
    child = students_col.find_one({"parent_id": parent_id_str})
    teacher_name = None
    teacher_email = None

    if child and child.get('teacher_id'):
        t = users_col.find_one({"_id": ObjectId(child['teacher_id'])})
        if t:
            teacher_name = t.get('name')
            teacher_email = t.get('email')

    unread_count = messages_col.count_documents({"receiver_id": parent_id_str, "is_read": False})
    return render_template(
        'parent/child.html',
        active_page='parent_child',
        child=child,
        teacher_name=teacher_name,
        teacher_email=teacher_email,
        unread_count=unread_count
    )

@app.route('/parent/attendance')
@login_required
@role_required('parent')
def parent_attendance():
    parent_id_str = str(current_user.id)
    child = students_col.find_one({"parent_id": parent_id_str})

    attendance_records = []
    total_days = 0
    present_days = 0
    absent_days = 0
    attendance_percentage = 0.0

    if child:
        stu_id = child.get('student_id')
        attendance_records = list(attendance_col.find({"student_id": stu_id}).sort('date', -1))
        total_days = len(attendance_records)
        present_days = sum(1 for r in attendance_records if r.get('status') == 'Present')
        absent_days = total_days - present_days
        if total_days > 0:
            attendance_percentage = round((present_days / total_days) * 100, 1)

    unread_count = messages_col.count_documents({"receiver_id": parent_id_str, "is_read": False})
    return render_template(
        'parent/attendance.html',
        active_page='parent_attendance',
        child=child,
        attendance_records=attendance_records,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        attendance_percentage=attendance_percentage,
        unread_count=unread_count
    )

@app.route('/parent/marks')
@login_required
@role_required('parent')
def parent_marks():
    parent_id_str = str(current_user.id)
    child = students_col.find_one({"parent_id": parent_id_str})

    marks_list = []
    average_percentage = 0.0

    if child:
        stu_id = child.get('student_id')
        marks_list = list(marks_col.find({"student_id": stu_id}).sort('_id', -1))
        if marks_list:
            total_earned = sum(m.get('marks', 0) for m in marks_list)
            total_possible = sum(m.get('total', 100) for m in marks_list)
            if total_possible > 0:
                average_percentage = round((total_earned / total_possible) * 100, 1)

    unread_count = messages_col.count_documents({"receiver_id": parent_id_str, "is_read": False})
    return render_template(
        'parent/marks.html',
        active_page='parent_marks',
        child=child,
        marks_list=marks_list,
        average_percentage=average_percentage,
        unread_count=unread_count
    )

@app.route('/parent/messages')
@login_required
@role_required('parent')
def parent_messages():
    parent_id_str = str(current_user.id)
    child = students_col.find_one({"parent_id": parent_id_str})
    teacher = None
    messages = []

    if child and child.get('teacher_id'):
        teacher = users_col.find_one({"_id": ObjectId(child['teacher_id'])})
        # Mark incoming messages as read
        messages_col.update_many(
            {
                "receiver_id": parent_id_str,
                "student_id": child['student_id'],
                "is_read": False
            },
            {"$set": {"is_read": True}}
        )
        # Fetch conversation history
        messages = list(messages_col.find({"student_id": child['student_id']}).sort('timestamp', 1))

    unread_count = messages_col.count_documents({"receiver_id": parent_id_str, "is_read": False})
    return render_template(
        'parent/messages.html',
        active_page='parent_messages',
        child=child,
        teacher=teacher,
        messages=messages,
        unread_count=unread_count
    )

@app.route('/parent/messages/send', methods=['POST'])
@login_required
@role_required('parent')
def parent_send_message():
    parent_id_str = str(current_user.id)
    child = students_col.find_one({"parent_id": parent_id_str})
    message_text = request.form.get('message', '').strip()

    if child and child.get('teacher_id') and message_text:
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        messages_col.insert_one({
            "sender_id": parent_id_str,
            "receiver_id": child['teacher_id'],
            "student_id": child['student_id'],
            "message": message_text,
            "timestamp": timestamp_str,
            "is_read": False
        })
        flash("Message sent to teacher.", "success")
    return redirect(url_for('parent_messages'))

# Shortcut Universal /messages Route
@app.route('/messages')
@login_required
def messages_shortcut():
    if current_user.role == 'parent':
        return redirect(url_for('parent_messages'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_messages'))
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------
# CUSTOM ERROR HANDLERS
# ---------------------------------------------------------

@app.errorhandler(400)
def bad_request_error(e):
    return render_template('error.html', error_code=400, error_title="Bad Request", error_message="The request could not be processed due to invalid syntax or parameters."), 400

@app.errorhandler(403)
def forbidden_error(e):
    return render_template('error.html', error_code=403, error_title="Access Forbidden", error_message="You do not have administrative permissions to view or alter this resource."), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template('error.html', error_code=404, error_title="Page Not Found", error_message="The page or resource you requested could not be found."), 404

@app.errorhandler(405)
def method_not_allowed_error(e):
    return render_template('error.html', error_code=405, error_title="Method Not Allowed", error_message="The requested HTTP method is not allowed on this path."), 405

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_title="Internal Server Error", error_message="An unexpected system error occurred on the server. Please try again shortly."), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='127.0.0.1', port=port)
