import argparse
import logging
import time
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import requests

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


def build_jikan_url(endpoint: str, **params) -> str:
    """Construct a URL for the Jikan API with given endpoint and parameters."""
    return f"{BASE_URL}/{endpoint}?{'&'.join(f'{key}={value}' for key, value in params.items())}"


@dataclass
class Anime:
    anime_id: int
    title: str
    title_english: str = ""
    title_japanese: str = ""
    title_synonyms: str = ""
    url: str = ""
    image_url: str = ""
    trailer_url: str = ""
    type: str = ""
    source: str = ""
    episodes: int = 0
    status: str = ""
    airing: bool = False
    aired_from: str = ""
    aired_to: str = ""
    duration: str = ""
    rating: str = ""
    score: float = 0.0
    scored_by: int = 0
    rank: int = 0
    popularity: int = 0
    members: int = 0
    favorites: int = 0
    synopsis: str = ""
    background: str = ""
    season: str = ""
    year: int = 0
    broadcast_day: str = ""
    broadcast_time: str = ""
    producers: str = ""
    licensors: str = ""
    studios: str = ""
    genres: str = ""
    themes: str = ""

    @classmethod
    def from_api_response(cls, data: Dict):
        return cls(
            anime_id=data.get("mal_id"),
            title=data.get("title"),
            title_english=data.get("title_english"),
            title_japanese=data.get("title_japanese"),
            title_synonyms=", ".join(data.get("title_synonyms", [])),
            url=data.get("url"),
            image_url=data.get("images", {}).get("jpg", {}).get("image_url"),
            trailer_url=data.get("trailer", {}).get("url"),
            type=data.get("type"),
            source=data.get("source"),
            episodes=data.get("episodes"),
            status=data.get("status"),
            airing=data.get("airing"),
            aired_from=data.get("aired", {}).get("from"),
            aired_to=data.get("aired", {}).get("to"),
            duration=data.get("duration"),
            rating=data.get("rating"),
            score=data.get("score"),
            scored_by=data.get("scored_by"),
            rank=data.get("rank"),
            popularity=data.get("popularity"),
            members=data.get("members"),
            favorites=data.get("favorites"),
            synopsis=data.get("synopsis"),
            background=data.get("background"),
            season=data.get("season"),
            year=data.get("year"),
            broadcast_day=data.get("broadcast", {}).get("day"),
            broadcast_time=data.get("broadcast", {}).get("time"),
            producers=", ".join([producer["name"] for producer in data.get("producers", [])]),
            licensors=", ".join([licensor["name"] for licensor in data.get("licensors", [])]),
            studios=", ".join([studio["name"] for studio in data.get("studios", [])]),
            genres=", ".join([genre["name"] for genre in data.get("genres", [])]),
            themes=", ".join([theme["name"] for theme in data.get("themes", [])]),
        )


@dataclass
class Character:
    character_id: int
    anime_id: int
    name: str
    name_kanji: str = ""
    nicknames: str = ""
    url: str = ""
    image_url: str = ""
    favorites: int = 0
    about: str = ""
    role: str = ""
    voice_actor_name: str = ""
    voice_actor_lang: str = ""
    voice_actor_image_url: str = ""

    @classmethod
    def from_api_response(cls, character: Dict, anime_id: int, full_details: Dict):
        return cls(
            character_id=character["character"]["mal_id"],
            anime_id=anime_id,
            name=character["character"]["name"],
            name_kanji=full_details.get("name_kanji"),
            nicknames=", ".join(full_details.get("nicknames", [])),
            url=character["character"].get("url"),
            image_url=character["character"].get("images", {}).get("jpg", {}).get("image_url"),
            favorites=full_details.get("favorites"),
            about=full_details.get("about"),
            role=character.get("role"),
            voice_actor_name=", ".join([va["person"]["name"] for va in character.get("voice_actors", [])]),
            voice_actor_lang=", ".join([va["language"] for va in character.get("voice_actors", [])]),
            voice_actor_image_url=", ".join([va["person"]["images"]["jpg"]["image_url"] for va in character.get("voice_actors", [])])
        )


def get_anime_list(limit: int) -> List[Anime]:
    """Fetches a list of isekai anime from the Jikan API and returns a list of Anime objects."""
    anime_list = []
    page = 1
    while len(anime_list) < limit:
        data = fetch_data(build_jikan_url("anime", genres=GENRE_ISEKAI, page=page, limit=min(limit - len(anime_list), 25)))
        if 'data' in data:
            for anime_data in data['data']:
                anime_list.append(Anime.from_api_response(anime_data))
            logging.info(f"Fetched {len(data['data'])} anime from page {page}")
            page += 1
        else:
            break
    return anime_list


def get_anime_characters(anime_id: int, character_limit: int) -> List[Character]:
    """Fetches characters for a specific anime from the Jikan API and returns a list of Character objects."""
    character_list = []
    data = fetch_data(f"{BASE_URL}/anime/{anime_id}/characters")
    if 'data' in data:
        characters = data['data'][:character_limit]
        logging.info(f"Fetched {len(characters)}/{character_limit} characters for anime ID {anime_id}")
        for character in characters:
            full_details = fetch_data(f"{BASE_URL}/characters/{character['character']['mal_id']}").get('data', {})
            character_list.append(Character.from_api_response(character, anime_id, full_details))
    return character_list


def main():
    parser = argparse.ArgumentParser(description="Fetch and create a dataset of Isekai anime and their characters.")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Limit the number of anime to fetch.")
    parser.add_argument("-c", "--characters", action="store_true", help="Include character details in the dataset.")
    parser.add_argument("-cl", "--character_limit", type=int, default=10, help="Limit the number of characters to fetch per anime.")
    parser.add_argument("-a", "--anime_file", type=str, default="anime.csv", help="Filename for saving anime data.")
    parser.add_argument("-ch", "--character_file", type=str, default="characters.csv", help="Filename for saving character data.")
    args = parser.parse_args()

    anime_list = get_anime_list(args.limit)
    anime_df = pd.DataFrame([anime.__dict__ for anime in anime_list])
    anime_df.to_csv(args.anime_file, index=False, encoding='utf-8')
    logging.info(f"Anime data saved to {args.anime_file}")

    if args.characters:
        character_list = []
        for anime in anime_list:
            character_list.extend(get_anime_characters(anime.anime_id, args.character_limit))
        character_df = pd.DataFrame([character.__dict__ for character in character_list])
        character_df.to_csv(args.character_file, index=False, encoding='utf-8')
        logging.info(f"Character data saved to {args.character_file}")


if __name__ == "__main__":
    main()