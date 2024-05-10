from datetime import datetime
import json
import math

import openai
import serpapi


class TripPlan:
    def __init__(self, cfg='cfg.json'):
        self.cfg = self.load_config(cfg)

        # setup api keys
        openai.api_key = self.cfg["OPENAI_API_KEY"]
        self.serp_client = serpapi.Client(api_key=self.cfg["SERPAPI_API_KEY"])

        # user trip preferences
        self.start_date = None
        self.end_date = None
        self.month = ''
        self.budget = math.inf
        self.trip_type = ''

        self.get_user_trip_preferences()

    @staticmethod
    def load_config(cfg):
        """
        loading the json config
        :return:
        """
        with open(cfg) as config_file:
            return json.load(config_file)

    def get_user_trip_preferences(self):
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


def main():
    plan = TripPlan()
    print(plan.__dict__)


if __name__ == '__main__':
    main()
