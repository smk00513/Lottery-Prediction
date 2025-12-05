Lotto Analysis and Personalized Recommendation System

This project provides a full-stack system for analyzing lotto data and generating personalized number recommendations using statistical models.

1. Prerequisites

Before running the system, ensure the following are installed:

Python 3.8+

PostgreSQL (running)

Project CSV files

1600.csv

6011200.csv

2. Environment Setup and Dependency Installation
2.1 Create Python Virtual Environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows CMD
# .\venv\Scripts\Activate     # Windows PowerShell

2.2 Install Required Libraries
pip install -r requirements.txt

2.3 Create .env File

Create a .env file in the project root:

SECRET_KEY="your_secret_key_here_must_be_long"

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="lotto_project"
DB_USER="postgres"
DB_PASSWORD="your_db_password"

3. Database Initialization
3.1 Create PostgreSQL Database

Create a new database named:

lotto_project


(or the name set in .env)

3.2 Create Required Tables

Execute the following SQL:

CREATE TABLE user_account (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    join_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(10)
        CHECK (status IN ('active', 'inactive'))
        DEFAULT 'active'
);

CREATE TABLE lotto_draw (
    draw_no INT PRIMARY KEY,
    draw_date DATE NOT NULL,

    n1 INT CHECK (n1 BETWEEN 1 AND 45),
    n2 INT CHECK (n2 BETWEEN 1 AND 45),
    n3 INT CHECK (n3 BETWEEN 1 AND 45),
    n4 INT CHECK (n4 BETWEEN 1 AND 45),
    n5 INT CHECK (n5 BETWEEN 1 AND 45),
    n6 INT CHECK (n6 BETWEEN 1 AND 45),
    bonus INT CHECK (bonus BETWEEN 1 AND 45),

    CONSTRAINT draw_sorted_and_distinct CHECK (
        n1 < n2 AND n2 < n3 AND n3 < n4 AND n4 < n5 AND n5 < n6
        AND bonus NOT IN (n1, n2, n3, n4, n5, n6)
    )
);

CREATE TABLE user_pick (
    pick_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES user_account(user_id),
    draw_no INT NOT NULL REFERENCES lotto_draw(draw_no),
    reg_date TIMESTAMP DEFAULT NOW(),

    p1 INT CHECK (p1 BETWEEN 1 AND 45),
    p2 INT CHECK (p2 BETWEEN 1 AND 45),
    p3 INT CHECK (p3 BETWEEN 1 AND 45),
    p4 INT CHECK (p4 BETWEEN 1 AND 45),
    p5 INT CHECK (p5 BETWEEN 1 AND 45),
    p6 INT CHECK (p6 BETWEEN 1 AND 45),

    CONSTRAINT pick_sorted_and_distinct CHECK (
        p1 < p2 AND p2 < p3 AND p3 < p4 AND p4 < p5 AND p5 < p6
    ),

    match_count INT DEFAULT 0,
    is_bonus_match BOOLEAN DEFAULT FALSE,
    ranking INT DEFAULT 0
);

CREATE TABLE recommend_result (
    rec_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES user_account(user_id),
    draw_target INT NOT NULL,

    r1 INT CHECK (r1 BETWEEN 1 AND 45),
    r2 INT CHECK (r2 BETWEEN 1 AND 45),
    r3 INT CHECK (r3 BETWEEN 1 AND 45),
    r4 INT CHECK (r4 BETWEEN 1 AND 45),
    r5 INT CHECK (r5 BETWEEN 1 AND 45),
    r6 INT CHECK (r6 BETWEEN 1 AND 45),

    model_version VARCHAR(50),
    used_pick_id INT UNIQUE REFERENCES user_pick(pick_id),

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT rec_sorted_and_distinct CHECK (
        r1 < r2 AND r2 < r3 AND r3 < r4 AND r4 < r5 AND r5 < r6
    )
);

CREATE TABLE lotto_stat (
    number INT PRIMARY KEY
        CHECK (number BETWEEN 1 AND 45),

    frequency INT DEFAULT 0,
    last_draw_gap INT DEFAULT NULL
);

3.3 Load Initial Draw Data
python scripts/load_lotto_data.py

3.4 Update Statistics and Recommendation View
Update Statistics
from services.stat_service import StatService
StatService.update_statistics()

Create Recommendation View

Executed automatically during statistics update:

from services.recommend_service import RecommendService
RecommendService.create_recommend_view_only()

4. Running the Web Application
Set Flask App
export FLASK_APP=app.py

(Optional) Enable Development Mode
export FLASK_ENV=development

Run Server
flask run


Open in browser:

http://127.0.0.1:5000