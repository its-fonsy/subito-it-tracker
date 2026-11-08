import requests
import json
import copy


MAX_PRICE = 99999999


class SubitoQuery:
    def __init__(
        self,
        title: str = "",
        text: str = "",
        min: int = -1,
        max: int = MAX_PRICE,
    ) -> None:
        self.text = text or ""
        self.title = title or ""
        self.max_price = max or MAX_PRICE
        self.min_price = min or 0

    def get_text(self) -> str:
        return self.text

    def get_title(self) -> str:
        return self.title

    def price_is_in_range(self, price: int) -> bool:
        max = self.max_price or MAX_PRICE
        min = self.min_price or 0
        return price <= max and price >= min

    def from_dict(self, data: dict) -> None:
        self.text = data["text"] or ""
        self.title = data["title"] or ""
        self.max_price = data["max_price"] or MAX_PRICE
        self.min_price = data["min_price"] or 0


class SubitoItem:
    def __init__(self) -> None:
        self.aid: str = ""
        self.title: str = ""
        self.price: int = MAX_PRICE
        self.date: str = ""
        self.geo: str = ""
        self.url: str = ""
        self.tracked: bool = False

    def reset(self) -> None:
        self.title = ""
        self.price = MAX_PRICE
        self.date = ""
        self.geo = ""
        self.url = ""
        self.tracked = False

    def from_dict(self, data: dict) -> None:
        self.aid = data["aid"] or ""
        self.title = data["title"] or ""
        self.price = data["price"] or MAX_PRICE
        self.date = data["date"] or ""
        self.geo = data["geo"] or ""
        self.url = data["url"] or ""
        self.tracked = data["tracked"] or False

    def dump(self) -> str:
        dump = f"Title = {self.title}\n"
        dump += f"Price = {self.price}\n"
        dump += f"Date = {self.date}\n"
        dump += f"Geo = {self.geo}\n"
        dump += f"Url = {self.url}\n"
        dump += f"Id = {self.aid}\n"
        dump += f"Tracked = {self.tracked}"
        return dump

    def is_tracked(self) -> bool:
        return self.tracked

    def __str__(self) -> str:
        string = f"{self.date.split()[0]}"
        string += f" {int(self.price)} EUR"
        string += f" {self.geo},"
        string += f" {self.title}"
        return string

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SubitoItem):
            return False
        return self.aid == other.aid


class SubitoApi:
    def __init__(self):
        pass

    def search(self, query: SubitoQuery) -> list[SubitoItem]:

        url = "https://www.subito.it/hades/v1/search/items"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Subito-Environment-ID": "",
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
            "start": 0,
        }

        # Send request
        raw_response = requests.request(
            "GET", url, data="", headers=headers, params=querystring
        )

        dict_response = json.loads(raw_response.text)
        data = {}
        result_list = []

        # Parse all the AD found
        it = SubitoItem()
        for ad in dict_response["ads"]:
            it.reset()

            # Get the price from the AD
            price = 0
            try:
                for feature in ad["features"]:
                    if feature["uri"] == "/price":
                        price = int(feature["values"][0]["key"])
                        break
            except Exception as e:
                print(f"Warning: can't find price for {ad['subject']}, error {e}")
                continue

            if not price or not query.price_is_in_range(price):
                continue

            try:
                town = ad["geo"]["town"]["friendly_name"]
                city = ad["geo"]["city"]["short_name"]

                data["title"] = ad["subject"]
                data["aid"] = ad["urn"].split(":")[2]
                data["price"] = price
                data["date"] = ad["dates"]["display"]
                data["geo"] = f"{town} ({city})"
                data["url"] = ad["urls"]["default"]
                data["tracked"] = False
            except Exception as e:
                print(f"Warning: can required metadata, error {e}")
                continue

            it.from_dict(data)
            result_list.append(copy.copy(it))

        return result_list
