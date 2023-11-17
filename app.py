from flask import Flask, jsonify, request, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'dbuserdbuser'
app.config['MYSQL_DB'] = 'e6156'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

DEFAULT_PER_PAGE = 1

def pagination_links(page, total_pages, endpoint, per_page, filters):
    links = {}

    # Include filters in pagination links
    filters_str = '&'.join([f"{key}={value}" for key, value in filters.items()])
    base_url = url_for(endpoint) + '?' + filters_str
    if filters_str != "":
        base_url += '&'

    links['first'] = base_url + f"page=1&per_page={per_page}"
    links['last'] = base_url + f"page={total_pages}&per_page={per_page}"
    links['current'] = base_url + f"page={page}&per_page={per_page}"
    links['prev'] = None
    links['next'] = None
    if page > 1:
        links['prev'] = base_url + f"page={page - 1}&per_page={per_page}"

    if page < total_pages:
        links['next'] = base_url + f"page={page + 1}&per_page={per_page}"

    return links

@app.route("/")
def hello_world():
    return "Hello World!\n"

@app.route('/api/review/', methods=['GET'])
def get_reviews():
    '''
        Get reviews (filter accepted)
    '''
    cur = mysql.connection.cursor()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))  # Default to 10 items per page

    filters = {key: value for key, value in request.args.items() if key not in ['page', 'per_page']}
    offset = (page - 1) * per_page

    query = f"SELECT * FROM review "
    query_filters = "WHERE 1=1"
    for key, value in filters.items():
        # Check the type of the value and format accordingly
        if isinstance(value, str):
            query_filters += f" AND {key} = '{value}'"
        else:
            query_filters += f" AND {key} = {value}"
    query += query_filters
    query += f" LIMIT {offset}, {per_page}"

    cur.execute(query)
    data = cur.fetchall()

    # Calculate total number of items and pages
    cur.execute(f"SELECT COUNT(*) FROM review "+query_filters)
    total_items = cur.fetchone()['COUNT(*)']
    total_pages = (total_items + per_page - 1) // per_page

    # Generate pagination links
    links = pagination_links(page, total_pages, 'get_reviews', per_page, filters)

    cur.close()

    return jsonify({'data': data, 'links': links})

@app.route('/api/review/<int:review_id>/', methods=['GET'])
def get_review_by_id(review_id):
    '''
        Get a review by review id
    '''
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM review WHERE review_id = %s''', (review_id,))
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/api/review/user/<int:user_id>/', methods=['GET'])
def get_review_by_user_id(user_id):
    '''
        Get all reviews under a specific user
    '''
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM review WHERE user_id = %s''', (user_id,))
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/api/review/', methods=['POST'])
def add_review():
    '''
        Add new review
    '''
    cur = mysql.connection.cursor()
    data = request.json

    keys = ', '.join(data.keys()) + ', pinned'
    values = ', '.join('%s' for _ in data.values()) + ', false'

    query = f"INSERT INTO review ({keys}) VALUES ({values})"

    cur.execute(query, tuple(data.values()))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review posted successfully'})

@app.route('/api/review/<int:review_id>/', methods=['PUT'])
def update_review(review_id):
    '''
        Update a review by review id
    '''
    cur = mysql.connection.cursor()
    data = request.json

    set_clause = ', '.join(f"{key} = %s" for key in data.keys())
    query = f"UPDATE review SET {set_clause} WHERE review_id = %s"

    cur.execute(query, tuple(data.values()) + (review_id,))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review updated successfully'})

@app.route('/api/admin/pin_review/<int:review_id>/', methods=['PUT'])
def pin_review(review_id):
    '''
        Pin a review by admin
    '''
    cur = mysql.connection.cursor()

    query = f"UPDATE review SET pinned = 1 WHERE review_id = %s"

    cur.execute(query, (review_id,))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review pinned successfully'})

@app.route('/api/review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    cur = mysql.connection.cursor()
    cur.execute('''DELETE FROM review WHERE review_id = %s''', (review_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review deleted successfully'})

@app.route('/api/review/comment/<int:comment_id>/', methods=['GET'])
def get_comment_by_id(comment_id):
    '''
        Get a comment by comment id
    '''
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM comment WHERE comment_id = %s''', (comment_id,))
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/api/review/<int:review_id>/comment/', methods=['GET'])
def get_comments_by_review_id(review_id):
    '''
        Get all comments for a review
    '''
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM comment WHERE review_id = %s''', (review_id,))
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/api/review/comment/', methods=['POST'])
def reply_review():
    '''
        Reply to a review
    '''
    cur = mysql.connection.cursor()
    data = request.json

    keys = ', '.join(data.keys())
    values = ', '.join('%s' for _ in data.values())

    query = f"INSERT INTO comment ({keys}) VALUES ({values})"

    cur.execute(query, tuple(data.values()))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review replied successfully'})

@app.route('/api/review/comment/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    '''
        Update a comment/like/dislike/report by comment id
    '''
    cur = mysql.connection.cursor()
    data = request.json

    set_clause = ', '.join(f"{key} = %s" for key in data.keys())
    query = f"UPDATE comment SET {set_clause} WHERE comment_id = %s"

    cur.execute(query, tuple(data.values()) + (comment_id,))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Comment updated successfully'})

@app.route('/api/review/comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    cur = mysql.connection.cursor()
    cur.execute('''DELETE FROM comment WHERE comment_id = %s''', (comment_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Comment deleted successfully'})

if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
