from dataclasses import field, dataclass


@dataclass
class VideoKey:
    my_anime_list_id: int = field(metadata={'data_key': 'MyAnimeListId'})
    dub: str = field(metadata={'data_key': 'Dub'})
    episode: int = field(metadata={'data_key': 'Episode'})
