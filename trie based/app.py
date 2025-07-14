import sqlite3
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from pytrends.request import TrendReq
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
        pytrend = TrendReq(hl='en-US', timeout=(2, 5))
        suggestions = pytrend.suggestions(keyword=q)
        return [s['title'] for s in suggestions][:5]
    except Exception as e:
        print(f"Google Trends error: {e}")
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
        return []
    except Exception as e:
        print(f"Wikipedia suggestions error: {e}")
        return []

def get_wikipedia_results(q):
    try:
        # Step 1: Search for articles
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": q,
            "srlimit": 5,
            "format": "json"
        }
        res = requests.get(url, params=params, timeout=3)
        if res.status_code != 200:
            print(f"Wikipedia search failed with status: {res.status_code}")
            return []
        
        search_results = res.json().get('query', {}).get('search', [])
        if not search_results:
            return []

        # Step 2: Fetch thumbnails for the search results
        titles = [r['title'] for r in search_results]
        params = {
            "action": "query",
            "prop": "pageimages",
            "titles": "|".join(titles),
            "pithumbsize": 100,
            "format": "json"
        }
        res = requests.get(url, params=params, timeout=3)
        if res.status_code != 200:
            print(f"Wikipedia images failed with status: {res.status_code}")
            images = {}
        else:
            pages = res.json().get('query', {}).get('pages', {})
            images = {pages[p]['title']: pages[p].get('thumbnail', {}).get('source') for p in pages if 'thumbnail' in pages[p]}

        # Step 3: Format results with snippets and images
        formatted_results = []
        for r in search_results:
            formatted_results.append({
                'title': r['title'],
                'snippet': r['snippet'].replace('<span class="searchmatch">', '').replace('</span>', ''),
                'url': f"https://en.wikipedia.org/wiki/{requests.utils.quote(r['title'])}",
                'image': images.get(r['title'], '')  # Empty string if no image
            })
        return formatted_results
    except Exception as e:
        print(f"Wikipedia results error: {e}")
        return []

def get_all_queries():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('SELECT query FROM search_history')
            return [row[0] for row in c.fetchall()]
    except Exception as e:
        print(f"Database error: {e}")
        return []

def get_ranked_suggestions(q):
    try:
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
    except Exception as e:
        print(f"Ranked suggestions error: {e}")
        return []

# === Routes ===

@app.route('/search', methods=['POST'])
def save_query():
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    if query:
        insert_or_update_query(query)
        return jsonify({'message': 'Query saved'}), 200
    return jsonify({'error': 'No query provided'}), 400

@app.route('/suggest', methods=['GET'])
def suggest():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify({'suggestions': [], 'results': []})

    # Get suggestions
    local_suggestions = get_ranked_suggestions(q)
    fuzzy = []
    if not local_suggestions:
        all_queries = get_all_queries()
        fuzzy = [f[0] for f in process.extract(q, all_queries, limit=5, score_cutoff=60)]
    
    wiki = get_wikipedia_suggestions(q)
    google_trends = get_google_trends_suggestions(q)

    # Merge suggestions, prioritize local → fuzzy → wiki → google trends
    suggestions = list(dict.fromkeys(
        local_suggestions + fuzzy + wiki + google_trends
    ))[:10]

    # Get Wikipedia results for the query
    results = get_wikipedia_results(q) if q else []

    return jsonify({
        'suggestions': suggestions,
        'results': results
    })

# Initialize DB
if __name__ == '__main__':
    init_db()
    app.run(debug=True)