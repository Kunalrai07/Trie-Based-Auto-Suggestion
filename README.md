# 🔍 Trie-Based Smart Search Engine (Google-like Auto Suggestion)

A powerful and intelligent search engine built using **Trie Data Structure**, integrated with:
- Real-time **auto-suggestions** (like Google/Bing)
- **Fuzzy matching** using Levenshtein Distance
- **Spelling correction**
- Live **Wikipedia scraping**
- Dynamic learning from **user clicks**
- Search popularity based on **frequency** and **timestamp**
- Powered by **Flask API + JavaScript frontend**

---

## 🚀 Features

- ✅ **Trie-based Auto-Suggestions** for blazing fast performance
- 🔎 **Fuzzy Search** using Levenshtein distance
- ✍️ **Spelling correction** for words and phrases
- 📈 **Dynamic learning**: Suggestions improve over time with use
- 📅 **Timestamp and popularity ranking** for top queries
- 🧠 **Search Result Generation** from:
  - Wikipedia (via BeautifulSoup)
  - Other sources (optional to extend)
- 💾 **SQLite Database** to store search history and user clicks

---

## 📁 Project Structure
📦 trie-search-engine/
├── app.py # Flask backend with search API and Trie logic
├── trie.py # Trie data structure for auto-completion
├── templates/
│ └── index.html # Frontend search UI (HTML + JS)
├── static/
│ └── styles.css # Optional: Add your custom styles here
├── search.db # SQLite database for history and clicks
└── README.md # You're reading it!

## ⚙️ Tech Stack

- 💻 **Frontend**: HTML, CSS, JavaScript (AJAX)
- 🔙 **Backend**: Flask (Python)
- 🧠 **DSA**: Trie, Levenshtein Distance
- 🗃️ **Database**: SQLite
- 🌐 **Scraping**: BeautifulSoup (Wikipedia)

