from dataclasses import dataclass, field

from Matcher.models.Interval import Interval


@dataclass
class Scenes:
    opening: Interval | None = field(metadata={'data_key': 'Opening'})
    ending: Interval | None = field(metadata={'data_key': 'Ending'})
    scene_after_ending: Interval | None = field(metadata={'data_key': 'SceneAfterEnding'})
