from flask import Flask, render_template, request, send_file

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from datetime import datetime

import uuid
import os

# FLASK APP
app = Flask(__name__)

# CREATE OUTPUT FOLDER
os.makedirs("output", exist_ok=True)


# HOME PAGE
@app.route("/", methods=["GET", "POST"])
def home():

    # WHEN USER SUBMITS FORM
    if request.method == "POST":

        # GET FORM DATA
        song_name = request.form["song_name"]
        owner = request.form["owner"]
        qr_link = request.form["qr_link"]

        # AUTO TIMESTAMP
        timestamp = datetime.now().strftime(
            "%m/%d/%Y %I:%M %p"
        )

        # AUTO TOKEN
        token_id = uuid.uuid4().hex

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
        c.setStrokeColor(HexColor("#2E7D32"))

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
            "MCG : Music Copyrights Generator"
        )

        # TITLE
        c.setFont(
            "Helvetica-Bold",
            20
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            650,
            "CERTIFICATE OF MUSIC COPYRIGHT"
        )

        # SONG NAME
        c.setFont(
            "Helvetica-Bold",
            24
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            560,
            song_name
        )

        # DESCRIPTION
        c.setFont(
            "Helvetica",
            11
        )

        description = (
            "MCG certifies this work as registered "
            "intellectual property ownership."
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            500,
            description
        )

        # OWNER
        c.setFont(
            "Helvetica-Bold",
            16
        )

        c.drawString(
            120,
            380,
            f"OWNER: {owner}"
        )

        # TIMESTAMP
        c.drawString(
            120,
            340,
            f"TIMESTAMP: {timestamp}"
        )

        # TOKEN LABEL
        c.drawString(
            120,
            300,
            "TOKEN ID:"
        )

        # TOKEN VALUE
        c.setFont(
            "Helvetica",
            10
        )

        c.drawString(
            120,
            280,
            token_id
        )

        # QR CODE
        qr_code = qr.QrCodeWidget(qr_link)

        bounds = qr_code.getBounds()

        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]

        d = Drawing(
            90,
            90,
            transform=[
                90.0 / width,
                0,
                0,
                90.0 / height,
                0,
                0
            ]
        )

        d.add(qr_code)

        renderPDF.draw(
            d,
            c,
            420,
            240
        )

        # FOOTER
        c.setFillColor(HexColor("#000000"))

        c.setFont(
            "Helvetica",
            9
        )

        c.drawCentredString(
            PAGE_WIDTH / 2,
            40,
            "MCG : Music Copyrights Generator"
        )

        # SAVE PDF
        c.save()

        # RETURN PDF DOWNLOAD
        return send_file(
            output_file,
            as_attachment=True
        )

    # LOAD WEBSITE
    return render_template("index.html")


# RUN FLASK
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )