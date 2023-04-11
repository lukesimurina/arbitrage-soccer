from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def find_index_of_game(matches, team1, team2):
    for i, game in enumerate(matches):
        if {team1, team2} == set(game[:2]):
            return i
    return -1  # Return -1 if the game is not found


def scrape(sportsbet_link="", ladbrokes_link="", pointsbet_link="", bet365_link=""):
    matches = []
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=ChromeService(executable_path=ChromeDriverManager().install()),
        options=options,
    )
    driver.get(sportsbet_link)
    # Define the maximum time to wait for the elements to appear in seconds
    WAIT_TIME = 10

    # Define the XPATH for the elements for sportsbet
    XPATH_SPORTSBET = '//div[@data-automation-id="content-scroll-container"]//div[@data-automation-id="content-background"]//div[@data-automation-id="competition-matches-container"]//li'

    # Wait for the elements to appear
    sportsbet_li = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_all_elements_located((By.XPATH, XPATH_SPORTSBET))
    )
    sportsbet_li_formatted = []
    print("Scraped games from Sportsbet")
    for i in sportsbet_li:
        match_odds = i.find_elements(By.XPATH, ".//button")
        arr1 = []
        for i in match_odds:
            arr1.append(i.text.split("\n"))
        sportsbet_li_formatted.append(arr1.copy())
    print("Formatted games from Sportsbet")
    for i in sportsbet_li_formatted:
        match_formatted = [
            i[0][0],
            i[2][0],
            "date",
            [["Sportsbet", float(i[0][1]), float(i[1][1]), float(i[2][1])]],
        ]
        matches.append(match_formatted.copy())
    driver.quit()
    print("Starting Ladbrokes")
    driver1 = webdriver.Chrome(
        service=ChromeService(executable_path=ChromeDriverManager().install()),
        options=options,
    )
    driver1.get(ladbrokes_link)

    # Define the XPATH for the elements for ladbrokes
    XPATH_LADBROKES = '//div[@class="sports-event-entry-with-markets"]/div[1]//div[@class="sports-market-primary__prices-inner"]'

    # Wait for the elements to appear
    ladbrokes_li = WebDriverWait(driver1, WAIT_TIME).until(
        EC.presence_of_all_elements_located((By.XPATH, XPATH_LADBROKES))
    )
    print("Scraped games from Ladbrokes")
    ladbrokes_games_odds = []
    for game in ladbrokes_li:
        game_buttons = game.find_elements(By.XPATH, ".//button")
        game_odds = []
        for i in game_buttons:
            game_odds.append(i.text.split("\n"))
        ladbrokes_games_odds.append(game_odds.copy())

    for game in ladbrokes_games_odds:
        index = find_index_of_game(matches, game[0][0], game[2][0])
        if index != -1:
            matches[index][3].append(
                ["Ladbrokes", float(game[0][1]), float(game[1][1]), float(game[2][1])]
            )

    driver1.quit()

    # Bet365

    return matches


def compute_highest_odds_football(odds):
    highest_odds = []

    for game in odds:
        game_highest = {
            "team1": "",
            "team2": "",
            "date": "",
            "odds": {
                "team1_win": {"bookie": "", "odd": 0},
                "draw": {"bookie": "", "odd": 0},
                "team2_win": {"bookie": "", "odd": 0},
            },
        }
        game_highest["team1"] = game[0]
        game_highest["team2"] = game[1]
        game_highest["date"] = game[2]

        # Best odds for team1 win
        team1_win_bookie, team1_win_odd = "", 0
        for bookie in game[3]:
            if bookie[1] > team1_win_odd:
                team1_win_bookie = bookie[0]
                team1_win_odd = bookie[1]
        game_highest["odds"]["team1_win"]["bookie"] = team1_win_bookie
        game_highest["odds"]["team1_win"]["odd"] = team1_win_odd

        # Best odds for draw
        draw_bookie, draw_odd = "", 0
        for bookie in game[3]:
            if bookie[2] > draw_odd:
                draw_bookie = bookie[0]
                draw_odd = bookie[2]
        game_highest["odds"]["draw"]["bookie"] = draw_bookie
        game_highest["odds"]["draw"]["odd"] = draw_odd

        # Best odds for team2 win
        team2_win_bookie, team2_win_odd = "", 0
        for bookie in game[3]:
            if bookie[3] > team2_win_odd:
                team2_win_bookie = bookie[0]
                team2_win_odd = bookie[3]
        game_highest["odds"]["team2_win"]["bookie"] = team2_win_bookie
        game_highest["odds"]["team2_win"]["odd"] = team2_win_odd

        highest_odds.append(game_highest.copy())
    return highest_odds


def arbitrage_football(game, stake):
    team1_win = game["odds"]["team1_win"]["odd"]
    draw = game["odds"]["draw"]["odd"]
    team2_win = game["odds"]["team2_win"]["odd"]
    total_invest = stake
    team1_win_outlay = total_invest / team1_win
    team2_win_outlay = total_invest / team2_win
    draw_outlay = total_invest / draw
    total_outlay = team1_win_outlay + team2_win_outlay + draw_outlay
    if (1 / team1_win + 1 / draw + 1 / team2_win) < 1:
        profit = total_invest - total_outlay
        roi = (profit / total_invest) * 100
        return (
            True,
            roi,
            profit,
            {
                "team1_win": team1_win_outlay,
                "draw": draw_outlay,
                "team2_win": team2_win_outlay,
            },
        )
    else:
        return False, 0, 0, {}


def display_results(odds, stake):
    highest_odds = compute_highest_odds_football(odds)
    print("\n")
    for game in highest_odds:
        print(game["team1"], "vs", game["team2"])
        print(
            game["team1"],
            "win:",
            game["odds"]["team1_win"]["bookie"],
            game["odds"]["team1_win"]["odd"],
        )
        print("Draw:", game["odds"]["draw"]["bookie"], game["odds"]["draw"]["odd"])
        print(
            game["team2"],
            "win:",
            game["odds"]["team2_win"]["bookie"],
            game["odds"]["team2_win"]["odd"],
        )
        possible, roi, profit, inv = arbitrage_football(game, stake)
        print("Arbitrage:", possible)
        print("ROI:", str(roi) + "%")
        print("Profit:", "$" + str(profit))
        print("Investment:", inv)
        print("\n")


if __name__ == "__main__":
    matches = scrape(
        "https://www.sportsbet.com.au/betting/soccer/italy/italian-serie-a",
        "https://www.ladbrokes.com.au/sports/soccer/italy/italian-serie-a",
    )
    print("Done scraping")
    display_results(matches, 1000)
