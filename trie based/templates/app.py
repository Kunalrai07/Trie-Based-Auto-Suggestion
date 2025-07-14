import sqlite3
import requests
from flask import Flask, request, jsonify
from pytrends.request import TrendReq
from flask_cors import CORS
from rapidfuzz import process
from datetime import datetime

app = Flask(__name__)
CORS(app)

# === Setup SQLite DB ===
DB_NAME = 'search.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                query TEXT PRIMARY KEY,
                timestamp TEXT,
                count INTEGER
            )
        ''')
        conn.commit()

def insert_or_update_query(query):
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT count FROM search_history WHERE query = ?', (query,))
        row = c.fetchone()
        if row:
            c.execute('''
                UPDATE search_history
                SET count = count + 1, timestamp = ?
                WHERE query = ?
            ''', (now, query))
        else:
            c.execute('''
                INSERT INTO search_history (query, timestamp, count)
                VALUES (?, ?, 1)
            ''', (query, now))
        conn.commit()

def get_google_trends_suggestions(q):
    try:
        pytrend = TrendReq()
        suggestions = pytrend.suggestions(keyword=q)
        return [s['title'] for s in suggestions][:5]
    except:
        return []

def get_wikipedia_suggestions(q):
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": q,
            "limit": 5,
            "namespace": 0,
            "format": "json"
        }
        res = requests.get(url, params=params, timeout=2)
        if res.status_code == 200:
            return res.json()[1]  # list of suggestions
    except:
        return []
    return []

def get_all_queries():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT query FROM search_history')
        return [row[0] for row in c.fetchall()]

def get_ranked_suggestions(q):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT query, count, timestamp
            FROM search_history
            WHERE query LIKE ? OR query LIKE ?
            ORDER BY count DESC, timestamp DESC
            LIMIT 10
        ''', (q + '%', '%' + q + '%'))
        return [row[0] for row in c.fetchall()]

# === Routes ===

@app.route('/search', methods=['POST'])
def save_query():
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    if query:
        insert_or_update_query(query)
    return jsonify({'message': 'Query saved'}), 200

@app.route('/suggest', methods=['GET'])
def suggest():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])

    local_suggestions = get_ranked_suggestions(q)
    fuzzy = []
    if not local_suggestions:
        all_queries = get_all_queries()
        fuzzy = process.extract(q, all_queries, limit=5, score_cutoff=60)

    wiki = get_wikipedia_suggestions(q)

    # Merge all, prioritize local → fuzzy → wiki
    suggestions = list(dict.fromkeys(
        local_suggestions + [f[0] for f in fuzzy] + wiki
    ))
    return jsonify(suggestions[:10])


# Initialize DB
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
