from sqlalchemy import create_engine, text, select
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import Session, Users, Flashcards, Categories,Decks,Tags
from time import sleep
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = 'secret'
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANANT"] = False
app.config["SESSION_TYPE"] = 'filesystem'

engine = create_engine('sqlite:///flashcards.db')
connection = engine.connect()


def initdb():
    categories = ["Mathematics Advanced", "Biology", "Modern History", "Physics", "Legal Studies"]
    tags = ["Algebra", "WW2", "Crime", "Electricity", "Plants"]
    dbsession = Session()
    try:
        for cat in categories:
            query = text("INSERT OR IGNORE INTO categories (name) VALUES (:cat)")
            dbsession.execute(query, {'cat':cat})
        for tag in tags:
            query = text(f"INSERT OR IGNORE INTO tags (tag_name) VALUES (:tag)")
            dbsession.execute(query, {'tag':tag})
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
        decks = dbsession.execute(text(
            "SELECT deck_id, name FROM decks WHERE user_id = :user_id"
        ),{'user_id':user_id}).fetchall()

        print("Decks:")
        for deck in decks:
            print(f"DeckID: {deck[0]}, Name: {deck[1]}")
        flashcards = {}
        for deck in decks:
            deck_id = deck[0]
            flashcardquery = text("""
                SELECT f.card_id, f.question, f.answer, c.name AS category_name, t.tag_name AS tag_name
                FROM flashcards f
                JOIN categories c ON f.category_id = c.category_id
                JOIN tags t ON f.tag_id = t.tag_id
                WHERE f.deck_id = :deck_id
            """)
            deckflashcards = dbsession.execute(flashcardquery,{'deck_id':deck_id}).fetchall()
            for card in deckflashcards:
                print(card)
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
        query = text("SELECT user_id, username FROM users WHERE username = :username AND password = :password")
        try:
            result = dbsession.execute(query,{'username':username,'password':password} ).fetchone()
            if result:
                user_id = result[0]
                msg="Successful Login!"
                session['username'] = username
                session['user_id'] = user_id
                return redirect(url_for("index"))

            else:
                msg="Wrong email/password! (or account doesn't exist!)"
        except Exception as e:
            msg="Error occured"
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
    categories = dbsession.execute(text(f"SELECT name FROM categories")).fetchall()
    tags = dbsession.execute(text(f"SELECT tag_name FROM tags")).fetchall()
    for category in categories:
        catnames.append(category[0])
    for tag in tags:
        tagnames.append(tag[0])


    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")
        tag = request.form.get("tag")
        category = request.form.get("category")
        current_time = datetime.now()
        username = session.get("username")
        try:
            # get userid
            user_id_result = dbsession.execute(
                text("SELECT user_id FROM users WHERE username = :username"),{'username':username}
                ).fetchone()
            if not user_id_result:
                flash("User not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            user_id = user_id_result[0]
            # get category id
            category_result = dbsession.execute(text(f"SELECT category_id FROM categories WHERE name = :category"),{'category':category}).fetchone()
            if not category_result:
                flash("Category not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            category_id = category_result[0]
            # get tag id
            tag_result = dbsession.execute(text("SELECT tag_id FROM tags WHERE tag_name = :tag"),{'tag':tag}).fetchone()
            if not tag_result:
                flash("Tag not found!!")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)
            tag_id = tag_result[0]
            # check if inputs are valid
            if not (question and answer and category_id and tag_id and user_id):
                flash("All fields are required")
                return render_template('addquestion.html', categories = categories, tags=tags,msg=msg)

            #find/create deck 
            deck_query = text("""
                SELECT deck_id FROM decks
                WHERE user_id = :user_id AND name = :tag
            """)

            deck_result = dbsession.execute(deck_query, {
                'user_id':user_id,
                'tag':tag
            }).fetchone()

            if not deck_result:
                # insert new deck to db
                insert_deck = text("""
                    INSERT INTO decks (user_id,name)
                    VALUES (:user_id,:tag)
                """)
                dbsession.execute(insert_deck, {'user_id':user_id, 'tag':tag})

                # get new deck's id 
                deck_result = dbsession.execute(deck_query,{'user_id':user_id, 'tag':tag}).fetchone()

            deck_id = deck_result[0]

            insertquery = text(
                f"""
                INSERT INTO flashcards (user_id, question, answer, category_id,tag_id,created_date, deck_id)
                VALUES (:user_id, :question, :answer, :category_id, :tag_id, :current_time, :deck_id)
                """
            )
            dbsession.execute(insertquery, {
                'user_id':user_id,
                'question': question,
                'answer': answer,
                'category_id': category_id,
                'tag_id': tag_id,
                'current_time':current_time, 
                'deck_id':deck_id
            })
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
            existingtags = dbsession.execute(text(
                f"SELECT * FROM tags WHERE tag_name = '{tag_name}'"
            )).fetchone()
            if existingtags:
                flash("Tag already exists!")
            else:
                dbsession.execute(text(
                    f"INSERT INTO tags (tag_name) VALUES ('{tag_name}')"
                ))
                dbsession.commit()
                flash("Tag successfully added!")
        except Exception as e:
            dbsession.rollback()
            flash("An error has occured while adding the tag :(")
            print(f"Erorr {e}")
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
            existingcat = dbsession.execute(text(
                f"SELECT * FROM categories WHERE name = '{category_name}'"
            )).fetchone()
            if existingcat:
                flash("Category already exists!")
            else:
                dbsession.execute(text(
                    f"INSERT INTO categories (name) VALUES ('{category_name}')"
                ))
                dbsession.commit()
                flash("Category successfully added!")
        except Exception as e:
            dbsession.rollback()
            flash("An error has occured while adding the category :(")
            print(f"Erorr {e}")
        finally:
            dbsession.close()
    return render_template("addcategory.html",msg=msg)

@app.route('/flashcards',methods=["POST","GET"])
@login_required
def flashcards():
    if request.method == "GET":
        dbsession = Session()
        try:
            tags = dbsession.execute(text("SELECT tag_name FROM tags")).fetchall()
            tag_names = []
            for tag in tags:
                tag_names.append(tag[0])
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
            flashcards = dbsession.execute(
                text(
                    """
                    SELECT question,answer
                    FROM flashcards f
                    JOIN tags t ON f.tag_id = t.tag_id 
                    WHERE t.tag_name = :tag 
                    """
                ), {'tag':tag}).fetchall()
            if not flashcards:
                flash("No flashcards found for the selected tag")
                return redirect(url_for("flashcards"))
            flashcard_dicts = []
            for flashcard in flashcards:
                flashcard_dict = {"question":flashcard[0], "answer":flashcard[1]}
                flashcard_dicts.append(flashcard_dict)
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
        tags = dbsession.execute(text("SELECT tag_name FROM tags"))
        tag_names = []
        for tag in tags:
            tag_names.append(tag[0])
        if request.method == "POST":
            num_questions = request.form.get("num_quest")
            tag = request.form.get("tag")

            if not num_questions.isdigit() or int(num_questions) <= 0:
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
        question_query = text("""
            SELECT f.question, f.answer 
            FROM flashcards f 
            JOIN tags t ON f.tag_id = t.tag_id
            WHERE t.tag_name = :tag AND f.user_id = :user_id
        """)
        questions = dbsession.execute(question_query, {'tag':tag, 'user_id':user_id}).fetchall()
        if not questions:
            flash("No questions found for the tag")
            return redirect(url_for("quiz_setup"))
        print(questions)
        if current_question_index >= num_questions or current_question_index >= len(questions):
            flash(f"Quiz Completed! Your score: {session.get('quiz_score')}/{num_questions}")
            session.pop('quiz_tag', None)
            session.pop('quiz_num_questions',None)
            session.pop('quiz_current_question',None)
            session.pop('quiz_score',None)
            return redirect(url_for("index"))

        current_question, correct_answer = questions[current_question_index]
        
        if request.method == "POST":
            user_answer = request.form.get("user_answer")
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
        dbsession = Session()
        new_user = Users(username=username, email=email, password=password)
        dbsession.add(new_user)
        try:
            dbsession.commit()
            return redirect(url_for("login"))
        except Exception:
            dbsession.rollback()
        finally:
            dbsession.close()
    return render_template('register.html')

@app.route("/logout")
def logout():
    session['username'] = None
    return redirect(url_for("index"))   


if __name__ == '__main__':
    app.run(debug=True)
