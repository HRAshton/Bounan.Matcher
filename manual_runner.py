import logging

from dotenv import load_dotenv
from Common.py.models import VideoKey
from Matcher.config.config import Config
from Matcher.config.config import Config
import Matcher.main
from Matcher.matcher_logger import setup_logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    anime_keys: list[str] = [
        # "59360#Beloved",
    ]

    logger.info("Initializing the configuration...")
    load_dotenv()
    Config.initialize_from_ssm()
    setup_logging()

    for anime_key in anime_keys:
        mal_id, group = anime_key.split("#")
        print(f"Processing {mal_id} from {group}")
        videos_to_match = VideoKey(my_anime_list_id=int(mal_id), dub=group, episode=-1)
        Matcher.main._process_videos([videos_to_match], force=True)
