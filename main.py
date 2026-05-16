import os
import random
import string
import hashlib
import smtplib
from email.mime.text import MIMEText
import mysql.connector
from datetime import datetime, timedelta

# Environment Configuration (Prevents committing hardcoded passwords to public GitHub repositories)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YOUR_SECURE_PASSWORD")  # Set via environment variables
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
    print("System Setup Failed: Unable to verify or create database connection. Exiting.")
    exit()

# Initialize Global Database Connections
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

# Ensure schema configuration on execution
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

def admin_otp_login():
    print("\n--- ADMINISTRATOR ACCESS PORTAL ---")
    email = input("Enter admin email address: ").strip()
    
    cur.execute("SELECT name FROM alladmins WHERE emailid = %s", (email,))
    admin_exists = cur.fetchone()
    
    if not admin_exists:
        print("Access Denied: Email address is not authorized as an Administrator.")
        return False

    otp = generate_otp()
    store_otp(email, otp)
    
    if send_email(otp, email):
        print(f"A 2-Step Verification code has been dispatched to {email}.")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            user_otp = input("Enter 6-Digit OTP: ").strip()
            if verify_otp(email, user_otp):
                print(f"Authentication Successful. Welcome back, {admin_exists[0]}.")
                admin_menu()
                return True
            if attempt < max_attempts:
                print(f"Invalid verification code. {max_attempts - attempt} attempts remaining.")
        print("Security Alert: Max attempts reached. Session terminated.")
    else:
        print("System Error: Failed to initiate secure multi-factor authentication dispatch loop.")
    return False

# ... [Keep your menu operations, voting logic, and queries as defined in your prompt]

def main_menu():
    while True:
        print("\n=== SECURE ONLINE VOTING SYSTEM ===")
        print("1. Administrator Access via Secure OTP")
        print("2. Student Registration & Terminal")
        print("3. Terminate System")
        choice = input("Select System Interface: ").strip()
        
        if choice == '1':
            admin_otp_login()
        elif choice == '2':
            class_num, section = student_login()
            if class_num is not None or section is not None:
                student_menu(class_num, section)
        elif choice == '3':
            print("Shutting down database pipelines... Operations ended securely.")
            break
        else:
            print("Operational Error: Option invalid.")

if __name__ == "__main__":
    try:
        main_menu()
    finally:
        cur.close()
        conn.close()
