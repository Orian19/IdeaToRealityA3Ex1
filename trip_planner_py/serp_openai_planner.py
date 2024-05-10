from datetime import datetime
import json
import math

from openai import OpenAI
import serpapi


class TripPlan:
    def __init__(self, cfg='cfg.json'):
        self.cfg = self._load_config(cfg)

        # setup api keys
        self.openai_client = OpenAI(api_key=self.cfg["OPENAI_API_KEY"])
        self.serp_client = serpapi.Client(api_key=self.cfg["SERPAPI_API_KEY"])

        # user trip preferences
        self.start_date = None
        self.end_date = None
        self.month = ''
        self.budget = math.inf
        self.trip_type = ''

        # openai suggestion
        self.possible_destinations = ''

    def create_trip(self):
        """
        create the entire trip plan and show the user the details: cost, flight, hotel, daily plan and the images
        :return:
        """
        self._get_user_trip_preferences()
        self._get_trip_suggestions()

    @staticmethod
    def _load_config(cfg: str) -> any:
        """
        loading the json config
        :return:
        """
        with open(cfg) as config_file:
            return json.load(config_file)

    def _get_user_trip_preferences(self) -> None:
        """
        get user preferences about start,end dates as well as budget and trip type
        :return:
        """
        # start_date = input("Enter the start date of your planned trip (YYYY-MM-DD): ")
        # end_date = input("Enter the end date of your planned trip (YYYY-MM-DD): ")
        # self.budget = float(input("Enter your total budget in USD for the trip: "))
        # self.trip_type = input("Enter the type of trip (ski/beach/city): ")

        start_date = '2024-10-10'
        end_date = '2024-10-15'
        self.budget = 1000
        self.trip_type = 'city'

        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.month = self.start_date.strftime("%B")  # get the month name

    def _get_trip_suggestions(self) -> None:
        """
        get trip suggestions from chatgpt - 5 possible places in the world based on the month of the trip
        :return:
        """
        prompt = (f"Suggest 5 possible places in the world for a {self.trip_type} trip in {self.month}. "
                  f"GIVE JUST NAMES, ONE PLACE IN EACH LINE (DO NOT NUMBER THE OPTIONS!!!)")
        response = self.openai_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable travel assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        self.possible_destinations = response.choices[0].message.content.strip().replace('-','').split("\n")

        print(f"Suggested destinations for a {self.trip_type} trip in {self.month}:")
        for i, destination in enumerate(self.possible_destinations, start=1):
            print(f"{i}. {destination}")


def main():
    plan = TripPlan()
    plan.create_trip()


if __name__ == '__main__':
    main()
