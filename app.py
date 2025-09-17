from sqlalchemy import select
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import Session, Users, Flashcards, Categories, Decks, Tags
from werkzeug.security import generate_password_hash, check_password_hash
from time import sleep
from datetime import datetime
from functools import wraps
import secrets


app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = secrets.token_urlsafe(32)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = 'filesystem'

# Database engine is configured in `database.py` and sessions are provided by `Session`.


def initdb():
    categories = ["Mathematics Advanced", "Biology", "Modern History", "Physics", "Legal Studies"]
    tags = ["Algebra", "WW2", "Crime", "Electricity", "Plants"]
    dbsession = Session()
    try:
        for cat in categories:
            existing = dbsession.execute(select(Categories).filter_by(name=cat)).scalar_one_or_none()
            if not existing:
                dbsession.add(Categories(name=cat))
        for tag in tags:
            existing = dbsession.execute(select(Tags).filter_by(tag_name=tag)).scalar_one_or_none()
            if not existing:
                dbsession.add(Tags(tag_name=tag))
        dbsession.commit()
    except Exception as e:
        dbsession.rollback()
        print(f"error: {e}")
    finally:
        dbsession.close()

initdb()

def login_required(f):
    """Decorate routes to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def check_pass(password):
    #check that > 8 char, contains upper and lower and a digit
    if len(password) <8:
        return False
    #look for upper
    found = False
    for letter in password:
        if letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            found = True
    if not found:
        return False
    #look for lower
    found = False
    for letter in password:
        if letter in "abcdefghijklmnopqrstuvwxyz":
            found = True
    if not found:
        return False
    #look for digit
    found = False
    for letter in password:
        if letter in "0123456789":
            found = True
    if not found:
        return False
    return True

@app.route('/')
@login_required
def index():
    user_id = session.get("user_id")

    dbsession = Session()

    try:
        print(f"UserID: {user_id}")
        decks = dbsession.execute(select(Decks).filter_by(user_id=user_id)).scalars().all()

        print("Decks:")
        for deck in decks:
            print(f"DeckID: {deck.deck_id}, Name: {deck.name}")
        flashcards = {}
        for deck in decks:
            deck_id = deck.deck_id
            deckflashcards = dbsession.execute(
                select(Flashcards).filter_by(deck_id=deck_id)
            ).scalars().all()
            for card in deckflashcards:
                print((card.card_id, card.question, card.answer, card.category.name if card.category else None, card.tag.tag_name if card.tag else None))
            flashcards[deck_id] = deckflashcards
        return render_template('index.html',decks=decks,flashcards=flashcards)
    except Exception as e:
        dbsession.rollback()
        flash("An Erorr Occured!")
        print(f"Error: {e}")
        return redirect(url_for('login'))
    finally:
        dbsession.close()
@app.route('/login', methods=["POST","GET"])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        dbsession = Session()
        try:
            user = dbsession.execute(select(Users).filter_by(username=username)).scalar_one_or_none()
            if user and check_password_hash(user.password, password):
                msg = "Successful Login!"
                session['username'] = user.username
                session['user_id'] = user.user_id
                return redirect(url_for("index"))
            else:
                msg = "Wrong username/password! (or account doesn't exist!)"
        except Exception as e:
            msg = "Error occurred"
            print(e)
            dbsession.rollback()
        finally:
            dbsession.close()
    return render_template('login.html',msg=msg)

@app.route("/addquestion", methods=["POST","GET"])
def addquestion():
    msg=""
    catnames = []
    tagnames = []
    dbsession = Session()
    categories = dbsession.execute(select(Categories)).scalars().all()
    tags = dbsession.execute(select(Tags)).scalars().all()
    for category in categories:
        catnames.append(category.name)
    for tag in tags:
        tagnames.append(tag.tag_name)


    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")
        tag = request.form.get("tag")
        category = request.form.get("category")
        current_time = datetime.now()
        username = session.get("username")
        try:
            # get user
            user = dbsession.execute(select(Users).filter_by(username=username)).scalar_one_or_none()
            if not user:
                flash("User not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            user_id = user.user_id
            # get category
            category_obj = dbsession.execute(select(Categories).filter_by(name=category)).scalar_one_or_none()
            if not category_obj:
                flash("Category not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            category_id = category_obj.category_id
            # get tag
            tag_obj = dbsession.execute(select(Tags).filter_by(tag_name=tag)).scalar_one_or_none()
            if not tag_obj:
                flash("Tag not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            tag_id = tag_obj.tag_id
            # check if inputs are valid
            if not (question and answer and category_id and tag_id and user_id):
                flash("All fields are required")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)

            #find/create deck 
            deck = dbsession.execute(select(Decks).filter_by(user_id=user_id, name=tag)).scalar_one_or_none()
            if not deck:
                deck = Decks(user_id=user_id, name=tag)
                dbsession.add(deck)
                dbsession.flush()  # ensure deck.deck_id is populated
            deck_id = deck.deck_id

            new_card = Flashcards(
                user_id=user_id,
                question=question,
                answer=answer,
                category_id=category_id,
                tag_id=tag_id,
                created_date=current_time,
                deck_id=deck_id,
            )
            dbsession.add(new_card)
            dbsession.commit()
            flash("Flashcard successfully added!")
        except Exception as e:
            dbsession.rollback()
            flash("An error occured")
            print(f"Error: {e}")

        finally:
            dbsession.close()

    return render_template("addquestion.html", tags=tagnames,categories=catnames,msg=msg)

@app.route('/addtag', methods=["POST","GET"])
@login_required
def addtag():
    msg = ""
    if request.method == "POST":
        tag_name = request.form.get("tag_name")
        if not tag_name:
            flash("Tag name cannot be empty")
            return render_template("addtag.html",msg=msg)
        dbsession = Session()
        try:
            existing = dbsession.execute(select(Tags).filter_by(tag_name=tag_name)).scalar_one_or_none()
            if existing:
                flash("Tag already exists!")
            else:
                dbsession.add(Tags(tag_name=tag_name))
                dbsession.commit()
                flash("Tag successfully added!")
        except Exception as e:
            dbsession.rollback()
            flash("An error has occured while adding the tag :(")
            print(f"Error {e}")
        finally:
            dbsession.close()
    return render_template("addtag.html",msg=msg)

@app.route('/addcategory', methods=["POST","GET"])
@login_required
def addcategory():
    msg = ""
    if request.method == "POST":
        category_name = request.form.get("category_name")
        if not category_name:
            flash("Category name cannot be empty")
            return render_template("addcategory.html",msg=msg)
        
        dbsession = Session()
        try:
            existing = dbsession.execute(select(Categories).filter_by(name=category_name)).scalar_one_or_none()
            if existing:
                flash("Category already exists!")
            else:
                dbsession.add(Categories(name=category_name))
                dbsession.commit()
                flash("Category successfully added!")
        except Exception as e:
            dbsession.rollback()
            flash("An error has occured while adding the category :(")
            print(f"Error {e}")
        finally:
            dbsession.close()
    return render_template("addcategory.html",msg=msg)

@app.route('/flashcards',methods=["POST","GET"])
@login_required
def flashcards():
    if request.method == "GET":
        dbsession = Session()
        try:
            tags = dbsession.execute(select(Tags)).scalars().all()
            tag_names = [t.tag_name for t in tags]
            return render_template("flashcard_setup.html",tags=tag_names)
        finally:
            dbsession.close()
    else:
        tag = request.form.get("tag")
        if not tag:
            flash("Please select a tag")
            return redirect(url_for("flashcards"))
        dbsession = Session()
        try:
            tag_obj = dbsession.execute(select(Tags).filter_by(tag_name=tag)).scalar_one_or_none()
            if not tag_obj:
                flash("No flashcards found for the selected tag")
                return redirect(url_for("flashcards"))
            flashcards = dbsession.execute(select(Flashcards).filter_by(tag_id=tag_obj.tag_id)).scalars().all()
            if not flashcards:
                flash("No flashcards found for the selected tag")
                return redirect(url_for("flashcards"))
            flashcard_dicts = [{"question":f.question, "answer":f.answer} for f in flashcards]
            session['flashcards'] = flashcard_dicts
            session["current_card"] = 0

            return render_template("flashcards.html", flashcard=session['flashcards'][0])
        finally:
            dbsession.close()

@app.route("/next_flashcard",methods=["POST"])
@login_required
def next_flashcard():
    if "flashcards" not in session or 'current_card' not in session:
        flash("No flashcards avaliable, start again :)")
        return redirect(url_for("flashcards"))
    session['current_card'] += 1
    if session['current_card'] >= len(session['flashcards']):
        flash("You have completed all the flashcards!")
        return redirect(url_for("flashcards"))
    return render_template("flashcards.html",flashcard=session["flashcards"][session['current_card']])

@app.route('/quiz_setup',methods=["POST","GET"])
@login_required
def quiz_setup():
    dbsession = Session()
    try:
        tags = dbsession.execute(select(Tags)).scalars().all()
        tag_names = [t.tag_name for t in tags]
        if request.method == "POST":
            num_questions = request.form.get("num_quest")
            tag = request.form.get("tag")

            if not num_questions or not str(num_questions).isdigit() or int(num_questions) <= 0:
                flash("Enter a valid number of questions")
                return render_template("quiz_setup.html", tags=tag_names)
            session['quiz_tag'] = tag
            session['quiz_num_questions'] = int(num_questions)
            session['quiz_current_question'] = 0
            session['quiz_score'] = 0

            return redirect(url_for("quiz"))
    finally:
        dbsession.close()
    return render_template("quiz_setup.html",tags=tag_names)

@app.route("/quiz", methods=["GET","POST"])
@login_required
def quiz():
    dbsession = Session()
    tag = session.get('quiz_tag')
    num_questions = session.get('quiz_num_questions')
    current_question_index = session.get("quiz_current_question",0)
    user_id = session.get("user_id")

    try:
        tag_obj = dbsession.execute(select(Tags).filter_by(tag_name=tag)).scalar_one_or_none()
        if not tag_obj:
            flash("No questions found for the tag")
            return redirect(url_for("quiz_setup"))
        questions = dbsession.execute(select(Flashcards).filter_by(tag_id=tag_obj.tag_id, user_id=user_id)).scalars().all()
        if not questions:
            flash("No questions found for the tag")
            return redirect(url_for("quiz_setup"))
        if current_question_index >= num_questions or current_question_index >= len(questions):
            flash(f"Quiz Completed! Your score: {session.get('quiz_score')}/{num_questions}")
            session.pop('quiz_tag', None)
            session.pop('quiz_num_questions',None)
            session.pop('quiz_current_question',None)
            session.pop('quiz_score',None)
            return redirect(url_for("index"))

        current = questions[current_question_index]
        current_question = current.question
        correct_answer = current.answer

        if request.method == "POST":
            user_answer = request.form.get("user_answer","").strip()
            if user_answer.lower() == correct_answer.lower():
                session['quiz_score'] += 1
                flash("Correct!")
            else:
                flash(f"Incorrect - the correct answer was {correct_answer}")
            session['quiz_current_question'] += 1
            return redirect(url_for("quiz"))

        return render_template("quiz.html", question=current_question, current_index = current_question_index+1, total_questions=num_questions)
    finally:
        dbsession.close()
@app.route('/register', methods=["POST","GET"])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        # basic password policy check
        if not check_pass(password):
            flash("Password must be at least 8 characters and include upper, lower and a digit")
            return render_template('register.html')

        dbsession = Session()
        try:
            existing = dbsession.execute(select(Users).filter_by(username=username)).scalar_one_or_none()
            if existing:
                flash("Username already taken")
                return render_template('register.html')
            hashed = generate_password_hash(password)
            new_user = Users(username=username, email=email, password=hashed)
            dbsession.add(new_user)
            dbsession.commit()
            return redirect(url_for("login"))
        except Exception as e:
            dbsession.rollback()
            print(f"Error creating user: {e}")
        finally:
            dbsession.close()
    return render_template('register.html')

@app.route("/logout")
def logout():
    session['username'] = None
    return redirect(url_for("index"))   


if __name__ == '__main__':
    app.run(debug=True)
