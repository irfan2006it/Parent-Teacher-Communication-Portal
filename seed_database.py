"""
Database Seed Script: Parent–Teacher Communication Portal
College Micro Project Lab Submission
Populates sample demonstration data:
- 1 Admin: admin@ptportal.com / Admin@123
- 1 Teacher: teacher@ptportal.com / Teacher@123
- 2 Parents:
    - parent@ptportal.com / Parent@123
    - parent2@ptportal.com / Parent@123
- 3 Students:
    - STU001: Rahul Kumar (Class III-B)
    - STU002: Priya Sharma (Class III-B)
    - STU003: Arun Patel (Class III-B)
- Sample Attendance Records
- Sample Marks Records
- Sample Messages Thread
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def seed(db=None, users_col=None, students_col=None, attendance_col=None, marks_col=None, messages_col=None):
    if users_col is None:
        import app
        if app.users_col.count_documents({}) > 0:
            # Auto-seed already populated the database upon app import
            return
        db = app.db
        users_col = app.users_col
        students_col = app.students_col
        attendance_col = app.attendance_col
        marks_col = app.marks_col
        messages_col = app.messages_col

    print("\n Clearing old records from collections...")
    users_col.delete_many({})
    students_col.delete_many({})
    attendance_col.delete_many({})
    marks_col.delete_many({})
    messages_col.delete_many({})

    # 1. Seed Users with Hashed Passwords
    print(" Seeding demo user accounts...")
    admin_user = {
        "name": "System Administrator",
        "email": "admin@ptportal.com",
        "password": generate_password_hash("Admin@123"),
        "role": "admin"
    }
    admin_id = str(users_col.insert_one(admin_user).inserted_id)

    teacher_user = {
        "name": "Prof. John Sharma",
        "email": "teacher@ptportal.com",
        "password": generate_password_hash("Teacher@123"),
        "role": "teacher"
    }
    teacher_id = str(users_col.insert_one(teacher_user).inserted_id)

    parent_user_1 = {
        "name": "Ramesh Kumar",
        "email": "parent@ptportal.com",
        "password": generate_password_hash("Parent@123"),
        "role": "parent"
    }
    parent_1_id = str(users_col.insert_one(parent_user_1).inserted_id)

    parent_user_2 = {
        "name": "Sunita Patel",
        "email": "parent2@ptportal.com",
        "password": generate_password_hash("Parent@123"),
        "role": "parent"
    }
    parent_2_id = str(users_col.insert_one(parent_user_2).inserted_id)

    # 2. Seed 3 Students
    print(" Seeding student records...")
    students = [
        {
            "name": "Rahul Kumar",
            "student_id": "STU001",
            "class": "III",
            "section": "B",
            "parent_id": parent_1_id,
            "teacher_id": teacher_id
        },
        {
            "name": "Priya Kumar",
            "student_id": "STU002",
            "class": "III",
            "section": "B",
            "parent_id": parent_1_id,
            "teacher_id": teacher_id
        },
        {
            "name": "Arun Patel",
            "student_id": "STU003",
            "class": "III",
            "section": "B",
            "parent_id": parent_2_id,
            "teacher_id": teacher_id
        }
    ]
    students_col.insert_many(students)

    # 3. Seed Attendance Records (Last 10 Days)
    print(" Seeding attendance logs...")
    today = datetime.now()
    attendance_records = []

    # Generate 10 days of attendance for STU001 (Rahul Kumar)
    for i in range(10):
        att_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        status = "Present" if i != 3 else "Absent" # 90% attendance
        attendance_records.append({
            "student_id": "STU001",
            "date": att_date,
            "status": status
        })

    # Generate attendance for STU002 and STU003
    for i in range(5):
        att_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        attendance_records.append({"student_id": "STU002", "date": att_date, "status": "Present"})
        attendance_records.append({"student_id": "STU003", "date": att_date, "status": "Present" if i % 2 == 0 else "Absent"})

    attendance_col.insert_many(attendance_records)

    # 4. Seed Academic Marks
    print(" Seeding examination marks...")
    marks = [
        # Marks for Rahul Kumar (STU001)
        {"student_id": "STU001", "subject": "Mathematics", "exam": "Internal Test 1", "marks": 85.0, "total": 100.0},
        {"student_id": "STU001", "subject": "Science", "exam": "Internal Test 1", "marks": 78.0, "total": 100.0},
        {"student_id": "STU001", "subject": "English", "exam": "Internal Test 1", "marks": 90.0, "total": 100.0},
        {"student_id": "STU001", "subject": "Social Studies", "exam": "Internal Test 1", "marks": 82.0, "total": 100.0},

        # Marks for Priya Kumar (STU002)
        {"student_id": "STU002", "subject": "Mathematics", "exam": "Internal Test 1", "marks": 94.0, "total": 100.0},
        {"student_id": "STU002", "subject": "Science", "exam": "Internal Test 1", "marks": 88.0, "total": 100.0},

        # Marks for Arun Patel (STU003)
        {"student_id": "STU003", "subject": "Mathematics", "exam": "Internal Test 1", "marks": 72.0, "total": 100.0},
        {"student_id": "STU003", "subject": "Science", "exam": "Internal Test 1", "marks": 75.0, "total": 100.0}
    ]
    marks_col.insert_many(marks)

    # 5. Seed Messages between Parent Ramesh Kumar and Teacher John Sharma
    print(" Seeding communication messages...")
    t1 = (today - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
    t2 = (today - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    t3 = (today - timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')

    sample_messages = [
        {
            "sender_id": parent_1_id,
            "receiver_id": teacher_id,
            "student_id": "STU001",
            "message": "Hello Sir, how is my child performing in Mathematics?",
            "timestamp": t1,
            "is_read": True
        },
        {
            "sender_id": teacher_id,
            "receiver_id": parent_1_id,
            "student_id": "STU001",
            "message": "Hello Mr. Kumar! Rahul is performing well in class. He scored 85/100 in Internal Test 1.",
            "timestamp": t2,
            "is_read": True
        },
        {
            "sender_id": teacher_id,
            "receiver_id": parent_1_id,
            "student_id": "STU001",
            "message": "He just needs a little more regular practice with geometry word problems.",
            "timestamp": t3,
            "is_read": False
        }
    ]
    messages_col.insert_many(sample_messages)

    print("\n Database Seeding Completed Successfully!")
    print("==================================================")
    print("DEMO LOGIN CREDENTIALS:")
    print("1. Admin:   admin@ptportal.com   | Admin@123")
    print("2. Teacher: teacher@ptportal.com | Teacher@123")
    print("3. Parent:  parent@ptportal.com  | Parent@123")
    print("4. Parent2: parent2@ptportal.com | Parent@123")
    print("==================================================")

if __name__ == '__main__':
    seed()
