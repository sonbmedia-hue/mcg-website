from flask import Flask, render_template, request, send_file

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from werkzeug.utils import secure_filename

from datetime import datetime

import uuid
import hashlib
import sqlite3
import os

# FLASK APP
app = Flask(__name__)

# CREATE FOLDERS
os.makedirs("output", exist_ok=True)

os.makedirs("uploads", exist_ok=True)

# DATABASE SETUP
conn = sqlite3.connect(
    "prm_database.db",
    check_same_thread=False
)

cursor = conn.cursor()

# CREATE TABLE
cursor.execute("""

CREATE TABLE IF NOT EXISTS certificates (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    song_name TEXT,

    owner TEXT,

    lyrics TEXT,

    timestamp TEXT,

    token_id TEXT,

    lyrics_hash TEXT,

    audio_hash TEXT,

    qr_link TEXT

)

""")

conn.commit()


# HOME PAGE
@app.route("/", methods=["GET", "POST"])
def home():

    # FORM SUBMITTED
    if request.method == "POST":

        # FORM DATA
        song_name = request.form["song_name"]

        owner = request.form["owner"]

        lyrics = request.form["lyrics"]

        # MUSIC FILE
        music_file = request.files["music_file"]

        # AUTO TIMESTAMP
        timestamp = datetime.now().strftime(
            "%m/%d/%Y %I:%M %p"
        )

        # TOKEN ID
        token_id = uuid.uuid4().hex

        # AUTO VERIFICATION LINK
        qr_link = f"https://mcg-website.onrender.com/verify/{token_id}"

        # LYRICS HASH
        lyrics_hash = hashlib.sha256(
            lyrics.encode()
        ).hexdigest()

        # SAVE MUSIC FILE
        filename = secure_filename(
            music_file.filename
        )

        music_path = os.path.join(
            "uploads",
            filename
        )

        music_file.save(music_path)

        # AUDIO HASH
        with open(music_path, "rb") as f:

            audio_bytes = f.read()

        audio_hash = hashlib.sha256(
            audio_bytes
        ).hexdigest()

        # CHECK FOR DUPLICATE AUDIO
        cursor.execute(

            "SELECT * FROM certificates WHERE audio_hash=?",

            (audio_hash,)
        )

        existing_audio = cursor.fetchone()

        if existing_audio:

            return """

            <html>

            <body style='
            background:#0f0f0f;
            color:white;
            font-family:Arial;
            padding:60px;
            '>

            <h1 style='color:red;'>
            DUPLICATE AUDIO DETECTED
            </h1>

            <p>
            This audio fingerprint already exists
            in the PRM registry.
            </p>

            </body>

            </html>

            """

        # SAFE FILE NAME
        safe_name = song_name.replace(" ", "_")

        output_file = f"output/{safe_name}.pdf"

        # CREATE PDF
        c = canvas.Canvas(
            output_file,
            pagesize=letter
        )

        PAGE_WIDTH, PAGE_HEIGHT = letter

        # BACKGROUND
        c.setFillColor(HexColor("#F5F5F5"))

        c.rect(
            0,
            0,
            PAGE_WIDTH,
            PAGE_HEIGHT,
            fill=1
        )

        # BORDER
        c.setStrokeColor(HexColor("#1B5E20"))

        c.setLineWidth(2)

        c.rect(
            20,
            20,
            PAGE_WIDTH - 40,
            PAGE_HEIGHT - 40
        )

        # TEXT COLOR
        c.setFillColor(HexColor("#000000"))

        # HEADER
        c.setFont(
            "Helvetica-Bold",
            24
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            720,
            "PRM : Protection Rights Management"
        )

        # SUBTITLE
        c.setFont(
            "Helvetica-Bold",
            18
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            680,
            "CERTIFICATE OF CREATIVE OWNERSHIP"
        )

        # SONG TITLE
        c.setFont(
            "Helvetica-Bold",
            24
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            620,
            song_name
        )

        # DESCRIPTION
        c.setFont(
            "Helvetica",
            11
        )

        description = (
            "PRM certifies this work as protected "
            "creative intellectual property ownership."
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            580,
            description
        )

        # OWNER
        c.setFont(
            "Helvetica-Bold",
            15
        )

        c.drawString(
            80,
            520,
            f"OWNER: {owner}"
        )

        # TIMESTAMP
        c.drawString(
            80,
            490,
            f"TIMESTAMP: {timestamp}"
        )

        # TOKEN ID
        c.drawString(
            80,
            460,
            "TOKEN ID:"
        )

        c.setFont(
            "Helvetica",
            9
        )

        c.drawString(
            80,
            440,
            token_id
        )

        # LYRICS HASH
        c.setFont(
            "Helvetica-Bold",
            12
        )

        c.drawString(
            80,
            400,
            "LYRICS HASH:"
        )

        c.setFont(
            "Helvetica",
            8
        )

        c.drawString(
            80,
            385,
            lyrics_hash[:70]
        )

        # AUDIO HASH
        c.setFont(
            "Helvetica-Bold",
            12
        )

        c.drawString(
            80,
            355,
            "AUDIO HASH:"
        )

        c.setFont(
            "Helvetica",
            8
        )

        c.drawString(
            80,
            340,
            audio_hash[:70]
        )

        # LYRICS SECTION
        c.setFont(
            "Helvetica-Bold",
            13
        )

        c.drawString(
            80,
            300,
            "REGISTERED LYRICS:"
        )

        c.setFont(
            "Helvetica",
            10
        )

        lyrics_y = 280

        lyrics_lines = lyrics.splitlines()

        for line in lyrics_lines[:10]:

            c.drawString(
                80,
                lyrics_y,
                line[:90]
            )

            lyrics_y -= 14

        # QR CODE
        qr_code = qr.QrCodeWidget(qr_link)

        bounds = qr_code.getBounds()

        width = bounds[2] - bounds[0]

        height = bounds[3] - bounds[1]

        d = Drawing(
            100,
            100,
            transform=[
                100.0 / width,
                0,
                0,
                100.0 / height,
                0,
                0
            ]
        )

        d.add(qr_code)

        renderPDF.draw(
            d,
            c,
            430,
            120
        )

        # FOOTER
        c.setFillColor(HexColor("#000000"))

        c.setFont(
            "Helvetica",
            10
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            40,
            "PRM : Protection Rights Management"
        )

        # SAVE PDF
        c.save()

        # SAVE TO DATABASE
        cursor.execute("""

        INSERT INTO certificates (

            song_name,
            owner,
            lyrics,
            timestamp,
            token_id,
            lyrics_hash,
            audio_hash,
            qr_link

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            song_name,
            owner,
            lyrics,
            timestamp,
            token_id,
            lyrics_hash,
            audio_hash,
            qr_link

        ))

        conn.commit()

        # RETURN PDF
        return send_file(
            output_file,
            as_attachment=True
        )

    # LOAD WEBSITE
    return render_template("index.html")


# VERIFICATION PAGE
# VERIFICATION PAGE
@app.route("/verify/<token>")
def verify(token):

    cursor.execute(
        "SELECT * FROM certificates WHERE token_id=?",
        (token,)
    )

    certificate = cursor.fetchone()

    if certificate:

        return f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<title>PRM Verification</title>

<style>

body{{
    background:#0f0f0f;
    color:white;
    font-family:Arial;
    padding:40px;
}}

.card{{
    max-width:900px;
    margin:auto;
    background:#1b1b1b;
    padding:45px;
    border-radius:24px;
}}

.logo{{
    font-size:42px;
    color:#4CAF50;
    font-weight:bold;
    margin-bottom:10px;
}}

.subtitle{{
    color:#999;
    margin-bottom:35px;
}}

.verified{{
    background:#16351d;
    color:#4CAF50;
    padding:18px;
    border-radius:14px;
    font-size:24px;
    font-weight:bold;
    margin-bottom:35px;
    text-align:center;
}}

.section{{
    margin-bottom:25px;
}}

.label{{
    color:#4CAF50;
    margin-bottom:8px;
    font-size:14px;
}}

.value{{
    background:#242424;
    padding:18px;
    border-radius:12px;
    word-wrap:break-word;
}}

.hash{{
    font-size:12px;
    color:#ccc;
}}

.footer{{
    text-align:center;
    margin-top:40px;
    color:#666;
}}

</style>

</head>

<body>

<div class="card">

<div class="logo">
PRM
</div>

<div class="subtitle">
Protection Rights Management Verification Portal
</div>

<div class="verified">
✅ VERIFIED REGISTRATION
</div>

<div class="section">

<div class="label">
SONG TITLE
</div>

<div class="value">
{certificate[1]}
</div>

</div>

<div class="section">

<div class="label">
RIGHTS OWNER
</div>

<div class="value">
{certificate[2]}
</div>

</div>

<div class="section">

<div class="label">
REGISTRATION TIMESTAMP
</div>

<div class="value">
{certificate[4]}
</div>

</div>

<div class="section">

<div class="label">
TOKEN ID
</div>

<div class="value hash">
{certificate[5]}
</div>

</div>

<div class="section">

<div class="label">
LYRICS HASH
</div>

<div class="value hash">
{certificate[6]}
</div>

</div>

<div class="section">

<div class="label">
AUDIO HASH
</div>

<div class="value hash">
{certificate[7]}
</div>

</div>

<div class="footer">
PRM © 2026 — Protection Rights Management
</div>

</div>

</body>

</html>
"""

    return """
<!DOCTYPE html>
<html>

<body style="
background:#0f0f0f;
color:white;
font-family:Arial;
padding:60px;
">

<h1 style="color:red;">
INVALID CERTIFICATE
</h1>

<p>
This PRM registration could not be verified.
</p>

</body>

</html>
"""


# RUN SERVER
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )