# shared_functions.py

import logging
from datetime import datetime, timedelta
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('PIL').setLevel(logging.ERROR)  # Reduce verbosity
logging.getLogger('fontTools').setLevel(logging.ERROR)  # Reduce verbosity

def fetch_games(teams, acc_guids, selected_date):
    games = []
    try:
        for team in teams:
            url = f"http://vblcb.wisseq.eu/VBLCB_WebService/data/TeamMatchesByGuid?teamguid=BVBL1447{team}"
            response = requests.get(url)
            response.raise_for_status()  # Raises an error for bad status codes

            game_data_list = response.json()
            logging.debug(f"Fetched {len(game_data_list)} games for team {team}.")

            for game_data in game_data_list:
                game_acc_guid = game_data.get("accGUID")
                logging.info(f"Checking game with accGUID: {game_acc_guid}")

                if game_acc_guid in acc_guids:
                    game_date_str = game_data.get("datumString")
                    try:
                        game_date = datetime.strptime(game_date_str, "%d-%m-%Y").date()
                    except ValueError:
                        try:
                            game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                        except ValueError:
                            logging.warning(f"Unrecognized date format: {game_date_str}")
                            continue

                    if game_date == selected_date:
                        games.append(game_data)
                        logging.info(f"Game on selected date: {game_data}")
                else:
                    logging.debug(f"No match for accGUID: {game_acc_guid}")

    except requests.RequestException as e:
        logging.error(f"Error fetching games for team {team}: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Error processing game data: {e}")

    logging.info(f"Total games found: {len(games)}")
    return games

def group_games_by_date(games):
    games_by_date = {}
    for game in games:
        game_date_str = game.get("datumString")
        try:
            game_date = datetime.strptime(game_date_str, "%d-%m-%Y").date()
        except ValueError:
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
            except ValueError:
                logging.warning(f"Unrecognized date format: {game_date_str}")
                continue
        if game_date not in games_by_date:
            games_by_date[game_date] = []
        games_by_date[game_date].append(game)
    return games_by_date

def split_team_name(team_name):
    """Split the team name into two lines if it's too long."""
    if len(team_name) > 25:
        words = team_name.split()
        mid_point = len(words) // 2
        # Attempt to find a suitable split point for balanced lengths
        split_index = mid_point
        while split_index > 0 and len(" ".join(words[:split_index])) > 25:
            split_index -= 1
        return "<br/>".join([" ".join(words[:split_index]), " ".join(words[split_index:])])
    return team_name