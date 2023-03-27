import requests
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = "SECRET KEY"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-10-movies.db'
Bootstrap(app)
db = SQLAlchemy(app)
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
# Get you api key from the website
MOVIE_DB_API_KEY = "API_KEY"


class RateMovieForm(FlaskForm):
    """
    Makes a form.
    Used to ask the user to rate the movie out of 10 and to give a review
    """
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    """
    Makes a form.
    Used to ask the user to search for a movie
    """
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class Movie(db.Model):
    """
    Makes a movie database.
    Creates a movie data base.
    Use db.createall() to create the movie database
    Only needs to be run once.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


# Only needs to be written once. Can be commented out afterwards
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    """
    Renders home page
    Shows all the movies in the database ranked in order from lowest to highest (10 - 1)
    """
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()
    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    movie_count = len(all_movies)
    return render_template("index.html", movies=all_movies, count=movie_count)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    """
    Renders edit page
    Allows users to edit the movie they clicked on with a post request.
    """
    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_selected.rating = form.rating.data
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie_selected, form=form)


@app.route("/delete")
def delete_movie():
    """
    Deletes the movie with the given id
    """
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    """
    Renders add_movie page. Allows users to search up a movie and then it
    redirects the user to another page that uses the api to render all the movies
    with the given name in the database from themoviedb.org's database
    using an API.
    """
    form = AddMovieForm()
    if request.method == "POST":
        if form.validate_on_submit():
            movie_title = request.form["title"]
            response = requests.get(
                url=MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
            data = response.json()['results']
            return render_template("select.html", movies=data)
    return render_template("add.html", form=form)


@app.route("/find")
def get_movie_details():
    """
    When a movie is clicked on, the movie gets added to the data base and it redirects the user
    to edit the movie details such as the rating and the review. 
    The rest of the movie details gets autofilled from the API.
    """
    movie_id = request.args.get('id')
    if movie_id:
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key="
                                f"{MOVIE_DB_API_KEY}&language=en-US")
        data = response.json()
        new_movie = Movie(
            title=data['original_title'],
            year=data['release_date'].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
            description=data['overview']
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('rate_movie', id=new_movie.id))


if __name__ == '__main__':
    """
    Runs the program
    """
    app.run(debug=True)
