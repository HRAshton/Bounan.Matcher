from dataclasses import dataclass, field


@dataclass
class Interval:
    start: float = field(metadata={'data_key': 'Start'})
    end: float = field(metadata={'data_key': 'End'})
