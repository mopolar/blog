import sys
from flask import request, jsonify, abort
from flaskblog import app, db, bcrypt
from flaskblog.models import Token, Post, User
import datetime
import json


# method used to create a token that can be used
@app.route('/api/token/public', methods=['POST'])
def get_token():
	data = request.form 

	if 'email' not in data or 'password' not in data:
		return abort(400)  # HTTP code 400: bad request

	user = User.query.filter_by(email=data['email']).first()
	if user and bcrypt.check_password_hash(user.password, data['password']):
		# if login info is correct, create a new token
		expired = datetime.datetime.now() + datetime.timedelta(minutes=60)
		token_string = bcrypt.generate_password_hash(str(expired)).decode('utf-8')
		new_token = Token(token=token_string, date_expired=expired, user_id=user.id)
		db.session.add(new_token)
		try:
			db.session.commit()
			return jsonify({'token': token_string,
							'message': 'Login successful!',
							'user_id': user.id,
							'expire': expired.strftime('%Y-%m-%d %H:%M:%S')})
		except:
			db.session.rollback()
			return abort(400)  # HTTP code 400: bad request
	else:
		info = dict(message='Login Unsuccessful. Please check email and password.')
		return jsonify(info)


# inform user of the webservice about its capabilities
@app.route('/api/', methods=['GET'])
def api():
	info = dict()
	info['message'] = 'This is the API to consume blog posts'
	info['services'] = []
	info['services'].append({'url': '/api/posts', 'method': 'GET', 'description': 'Gets a list of posts'})
	return jsonify(info)


# method that returns all the posts
@app.route('/api/posts', methods=['GET'])
def api_get_posts():
	posts = Post.query.all()
	return jsonify([i.serialize for i in posts])


# method that returns a specific post
@app.route('/api/post/<int:post_id>', methods=['GET'])
def api_get_post(post_id):
	post = Post.query.get_or_404(post_id)
	return jsonify(post.serialize)


# method that inserts a new post
@app.route('/api/posts', methods=['POST'])
def api_create_post():
	data = request.json

	token_string = request.headers['Authorization'].split(' ')[1]
	token = Token.query.filter_by(token=token_string).first()

	if 'title' in data and 'content_type' in data and 'content' in data:
		post = Post(title=data['title'],
					content_type=data['content_type'],
					content=data['content'],
					user_id=token.user_id)
		db.session.add(post)
		try:
			db.session.commit()
			return jsonify(post), 201  # status 201 means "CREATED"
		except Exception as e:
			print('The WebService API experienced an error: ', e, file=sys.stderr)
			db.session.rollback()
			abort(400)
	else:
		return abort(400)  # HTTP code 400: bad request


# method PUT replaces the entire object
@app.route('/api/post/<int:post_id>', methods=['PUT'])
def api_update_post(post_id):
	post = Post.query.get_or_404(post_id)
	data = request.json

	token_string = request.headers['Authorization'].split(' ')[1]
	cur_token = Token.query.filter_by(token=token_string).first()
	if cur_token.user_id != post.user_id:
		abort(401)

	if 'title' in data and 'content_type' in data and 'content' in data and 'user' in data:
		post.title = data['title']
		post.content_type = data['content_type']
		post.content = data['content']
		try:
			db.session.commit()
			return jsonify(post), 200
		except Exception as e:
			print('The WebService API experienced an error: ', e, file=sys.stderr)
			db.sesion.rollback()
			abort(400)
	else:
		return abort(400)  # HTTP code 400: bad request


# method PATCH changes only a few (not always all) the attributes of the object
@app.route('/api/post/<int:post_id>', methods=['PATCH'])
def api_replace_post(post_id):
	post = Post.query.get_or_404(post_id)
	data = request.json

	token_string = request.headers['Authorization'].split(' ')[1]
	cur_token = Token.query.filter_by(token=token_string).first()
	if cur_token.user_id != post.user_id:
		abort(401)

	if 'title' in data or 'content_type' in data or 'content' in data:
		if 'title' in data:
			post.title = data['title']
		if 'content_type' in data:
			post.content_type = data['content_type']
		if 'content' in data:
			post.content = data['content']

		try:
			db.session.commit()
			return jsonify(post), 200
		except Exception as e:
			print('The WebService API experienced an error: ', e, file=sys.stderr)
			abort(400)
	else:
		return abort(400)  # HTTP code 400: bad request


# method that deletes one post by its id
@app.route('/api/post/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
	post = Post.query.get_or_404(post_id)

	token_string = request.headers['Authorization'].split(' ')[1]
	cur_token = Token.query.filter_by(token=token_string).first()
	if cur_token.user_id != post.user_id:
		abort(401)

	db.session.delete(post)
	try:
		db.session.commit()
		return jsonify({'message': f'Post {post_id} deleted'}), 200
	except Exception as e:
		print('The WebService API experienced an error: ', e, file=sys.stderr)
		db.session.rollback()
		abort(400)  # HTTP code 400: bad request
