import argparse
import logging
import time
from typing import Dict, List

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://api.jikan.moe/v4"
GENRE_ISEKAI = 62
RATE_LIMIT_DELAY = 2  # Delay in seconds to manage API rate limits


def fetch_data(url: str, params: Dict = None) -> Dict:
    """Fetch data from the given URL with specified parameters."""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        time.sleep(RATE_LIMIT_DELAY)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {}


def get_anime_list(limit: int) -> List[Dict]:
    """Fetches a list of isekai anime from the Jikan API."""
    anime_list = []
    page = 1
    while len(anime_list) < limit:
        data = fetch_data(
            f"{BASE_URL}/anime",
            params={
                "genres": GENRE_ISEKAI,
                "page": page,
                "limit": min(limit - len(anime_list), 25),
            },
        )
        if 'data' in data:
            anime_list.extend(data['data'])
            logging.info(f"Fetched {len(data['data'])} anime from page {page}")
            page += 1
        else:
            break
    return anime_list


def get_anime_characters(anime_id: int, character_limit: int) -> List[Dict]:
    """Fetches characters for a specific anime from the Jikan API."""
    data = fetch_data(f"{BASE_URL}/anime/{anime_id}/characters")
    if 'data' in data:
        characters = data['data'][:character_limit]
        logging.info(f"Fetched {len(characters)}/{character_limit} characters for anime ID {anime_id}")
        return characters
    return []


def parse_anime_details(anime: Dict) -> Dict:
    """Parses anime details into a dictionary."""
    return {
        "anime_id": anime.get("mal_id"),
        "title": anime.get("title"),
        "title_english": anime.get("title_english"),
        "title_japanese": anime.get("title_japanese"),
        "title_synonyms": ", ".join(anime.get("title_synonyms", [])),
        "url": anime.get("url"),
        "image_url": anime.get("images", {}).get("jpg", {}).get("image_url"),
        "trailer_url": anime.get("trailer", {}).get("url"),
        "type": anime.get("type"),
        "source": anime.get("source"),
        "episodes": anime.get("episodes"),
        "status": anime.get("status"),
        "airing": anime.get("airing"),
        "aired_from": anime.get("aired", {}).get("from"),
        "aired_to": anime.get("aired", {}).get("to"),
        "duration": anime.get("duration"),
        "rating": anime.get("rating"),
        "score": anime.get("score"),
        "scored_by": anime.get("scored_by"),
        "rank": anime.get("rank"),
        "popularity": anime.get("popularity"),
        "members": anime.get("members"),
        "favorites": anime.get("favorites"),
        "synopsis": anime.get("synopsis"),
        "background": anime.get("background"),
        "season": anime.get("season"),
        "year": anime.get("year"),
        "broadcast_day": anime.get("broadcast", {}).get("day"),
        "broadcast_time": anime.get("broadcast", {}).get("time"),
        "producers": ", ".join([producer["name"] for producer in anime.get("producers", [])]),
        "licensors": ", ".join([licensor["name"] for licensor in anime.get("licensors", [])]),
        "studios": ", ".join([studio["name"] for studio in anime.get("studios", [])]),
        "genres": ", ".join([genre["name"] for genre in anime.get("genres", [])]),
        "themes": ", ".join([theme["name"] for theme in anime.get("themes", [])]),
    }


def parse_character_details(character: Dict, anime_id: int) -> Dict:
    """Parses character details into a dictionary."""
    return {
        "character_id": character["character"]["mal_id"],
        "anime_id": anime_id,
        "name": character["character"]["name"],
        "name_kanji": character["character"].get("name_kanji"),
        "nicknames": ", ".join(character["character"].get("nicknames", [])),
        "url": character["character"].get("url"),
        "image_url": character["character"].get("images", {}).get("jpg", {}).get("image_url"),
        "favorites": character["character"].get("favorites"),
        "about": character["character"].get("about"),
        "role": character.get("role"),
        "voice_actor_name": ", ".join([va["person"]["name"] for va in character.get("voice_actors", [])]),
        "voice_actor_lang": ", ".join([va["language"] for va in character.get("voice_actors", [])]),
        "voice_actor_image_url": ", ".join([va["person"]["images"]["jpg"]["image_url"] for va in character.get("voice_actors", [])])
    }


def save_to_csv(data: List[Dict], filename: str):
    """Saves data to a CSV file using pandas."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    logging.info(f"Data saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Fetch and create a dataset of Isekai anime and their characters.")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Limit the number of anime to fetch.")
    parser.add_argument("-c", "--characters", action="store_true", help="Include character details in the dataset.")
    parser.add_argument("-cl", "--character_limit", type=int, default=10, help="Limit the number of characters to fetch per anime.")
    parser.add_argument("-a", "--anime_file", type=str, default="anime.csv", help="Filename for saving anime data.")
    parser.add_argument("-ch", "--character_file", type=str, default="characters.csv", help="Filename for saving character data.")
    args = parser.parse_args()

    anime_list = get_anime_list(args.limit)
    parsed_anime_list = [parse_anime_details(anime) for anime in anime_list]
    save_to_csv(parsed_anime_list, args.anime_file)

    if args.characters:
        all_characters = []
        for anime in anime_list:
            anime_id = anime.get("mal_id")
            if anime_id:
                characters = get_anime_characters(anime_id, args.character_limit)
                parsed_characters = [parse_character_details(character, anime_id) for character in characters]
                all_characters.extend(parsed_characters)
        save_to_csv(all_characters, args.character_file)


if __name__ == "__main__":
    main()
