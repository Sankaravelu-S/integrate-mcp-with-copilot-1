# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up and unregister students for activities
- Persist data in a local SQLite database

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Initialize or migrate the local database schema:

   ```
   sqlite3 data/school.sqlite < migrations/001_initial_schema.sql
   ```

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                         | Get all activities with details and current participant list |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`    | Sign up for an activity                                      |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove a student from an activity                             |

## Data Model

The application stores data in SQLite (`src/data/school.sqlite`) with these tables:

1. **activities**
   - `id`, `name`, `description`, `schedule`, `max_participants`
2. **users**
   - `id`, `email`
3. **enrollments**
   - `id`, `activity_id`, `user_id`

The app auto-creates missing tables at startup and seeds default activities when the database is empty.
