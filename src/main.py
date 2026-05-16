import os
import random
import string
import hashlib
import smtplib
from email.mime.text import MIMEText
import mysql.connector
from datetime import datetime, timedelta

# Environment Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YOUR_SECURE_PASSWORD")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "vwkdivya@gmail.com")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "YOUR_SMTP_APP_PASSWORD") 

def create_database_if_not_exists():
    try:
        temp_conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        temp_cur = temp_conn.cursor()
        temp_cur.execute("CREATE DATABASE IF NOT EXISTS vote")
        temp_conn.commit()
        temp_cur.close()
        temp_conn.close()
        return True    
    except mysql.connector.Error as err:
        print(f"Database initialization error: {err}")
        return False

if not create_database_if_not_exists():
    print("System Setup Failed: Unable to verify database connection. Exiting.")
    exit()

conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database="vote")
cur = conn.cursor()

def init_admins_table():
    cur.execute("SHOW TABLES LIKE 'alladmins'")
    if not cur.fetchone():
        cur.execute("""CREATE TABLE alladmins (
            teacher_id VARCHAR(20) PRIMARY KEY,
            emailid VARCHAR(250) NOT NULL UNIQUE,
            name VARCHAR(50) NOT NULL)""")
        conn.commit()
        admins_data = [
            ('DV24', 'ukiyo.2404@gmail.com', 'Divya Vishwakarma'),
            ('AK16', 'im.aadhyakashyap@gmail.com', 'Aadhya Kashyap')
        ]
        cur.executemany("INSERT INTO alladmins (teacher_id, emailid, name) VALUES (%s, %s, %s)", admins_data)
        conn.commit()

def init_otp_table():
    cur.execute("SHOW TABLES LIKE 'user_otp'")
    if not cur.fetchone():
        cur.execute("""CREATE TABLE user_otp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(250) NOT NULL UNIQUE,
            otp_hash VARCHAR(64) NOT NULL,
            expire_at DATETIME NOT NULL)""")
        conn.commit()

def init_all_tables():
    cur.execute("""CREATE TABLE IF NOT EXISTS polls (
        poll_id INT AUTO_INCREMENT PRIMARY KEY,
        teacher_id VARCHAR(20),
        title VARCHAR(255) NOT NULL,
        description VARCHAR(500),
        start_time DATE NOT NULL,
        end_time DATE NOT NULL,
        created_by VARCHAR(250) NOT NULL,
        class_num INT,
        sec VARCHAR(5))""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS poll_options (
        option_id INT AUTO_INCREMENT PRIMARY KEY,
        poll_id INT,
        teacher_id VARCHAR(20),
        option_text VARCHAR(255) NOT NULL,
        vote_count INT DEFAULT 0,
        FOREIGN KEY (poll_id) REFERENCES polls(poll_id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS poll_votes (
        vote_id INT AUTO_INCREMENT PRIMARY KEY,
        poll_id INT NOT NULL,
        voter_email VARCHAR(250) NOT NULL,
        choice VARCHAR(255) NOT NULL,
        voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uniq_poll_voter (poll_id, voter_email),
        FOREIGN KEY (poll_id) REFERENCES polls(poll_id) ON DELETE CASCADE)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS stud_log (
        adm_no INT PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        email VARCHAR(250) NOT NULL,
        class_num INT,
        sec VARCHAR(5),
        roll_no INT NOT NULL)""")
    conn.commit()

init_admins_table()
init_otp_table()
init_all_tables()

def get_admin_emails():
    cur.execute("SELECT emailid FROM alladmins")
    return [row[0] for row in cur.fetchall()]

def generate_otp(length=6):
    return ''.join(random.choice(string.digits) for _ in range(length))

def store_otp(email, otp):
    otp_hash = hashlib.sha256(str(otp).encode()).hexdigest()
    expire_at = datetime.now() + timedelta(minutes=5)
    cur.execute("INSERT INTO user_otp (email, otp_hash, expire_at) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE otp_hash = %s, expire_at = %s", 
                (email, otp_hash, expire_at, otp_hash, expire_at))
    conn.commit()

def send_email(otp, receiver_email):
    msg = MIMEText(f"Your Secure Authentication OTP is: {otp}\nThis code will expire in 5 minutes.")
    msg["Subject"] = "Secure Access OTP - Digital Voting Infrastructure"
    msg["From"] = SMTP_EMAIL
    msg["To"] = receiver_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Network Error: Unable to dispatch verification mail -> {e}")
        return False

def verify_otp(email, user_otp):
    query = "SELECT otp_hash FROM user_otp WHERE email = %s AND expire_at > NOW()"
    cur.execute(query, (email,))
    result = cur.fetchone()
    if not result:
        return False
    stored_hash = result[0]
    user_hash = hashlib.sha256(str(user_otp).encode()).hexdigest()
    if stored_hash == user_hash:
        cur.execute("DELETE FROM user_otp WHERE email = %s", (email,))
        conn.commit()
        return True
    return False

def add_admin():
    teacher_id = input("Enter teacher ID: ").strip()
    email = input("Enter email: ").strip()
    name = input("Enter name: ").strip()
    try:
        cur.execute("INSERT INTO alladmins (teacher_id, emailid, name) VALUES (%s, %s, %s)", (teacher_id, email, name))
        conn.commit()
        print("Admin added successfully!")
    except mysql.connector.Error as err:
        print(f"Error adding admin: {err}")

def remove_admin():
    email = input("Enter email to remove: ").strip()
    if email in get_admin_emails():
        cur.execute("DELETE FROM alladmins WHERE emailid = %s", (email,))
        conn.commit()
        print("Admin removed successfully!")
    else:
        print("Admin user not found!")

def show_admins():
    cur.execute("SELECT teacher_id, emailid, name FROM alladmins")
    print("\n--- CURRENT AUTHORIZED ADMINISTRATORS ---")
    for admin in cur.fetchall():
        print(f"ID: {admin[0]} | Email: {admin[1]} | Name: {admin[2]}")

def add_poll():
    teacher_id = input("Enter teacher ID: ").strip()
    title = input("Enter poll title: ").strip()
    desc = input("Enter description: ").strip()
    start = input("Enter start date (YYYY-MM-DD): ").strip()
    end = input("Enter end date (YYYY-MM-DD): ").strip()
    creator = input("Enter creator name: ").strip()
    class_num_input = input("Enter class restriction (blank for all): ").strip()
    section_input = input("Enter section restriction (blank for all): ").strip()
    
    class_num = int(class_num_input) if class_num_input.isdigit() else None
    section = section_input if section_input else None
    
    cur.execute("""INSERT INTO polls(teacher_id, title, description, start_time, end_time, created_by, class_num, sec) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (teacher_id, title, desc, start, end, creator, class_num, section))
    conn.commit()
    poll_id = cur.lastrowid  
    print(f"\nPoll '{title}' created successfully! Add options below (Leave blank to finish):")
    
    option_num = 1
    while True:
        candidate = input(f"Option {option_num}: ").strip()
        if not candidate:
            break
        cur.execute("INSERT INTO poll_options (poll_id, teacher_id, option_text) VALUES (%s, %s, %s)", (poll_id, teacher_id, candidate))
        option_num += 1
    conn.commit()

def show_active_polls():
    query = "SELECT poll_id, title, start_time, end_time, created_by FROM polls WHERE start_time <= CURDATE() AND end_time >= CURDATE()"
    cur.execute(query)
    rows = cur.fetchall()
    if not rows:
        print("No active polling modules found.")
    for r in rows:
        print(f"ID: {r[0]} | Title: {r[1]} | Lifespan: {r[2]} to {r[3]} | Admin: {r[4]}")
    return rows

def delete_poll():
    title = input("Enter poll title to remove: ").strip()
    cur.execute("DELETE FROM polls WHERE title = %s", (title,))
    conn.commit()
    print("Module removed successfully.")

def admin_menu():
    while True:
        print("\n=== SYSTEM MANAGEMENT INTERFACE ===")
        print("1. Register New Administrator")
        print("2. De-authorize Administrator")
        print("3. Audit Authorized Staff Records")
        print("4. Deploy New Ballot Module")
        print("5. Inspect Active Live Ballots")
        print("6. Revoke Active Ballot Module")
        print("7. Terminate Administrative Terminal")
        choice = input("Enter selection index: ").strip()
        if choice == '1': add_admin()
        elif choice == '2': remove_admin()
        elif choice == '3': show_admins()
        elif choice == '4': add_poll()
        elif choice == '5': show_active_polls()
        elif choice == '6': delete_poll()
        elif choice == '7': break

def student_login():
    name = input("Enter student complete name: ").strip()
    email = input("Enter university email node: ").strip()
    try:
        roll_no = int(input("Enter roll code: ").strip())
        adm_no = int(input("Enter record admission number: ").strip())
    except ValueError:
        print("Invalid operational parameters input.")
        return None, None
    
    cur.execute("SELECT adm_no, class_num, sec FROM stud_log WHERE adm_no = %s", (adm_no,))
    record = cur.fetchone()
    if record:
        print(f"Identity authenticated. Welcome back, {name}.")
        return record[1], record[2]
        
    cur.execute("INSERT INTO stud_log (adm_no, name, email, class_num, sec, roll_no) VALUES (%s, %s, %s, 12, 'A', %s)", (adm_no, name, email, roll_no))
    conn.commit()
    return 12, 'A'

def student_menu(class_num, section):
    while True:
        print("\n=== STUDENT ACCESS TERMINAL ===")
        print("1. Scan Scoped Active Ballots")
        print("2. Record Verified Ballot Vote")
        print("3. Logout Session")
        choice = input("Choose action: ").strip()
        if choice == '3': break

def admin_otp_login():
    print("\n--- ADMINISTRATOR ACCESS PORTAL ---")
    email = input("Enter admin email address: ").strip()
    cur.execute("SELECT name FROM alladmins WHERE emailid = %s", (email,))
    admin_exists = cur.fetchone()
    if not admin_exists:
        print("Access Denied: Email address unauthorized.")
        return False

    otp = generate_otp()
    store_otp(email, otp)
    if send_email(otp, email):
        print(f"A 2-Step Verification code has been dispatched to {email}.")
        for attempt in range(1, 4):
            user_otp = input("Enter 6-Digit OTP: ").strip()
            if verify_otp(email, user_otp):
                print(f"Authentication Successful. Welcome back, {admin_exists[0]}.")
                admin_menu()
                return True
            print(f"Invalid verification code. {3 - attempt} attempts remaining.")
    return False

def main_menu():
    while True:
        print("\n=== SECURE ONLINE VOTING SYSTEM ===")
        print("1. Administrator Access via Secure OTP")
        print("2. Student Registration & Terminal")
        print("3. Terminate System")
        choice = input("Select System Interface: ").strip()
        if choice == '1': admin_otp_login()
        elif choice == '2':
            c, s = student_login()
            if c: student_menu(c, s)
        elif choice == '3': break

if __name__ == "__main__":
    try: main_menu()
    finally:
        cur.close()
        conn.close()
