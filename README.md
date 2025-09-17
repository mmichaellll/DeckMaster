# DeckMaster

DeckMaster is a lightweight Flask web application for creating, organizing and studying flashcards and quizzes. It uses SQLite (via SQLAlchemy) for storage and includes simple session-based authentication, tag/category management, flashcard decks, a flashcard study view and a quiz flow.

## Features

- **User accounts:** register and login (session-based).
- **Flashcards:** create flashcards with question, answer, category and tag.
- **Decks:** flashcards are grouped into decks automatically by tag and user.
- **Flashcard study mode:** view flashcards for a selected tag and step through cards.
- **Quiz mode:** take a quiz for a selected tag and track score.
- **Admin data seeding:** initial categories and tags are inserted when the app first runs.

## Requirements

- Python 3.10+ (the workspace shows Python 3.12 artifacts but 3.10+ is recommended)
- `Flask`
- `SQLAlchemy`

Install dependencies (example):

```bash
python -m venv .venv
source .venv/bin/activate
pip install Flask SQLAlchemy
```

If you prefer, create a `requirements.txt` with these two lines:

```
Flask
SQLAlchemy
```

## Quick Start

1. Ensure dependencies are installed (see Requirements).
2. Run the app locally:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py
```

3. Open the app at `http://127.0.0.1:5000/` and register a new user.

Notes:

- The app uses a SQLite DB file named `flashcards.db` created next to `app.py`.
- On first run `initdb()` inserts a small set of default categories and tags.

## Database

- Database engine: SQLite (see `create_engine('sqlite:///flashcards.db')` in `app.py`).
- ORM/session: `database.py` (models and `Session` class are defined there).
- The app expects tables for `users`, `flashcards`, `categories`, `tags`, and `decks`.

If you need to recreate the DB, remove the `flashcards.db` file and restart the app. The app will re-create the file (models/migrations are in `database.py`).

## Routes (summary)

The following routes are implemented in `app.py`:

- `GET /` - Dashboard showing a user's decks and flashcards (requires login).
- `GET, POST /login` - Login page and authentication.
- `GET, POST /register` - Register a new user.
- `GET /logout` - Log out the current session.
- `GET, POST /addquestion` - Add a new flashcard (select category and tag).
- `GET, POST /addtag` - Add a new tag (login required).
- `GET, POST /addcategory` - Add a new category (login required).
- `GET, POST /flashcards` - Flashcard study setup (choose tag) and study mode.
- `POST /next_flashcard` - Advance to the next flashcard in study mode.
- `GET, POST /quiz_setup` - Setup a quiz (number of questions and tag).
- `GET, POST /quiz` - Take the quiz and track score.

See the templates in the `templates/` directory for the UI pages: `index.html`, `login.html`, `register.html`, `addquestion.html`, `addtag.html`, `addcategory.html`, `flashcard_setup.html`, `flashcards.html`, `quiz_setup.html`, `quiz.html`.

## Templates & Static

- Templates: `templates/` contains all Jinja2 templates.
- Static: `static/` contains `style.css` and an `images/` folder.

## Security Notes & Known Issues

This project is a simple demo and contains several security and correctness issues you should address before using it in production:

- **Plaintext passwords:** The code stores and compares raw passwords. Passwords must be hashed using a secure algorithm (e.g., `bcrypt` via `werkzeug.security` or `passlib`).
- **SQL injection risk:** Some places use Python f-strings to build SQL (for example in the `addtag` and `addcategory` routes). Use parameterized queries or SQLAlchemy ORM methods instead of string interpolation.
- **Session handling:** The app uses Flask sessions with a randomly generated `app.secret_key` which is fine for local development but should be configured from a secure environment variable in production.
- **Authentication helpers:** Consider using `Flask-Login` for a robust login/session management implementation.
- **Input validation/sanitization:** Several inputs are not thoroughly validated or sanitized (e.g., form inputs, numeric inputs). Add server-side validation and consider CSRF protection (e.g., `Flask-WTF`).

## Suggested Improvements

- Hash passwords and add a password reset flow.
- Replace raw SQL text and f-strings with SQLAlchemy ORM models and safe parameter binding.
- Add tests for the major flows (register/login, add card, study, quiz).
- Add pagination/filtering for large decks and an API for programmatic access.

## Contributing

Feel free to open issues or submit pull requests. If you make security fixes (password hashing, SQL parameterization), please include tests.

## License

This repository currently has no license file. Add a `LICENSE` if you want to allow others to reuse the code.
