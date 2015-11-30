from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Movie, User
import re

engine = create_engine('postgres://csajqmbvzicfmy:Ziw2YSvCtPWiYebo6GkSqnEpZN@ec2-54-197-253-142.compute-1.amazonaws.com:5432/d4jhvu06cnvfpe')
# engine = create_engine('sqlite:///movies.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def reformat(trailer):
	# re-format the movies structure
	youtube_id_match = re.search(r'(?<=v=)[^&#]+', trailer)
	youtube_id_match = youtube_id_match or re.search(r'(?<=be/)[^&#]+', trailer)
	trailer_youtube_id = (youtube_id_match.group(0) if youtube_id_match else None)
	return trailer_youtube_id

user1 = User(name="Qi Chen", email="chittychen90@gmail.com")
session.add(user1)
session.commit()

trailer = reformat("https://www.youtube.com/watch?v=seMwpP0yeu4")
movie1 = Movie(user_id=1, name="Inside Out", poster="http://screenrant.com/wp-content/uploads/inside-out-poster.jpg", trailer=trailer, genre="Animation")
session.add(movie1)
session.commit()

trailer = reformat("https://www.youtube.com/watch?v=2LqzF5WauAw")
movie2 = Movie(user_id=1,name="Interstellar", poster="http://www.hollywoodreporter.com/sites/default/files/custom/Blog_Images/interstellar3.jpg", trailer=trailer, genre="Sci-Fi")
session.add(movie2)
session.commit()

trailer = reformat("https://www.youtube.com/watch?v=Ym3LB0lOJ0o")
movie3 = Movie(user_id=1,name="Gone Girl", poster="https://dbmoviesblog.files.wordpress.com/2015/10/poster-gg.jpg", trailer=trailer, genre="drama")
session.add(movie3)
session.commit()

trailer = reformat("https://www.youtube.com/watch?v=KDvPcBeOn8E")
movie4 = Movie(user_id=1,name="Dallas Buyers Club", poster="http://cdn.collider.com/wp-content/uploads/dallas-buyers-club-poster1.jpg", trailer=trailer, genre="Biography")
session.add(movie4)
session.commit()


trailer = reformat("https://www.youtube.com/watch?v=z3biFxZIJOQ")
movie5 = Movie(user_id=1,name="Big Hero 6", poster="http://cdn.collider.com/wp-content/uploads/big-hero-6-poster-baymax-hi-res.jpg", trailer=trailer, genre="Animation")
session.add(movie5)
session.commit()


trailer = reformat("https://www.youtube.com/watch?v=u1uP_8VJkDQ")
movie6 = Movie(user_id=1,name="Nightcrawler", genre="Thriller", poster="http://cdn.collider.com/wp-content/uploads/nightcrawler-poster-final.jpg", trailer=trailer)
session.add(movie6)
session.commit()

print "Loaded Movies Successfully!"