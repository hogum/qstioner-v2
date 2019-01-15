"""
    This module contains the database queries used in the application models
"""

CREATE_TABLE_USERS = """
    CREATE TABLE IF NOT EXISTS USERS (
    ID SERIAL PRIMARY KEY NOT NULL,
    FIRSTNAME VARCHAR(60) NOT NULL,
    LASTNAME VARCHAR(60) NOT NULL,
    OTHERNAME VARCHAR(50),
    USERNAME VARCHAR(30) NOT NULL,
    EMAIL VARCHAR(40) NOT NULL,
    ISADMIN BOOLEAN DEFAULT FALSE,
    PHONENUMBER INTEGER NOT NULL
    );
"""

CREATE_TABLE_MEETUPS = """
    CREATE TABLE IF NOT EXISTS MEETUPS (
    ID SERIAL PRIMARY KEY NOT NULL,
    TOPIC VARCHAR(112) NOT NULL,
    IMAGES VARCHAR(1024)[],
    LOCATION VARCHAR(50) NOT NULL,
    HAPPENING_ON DATE NOT NULL DEFAULT CURRENT_DATE,
    TAGS TEXT []
    );
"""

CREATE_TABLE_QUESTIONS = """
    CREATE TABLE IF NOT EXISTS QUESTIONS (
    ID SERIAL PRIMARY KEY NOT NULL,
    TITLE VARCHAR(40) NOT NULL;
    BODY VARCHAR(40) NOT NULL,
    CREATED_BY INTEGER REFERENCES USERS (ID),
    MEETUP INTEGER REFERENCES MEETUPS(ID),
    VOTES INTEGER NOT NULL,
    CREATED_AT DATE DEFAULT CURRENT_DATE
    );
"""

CREATE_TABLE_RSVPS = """
    CREATE TABLE IF NOT EXISTS RSVPS (
    ID SERIAL NOT NULL,
    MEETUP INTEGER NOT NULL,
    USER INTEGER NOT NULL,
    PRIMARY KEY(USER, MEETUP)
    );
"""

CREATE_TABLE_TOKENS = """
    CREATE TABLE IF NOT EXISTS TOKENS (
    ID SERIAL PRIMARY KEY NOT NULL,
    TOKEN VARCHAR(256)
    );
"""

CREATE_USER = """
    INSERT INTO users (firstname, lastname, othername, email,
    username, isadmin, phonenumber)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id, firstname, lastname, othername, email,
    username, isadmin, phonenumber;
"""

DROP_TABLES = """
    DROP TABLE IF EXISTS USERS, MEETUPS, QUESTIONS, RSVPS
    TOKENS;
"""

GET_USER_BY_NAME = """
        SELECT * FROM USERS WHERE name = %s
"""

GET_BY_EMAIL = """
        SELECT * FROM USERS WHERE email = %s
"""
