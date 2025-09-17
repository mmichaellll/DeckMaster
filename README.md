# DeckMaster

DeckMaster is a small Flask application for creating, organizing and studying flashcards. It uses SQLAlchemy ORM with a SQLite database and provides session-based authentication, tag/category management, deck grouping, a flashcard study mode and a quiz flow.

## Quick features

- Register and login users (hashed passwords).
- Create flashcards with question, answer, category and tag.
- Decks are grouped per-user and by tag.
- Study flashcards by tag and step through cards.
- Quiz mode: pick a tag and number of questions, track score.

## Requirements

- Python 3.10+
- Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Start the app locally:

```bash
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## Key files

- `app.py` — Flask routes and application logic.
- `database.py` — SQLAlchemy ORM models and session setup.
- `templates/` — Jinja2 templates for the UI.
- `static/` — CSS and images.

## Routes (summary)

- `/` — Dashboard with decks and flashcards (login required).
- `/login` — Login page.
- `/register` — Register a new user.
- `/logout` — Log out.
- `/addquestion` — Add a flashcard.
- `/addtag` — Add a tag.
- `/addcategory` — Add a category.
- `/flashcards` — Setup study mode and view flashcards.
- `/next_flashcard` — Advance to next flashcard.
- `/quiz_setup` — Setup quiz (select tag and number of questions).
- `/quiz` — Take quiz and track score.

## Database

The app uses SQLite (`flashcards.db`) and defines models in `database.py`: `Users`, `Flashcards`, `Categories`, `Decks`, and `Tags` with relationships configured.
