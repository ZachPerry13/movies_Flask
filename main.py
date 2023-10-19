from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, flash, session
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_BINDS'] = {'deleted_db': 'sqlite:///deleted_db.db'}
app.secret_key = 'vfsdwef2ef2fsdFdFSSFSEFef22f23432432rdfsdfasefwef'
db = SQLAlchemy(app)

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'home', 'static']  # Add 'home' and 'static' to the allowed routes

    # Exclude the flash message for GET requests
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        print(f"DEBUG: Endpoint: {request.endpoint}")
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))


bcrypt = Bcrypt(app)
def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

# Add the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class DeletedVideoModel(db.Model):
    __bind_key__ = 'deleted_db'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, nullable=False)
    likes = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"DeletedVideo(name={self.name}, views={self.views}, likes={self.likes})"
    
class VideoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, nullable=False)
    likes = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Video(name={self.name}, views={self.views}, likes={self.likes})"


video_put_args = reqparse.RequestParser()
video_put_args.add_argument("name", type=str, help="Name of the video is required", required=True)
video_put_args.add_argument("views", type=int, help="Views of the video", required=True)
video_put_args.add_argument("likes", type=int, help="Likes on the video", required=True)

video_update_args = reqparse.RequestParser()
video_update_args.add_argument("name", type=str, help="Name of the video is required")
video_update_args.add_argument("views", type=int, help="Views of the video")
video_update_args.add_argument("likes", type=int, help="Likes on the video")

resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'views': fields.Integer,
	'likes': fields.Integer
}

class Video(Resource):
	@marshal_with(resource_fields)
	def get(self, video_id):
		result = VideoModel.query.filter_by(id=video_id).first()
		if not result:
			abort(404, message="Could not find video with that id")
		return result

	@marshal_with(resource_fields)
	def put(self, video_id):
		args = video_put_args.parse_args()
		result = VideoModel.query.filter_by(id=video_id).first()
		if result:
			abort(409, message="Video id taken...")

		video = VideoModel(id=video_id, name=args['name'], views=args['views'], likes=args['likes'])
		db.session.add(video)
		db.session.commit()
		return video, 201

	@marshal_with(resource_fields)
	def patch(self, video_id):
		args = video_update_args.parse_args()
		result = VideoModel.query.filter_by(id=video_id).first()
		if not result:
			abort(404, message="Video doesn't exist, cannot update")

		if args['name']:
			result.name = args['name']
		if args['views']:
			result.views = args['views']
		if args['likes']:
			result.likes = args['likes']

		db.session.commit()

		return result


	def delete(self, video_id):
			video = VideoModel.query.get(video_id)
			if not video:
				error_message = {'error': 'Video not found'}
				return make_response(jsonify(error_message), 404)

			# Move the deleted video to the DeletedVideoModel
			deleted_video = DeletedVideoModel(
				name=video.name,
				views=video.views,
				likes=video.likes
			)

			# Use the existing db.session for the deleted_db
			db.session.add(deleted_video)
			db.session.commit()

			# Delete the video from the original database
			db.session.delete(video)
			db.session.commit()

			success_message = {'message': 'Video deleted successfully', 'id': video.id}
			return make_response(jsonify(success_message), 200)




api.add_resource(Video, "/video/<int:video_id>")


# Add a new route to handle movie addition
@app.route('/video', methods=['GET', 'POST'])
def handle_video():
    if request.method == 'GET':
        # Handle GET request (e.g., display a form)
        return render_template('your_get_template.html')
    elif request.method == 'POST':
        # Handle POST request (e.g., add a new video)
        args = video_put_args.parse_args()
        video = VideoModel(name=args['name'], views=args['views'], likes=args['likes'])
        db.session.add(video)
        db.session.commit()
        return render_template('your_post_template.html', video=video)

@app.route('/')
def home():
    return render_template('index.html')

# Change the route to query the VideoModel
@app.route('/delete_video_form')
def delete_video_form():
    videos = VideoModel.query.all()  # Query the main database
    return render_template('delete_video.html', videos=videos)

@app.route('/add_video_form')
def add_video_form():
    return render_template('add_video_form.html')

@app.route('/all_videos')
def all_videos():
    videos = VideoModel.query.all()
    return render_template('all_videos.html', videos=videos)

# Change the route to query the DeletedVideoModel
@app.route('/deleted_videos')
def deleted_videos():
    videos = DeletedVideoModel.query.all()
    return render_template('deleted_videos.html', videos=videos)


# Route to get all videos
@app.route('/api/videos', methods=['GET'])
def get_all_videos():
    videos = VideoModel.query.all()
    video_list = [{'id': video.id, 'name': video.name, 'views': video.views, 'likes': video.likes} for video in videos]
    return jsonify(video_list)

# Route to add a new video
@app.route('/api/videos', methods=['POST'])
def add_video():
    try:
        data = request.json

        if data is None:
            return jsonify({'error': 'Missing JSON data in the request body'}), 400

        required_fields = ['id', 'name', 'likes', 'views']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        video_data = {
            'id': int(data['id']),
            'name': data['name'],
            'likes': int(data['likes']),
            'views': int(data['views'])
        }
        # Create a new VideoModel object and add it to the database
        new_video = VideoModel(**video_data)
        db.session.add(new_video)
        db.session.commit()

        return jsonify({'message': 'Video added successfully'}), 201

    except IntegrityError as e:
        # Handle unique constraint violation
        db.session.rollback()  # Rollback the transaction to avoid leaving the database in an inconsistent state
        return jsonify({'error': 'Provided ID is not unique'}), 409  # HTTP status code 409 for conflict

    except Exception as e:
        return jsonify({'error': f'Error processing the request: {str(e)}'}), 500
    
# Route to get all deleted videos
@app.route('/api/deleted_videos', methods=['GET'])
def get_all_deleted_videos():
    videos = DeletedVideoModel.query.all()
    video_list = [{'id': video.id, 'name': video.name, 'views': video.views, 'likes': video.likes} for video in videos]
    return jsonify(video_list)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # If it's a GET request, render the registration form
        return render_template('register.html')
    elif request.method == 'POST':
        try:
            # Get user data from the request
            data = request.form

            # Check if request.form is None
            if not data:
                flash('Missing form data in the request body', 'danger')
                return redirect(url_for('register'))

            # Validate the presence of required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if field not in data:
                    flash(f'Missing required field: {field}', 'danger')
                    return redirect(url_for('register'))

            # Hash the password (you may use your preferred method for this)
            hashed_password = hash_password(data['password'])

            # Create a new User object
            new_user = User(username=data['username'], email=data['email'], password=hashed_password)

            # Add the user to the database
            db.session.add(new_user)
            db.session.commit()

            flash('User registered successfully. You can now log in.', 'success')
            return redirect(url_for('login'))

        except IntegrityError as e:
            # Handle unique constraint violation (email already exists)
            db.session.rollback()  # Rollback the transaction to avoid leaving the database in an inconsistent state
            flash('Email is already in use. Please choose a different email.', 'danger')
            return redirect(url_for('register'))

        except Exception as e:
            flash(f'Error processing the request: {str(e)}', 'danger')
            return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user_id in the session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')

    return render_template('login.html')

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=443,ssl_context=('cert.pem','key.pem'), debug=True)