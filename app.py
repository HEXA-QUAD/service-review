# https://codelabs.developers.google.com/codelabs/cloud-app-engine-python3#0
# https://columbiauniversity.zoom.us/rec/play/wCYEMPxn-r4h_sooepcAcp7WIvt9DuL85rA08it3yq-AhuGF13NtzqcRCoZWW9D6KE5bimxq-NBu5PkO.k-ZYTjoKJlMIxC0P

from flask import Flask, jsonify, request, url_for
from flask_mysqldb import MySQL
from sendSNS import send2SNS
import requests
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'database-1.cvlxq8ccnbut.us-east-1.rds.amazonaws.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'Natalie3399!'
app.config['MYSQL_DB'] = 'review'

# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'dbuserdbuser'
# app.config['MYSQL_DB'] = 'e6156'

app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

DEFAULT_PER_PAGE = 10

profanity_api_url = 'https://api.api-ninjas.com/v1/profanityfilter'

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
def home_page():
    return "review API!\n"

@app.route('/api/review/', methods=['GET'])
def get_review():
    '''
        Get reviews (filter accepted)
    '''
    cur = mysql.connection.cursor()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))

    filters = {key: value for key, value in request.args.items() if key not in ['page', 'per_page']}
    offset = (page - 1) * per_page

    query = f"SELECT * FROM review "
    query_filters = "WHERE 1=1"
    for key, value in filters.items():
        if isinstance(value, str):
            query_filters += f" AND {key} = '{value}'"
        else:
            query_filters += f" AND {key} = {value}"
    query += query_filters
    query += f" LIMIT {offset}, {per_page}"

    cur.execute(query)
    data = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) FROM review "+query_filters)
    total_items = cur.fetchone()['COUNT(*)']
    total_pages = (total_items + per_page - 1) // per_page

    links = pagination_links(page, total_pages, 'get_review', per_page, filters)

    cur.close()
    return jsonify({'data': data, 'links': links})

@app.route('/api/review/', methods=['POST'])
def post_review():
    '''
        post a new review
    '''
    cur = mysql.connection.cursor()
    data = request.json

    api_url = profanity_api_url + '?text={}'.format(data['contents'])
    response = requests.get(api_url, headers={'X-Api-Key': 'M0eB3+yE0Y1SeYEcPge8pw==RCoIJ0GIrXiOguwn'})
    if response.status_code == requests.codes.ok:
        is_profanity = response.text["has_profanity"]
        if is_profanity:
            values = ', '.join('%s' for _ in data.values()) + ', false, false'
            send2SNS()
        else:
            values = ', '.join('%s' for _ in data.values()) + ', false, true'
    else:
        print("Error:", response.status_code, response.text)

    keys = ', '.join(data.keys()) + ', pinned, shown'

    query = f"INSERT INTO review ({keys}) VALUES ({values})"

    try:
        cur.execute(query, tuple(data.values()))
    except Exception as e:
        return jsonify({'error message': str(e)})
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Review posted successfully'})

@app.route('/api/review/', methods=['PUT'])
def update_review():
    '''
        Update a review by review id
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})
    if 'pinned' in data.keys():
        return jsonify({'error message': 'cannot modify "pinned" column'})

    api_url = profanity_api_url + '?text={}'.format(data['contents'])
    logging.info("hereeee"+api_url)
    response = requests.get(api_url, headers={'X-Api-Key': 'M0eB3+yE0Y1SeYEcPge8pw==RCoIJ0GIrXiOguwn'})
    if response.status_code == requests.codes.ok:
        is_profanity = response.text["has_profanity"]

        if is_profanity:
            values = ', '.join('%s' for _ in data.values()) + ', false, false'
            send2SNS()
        else:
            values = ', '.join('%s' for _ in data.values()) + ', false, true'
    else:
        print("Error:", response.status_code, response.text)

    set_clause = ', '.join(f"{key} = %s" for key in data.keys())
    query = f"UPDATE review SET {set_clause} WHERE review_id = %s"

    cur.execute(query, tuple(data.values()) + (review_id,))

    query = f"UPDATE review SET shown = 0 WHERE review_id = {review_id}"
    cur.execute(query)

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review updated successfully'})

@app.route('/api/review/', methods=['DELETE'])
def delete_review():
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})
    cur.execute('''DELETE FROM review WHERE review_id = %s''', (review_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review deleted successfully'})

@app.route('/api/admin/pin_review/', methods=['PUT'])
def pin_review():
    '''
        Pin a review by review id (only admin can use)
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})

    query = f"UPDATE review SET pinned = 1 WHERE review_id = {review_id}"

    cur.execute(query)

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': "Review pinned successfully"})

@app.route('/api/admin/unpin_review/', methods=['PUT'])
def unpin_review():
    '''
        Unpin a review by review id (only admin can use)
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})

    query = f"UPDATE review SET pinned = 0 WHERE review_id = {review_id}"

    cur.execute(query)

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': "Review unpinned successfully"})

@app.route('/api/admin/show_review/', methods=['PUT'])
def show_review():
    '''
        show a review by review id (only admin can use)
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})

    query = f"UPDATE review SET shown = 1 WHERE review_id = {review_id}"

    cur.execute(query)

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': "Review showed successfully"})

@app.route('/api/admin/hide_review/', methods=['PUT'])
def hide_review():
    '''
        hide a review by review id (only admin can use)
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        review_id = data['review_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})

    query = f"UPDATE review SET shown = 0 WHERE review_id = {review_id}"

    cur.execute(query)

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': "Review hided successfully"})

@app.route('/api/review/comment/', methods=['GET'])
def get_comment():
    '''
        Get comments (filter accepted in params)
    '''
    cur = mysql.connection.cursor()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))

    filters = {key: value for key, value in request.args.items() if key not in ['page', 'per_page']}
    offset = (page - 1) * per_page

    query = f"SELECT * FROM comment "
    query_filters = "WHERE 1=1"
    for key, value in filters.items():
        if isinstance(value, str):
            query_filters += f" AND {key} = '{value}'"
        else:
            query_filters += f" AND {key} = {value}"
    query += query_filters
    query += f" LIMIT {offset}, {per_page}"

    cur.execute(query)
    data = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) FROM comment " + query_filters)
    total_items = cur.fetchone()['COUNT(*)']
    total_pages = (total_items + per_page - 1) // per_page

    links = pagination_links(page, total_pages, 'get_comment', per_page, filters)

    cur.close()
    return jsonify({'data': data, 'links': links})

@app.route('/api/review/comment/like/', methods=['GET'])
def get_num_like_by_review():
    cur = mysql.connection.cursor()
    review_id = int(request.args.get('review_id', 1))

    query = f"SELECT COUNT(*) AS num_of_likes FROM comment WHERE type = 'like' AND review_id = {review_id}"
    cur.execute(query)
    data = cur.fetchall()

    cur.close()
    return jsonify(data)

@app.route('/api/review/comment/dislike/', methods=['GET'])
def get_num_dislike_by_review():
    cur = mysql.connection.cursor()
    review_id = int(request.args.get('review_id', 1))

    query = f"SELECT COUNT(*) AS num_of_likes FROM comment WHERE type = 'dislike' AND review_id = {review_id}"
    cur.execute(query)
    data = cur.fetchall()

    cur.close()
    return jsonify(data)

@app.route('/api/review/comment/', methods=['POST'])
def post_comment():
    '''
        Reply to a review
    '''
    cur = mysql.connection.cursor()
    data = request.json

    keys = ', '.join(data.keys())
    values = ', '.join('%s' for _ in data.values())

    query = f"INSERT INTO comment ({keys}) VALUES ({values})"

    try:
        cur.execute(query, tuple(data.values()))
    except Exception as e:
        return jsonify({'error message': str(e)})

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Review replied successfully'})

@app.route('/api/review/comment/', methods=['PUT'])
def update_comment():
    '''
        Update a comment/like/dislike/report by comment id
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        comment_id = data['comment_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})
    set_clause = ', '.join(f"{key} = %s" for key in data.keys())
    query = f"UPDATE comment SET {set_clause} WHERE comment_id = %s"

    cur.execute(query, tuple(data.values()) + (comment_id,))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Comment updated successfully'})

@app.route('/api/review/comment/', methods=['DELETE'])
def delete_comment():
    '''
        Delete a comment/like/dislike/report by comment id
    '''
    cur = mysql.connection.cursor()
    data = request.json
    try:
        comment_id = data['comment_id']
    except Exception as e:
        return jsonify({'error message': 'parameter not found: '+str(e)})
    cur.execute('''DELETE FROM comment WHERE comment_id = %s''', (comment_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Comment deleted successfully'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
