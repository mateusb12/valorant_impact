import json
import requests
from bs4 import BeautifulSoup

page = requests.get("https://rib.gg/series/12728?match=25609")
soup = BeautifulSoup(page.content, 'html.parser')

scripts = soup.findAll('script')
match_tag = scripts[5]
match_script = match_tag.contents[0].string
match_script = match_script[45:]

first_half = match_script[:match_script.find("?{}:")]
second_half = match_script[match_script.find("?{}:"):][4:]

with open("matches/script_a.txt", "w") as text_file:
    n = text_file.write(first_half)

with open("matches/script_b.txt", "w") as text_file:
    o = text_file.write(second_half)