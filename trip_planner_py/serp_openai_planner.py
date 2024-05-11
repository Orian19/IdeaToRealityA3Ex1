from datetime import datetime
import json
import math
import os
import re

from openai import OpenAI
import serpapi

import airportsdata

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
import uvicorn


app = FastAPI()

allowed_origin = os.getenv('CORS_ORIGIN', 'http://localhost:3000')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TripPreferences(BaseModel):
    """
    user preferences for the trip - using pydantic to validate data (type and context wise)
    """
    model_config = {
        "extra": "forbid",  # not allowing attributes that are not defined here to be sent from the client
    }
    start_date: str = Field(examples=["2024-10-10"], description="start date of the trip")
    end_date: str = Field(examples=["2024-10-15"], description="end date of the trip")
    budget: float = Field(examples=["3000"], description="budget in US $")
    trip_type: str = Field(examples=["city", "ski", "beach"], description="trip type")


class TripSelection(BaseModel):
    """
    user trip selection out of the available options - using pydantic to validate data (type and context wise)
    """
    model_config = {
        "extra": "forbid",  # not allowing attributes that are not defined here to be sent from the client
    }
    trip_selection_idx: int  # index from travel_options list


class TripResultsHandling(BaseModel):
    """
    trip results - using pydantic to validate data (type and context wise)
    """
    model_config = {
        "extra": "forbid",  # not allowing attributes that are not defined here to be sent from the client
    }
    email: EmailStr = Field(examples=["example@gmail.com"], description="email address to send results to", frozen=True)


def get_airport_iata_code(city_name: str) -> str:
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

        # final trip results
        self.trip_selection = None
        self.trip_plan = None
        self.trip_images = []

    def create_trip(self) -> None:
        """
        create the entire trip plan and show the user the details: cost, flight, hotel, daily plan and the images
        :return:
        """
        # self._get_user_trip_preferences()
        # self._get_trip_suggestions()
        # self._get_travel_options()
        # self._generate_daily_plan()
        # self._generate_images_trip_illustration()
        pass

    @staticmethod
    def _load_config(cfg: str) -> any:
        """
        loading the json config
        :return:
        """
        with open(cfg) as config_file:
            return json.load(config_file)

    def _get_trip_duration(self) -> int:
        """
        get trip duration in days (start date to end date)
        :return: duration in days
        """
        date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
        date2 = datetime.strptime(self.end_date, '%Y-%m-%d')
        return abs((date2 - date1).days)

    def get_user_trip_preferences(self, user_pref: TripPreferences):
        """
        get user preferences about start,end dates as well as budget and trip type
        :return:
        """

        self.start_date = user_pref.start_date
        self.end_date = user_pref.end_date
        self.budget = user_pref.budget
        self.trip_type = user_pref.trip_type

        # start_date = input("Enter the start date of your planned trip (YYYY-MM-DD): ")
        # end_date = input("Enter the end date of your planned trip (YYYY-MM-DD): ")
        # self.budget = float(input("Enter your total budget in USD for the trip: "))
        # self.trip_type = input("Enter the type of trip (ski/beach/city): ")

        # self.start_date = '2024-10-10'
        # self.end_date = '2024-10-15'
        # self.budget = 10000
        # self.trip_type = 'city'

        self.month = datetime.strptime(self.start_date, "%Y-%m-%d").strftime("%B")  # get the month name

        self.duration = self._get_trip_duration()

    def get_info_travel_assistant(self, prompt: str, temperature: float):
        """
        chatgpt travel assistant - returns helpful information give a prompt and temperature
        :param prompt: query
        :param temperature:
        :return:
        """
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
            temperature=temperature,
            max_tokens=1024,
        )

        return response

    def get_trip_suggestions(self) -> None:
        """
        get trip suggestions from chatgpt - 5 possible places in the world based on the month of the trip
        :return:
        """
        prompt = (f"Suggest 5 possible places(ONLY CITY NAME!!!) in the world for a {self.trip_type} trip in {self.month}. "
                  f"GIVE JUST CITY NAMES, ONE PLACE IN EACH LINE (DO NOT NUMBER THE OPTIONS!!!). "
                  f"I repeat, give only CITY name and don't number the opotions")
        response = self.get_info_travel_assistant(prompt, 1)
        response = response.choices[0].message.content.strip()
        self.possible_destinations = response.replace('- ', '').split("\n")
        if '1' in self.possible_destinations[0]:  # in case (annoying) chatgpt numbered the results
            self.possible_destinations = [re.sub(r'^\d+\.\s*', '', s) for s in response.split("\n")]

    def get_flight(self, destination: str) -> dict[str: float]:
        cheapest_flight = {}
        try:
            # TODO: uncomment
            response = self.serp_client.search(
                engine='google_flights',
                departure_id=get_airport_iata_code(self.origin),
                arrival_id=get_airport_iata_code(destination),
                outbound_date=self.start_date,
                return_date=self.end_date,
                show_hidden=True
                # stops=1
            )

            # TODO: delete
            # with open('flights_response.json') as response:
            #     response = json.load(response)

            # TODO: uncomment
            if response.data:
                response = response.data['best_flights'][0]
                cheapest_flight.update({destination: response})

            # TODO: delete
            # if response['best_flights']:
            #     response = response['best_flights'][0]
            #     cheapest_flight.update({destination: response})
        except serpapi.exceptions.SerpApiError as e:
            print(f"Error searching flights to {destination}: {e}")

        return cheapest_flight

    def get_hotel(self, destination: str, duration: int, budget: int) -> dict[str: int] | None:
        expensive_hotel = {}
        try:
            # TODO: uncomment
            response = self.serp_client.search(
                engine='google_hotels',
                q=f'{destination} hotels',
                adults=1,
                sort_by=3,  # sorts by low
                max_price=budget,
                check_in_date=self.start_date,
                check_out_date=self.end_date,
            )

            # TODO: delete
            # with open('hotels_response.json') as response:
            #     response = json.load(response)

            # TODO: uncomment
            if response.data:
                response = response.data['properties']
                for prop in reversed(response):
                    if prop['rate_per_night']['extracted_lowest'] * duration <= budget:
                        expensive_hotel.update({destination: prop})
                        return expensive_hotel

            # TODO: delete
            # if response['properties']:
            #     response = response['properties']
            #     for prop in reversed(response):
            #         if prop['prices'][0]['rate_per_night']['extracted_lowest'] * duration <= budget:
            #             expensive_hotel.update({destination: prop})
            #             return expensive_hotel
        except serpapi.exceptions.SerpApiError as e:
            print(f"Error searching hotels in {destination}: {e}")

        print("No hotels in your budget. You can't afford this trip")
        exit()

    def get_travel_options(self):
        """
        make a request to google flights using serapi and search for flights from Tel Aviv to each of the possible
        destinations chatgpt found. choosing the cheapest flight for each destination.
        then making a request to Google hotels using serapi and finding relevant hotels in each of the possible
        destinations. (finding a single hotel for the whole trip). finding the most expensive hotel (price wise) that
        the user can afford according to the budget.

        result - 5 possible destinations (flight+hotel for each destination)

        :return:
        """
        self.get_trip_suggestions()

        flights = {}  # cheapest
        hotels = {}  # most expensive (budget is after selecting the flight)
        for destination in self.possible_destinations:
            cheapest_flight = self.get_flight(destination)
            cheapest_flight_price = cheapest_flight.get(next(iter(cheapest_flight)))['price']
            if cheapest_flight_price >= self.budget:
                print("\nYou can't afford a trip to any of the suggested locations\n")
                exit()
            flights.update(cheapest_flight)

            expensive_hotel = self.get_hotel(destination, self.duration, int(self.budget - cheapest_flight_price))
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

    def generate_daily_plan(self, trip_selection: TripSelection):
        """
        get daily trip plan from OpenAI for the chosen location based on the dates of the trip
        :return:
        """
        self.trip_selection = self.travel_options[trip_selection.trip_selection_idx]
        prompt = (f"Create a daily plan for a {self.trip_type} trip to {self.trip_selection['destination']} from "
                  f"{self.start_date} to {self.end_date}.")
        response = self.get_info_travel_assistant(prompt, 0.7)
        self.trip_plan = response.choices[0].message.content.strip()

    def generate_images_trip_illustration(self):
        """
        generate 4 trip images from OpenAI's DALL-E that show how the trip will look like
        :return:
        """
        prompts = [
            f"A scenic view of {self.trip_selection['destination']} with {self.trip_type} activities. activities are: {self.trip_plan[:200]}",
            f"A person enjoying {self.trip_type} activities in {self.trip_selection['destination']}. activities are: {self.trip_plan[-500:]}",
            f"The greatest spot in {self.trip_selection['destination']}",
            f"{self.trip_selection['destination']} in one image (essence)",
        ]
        for prompt in prompts:
            response = self.openai_client.images.generate(
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            self.trip_images.append(response.data[0].url)

    @app.post("/trip_results/")
    def send_trip_results(self, user_email: TripResultsHandling):
        """
        send trip results: plans, images, etc... to the user's email
        :param user_email:
        :return:
        """
        print(user_email.email)


plan = TripPlan()


@app.post("/travel_options/")
def _get_user_trip_preferences(user_pref: TripPreferences):
    plan.get_user_trip_preferences(user_pref)
    plan.get_travel_options()
    if not plan.travel_options:
        raise HTTPException(status_code=404, detail="Data not found - Trip Options")
    return plan.travel_options


@app.post("/travel_plans/")
def generate_daily_plan(trip_selection: TripSelection):
    plan.generate_daily_plan(trip_selection)
    if not plan.trip_plan:
        raise HTTPException(status_code=404, detail="Data not found - Travel Plans")

    plan.generate_images_trip_illustration()
    if not plan.trip_images:
        raise HTTPException(status_code=404, detail="Data not found - Trip Images")

    return plan.trip_plan, plan.trip_images
