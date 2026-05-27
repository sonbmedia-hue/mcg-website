from flask import Flask, render_template, request, send_file

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from datetime import datetime

import uuid
import hashlib
import sqlite3
import os

# FLASK APP
app = Flask(__name__)

# CREATE OUTPUT FOLDER
os.makedirs("output", exist_ok=True)

# DATABASE SETUP
conn = sqlite3.connect(
    "prm_database.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS certificates (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    song_name TEXT,

    owner TEXT,

    lyrics TEXT,

    timestamp TEXT,

    token_id TEXT,

    lyrics_hash TEXT,

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

        # LYRICS SECTION
        c.setFont(
            "Helvetica-Bold",
            13
        )

        c.drawString(
            80,
            350,
            "REGISTERED LYRICS:"
        )

        c.setFont(
            "Helvetica",
            10
        )

        lyrics_y = 330

        lyrics_lines = lyrics.splitlines()

        for line in lyrics_lines[:15]:

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
            qr_link

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (

            song_name,
            owner,
            lyrics,
            timestamp,
            token_id,
            lyrics_hash,
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
@app.route("/verify/<token>")

def verify(token):

    cursor.execute(

        "SELECT * FROM certificates WHERE token_id=?",

        (token,)
    )

    certificate = cursor.fetchone()

    if certificate:

        return f"""

        <html>

        <head>

        <title>
        PRM Verification
        </title>

        <style>

        body{{
            background:#0f0f0f;
            color:white;
            font-family:Arial;
            padding:60px;
        }}

        .card{{
            max-width:800px;
            margin:auto;
            background:#1b1b1b;
            padding:40px;
            border-radius:20px;
        }}

        h1{{
            color:#4CAF50;
        }}

        .verified{{
            color:#4CAF50;
            font-size:24px;
            font-weight:bold;
            margin-bottom:25px;
        }}

        .item{{
            margin-bottom:18px;
            line-height:1.6;
        }}

        </style>

        </head>

        <body>

        <div class="card">

        <h1>
        PRM Verification Portal
        </h1>

        <div class="verified">
        ✅ VERIFIED REGISTRATION
        </div>

        <div class="item">
        <strong>Song:</strong>
        {certificate[1]}
        </div>

        <div class="item">
        <strong>Owner:</strong>
        {certificate[2]}
        </div>

        <div class="item">
        <strong>Timestamp:</strong>
        {certificate[4]}
        </div>

        <div class="item">
        <strong>Token ID:</strong>
        {certificate[5]}
        </div>

        <div class="item">
        <strong>Lyrics Hash:</strong><br>
        {certificate[6]}
        </div>

        </div>

        </body>

        </html>

        """

    return """

    <html>

    <body style="background:black;color:white;font-family:Arial;padding:60px;">

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