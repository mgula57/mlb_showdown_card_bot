from enum import Enum

class Datasource(str, Enum):
    MLB_API = "mlb_api"
    BREF = "bref"
    FANGRAPHS = "fangraphs"

    MANUAL = "manual"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            match value.lower():
                case 'mlb_api' | 'mlb' | 'mlbstatsapi':
                    return cls.MLB_API
                case 'bref' | 'baseball_reference' | 'baseballreference':
                    return cls.BREF
                case 'fangraphs' | 'fg':
                    return cls.FANGRAPHS
        return cls.BREF # Default to BREF if unrecognized
