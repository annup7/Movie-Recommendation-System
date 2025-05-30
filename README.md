# 🎬 Movie Recommendation System

A content-based movie recommendation system where users can select a movie and receive a list of similar movies based on plot summaries and tags. The system uses cosine similarity and the Nearest Neighbors algorithm to generate real-time recommendations through an interactive Streamlit web app.

---

## 🚀 Features

- 🔎 Clean web interface with movie search functionality
- 🎯 Content-based filtering using cosine similarity
- 🧠 Nearest Neighbors algorithm for similarity matching
- 🖼️ Dynamic suggestions with poster images and titles
- 🗄️ Backend connected to MySQL or PostgreSQL for data management
- 💡 Fast and user-friendly experience using Streamlit

---

## 🛠️ Tech Stack

- **Language:** Python  
- **Web Framework:** Streamlit  
- **ML Libraries:** scikit-learn  
- **Database:** MySQL / PostgreSQL  
- **Frontend:** HTML, CSS, Bootstrap

---

## ⚙️ Installation & Usage

1. **Clone the Repository**
git clone https://github.com/annup7/movie-recommendation-system.git
cd movie-recommendation-system

2. **Install Dependencies**
pip install -r requirements.txt

3. **Run the Streamlit App**
streamlit run app.py

---

## 🔍 How It Works

1. User selects a movie from the dropdown or search bar
2. The app computes cosine similarity between selected movie and all others
3. Top N most similar movies are retrieved using Nearest Neighbors
4. Poster images and movie titles are displayed dynamically

---

## 👨‍💻 Author
Anup Nalawade
📧 anupnalawadee@gmail.com
