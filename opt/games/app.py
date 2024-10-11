# app.py

import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
from datetime import datetime
from weasyprint import HTML
from shared_functions import fetch_games, group_games_by_date, split_team_name

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Configuration
TEAMS = [
    "HSE++1", "HSE++2", "DSE++1", "DSE++2", "J18++1", "J18++2",
    "J16++1", "J16++2", "G14++1", "G14++2", "G12++1", "G12++2",
    "G10++1", "G10++2", "G08++1", "M16++1", "M16++2", "M14++1",
    "M14++2", "M12++1"
]
VENUES = {
    "BVBL500419": "Boutersem",
    "BVBL500075": "Lubbeek"
}
LOGO_PATH = "https://hagelandunited.be/wp-content/uploads/2022/06/HagelandUnited_150x150.png"
GENERATED_PDFS_DIR = os.path.join(os.getcwd(), 'generated_pdfs')

# Ensure the directory exists
os.makedirs(GENERATED_PDFS_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_teams = request.form.getlist('teams')
        selected_venues = request.form.getlist('venues')
        selected_date_str = request.form.get('date')

        # Input validation
        if not selected_teams:
            flash('Please select at least one team.', 'danger')
            return redirect(url_for('index'))
        if not selected_venues:
            flash('Please select at least one venue.', 'danger')
            return redirect(url_for('index'))
        if not selected_date_str:
            flash('Please select a date.', 'danger')
            return redirect(url_for('index'))

        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('index'))

        # Map venue names back to GUIDs
        acc_guids = [guid for guid, name in VENUES.items() if name in selected_venues]

        # Fetch games
        games = fetch_games(selected_teams, acc_guids, selected_date)

        if not games:
            flash('No games found for the selected criteria.', 'info')
            return redirect(url_for('index'))

        # Generate PDFs
        try:
            # Generate Kleedkamer PDF
            kleedkamer_pdf = generate_kleedkamer_pdf(games, LOGO_PATH, selected_date)
            # Generate Individual Games PDFs
            individual_pdfs = generate_individual_games_pdf(games, LOGO_PATH)

            return render_template('result.html', kleedkamer_pdf=kleedkamer_pdf, individual_pdfs=individual_pdfs)
        except Exception as e:
            flash(f'Error generating PDFs: {e}', 'danger')
            return redirect(url_for('index'))

    return render_template('index.html', teams=TEAMS, venues=VENUES.values())

def generate_kleedkamer_pdf(games, logo_path, selected_date):
    from shared_functions import group_games_by_date  # Import inside function to avoid circular imports
    try:
        games_by_date = group_games_by_date(games)
        combined_games_html = ''
        combined_section = ''

        for date, games_on_date in games_by_date.items():
            if date != selected_date:
                continue  # Only process selected date
            
            # Sort games by beginTijd
            games_on_date = sorted(games_on_date, key=lambda game: game.get("beginTijd"))

            for i, game in enumerate(games_on_date):
                acc_guid = game.get("accGUID")
                
                if acc_guid == "BVBL500419":
                    kleedkamer_t = 'A' if i % 2 == 0 else 'B'
                    kleedkamer_u = '1' if i % 2 == 0 else '2'
                elif acc_guid == "BVBL500075":
                    kleedkamer_t = ''
                    kleedkamer_u = ''
                else:
                    kleedkamer_t = 'T'
                    kleedkamer_u = 'U'
                
                combined_games_html += f'''
                <tr style="border-top: solid 1px #000; border-bottom: solid 1px #000; line-height: {'1.25' if split_team_name(game.get("tTNaam")) != game.get("tTNaam") or split_team_name(game.get("tUNaam")) != game.get("tUNaam") else '2.5'};">
                    <td style="width: 5%; color: {'#002b5c' if i % 2 == 0 else '#96c11f'};">
                        {kleedkamer_t}
                    </td>
                    <td style="width: 45%; color: {'#002b5c' if i % 2 == 0 else '#96c11f'}; border-right: 1px solid black;">
                        {split_team_name(game.get("tTNaam"))}
                    </td>
                    <td style="width: 5%; color: {'#96c11f' if i % 2 == 0 else '#002b5c'};">
                        {kleedkamer_u}
                    </td>
                    <td style="width: 45%; color: {'#96c11f' if i % 2 == 0 else '#002b5c'};">
                        {split_team_name(game.get("tUNaam"))}
                    </td>
                </tr>
                '''

            combined_section += f'''
            <div style="page-break-before: always;">
                <div style="display: flex; justify-content: left; margin-top: 25px; margin-bottom: 25px;">
                    <img src="{logo_path}" alt="Club Logo" style="width:100px; margin-top: 10px;"/>
                    <div style="text-align: center; color: red; font-size: 108px; font-weight: bold;">&nbsp; KLEEDKAMERS BASKET</div>
                </div>

                <table style="width: 100%; border-collapse: collapse; text-align: center; font-weight: bold; font-size: 45px;">
                    {combined_games_html}
                </table>
            </div>
            '''

            # Footer section with date and location
            combined_section += f'''
            <div style="page-break-after: always; position: relative;">
                <div style="position: relative; height: 100px; page-break-inside: avoid;">
                    <div style="text-align: left; color: grey; font-size: 10px; font-weight: bold; position: absolute; bottom: 0; right: 10px;">
                        {date} - {games_on_date[0].get("accNaam", "Unknown Location")}
                    </div>
                    <div style="text-align: center; color: red; font-size: 40px; font-weight: bold; position: absolute; bottom: 40px; left: 50px;">
                        Gedeelde kleedkamers: Blijf niet langer aanwezig dan nodig.<br />
                    </div>
                    <div style="text-align: center; color: red; font-size: 40px; font-weight: bold; position: absolute; bottom: 0; left: 50px;">
                        Neem AL je spullen mee naar de wedstrijd!
                    </div>
                </div>
            </div>
            '''

            # Combine all HTML content
            full_html_content = f'''
            <html>
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Impact&display=swap" rel="stylesheet">
                <style>
                    @page {{
                        size: A4 landscape;
                        margin: 0; /* Full page width */
                    }}
                    body {{
                        margin: 0;
                        padding-bottom: 100px; /* Space for footer */
                        font-family: Impact, sans-serif;
                    }}
                </style>
            </head>
            <body>
                {combined_section}
            </body>
            </html>
            '''

        # Extract accNaam and format date for output file name
        first_game = games_on_date[0]  # Now using games_on_date as it's already filtered and sorted
        date_str = selected_date.strftime("%d-%m-%Y")  # Format date
        acc_name = first_game.get("accNaam", "Unknown").replace(" ", "_")  # Replace spaces with underscore
        output_file = f"Kleedkamer-{acc_name}-{date_str}.pdf"
        output_path = os.path.join(GENERATED_PDFS_DIR, output_file)
        
        HTML(string=full_html_content).write_pdf(output_path)
        app.logger.info(f"Kleedkamer PDF generated successfully: {output_file}")
        return output_file
    
    except Exception as e:
        app.logger.error(f"Error generating kleedkamer PDF: {e}")
        raise

def generate_individual_games_pdf(games, logo_path):
    from shared_functions import group_games_by_date  # Import inside function to avoid circular imports
    individual_pdfs = []
    try:
        # Group games by date
        games_by_date = group_games_by_date(games)

        for date, games_on_date in games_by_date.items():
            games_on_date.sort(key=lambda x: x.get("beginTijd"))  # Sort games by start time

            # Extract accNaam for the location of the first game of the day
            first_game = games_on_date[0]
            acc_name = first_game.get("accNaam", "Unknown").replace(" ", "_")  # Replace spaces with underscore
            date_str = date.strftime("%d-%m-%Y")
            output_file = f"Refs-{acc_name}-{date_str}.pdf"  # Format the output file name

            # Prepare HTML content for individual games
            individual_games_html = ""
            for game in games_on_date:
                individual_games_html += f'''
                <div style="page-break-after: always;">
                    <div style="display: flex; justify-content: space-between;">
                        <img src="{logo_path}" alt="Club Logo" style="width:100px;"/>
                        <div>
                            <div style="font-size: 12px; color: gray;">Hageland United vzw</div>
                            <div style="font-size: 12px; color: gray;">Grotendries 27</div>
                            <div style="font-size: 12px; color: gray;">3210 Lubbeek</div>
                            <div style="font-size: 12px; color: gray;">BTW: BE 0889.419.625</div>
                            <div style="font-size: 12px; color: gray;">IBAN: BE08 0015 2119 4113</div>
                        </div>
                    </div>
                    <h2 style="text-align: center; font-weight: bold; text-decoration: underline;">Wedstrijd Basketbal Vlaanderen</h2>
                    <table style="width: 100%; border-collapse: collapse; line-height: 2;">
                        <tr><td>Wedstrijd nummer:</td><td>{game.get("wedID", "")}</td></tr>
                        <tr><td>Datum:</td><td>{game.get("datumString", "")}</td></tr>
                        <tr><td>Start uur:</td><td>{game.get("beginTijd", "")}</td></tr>
                        <tr><td>Thuisploeg:</td><td>{game.get("tTNaam", "")}</td></tr>
                        <tr><td>Uitploeg:</td><td>{game.get("tUNaam", "")}</td></tr>
                    </table>

                    <h2 style="text-align: center; font-weight: bold; text-decoration: underline;">Vergoeding scheidsrechters</h2>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <th></th>
                            <th>Naam</th>
                            <th style="text-align: center; width: 120px;">Reiskosten</th>
                            <th style="text-align: center; width: 120px;">Vergoeding</th>
                            <th style="text-align: center; width: 120px;">Totaal</th>
                        </tr>
                        <tr>
                            <td style="padding: 15px 0;">1e</td>
                            <td style="padding: 15px 0;">{game.get("wedOff")[0] if game.get("wedOff") else ''}</td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                        </tr>
                        <tr>
                            <td style="padding: 15px 0;">2e</td>
                            <td style="padding: 15px 0;">{game.get("wedOff")[1] if game.get("wedOff") and len(game.get("wedOff")) > 1 else ''}</td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                            <td style="text-align: center; padding: 15px 0; width: 120px; border: solid 1px #000;"> , </td>
                        </tr>
                    </table>

                    <!-- Signature section -->
                    <div style="text-align: center; margin-top: 30px;">
                        <div style="display: inline-block; width: 43.5%; border: 1px solid black; height: 120px; padding: 10px; text-align: left; vertical-align: bottom;">
                            Voor ontvangst
                            <br style="margin-bottom: 10px;" />
                            <span style="display: block; margin-top: 80px;">
                                {game.get("wedOff")[0] if game.get("wedOff") else 'Scheidsrechter 1:'}
                            </span>
                        </div>
                        <div style="display: inline-block; width: 43.5%; border: 1px solid black; height: 120px; padding: 10px; text-align: left; vertical-align: bottom; margin-left: 5%;">
                            Voor ontvangst
                            <br style="margin-bottom: 10px;" />
                            <span style="display: block; margin-top: 80px;">
                                {game.get("wedOff")[1] if game.get("wedOff") and len(game.get("wedOff")) > 1 else 'Scheidsrechter 2:'}
                            </span>
                        </div>
                    </div>

                    <div style="text-align: center; color: gray; font-size: 8px; position: absolute; bottom: 0px; width: 100%;">
                        Hageland United vzw | Grotendries 27 - 3210 Lubbeek | BTW: BE0889.419.625 | IBAN: BE08 0015 2119 4113 | RPR Leuven
                    </div>
                </div>
                '''

            # Generate the PDF for the current date
            full_html_content = f'''
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                </style>
            </head>
            <body>
                {individual_games_html}
            </body>
            </html>
            '''
            output_path = os.path.join(GENERATED_PDFS_DIR, output_file)
            HTML(string=full_html_content).write_pdf(output_path)
            app.logger.info(f"Individual games PDF generated successfully for {date_str}: {output_file}")
            individual_pdfs.append(output_file)

        return individual_pdfs

    except Exception as e:
        app.logger.error(f"Error generating individual games PDF: {e}")
        raise

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(GENERATED_PDFS_DIR, filename, as_attachment=True)

# Health check route example in app.py
@app.route('/health')
def health_check():
    return jsonify(status='healthy'), 200

if __name__ == '__main__':
    app.run(debug=True)