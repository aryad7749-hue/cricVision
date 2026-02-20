from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# =====================================================
# ================= DATABASE SETUP ====================
# =====================================================

def init_db():
    conn = sqlite3.connect("cricket.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        team TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        opponent TEXT,
        runs INTEGER DEFAULT 0,
        balls INTEGER DEFAULT 0,
        fours INTEGER DEFAULT 0,
        sixes INTEGER DEFAULT 0,
        wickets INTEGER DEFAULT 0,
        FOREIGN KEY(player_id) REFERENCES players(id)
    )
    """)

    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect("cricket.db")
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# ================= FIXED 20 TEAMS ====================
# =====================================================

TEAMS = [
    "India","Australia","England","Pakistan","New Zealand",
    "South Africa","Sri Lanka","Bangladesh","Afghanistan",
    "West Indies","USA","Ireland","Scotland","Netherlands",
    "Nepal","UAE","Zimbabwe","Namibia","Oman","Canada"
]


# =====================================================
# ===================== ROUTES ========================
# =====================================================

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("home.html")


# ---------------- SQUAD (TEAM LIST) ----------------
@app.route('/squad')
def squad():
    return render_template("squad.html", teams=TEAMS)


# ---------------- TEAM PLAYERS ----------------
@app.route('/team/<team_name>')
def team_players(team_name):
    conn = get_connection()
    players = conn.execute(
        "SELECT * FROM players WHERE team=?",
        (team_name,)
    ).fetchall()
    conn.close()

    return render_template(
        "team_players.html",
        players=players,
        team_name=team_name
    )


# ---------------- PLAYER STATS ----------------
def get_player_stats(player_id):
    conn = get_connection()
    performances = conn.execute(
        "SELECT * FROM performance WHERE player_id=?",
        (player_id,)
    ).fetchall()

    total_runs = 0
    total_balls = 0
    total_wickets = 0
    total_matches = len(performances)

    for p in performances:
        total_runs += p["runs"]
        total_balls += p["balls"]
        total_wickets += p["wickets"]

    strike_rate = round((total_runs / total_balls * 100), 2) if total_balls > 0 else 0
    average = round((total_runs / total_matches), 2) if total_matches > 0 else 0

    conn.close()

    return {
        "matches": total_matches,
        "runs": total_runs,
        "strike_rate": strike_rate,
        "average": average,
        "wickets": total_wickets
    }


@app.route('/player/<int:player_id>')
def player(player_id):
    conn = get_connection()
    player = conn.execute(
        "SELECT * FROM players WHERE id=?",
        (player_id,)
    ).fetchone()
    conn.close()

    stats = get_player_stats(player_id)

    return render_template(
        "stats.html",
        player=player,
        stats=stats
    )


# ---------------- COMPARE ----------------
@app.route('/compare', methods=['GET', 'POST'])
def compare():
    conn = get_connection()
    players = conn.execute("SELECT * FROM players").fetchall()
    conn.close()

    stats1 = None
    stats2 = None

    if request.method == "POST":
        p1_id = request.form.get("player1")
        p2_id = request.form.get("player2")

        if p1_id and p2_id:
            stats1 = get_player_stats(p1_id)
            stats2 = get_player_stats(p2_id)

            player1 = next((p for p in players if str(p["id"]) == p1_id), None)
            player2 = next((p for p in players if str(p["id"]) == p2_id), None)

            if player1 and player2:
                stats1["player"] = player1
                stats2["player"] = player2

    return render_template(
        "compare.html",
        players=players,
        stats1=stats1,
        stats2=stats2
    )


# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin():
    conn = get_connection()
    players = conn.execute("SELECT * FROM players").fetchall()
    conn.close()

    return render_template(
        "admin.html",
        players=players,
        teams=TEAMS
    )


# ---------------- ADD PLAYER ----------------
@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form['name']
    role = request.form['role']
    team = request.form['team']

    conn = get_connection()
    conn.execute(
        "INSERT INTO players (name, role, team) VALUES (?, ?, ?)",
        (name, role, team)
    )
    conn.commit()
    conn.close()

    return redirect('/admin')


# ---------------- EDIT PLAYER ----------------
@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    conn = get_connection()

    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        team = request.form['team']

        conn.execute("""
            UPDATE players
            SET name=?, role=?, team=?
            WHERE id=?
        """, (name, role, team, player_id))
        conn.commit()
        conn.close()
        return redirect('/admin')

    player = conn.execute(
        "SELECT * FROM players WHERE id=?",
        (player_id,)
    ).fetchone()
    conn.close()

    return render_template(
        "edit_player.html",
        player=player,
        teams=TEAMS
    )


# ---------------- DELETE PLAYER ----------------
@app.route('/delete_player/<int:player_id>')
def delete_player(player_id):
    conn = get_connection()
    conn.execute("DELETE FROM players WHERE id=?", (player_id,))
    conn.execute("DELETE FROM performance WHERE player_id=?", (player_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')


# ---------------- ADD PERFORMANCE ----------------
@app.route('/add_performance', methods=['POST'])
def add_performance():
    player_id = request.form['player_id']
    opponent = request.form['opponent']
    runs = request.form.get('runs', 0)
    balls = request.form.get('balls', 0)
    fours = request.form.get('fours', 0)
    sixes = request.form.get('sixes', 0)
    wickets = request.form.get('wickets', 0)

    conn = get_connection()
    conn.execute("""
        INSERT INTO performance
        (player_id, opponent, runs, balls, fours, sixes, wickets)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (player_id, opponent, runs, balls, fours, sixes, wickets))
    conn.commit()
    conn.close()

    return redirect('/admin')


# =====================================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
