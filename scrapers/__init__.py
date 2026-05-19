from .uw_madison import UWMadisonScraper
from .wisc_state import WiscStateScraper
from .madison_city import MadisonCityScraper

ALL_SCRAPERS = [
    UWMadisonScraper(),
    WiscStateScraper(),
    MadisonCityScraper(),
]
