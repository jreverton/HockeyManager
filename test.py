import discord
import requests
import re
import settings
import time
from bs4 import BeautifulSoup as bs

from datetime import datetime, timedelta
from selenium import webdriver

# TEAM SCHEDULE
# team_homepage = bs(requests.get(settings.PRIMARY_URL + settings.TEAM_ID + "&seasonid=" + settings.SEASON_ID).text, "html.parser")
# schedule_table = team_homepage.find(class_="table-responsive")
# schedule_games = schedule_table.findAll("tr")

# home_teams = []
# away_teams = []
# game_day = []
# game_time = []

# for row in schedule_games:
#     data = row.findAll("td")
#     index =0
#     for cell in data:
#         team = cell.find("a")
        
#         if index == 0:
#             home_teams.append(team.text)
#         elif index == 1:
#             away_teams.append(team.text)
#         elif index == 2:
#             game_day.append(cell.text)
#         elif index == 3:
#             game_time.append(cell.text)
#         index = index + 1

# game_day[-1] = "Mon, Apr 29"

# # convert the game date to a date object for comparison
# current_year = str(datetime.today().year)
# game_date = datetime.strptime(game_day[-1] + " " + current_year, "%a, %b %d %Y").date()

# # for date compairons testing change delta
# game_date_test = game_date + timedelta(days=1)

# # testing for loop
# for i in range(len(game_day)):
#     game_date = datetime.strptime(game_day[i] + " " + current_year, "%a, %b %d %Y").date()
#     if datetime.today().date() < game_date < datetime.today().date() + timedelta(days=4) :
#         print(home_teams[i])
#         print(away_teams[i])
#         print(game_day[i])
#         print(game_time[i])
#         break

# results
# print(game_date)
# print(game_date_test)
# print(game_date_test > datetime.today().date())
# print(datetime.today().weekday())
# player_stat_dict = {
#     1: "Number",
#     3: "Name",
#     5: "Games Played",
#     7: "Goals",
#     9: "Assist",
#     11: "Points",
#     13: "Penalty Minutes",
#     15: "Power Play Goals",
#     17: "Short Handed Goals",
#     19: "Game Winning Goals",
#     21: "Power Play Goals Against"
# }

# goalie_stat_dict = {
#     1: "Number",
#     3: "Name",
#     5: "Games Played",
#     7: "Minutes",
#     9: "Wins",
#     11: "Loses",
#     12: "Ties",
#     14: "Shoot Outs",
#     16: "Goals Against",
#     18: "Goals Against Average",
#     20: "Saves",
#     22: "Save Percentage"
# }
# options =  webdriver.FirefoxOptions()
# options.add_argument("--headless")
# browser = webdriver.Firefox(options=options)
# browser.get("http://stats.pointstreak.com/players/players-team-roster.html?teamid=804660&seasonid=21384")
# time.sleep(2)
# team_info = browser.page_source
# browser.quit()
# team_info_soup = bs(team_info, "html.parser")
# player_name = 'Dylan Steele'
# player_name = 'Zach Shiff'
# player_name = 'Stephen Cary'
# players = team_stats.find_all("a", string=re.compile(player_name))
# print(players)
# print(players[1].parent.parent)
# player_row = players[0].parent.parent
# player_row = players[1].parent.parent
# # print(player_row)
# count = 0
# for item in player_row.contents:
#     print(count,  ": ", item.get_text(strip=True), item.get_text(strip=True)=='')
#     count =  count + 1
# secondary = False
# for tag in players:
#     player_row = tag.parent.parent
#     if not secondary:
#         for i in range(len(player_row.contents)):
#             if player_row.contents[i].get_text(strip=True) != '':
#                 print(f"{player_stat_dict[i]} : {player_row.contents[i].get_text(strip=True)}")
#         secondary = True
#     else:
#         for i in range(len(player_row.contents)):
#             if player_row.contents[i].get_text(strip=True) != '':
#                 print(f"{goalie_stat_dict[i]} : {player_row.contents[i].get_text(strip=True)}")
#     print()

# for count2 in range(1, len(player_row.contents), 2):
#     print(f"{stat_dict[count2]} : {player_row.contents[count2].get_text(strip=True)}")
# options =  webdriver.FirefoxOptions()
# options.add_argument("--headless")
# browser = webdriver.Firefox(options=options)
# browser.get("http://stats.pointstreak.com/players/players-team-roster.html?teamid=804660&seasonid=21384")
# time.sleep(2)
# team_info = browser.page_source
# browser.quit()

# team_info_soup = bs(team_info, "html.parser")
# team_stats = team_info_soup.find(id="team-stats")
# team_ranks = team_stats.find_all(class_="nova-team-rank")
# team_stats_v_div = team_stats.find_all(class_="morris-hover morris-default-style")
# ranks = {}
# stats = {}

# for tag in team_ranks:
#     label = tag.find(class_="nova-team-rank__label").text
#     rank = tag.find(class_="nova-team-rank__ranking").text
#     value = tag.find(class_="text-center").text[1:-1]
#     ranks[label] = [rank, value]

# for tag in team_stats_v_div:
#     # print("label:", tag.find(class_="morris-hover-row-label").text)
#     # print("1:", tag.find_all(class_="morris-hover-point")[0].text.replace("\t", '').replace("\n", '').split(" ")[-1])
#     # print("2:", tag.find_all(class_="morris-hover-point")[1].text.replace("\t", '').replace("\n", '').split(" ")[-1])
#     # print()
#     stats[tag.find(class_="morris-hover-row-label").text] = {
#         "Team": tag.find_all(class_="morris-hover-point")[0].text.replace("\t", '').replace("\n", '').split(" ")[-1],
#         "Division": tag.find_all(class_="morris-hover-point")[1].text.replace("\t", '').replace("\n", '').split(" ")[-1]
#     }

# print(stats)
# print("\n\n")
# print(ranks)

# print(team_stats_v_div)
# print(team_stats_v_div[0])

standings_page = bs(requests.get("http://stats.pointstreak.com/players/players-division-standings.html?divisionid=120127&seasonid=21384").text, "html.parser")
standings_table = standings_page.find_all(class_="table table-hover table-striped nova-stats-table")[0].find_all("tr")
standings_table = standings_table[1:]
header = ["Team Name", "GP", "W", "L", "OTW", "SOW", "OTL", "SOL", "PTS", "GF", "GA", "PIM", "Last 5", "Streak"]
rows= []
i = 0
for row in standings_table:
    temp = []
    for cell in row.contents:
        if cell.text == '' or cell.text== '\n' or cell.text == "\t" or cell.text == " ":
            continue
        else:
            if i%14 == 13:
                temp.append(cell.text.replace("\t", '').replace("\n", ''))
                rows.append(temp)
                i = i + 1
                temp=[]
            elif i%14 == 0:
                temp.append(cell.text.replace("\t", '').replace("\n", '')[1:])
                i = i + 1
            else:
                temp.append(cell.text.replace("\t", '').replace("\n", ''))
                i = i + 1