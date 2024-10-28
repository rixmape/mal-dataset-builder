# MAL Dataset Builder

## Project Context

The MAL Dataset Builder is a Python-based project aimed at creating a dataset of Isekai anime and their associated character from [MyAnimeList (MAL)](https://myanimelist.net/), utilizing the [Jikan API](https://jikan.moe/). This project provides an accessible way for users to collect structured information about anime and character for data analysis, trend observation, or building recommendation systems. The project fetches, processes, and saves this data into CSV files, making it easy to use in data-driven applications.

## Getting Started

To get started with the MAL Dataset Builder, you need Python 3.9 or later installed on your system. Clone the repository from GitHub:

```bash
https://github.com/rixmape/mal-dataset-builder.git
```

After cloning the repository, navigate to the project directory and install the required dependencies listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Run the script using the following command:

```bash
python mal_scraper.py -l <limit> [-c] [-cl <character_limit>] [-a <anime_file>] [-ch <character_file>]
```

The command-line arguments for running the script allow for some user configuration:

- `-l, --limit`: Limit the number of anime to fetch (default is 10).
- `-c, --character`: Include character details in the dataset (optional).
- `-cl, --character_limit`: Limit the number of character fetched per anime (default is 10).
- `-a, --anime_file`: Specify the filename for saving anime data (default is `anime.csv`).
- `-ch, --character_file`: Specify the filename for saving character data (default is `character.csv`).

## Data Output

The output of this project consists of two CSV files: `anime.csv` and `character.csv`. The tables below describe the fields available in each file.

### Anime Data (`anime.csv`)

| **Field Name**   | **Data Type** | **Description**                                                        |
| ---------------- | ------------- | ---------------------------------------------------------------------- |
| `anime_id`       | Integer       | Unique identifier for the anime.                                       |
| `title`          | String        | Title of the anime.                                                    |
| `title_english`  | String        | English title of the anime (if available).                             |
| `title_japanese` | String        | Japanese title of the anime.                                           |
| `title_synonyms` | String        | Comma-separated list of alternative titles.                            |
| `url`            | String        | URL to the anime’s MyAnimeList page.                                   |
| `image_url`      | String        | URL to the main image of the anime.                                    |
| `trailer_url`    | String        | URL to the anime’s trailer on YouTube (if available).                  |
| `type`           | String        | Type of the anime (e.g., TV, Movie, OVA).                              |
| `source`         | String        | The source material of the anime (e.g., Light Novel, Manga, Original). |
| `episodes`       | Integer       | Total number of episodes for the anime.                                |
| `status`         | String        | Status of the anime (e.g., Airing, Finished Airing).                   |
| `airing`         | Boolean       | Whether the anime is currently airing.                                 |
| `aired_from`     | String        | Start date of the anime's airing (in ISO 8601 format).                 |
| `aired_to`       | String        | End date of the anime's airing (in ISO 8601 format).                   |
| `duration`       | String        | Average duration per episode.                                          |
| `rating`         | String        | Content rating (e.g., PG-13, R).                                       |
| `score`          | Float         | Average user rating score for the anime.                               |
| `scored_by`      | Integer       | Number of users who have rated the anime.                              |
| `rank`           | Integer       | Overall ranking of the anime based on the score.                       |
| `popularity`     | Integer       | Popularity rank of the anime on MyAnimeList.                           |
| `members`        | Integer       | Total number of members who have added the anime to their lists.       |
| `favorites`      | Integer       | Number of users who have marked the anime as their favorite.           |
| `synopsis`       | String        | A brief summary or description of the anime.                           |
| `producers`      | String        | Comma-separated list of producers involved in the anime.               |
| `studios`        | String        | Comma-separated list of studios involved in the production.            |
| `genres`         | String        | Comma-separated list of genres associated with the anime.              |
| `themes`         | String        | Comma-separated list of themes (e.g., Isekai).                         |

### Character Data (`character.csv`)

| **Field Name**          | **Data Type** | **Description**                                                     |
| ----------------------- | ------------- | ------------------------------------------------------------------- |
| `character_id`          | Integer       | Unique identifier for the character.                                |
| `anime_id`              | Integer       | Foreign key reference to the corresponding anime from `anime.csv`.  |
| `name`                  | String        | Full name of the character.                                         |
| `name_kanji`            | String        | The character's name in kanji (if available).                       |
| `nicknames`             | String        | Comma-separated list of the character's nicknames.                  |
| `url`                   | String        | URL to the character’s MyAnimeList page.                            |
| `image_url`             | String        | URL to the character’s image.                                       |
| `favorites`             | Integer       | Number of users who have favorited the character.                   |
| `about`                 | String        | Detailed description or bio of the character.                       |
| `role`                  | String        | The character’s role in the anime (e.g., Main, Supporting).         |
| `voice_actor_name`      | String        | Comma-separated list of voice actor names who voiced the character. |
| `voice_actor_lang`      | String        | Comma-separated list of languages in which the character is voiced. |
| `voice_actor_image_url` | String        | URL to the image of the voice actor.                                |

## Jikan API

The MAL Dataset Builder utilizes the Jikan API, an unofficial API that provides read-only access to data from MyAnimeList. The project uses three main endpoints to gather anime and character information:

- **`/anime` Endpoint**: This endpoint fetches a list of anime based on search criteria such as genre, popularity, and status. It is used to retrieve the details of Isekai anime, including titles, genres, airing dates, scores, and more.

- **`/anime/{id}/characters` Endpoint**: This endpoint is used to fetch a list of characters for a specific anime, including each character's role (main or supporting) and their voice actor details.

- **`/characters/{id}` Endpoint**: This endpoint fetches complete details about a specific character, such as their biography, nicknames, favorite count, and associated images.

These endpoints work together to provide comprehensive data on both anime and their character, which the project processes into structured datasets for easy use and analysis.

For more information, visit the project repository at [GitHub](https://github.com/rixmape/mal-dataset-builder).
