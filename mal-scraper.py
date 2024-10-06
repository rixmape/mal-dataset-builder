import asyncio
import csv
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientError, ClientResponseError


@dataclass
class Config:
    anime_limit: int = 10
    characters_per_anime: int = 10
    anime_output: str = "anime.csv"
    characters_output: str = "characters.csv"
    log_level: str = "INFO"

class RateLimiter:
    def __init__(self, requests_per_second: int = 2, requests_per_minute: int = 50):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.last_request_time = 0
        self.requests_this_minute = 0
        self.minute_start_time = time.time()

    async def wait(self):
        current_time = time.time()

        # Check rate limit per second
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1 / self.requests_per_second:
            await asyncio.sleep(1 / self.requests_per_second - time_since_last_request)

        # Check rate limit per minute
        if current_time - self.minute_start_time >= 60:
            self.requests_this_minute = 0
            self.minute_start_time = current_time

        if self.requests_this_minute >= self.requests_per_minute:
            await asyncio.sleep(60 - (current_time - self.minute_start_time))
            self.requests_this_minute = 0
            self.minute_start_time = time.time()

        self.requests_this_minute += 1
        self.last_request_time = time.time()

class JikanAPI:
    BASE_URL = "https://api.jikan.moe/v4"

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        retries = 5
        backoff_time = 1  # Start with 1 second backoff

        while retries > 0:
            await self.rate_limiter.wait()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.BASE_URL}{endpoint}", params=params) as response:
                        response.raise_for_status()
                        return await response.json()
            except ClientResponseError as e:
                if e.status == 429:  # Rate limiting error
                    logging.warning(f"Rate limited. Backing off for {backoff_time} seconds.")
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff
                    retries -= 1
                else:
                    raise e
            except (ClientError, asyncio.TimeoutError) as e:
                logging.error(f"Network error: {e}. Retrying...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2
                retries -= 1
        raise Exception("Max retries exceeded after hitting rate limits or network errors")

class IsekaiAnimeScraper:
    def __init__(self, config: Config, api: JikanAPI):
        self.config = config
        self.api = api
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=self.config.log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    async def fetch_isekai_anime(self) -> List[Dict[str, Any]]:
        anime_list = []
        page = 1
        params = {
            "genres": "62",  # 62 is the genre ID for Isekai
            "order_by": "popularity",
            "sort": "asc",
            "sfw": "false",
            "limit": 25  # Max allowed by the API
        }

        while len(anime_list) < self.config.anime_limit:
            params["page"] = page
            try:
                response = await self.api.get("/anime", params)
                new_anime = response.get("data", [])

                if not new_anime:
                    break

                anime_list.extend(new_anime)
                page += 1
            except Exception as e:
                logging.error(f"Failed to fetch Isekai anime on page {page}: {e}")
                break

        return anime_list[:self.config.anime_limit]

    async def fetch_anime_characters(self, anime_id: int) -> List[Dict[str, Any]]:
        try:
            response = await self.api.get(f"/anime/{anime_id}/characters")
            return response.get("data", [])[:self.config.characters_per_anime]
        except Exception as e:
            logging.error(f"Failed to fetch characters for anime ID {anime_id}: {e}")
            return []

    async def fetch_character_details(self, character_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.api.get(f"/characters/{character_id}")
            return response.get("data", {})
        except Exception as e:
            logging.error(f"Failed to fetch details for character ID {character_id}: {e}")
            return None

    async def process_anime_data(self, anime_list: List[Dict[str, Any]]):
        try:
            with open(self.config.anime_output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "mal_id", "title", "title_english", "synopsis", "type", "episodes", "status",
                    "aired_from", "aired_to", "score", "scored_by", "rank", "popularity", "members",
                    "favorites", "studios", "genres", "themes", "duration", "rating", "season", "year"
                ])
                writer.writeheader()
                for anime in anime_list:
                    writer.writerow({
                        "mal_id": anime["mal_id"],
                        "title": anime["title"],
                        "title_english": anime.get("title_english", ""),
                        "synopsis": anime.get("synopsis", ""),
                        "type": anime["type"],
                        "episodes": anime["episodes"],
                        "status": anime["status"],
                        "aired_from": anime["aired"]["from"],
                        "aired_to": anime["aired"]["to"],
                        "score": anime["score"],
                        "scored_by": anime["scored_by"],
                        "rank": anime["rank"],
                        "popularity": anime["popularity"],
                        "members": anime["members"],
                        "favorites": anime["favorites"],
                        "studios": ", ".join(studio["name"] for studio in anime["studios"]),
                        "genres": ", ".join(genre["name"] for genre in anime["genres"]),
                        "themes": ", ".join(theme["name"] for theme in anime["themes"]),
                        "duration": anime["duration"],
                        "rating": anime["rating"],
                        "season": anime.get("season", ""),
                        "year": anime.get("year", "")
                    })
            logging.info(f"Successfully wrote anime data to {self.config.anime_output}")
        except Exception as e:
            logging.error(f"Failed to write anime data to CSV: {e}")

    async def process_character_data(self, all_characters: List[Dict[str, Any]]):
        try:
            with open(self.config.characters_output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "mal_id", "name", "name_kanji", "nicknames", "about", "role",
                    "anime_mal_id", "favorites", "voice_actors"
                ])
                writer.writeheader()
                for character in all_characters:
                    char_details = await self.fetch_character_details(character["character"]["mal_id"])
                    if not char_details:
                        continue
                    writer.writerow({
                        "mal_id": char_details["mal_id"],
                        "name": char_details["name"],
                        "name_kanji": char_details.get("name_kanji", ""),
                        "nicknames": ", ".join(char_details.get("nicknames", [])),
                        "about": char_details.get("about", ""),
                        "role": character["role"],
                        "anime_mal_id": character["anime_mal_id"],
                        "favorites": char_details["favorites"],
                        "voice_actors": ", ".join(f"'{va['person']['name']}:{va['language']}'" for va in character["voice_actors"])
                    })
            logging.info(f"Successfully wrote character data to {self.config.characters_output}")
        except Exception as e:
            logging.error(f"Failed to write character data to CSV: {e}")

    async def run(self):
        logging.info("Starting Isekai anime scraping")
        anime_list = await self.fetch_isekai_anime()
        logging.info(f"Fetched {len(anime_list)} Isekai anime")

        await self.process_anime_data(anime_list)

        all_characters = []
        tasks = []
        for anime in anime_list:
            tasks.append(self.fetch_anime_characters(anime["mal_id"]))
        results = await asyncio.gather(*tasks)

        for anime, characters in zip(anime_list, results):
            for character in characters:
                character["anime_mal_id"] = anime["mal_id"]
            all_characters.extend(characters)

        logging.info(f"Fetched {len(all_characters)} characters")

        await self.process_character_data(all_characters)

        logging.info("Scraping completed successfully")

if __name__ == "__main__":
    config = Config()
    rate_limiter = RateLimiter()
    api = JikanAPI(rate_limiter)
    scraper = IsekaiAnimeScraper(config, api)
    asyncio.run(scraper.run())
