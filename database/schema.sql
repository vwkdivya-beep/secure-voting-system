-- Secure Online Voting System Relational Schema
CREATE DATABASE IF NOT EXISTS vote;
USE vote;

CREATE TABLE IF NOT EXISTS alladmins (
    teacher_id VARCHAR(20) PRIMARY KEY,
    emailid VARCHAR(250) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_otp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(250) NOT NULL UNIQUE,
    otp_hash VARCHAR(64) NOT NULL,
    expire_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS polls (
    poll_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    start_time DATE NOT NULL,
    end_time DATE NOT NULL,
    created_by VARCHAR(250) NOT NULL,
    class_num INT,
    sec VARCHAR(5)
);

CREATE TABLE IF NOT EXISTS poll_options (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    poll_id INT,
    teacher_id VARCHAR(20),
    option_text VARCHAR(255) NOT NULL,
    vote_count INT DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls(poll_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS poll_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    poll_id INT NOT NULL,
    voter_email VARCHAR(250) NOT NULL,
    choice VARCHAR(255) NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_poll_voter (poll_id, voter_email),
    FOREIGN KEY (poll_id) REFERENCES polls(poll_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stud_log (
    adm_no INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(250) NOT NULL,
    class_num INT,
    sec VARCHAR(5),
    roll_no INT NOT NULL
);
