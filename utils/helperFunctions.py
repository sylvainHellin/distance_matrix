from geopy.geocoders import Nominatim
from utils.app_secrets import API_KEY_BINGMAPS as BingMapsKey, API_KEY_OPENROUTE
import requests
import pandas as pd
import gradio as gr
import asyncio
import aiohttp
from geopy.exc import GeocoderTimedOut
import time

def timed_function(func):
	def wrapper(*args, **kwargs):
		start_time = time.time()
		result = func(*args, **kwargs)
		end_time = time.time()
		print(f"{func.__name__} executed in {end_time - start_time} seconds")
		return result
	return wrapper

def extract_companies_and_destinations(path="input/input_clean.xlsx"):
    """
    This function extracts the companies and destinations from an Excel file.

    Parameters:
    path (str): The path to the Excel file. Defaults to "input/input_clean.xlsx".

    Returns:
    tuple: A tuple containing two lists. The first list contains the names of the companies. The second list contains the destinations.
    """
    df = pd.read_excel(path)
    df.drop(["Adresse", "PLZ", "Ort"], axis=1, inplace=True)
    destinations = df["Adresse_lang"].apply(lambda x: x.replace("\xa0", " ")).tolist()
    companies = df["Unternehmen"].tolist()
    return companies, destinations

async def get_coordinates_from_address(address: str) -> tuple:
	"""
	This function takes an address as input and returns the corresponding longitude and latitude.
	
	Parameters:
	address (str): The address to geocode.

	Returns:
	tuple: A tuple containing the longitude and latitude of the address.
	"""

	url = f"http://dev.virtualearth.net/REST/v1/Locations/DE/{address}?&key={BingMapsKey}"
	async with aiohttp.ClientSession() as session:
		async with session.get(url=url) as response:
			result = await response.json()
	coordinates = result["resourceSets"][0]["resources"][0]["geocodePoints"][0]["coordinates"]

	return coordinates[1], coordinates[0]

@timed_function
async def get_locations_from_addresses(addresses: list) -> list:
	"""
	This function takes a list of addresses and returns a list of their corresponding latitude and longitude.
	
	Parameters:
	addresses (list): A list of addresses to geocode.

	Returns:
	list: A list of tuples containing the latitude and longitude of each address.
	"""
	locations = [await get_coordinates_from_address(address) for address in addresses]
	locations = [[loc[0], loc[1]] for loc in locations]
	return locations

@timed_function
def compute_bike_travel_times_and_distances(locations):
	"""
	This function receives a list of geographical coordinates and calculates the time and distance it would take to cycle from the first location to all other locations in the list.
	The OpenRouteService API is used to perform these calculations.

	Parameters:
	locations (list): A list of geographical coordinates where each coordinate is represented as a list of two elements [longitude, latitude].

	Returns:
	distance_in_meters (list): A list of travel distances in meters.
	durations_in_minutes (list): A list of travel durations in minutes.
	"""

	profile = "cycling-regular"

	body = {
		"locations": locations,
		"sources": [0],
		"metrics":["distance","duration"]
	}

	headers = {
		'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
		'Authorization': API_KEY_OPENROUTE,
		'Content-Type': 'application/json; charset=utf-8'
	}

	url = f'https://api.openrouteservice.org/v2/matrix/{profile}'
	response = requests.post(url, json=body, headers=headers).json()

	distance_in_meters = response["distances"][0][1:] # a list of travel distance in meter
	distance_in_kilometers = [round(distance / 1000, 2) for distance in distance_in_meters]
	durations_in_seconds = response["durations"][0][1:] # a list of travel duration in seconds
	durations_in_minutes = [round(duration / 60, 2) for duration in durations_in_seconds] # a list of travel duration in minutes
	return durations_in_minutes, distance_in_kilometers



@timed_function
def compute_car_travel_times_and_distances(locations):
	"""
	This function receives a list of geographical coordinates and calculates the time and distance it would take to drive from the first location to all other locations in the list.
	The OpenRouteService API is used to perform these calculations.

	Parameters:
	locations (list): A list of geographical coordinates where each coordinate is represented as a list of two elements [longitude, latitude].

	Returns:
	distance_in_meters (list): A list of travel distances in meters.
	durations_in_minutes (list): A list of travel durations in minutes.
	"""

	profile = "driving-car"

	body = {
		"locations": locations,
		"sources": [0],
		"metrics":["distance","duration"]
	}

	headers = {
		'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
		'Authorization': API_KEY_OPENROUTE,
		'Content-Type': 'application/json; charset=utf-8'
	}

	url = f'https://api.openrouteservice.org/v2/matrix/{profile}'
	response = requests.post(url, json=body, headers=headers).json()

	distance_in_meters = response["distances"][0][1:] # a list of travel distance in meter
	distance_in_kilometers = [round(distance / 1000, 2) for distance in distance_in_meters]
	durations_in_seconds = response["durations"][0][1:] # a list of travel duration in seconds
	durations_in_minutes = [round(duration / 60, 2) for duration in durations_in_seconds] # a list of travel duration in minutes
	return durations_in_minutes, distance_in_kilometers


async def get_transit_duration_and_distance(wayPoint1, wayPoint2, travelMode="Transit", optimize="time", timeType="Arrival", dateTime="09:00:00", distanceUnit="Kilometer", BingMapsKey=BingMapsKey):
	"""
	This function calculates the travel duration and distance between two waypoints using Bing Maps API.

	Parameters:
	wayPoint1 (str): The address of the starting point.
	wayPoint2 (str): The address of the destination point.
	travelMode (str, optional): The mode of travel. Defaults to "Transit".
	optimize (str, optional): The optimization parameter. Defaults to "time".
	timeType (str, optional): The type of time to consider. Defaults to "Arrival".
	dateTime (str, optional): The time of arrival in the format "HH:MM:SS". Defaults to "09:00:00".
	distanceUnit (str, optional): The unit of distance. Defaults to "Kilometer".
	BingMapsKey (str, optional): The API key for Bing Maps. Defaults to BingMapsKey.

	Returns:
	tuple: The travel duration in minutes and the travel distance in kilometers.
	"""

	url = f"http://dev.virtualearth.net/REST/v1/Routes/{travelMode}?wayPoint.1={wayPoint1}&Waypoint.2={wayPoint2}&optimize={optimize}&timeType={timeType}&dateTime={dateTime}&distanceUnit={distanceUnit}&key={BingMapsKey}"
	
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			response = await resp.json()
	
	duration_in_seconds = response["resourceSets"][0]["resources"][0]["travelDuration"]
	distance_in_kilometers = response["resourceSets"][0]["resources"][0]["travelDistance"]
	duration_in_minutes = round(duration_in_seconds / 60, 2)
	distance_in_kilometers = round(distance_in_kilometers, 2)
	return duration_in_minutes, distance_in_kilometers

@timed_function
async def compute_transit_travel_times_and_distances(locations):
	"""
	This function calculates the travel duration and distance between a starting point and multiple destination points using the Bing Maps API.

	Parameters:
	locations (list): A list of addresses. The first address is the starting point and the rest are destination points.

	Returns:
	tuple: A tuple containing two lists. The first list contains travel durations in minutes from the starting point to each destination point. The second list contains the travel distances in kilometers from the starting point to each destination point.
	"""
	
	# The starting point is the first location in the list
	wayPoint1 = locations[0]
	
	# Initialize two empty lists to store the travel durations and distances
	durations_in_minutes = []
	distances_in_kilometers = []
	
	# Create a list of tasks for each destination point
	tasks = [get_transit_duration_and_distance(wayPoint1, wayPoint2) for wayPoint2 in locations[1:]]
	
	# Run the tasks concurrently and gather the results
	results = await asyncio.gather(*tasks)
	
	# Append the travel duration and distance to the respective lists
	for duration, distance in results:
		durations_in_minutes.append(duration)
		distances_in_kilometers.append(distance)
	
	# Return the lists of travel durations and distances
	return durations_in_minutes, distances_in_kilometers



async def compute_travel_times_and_distances(origin, destinations):
	
	# append the origin to the list of destination
	addresses = [origin] + destinations

	# compute the coordinates of the addresses
	locations = await get_locations_from_addresses(addresses)

	# compute the time and distance to travel via various transportation modes
	durations_cycling, distances_cycling = compute_bike_travel_times_and_distances(locations)
	durations_car, distances_car = compute_car_travel_times_and_distances(locations)
	durations_transit, distances_transit = await compute_transit_travel_times_and_distances(addresses)

	return durations_cycling, distances_cycling, durations_transit, distances_transit, durations_car, distances_car

async def compile_travel_times_and_distances(travel_time_and_distances, companies, destinations):

	durations_cycling, distances_cycling, durations_transit, distances_transit, durations_car, distances_car = await travel_time_and_distances
	# Load the results in a DataFrame

	data = {
		'Unternehmen': companies,
		'Adresse': destinations,
		'Duration Cycling (min)': durations_cycling,
		'Duration Transit (min)': durations_transit,
		'Duration Car (min)': durations_car,
		'Distance Cycling (km)': distances_cycling,
		# 'Distance Transit (km)': distances_transit,
		'Distance Car (km)': distances_car,
	}

	df = pd.DataFrame(data)

	return df


def export_to_excel(origin, df):
	path = f"distance matrix {origin}.xlsx"
	df.to_excel(path,index = False)
	return path

async def compute_and_display_travel_times_and_distances(origin="Färbergraben 16, München", path = "input/input_clean.xlsx"):
	companies, destinations = extract_companies_and_destinations(path=path)
	travel_time_and_distances = compute_travel_times_and_distances(origin=origin, destinations=destinations)
	df = await compile_travel_times_and_distances(travel_time_and_distances=travel_time_and_distances, companies=companies, destinations=destinations)
	styler = df.style.highlight_min(color='lightgreen', axis=0)

	return styler

placeholder_df = pd.DataFrame(columns = ['Unternehmen', 'Adresse', 'Duration Cycling (min)','Duration Transit (min)','Duration Car (min)','Distance Cycling (km)','Distance Car (km)'])

def generate_template_df(path="input/input_clean.xlsx"):
	return pd.read_excel(path)
	