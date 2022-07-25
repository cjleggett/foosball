import re
import json
from util import ROOT_DIR

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


TOKEN_FILE = ROOT_DIR / "slack_bot_tokens.json"


def load_tokens():
    with open(TOKEN_FILE) as f:
        data = json.load(f)
        return data


TOKENS = load_tokens()
app = App(token=TOKENS["bot-token"])

ID_TO_NAME = {
    "U0146GZMZBK": "DamianBarabonkov",
    "U0151DVTK41": "IvanDimitrov",
}


def parse_command(body):
    text = body['event']['text']
    command_r = '!\w+'
    search = re.search(f'{command_r}', text)
    if search:
        command = search.group(0)
        command_end_pos = search.span(0)[1]
        if command == '!g':
            trimmed_text = text[command_end_pos:]
            parse_score(trimmed_text)


def parse_score(text):
    user_id = '<@\w+>'
    team = f'((?:{user_id}\s*)+)'
    search = re.search(f'^\s*{team}\s*(\d+)\s*[-|:]\s*(\d+)\s*{team}$', text)
    if search:
        (team1, score1) = search.group(1), search.group(2)
        (team2, score2) = search.group(4), search.group(3)
        team1 = [ID_TO_NAME[tm] for tm in re.findall('<@(\w+)>', team1)]
        team2 = [ID_TO_NAME[tm] for tm in re.findall('<@(\w+)>', team2)]
        print("{t1} {s1} - {s2} {t2}".format(t1=team1, s1=score1, s2=score2, t2=team2))


@app.event("app_mention")
def event_test(say, body):
    parse_command(body)


if __name__ == "__main__":
    handler = SocketModeHandler(app, TOKENS['app-token'])
    handler.start()