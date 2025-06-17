import sqlite3
from mcp.server.fastmcp import FastMCP
from typing import List
from datetime import date

# Connect to SQLite database
conn = sqlite3.connect("meeting_scheduler.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER,
    name TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
)
""")
conn.commit()

# Initialize MCP
mcp = FastMCP("MeetingScheduler")

# Tool 1: Schedule a meeting
@mcp.tool()
def schedule_meeting(title: str, date: str, participants: List[str]) -> str:
    cursor.execute("INSERT INTO meetings (title, date) VALUES (?, ?)", (title, date))
    meeting_id = cursor.lastrowid
    for name in participants:
        cursor.execute("INSERT INTO participants (meeting_id, name) VALUES (?, ?)", (meeting_id, name))
    conn.commit()
    return f"Meeting '{title}' scheduled on {date} with {', '.join(participants)}."

# Tool 2: View meetings for a participant
@mcp.tool()
def get_meeting_schedule(participant: str) -> str:
    cursor.execute("""
        SELECT m.title, m.date FROM meetings m
        JOIN participants p ON m.id = p.meeting_id
        WHERE p.name = ?
        ORDER BY m.date ASC
    """, (participant,))
    rows = cursor.fetchall()
    if not rows:
        return f"No upcoming meetings found for {participant}."
    return "\n".join([f"{title} on {date_}" for title, date_ in rows])

# Tool 3: Cancel a meeting
@mcp.tool()
def cancel_meeting(title: str) -> str:
    cursor.execute("SELECT id FROM meetings WHERE title = ?", (title,))
    row = cursor.fetchone()
    if not row:
        return f"No meeting found with title '{title}'."
    meeting_id = row[0]
    cursor.execute("DELETE FROM participants WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    return f"Meeting '{title}' has been cancelled."

# Tool 4: Today's meetings
@mcp.tool()
def get_today_meetings() -> str:
    today = date.today().isoformat()
    cursor.execute("SELECT title FROM meetings WHERE date = ?", (today,))
    rows = cursor.fetchall()
    if not rows:
        return "No meetings scheduled for today."
    return "Today's meetings:\n" + "\n".join([row[0] for row in rows])

# Run the MCP server
if __name__ == "__main__":
    mcp.run()

