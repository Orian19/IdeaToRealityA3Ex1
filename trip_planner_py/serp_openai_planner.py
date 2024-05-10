from datetime import datetime
import json
import math

from openai import OpenAI
import serpapi

import airportsdata


def get_airport_iata_code(city_name):
    airports = airportsdata.load('IATA')  # Load airports data indexed by IATA code
    # Filter airports by city name
    matching_airports = {k: v for k, v in airports.items() if v['city'].lower() == city_name.lower()}

    if matching_airports:
        # Return the IATA code of the first matching airport
        first_key = next(iter(matching_airports))
        return matching_airports[first_key]['iata']
    return "No airport found"


class TripPlan:
    def __init__(self, cfg='cfg.json'):
        self.cfg = self._load_config(cfg)

        # setup api keys
        self.openai_client = OpenAI(api_key=self.cfg["OPENAI_API_KEY"])
        self.serp_client = serpapi.Client(api_key=self.cfg["SERPAPI_API_KEY"])

        # user trip preferences
        self.start_date = None
        self.end_date = None
        self.duration = 0
        self.month = ''
        self.budget = math.inf
        self.trip_type = ''

        # default origin
        self.origin = "Tel Aviv"

        # openai suggestion
        self.possible_destinations = []

        # serpapi results
        self.travel_options = []

    def create_trip(self):
        """
        create the entire trip plan and show the user the details: cost, flight, hotel, daily plan and the images
        :return:
        """
        self._get_user_trip_preferences()
        self._get_trip_suggestions()
        self._get_travel_options()

    @staticmethod
    def _load_config(cfg: str) -> any:
        """
        loading the json config
        :return:
        """
        with open(cfg) as config_file:
            return json.load(config_file)

    def _get_trip_duration(self):
        """
        get trip duration in days (start date to end date)
        :return:
        """
        date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
        date2 = datetime.strptime(self.end_date, '%Y-%m-%d')
        return abs((date2 - date1).days)

    def _get_user_trip_preferences(self) -> None:
        """
        get user preferences about start,end dates as well as budget and trip type
        :return:
        """
        # start_date = input("Enter the start date of your planned trip (YYYY-MM-DD): ")
        # end_date = input("Enter the end date of your planned trip (YYYY-MM-DD): ")
        # self.budget = float(input("Enter your total budget in USD for the trip: "))
        # self.trip_type = input("Enter the type of trip (ski/beach/city): ")

        self.start_date = '2024-10-10'
        self.end_date = '2024-10-15'
        self.budget = 10000
        self.trip_type = 'city'

        self.month = datetime.strptime(self.start_date, "%Y-%m-%d").strftime("%B")  # get the month name

        self.duration = self._get_trip_duration()

    def _get_trip_suggestions(self) -> None:
        """
        get trip suggestions from chatgpt - 5 possible places in the world based on the month of the trip
        :return:
        """
        prompt = (f"Suggest 5 possible places(ONLY CITY NAME!!!) in the world for a {self.trip_type} trip in {self.month}. "
                  f"GIVE JUST CITY NAMES, ONE PLACE IN EACH LINE (DO NOT NUMBER THE OPTIONS!!!). "
                  f"I repeat, give only CITY name and don't number the opotions")
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
            temperature=1,
            max_tokens=1024,
        )
        self.possible_destinations = response.choices[0].message.content.strip().replace('- ', '').split("\n")

        print(f"Suggested destinations for a {self.trip_type} trip in {self.month}:")
        for i, destination in enumerate(self.possible_destinations, start=1):
            print(f"{i}. {destination}")

    def _get_flight(self, destination: str) -> dict[str: float]:
        cheapest_flight = {}
        try:
            # response = self.serp_client.search(
            #     engine='google_flights',
            #     departure_id=get_airport_iata_code(self.origin),
            #     arrival_id=get_airport_iata_code(destination),
            #     outbound_date=self.start_date,
            #     return_date=self.end_date,
            #     show_hidden=True
            #     # stops=1
            # )

            with open('flights_response.json') as response:
                response = json.load(response)

            # if response.data:
            #     response = response.data['best_flights'][0]
            #     cheapest_flight.update({destination: response})

            if response['best_flights']:
                response = response['best_flights'][0]
                cheapest_flight.update({destination: response})
        except serpapi.exceptions.SerpApiError as e:
            print(f"Error searching flights to {destination}: {e}")

        return cheapest_flight

    def _get_hotel(self, destination: str, duration, budget: float) -> dict[str: float] | None:
        expensive_hotel = {}
        try:
            # response = self.serp_client.search(
            #     engine='google_hotels',
            #     q=f'{destination} hotels',
            #     adults=1,
            #     sort_by=3,  # sorts by low
            #     max_price=budget,
            #     check_in_date=self.start_date,
            #     check_out_date=self.end_date,
            # )

            with open('hotels_response.json') as response:
                response = json.load(response)

            # if response.data:
            #     response = response.data['properties']
            #     for prop in reversed(response):
            #         if prop['prices'][0]['rate_per_night']['extracted_lowest'] * duration <= budget:
            #             expensive_hotel.update({destination: prop})
            #             return expensive_hotel

            if response['properties']:
                response = response['properties']
                for prop in reversed(response):
                    if prop['prices'][0]['rate_per_night']['extracted_lowest'] * duration <= budget:
                        expensive_hotel.update({destination: prop})
                        return expensive_hotel
        except serpapi.exceptions.SerpApiError as e:
            print(f"Error searching hotels in {destination}: {e}")

        print("No hotels in your budget. You can't afford this trip")
        exit()

    def _get_travel_options(self) -> None:
        """
        make a request to google flights using serapi and search for flights from Tel Aviv to each of the possible
        destinations chatgpt found. choosing the cheapest flight for each destination.
        then making a request to Google hotels using serapi and finding relevant hotels in each of the possible
        destinations. (finding a single hotel for the whole trip). finding the most expensive hotel (price wise) that
        the user can afford according to the budget.

        result - 5 possible destinations (flight+hotel for each destination)

        :return:
        """
        flights = {}  # cheapest
        hotels = {}  # most expensive (budget is after selecting the flight)
        for destination in self.possible_destinations:
            cheapest_flight = self._get_flight(destination)
            cheapest_flight_price = cheapest_flight.get(next(iter(cheapest_flight)))['price']
            if cheapest_flight_price >= self.budget:
                print("\nYou can't afford a trip to any of the suggested locations\n")
                exit()
            flights.update(cheapest_flight)

            expensive_hotel = self._get_hotel(destination, self.duration, self.budget - cheapest_flight_price)
            hotels.update(expensive_hotel)

            # cheapest_flight_key = min(flights, key=lambda k: flights[k]['price'])
            # most_expensive_hotel_key = max(hotels, key=lambda k: hotels[k]['prices'][0]['rate_per_night']['extracted_lowest'])
            most_expensive_hotel_price = expensive_hotel.get(next(iter(
                expensive_hotel)))['prices'][0]['rate_per_night']['extracted_lowest']
            total_cost = cheapest_flight_price + most_expensive_hotel_price * self.duration
            self.travel_options.append({
                "destination": destination,
                "flight": cheapest_flight,
                "hotel": expensive_hotel,
                "total_cost": total_cost,
            })


def main():
    plan = TripPlan()
    plan.create_trip()


if __name__ == '__main__':
    main()
