"""Helpers for route data used by flight-search tests."""
import random

from utils.csv_reader import read_csv


def get_random_route() -> dict:
    """Return one random route row from data/flight_routes.csv."""
    routes = read_csv("flight_routes.csv")
    if not routes:
        raise ValueError("flight_routes.csv does not contain any route rows")
    return random.choice(routes)
