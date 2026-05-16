# Secure Multi-Factor Authentication (MFA) Digital Voting Infrastructure

An enterprise-ready, terminal-driven relational database application providing authenticated voting mechanisms for scholastic and institutional administration. Developed explicitly using Python 3 and MySQL relational schema architecture.

## Core Engineering Paradigms

* **Two-Step Secure Authentication Loop:** Integrates automated runtime 6-digit numeric generation protocols utilizing Python `random` pipelines.
* **Cryptographic MFA Verification System:** Sensitive authorization tokens are abstracted via salted `SHA-256` hashing mechanics inside volatile relational tables, protecting against downstream data exposure vulnerabilities.
* **Automated Ephemeral Data Windows:** Implements dynamic token lifecycle monitoring using `datetime` object tracking, introducing automated invalidation gates 5 minutes post-dispatch.
* **Relational Query Validation & Constraint Management:** Implements unique tuple keys (`uniq_poll_voter`) across target candidate parameters to eliminate voter fraud or double-voting conditions natively at the database level.

## System Architecture

### Relational Schema Diagram
* **alladmins:** Stores verified identity indexes mapped to primary administrator emails.
* **user_otp:** Manages active verification hashes, expiry structures, and authentication addresses.
* **polls:** Tracks structural configurations, scoping constraints (Class/Section restrictions), and lifespans of administrative items.
* **poll_votes:** Primary auditing ledger capturing immutable logs mapping specific student identities to unique poll decisions.

## Installation & Deployment Documentation

### 1. Configure Prerequisites
Ensure you run a structured local MySQL instance. Install operational packages via the terminal module:
```bash
pip install mysql-connector-python
