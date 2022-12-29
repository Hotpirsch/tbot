import requests
import re
import Metar
from airports import Airports, AirportNotFoundException


class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = None

        return last_update


class METARHandler:
    BASE_URL = ''

    def __init__(self, url):
        if url:
            self.BASE_URL = url

    def getmetar(self, station):
        report = ''
        url = "%s/%s.TXT" % (self.BASE_URL, station)
        resp = requests.get(url).text
        for line in resp.splitlines():
            if line.startswith(station):
                report = line.strip()
                try:
                    obs = Metar.Metar(report)
                    return obs
                except Exception as err:
                    return None
        if not report:
            return None


METAR_URL = "http://tgftp.nws.noaa.gov/data/observations/metar/stations"
greet_bot = BotHandler('389820756:AAE-qQ3d35wYFyGFFF9hJuWRqhfVKalB3h0')
metar_conn = METARHandler(METAR_URL)
airports = Airports()


def main():
    new_offset = None

    while True:
        greet_bot.get_updates(new_offset)

        last_update = greet_bot.get_last_update()
        print(last_update)
        # location shared: {'update_id': 857510542, 'message': {'message_id': 421, 'from': {'id': 314410973, 'is_bot': False, 'first_name': 'Christoph', 'last_name': 'Krüger', 'username': 'Hotpirsch', 'language_code': 'de'}, 'chat': {'id': 314410973, 'first_name': 'Christoph', 'last_name': 'Krüger', 'username': 'Hotpirsch', 'type': 'private'}, 'date': 1672314033, 'location': {'latitude': 49.968423, 'longitude': 8.059349}}}
        if last_update and 'message' in last_update.keys():

            last_update_id = last_update['update_id']
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']
            try:
                if 'text' in last_update['message'].keys():
                    last_chat_text = last_update['message']['text']
                    station = airports.lookup(last_chat_text).icao

                if 'location' in last_update['message'].keys():
                    loc_lat = last_update['message']['location']['latitude']
                    loc_lon = last_update['message']['location']['longitude']
                    station = airports.closeto(loc_lat, loc_lon)

            # station = re.search('([A-Z]{4})', last_chat_text.upper()).group(0)
            except AirportNotFoundException:
                station = ""

            if station:
                report = metar_conn.getmetar(station)
                if report is not None:
                    metar_output = report.string()
                else:
                    metar_output = "No weather report for station {}.".format(station)

                last_chat_name += ", here it comes:\n"+metar_output
                greet_bot.send_message(last_chat_id, 'Hi {}'.format(last_chat_name))

            else:
                greet_bot.send_message(last_chat_id,
                                       'Hi {}, I could not find an airport for that city.'.format(last_chat_name))

            new_offset = last_update_id + 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
