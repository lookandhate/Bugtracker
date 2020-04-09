import string
import random

letters = string.ascii_uppercase


def generate_api_key(length: int = 24) -> str:
    # Default len of api key is 24 symbols
    new_api_key = ''
    for _ in range(length):
        new_api_key += random.choice(letters)

    return new_api_key
