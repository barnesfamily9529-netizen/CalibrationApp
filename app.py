"""
Calibration Gage Management - Flask Application
Simple web app for managing calibration gages with SQLite backend.
"""

import sqlite3
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

DATABASE = Path(__file__).parent / "calibration.db"
app = Flask(__name__)
app.secret_key = "calibration-app-secret-key"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database and create tables if they don't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gage_id TEXT NOT NULL UNIQUE,
            description TEXT,
            location TEXT,
            last_calibration TEXT,
            next_calibration_due TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    """List all calibration gages."""
    conn = get_db()
    gages = conn.execute(
        "SELECT * FROM gages ORDER BY next_calibration_due ASC"
    ).fetchall()
    conn.close()
    return render_template("index.html", gages=gages)


@app.route("/add", methods=["GET", "POST"])
def add():
    """Add a new calibration gage."""
    if request.method == "POST":
        gage_id = request.form.get("gage_id", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        last_calibration = request.form.get("last_calibration", "").strip() or None
        next_calibration_due = request.form.get("next_calibration_due", "").strip() or None
        status = request.form.get("status", "Active").strip()

        if not gage_id:
            flash("Gage ID is required.", "error")
            return redirect(url_for("add"))

        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO gages (gage_id, description, location, 
                   last_calibration, next_calibration_due, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (gage_id, description, location, last_calibration, next_calibration_due, status),
            )
            conn.commit()
            flash("Gage added successfully.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("A gage with this ID already exists.", "error")
            return redirect(url_for("add"))
        finally:
            conn.close()

    return render_template("add.html")


@app.route("/edit/<int:gage_pk>", methods=["GET", "POST"])
def edit(gage_pk):
    """Edit an existing calibration gage."""
    conn = get_db()
    gage = conn.execute("SELECT * FROM gages WHERE id = ?", (gage_pk,)).fetchone()

    if not gage:
        conn.close()
        flash("Gage not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        gage_id = request.form.get("gage_id", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        last_calibration = request.form.get("last_calibration", "").strip() or None
        next_calibration_due = request.form.get("next_calibration_due", "").strip() or None
        status = request.form.get("status", "Active").strip()

        if not gage_id:
            flash("Gage ID is required.", "error")
            conn.close()
            return redirect(url_for("edit", gage_pk=gage_pk))

        try:
            conn.execute(
                """UPDATE gages SET gage_id=?, description=?, location=?,
                   last_calibration=?, next_calibration_due=?, status=?
                   WHERE id=?""",
                (gage_id, description, location, last_calibration, next_calibration_due, status, gage_pk),
            )
            conn.commit()
            flash("Gage updated successfully.", "success")
            conn.close()
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("A gage with this ID already exists.", "error")
            conn.close()
            return redirect(url_for("edit", gage_pk=gage_pk))

    conn.close()
    return render_template("edit.html", gage=gage)


@app.route("/delete/<int:gage_pk>", methods=["POST"])
def delete(gage_pk):
    """Delete a calibration gage."""
    conn = get_db()
    conn.execute("DELETE FROM gages WHERE id = ?", (gage_pk,))
    conn.commit()
    conn.close()
    flash("Gage deleted.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
