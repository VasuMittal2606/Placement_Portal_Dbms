# CampusHire – College Placement Portal

CampusHire is a **database-driven college placement portal** designed to manage the complete campus recruitment process through a centralized MySQL database.

The system provides separate interfaces for **Students, Recruiters, and Placement Officers**, covering profiles, job opportunities, applications, interviews, offers, and placements.

The primary focus is the **practical application of DBMS and MySQL concepts**, while Streamlit provides a user-friendly interface for interacting with the database.

## 🛠️ Technology Stack

| Component          | Technology        |
| ------------------ | ----------------- |
| Frontend           | Streamlit         |
| Backend            | Python            |
| Database           | MySQL             |
| Database Connector | `mysql.connector` |
| Version Control    | Git & GitHub      |

### Application Architecture

```text
Streamlit UI
     ↓
Python
     ↓
mysql.connector
     ↓
MySQL Database
```

---

## 👥 User Roles

### Student

* Manage profile and skills
* Browse available jobs
* Check eligibility
* Apply for jobs
* Track applications
* View interviews and offers

### Recruiter

* Manage company information
* Create and manage job openings
* Set eligibility and skill requirements
* View and shortlist applicants
* Schedule interviews
* Update interview results
* Make offers

### Placement Officer

* Manage students, companies, and jobs
* Monitor applications and interviews
* Manage offers and placements
* View placement statistics and reports

---

## 🔑 Key Features

* Role-based login and dashboards
* Student profile and skill management
* Job posting and management
* Job eligibility checking
* Application tracking
* Candidate shortlisting
* Interview scheduling and results
* Offer and placement management
* Placement analytics and reports
* Database-level validation and workflow management

Important application logic is handled through MySQL wherever possible.

Example:

```text
Student clicks "Apply"
        ↓
Streamlit
        ↓
Python + mysql.connector
        ↓
MySQL Procedure
        ↓
Eligibility & validation
        ↓
Application created
        ↓
Result displayed in Streamlit
```

---

## 🗄️ Database Structure

The database will be designed using an ER model and converted into a relational schema.

The final database may include entities such as:

```text
USER
STUDENT
SKILL
STUDENT_SKILL
COMPANY
JOB
JOB_SKILL
APPLICATION
INTERVIEW
OFFER
PLACEMENT
PLACEMENT_OFFICER
```

The schema will be refined according to the final application requirements.

---

## 📂 Project Structure

```text
CampusHire/
│
├── app.py
│
├── pages/
│   ├── login.py
│   ├── student.py
│   ├── recruiter.py
│   └── officer.py
│
├── database/
│   ├── connection.py
│   ├── student_db.py
│   ├── recruiter_db.py
│   ├── application_db.py
│   └── placement_db.py
│
├── mysql/
│   ├── schema.sql
│   ├── procedures.sql
│   ├── functions.sql
│   ├── triggers.sql
│   └── sample_data.sql
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd CampusHire
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Create the CampusHire database and execute the SQL files.

Configure the MySQL credentials in the Python database connection file.

**Do not commit passwords or other credentials to GitHub.**

### 5. Run the application

```bash
streamlit run app.py
```

---

## 🚀 Future Scope

Possible future improvements include:

* Resume management
* Email notifications
* Automated interview scheduling
* Advanced recruitment analytics
* Candidate recommendation
* Deployment for multiple colleges
