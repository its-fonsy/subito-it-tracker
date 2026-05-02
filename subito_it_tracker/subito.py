import requests
import json


class SubitoQuery:
    def __init__(self, title=None, text=None, min=None, max=None):
        self.text = text
        self.title = title
        self.max_price = max
        self.min_price = min

    def get_text(self):
        return self.text

    def get_title(self):
        return self.title

    def price_is_in_range(self, price):
        max = self.max_price or 99999999
        min = self.min_price or 0
        return price <= max and price >= min

    def from_dict(self, data):
        self.text = data["text"]
        self.title = data["title"]
        self.max_price = data["max_price"]
        self.min_price = data["min_price"]


class SubitoItem:
    def __init__(self):
        self.title: str = None
        self.price: int = None
        self.date: str = None
        self.geo: str = None
        self.url: str = None
        self.tracked: bool = None

    def from_dict(self, data):
        self.title = data["title"]
        self.price = data["price"]
        self.date = data["date"]
        self.geo = data["geo"]
        self.url = data["url"]
        self.tracked = data["tracked"]

    def dump(self):
        dump = f"Title = {self.title}\n"
        dump += f"Price = {self.price}\n"
        dump += f"Date = {self.date}\n"
        dump += f"Geo = {self.geo}\n"
        dump += f"Url = {self.url}\n"
        dump += f"Tracked = {self.tracked}"
        return dump

    def is_tracked(self):
        return self.tracked

    def __str__(self):
        string = f"{self.date.split()[0]}"
        string += f" {int(self.price)} EUR"
        string += f" {self.geo},"
        string += f" {self.title}"
        return string

    def __eq__(self, other):
        return self.title == other.title and \
            self.price == other.price and \
            self.date == other.date and \
            self.geo == other.geo and \
            self.url == other.url


class SubitoApi:

    def __init__(self):
        pass

    def search(self, query: SubitoQuery) -> list[SubitoItem]:

        if not query:
            return None

        result_list = []
        url = "https://www.subito.it/hades/v1/search/items"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Subito-Environment-ID": ""
        }
        querystring = {
            "q": query.get_text(),
            "t": "s",
            "qso": "false",
            "ndo": "false",
            "shp": "false",
            "urg": "false",
            "sort": "datedesc",
            "lim": 100,
            "start": 0
        }

        raw_response = requests.request("GET", url, data="",
                                        headers=headers, params=querystring)

        dict_response = json.loads(raw_response.text)
        data = {}
        for ad in dict_response['ads']:
            it = SubitoItem()

            price = None
            for feature in ad["features"]:
                if feature["uri"] == "/price":
                    price = int(feature["values"][0]["key"])
                    break

            if not price or not query.price_is_in_range(price):
                continue

            town = ad["geo"]["town"]["friendly_name"]
            city = ad["geo"]["city"]["short_name"]

            data["title"] = ad['subject']
            data["price"] = price
            data["date"] = ad["dates"]["display"]
            data["geo"] = f"{town} ({city})"
            data["url"] = ad["urls"]["default"]
            data["tracked"] = False

            it.from_dict(data)
            result_list.append(it)

        return result_list
