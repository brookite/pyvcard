import enum


class _STATE(enum.Enum):
    BEGIN = 0
    END = 1


class VERSION(enum.Enum):
    """Enum of vCard versions. Supported 2.1-4.0 versions"""
    @staticmethod
    def get(version):
        """
        Returns version enum
        """
        if version == "2.1":
            return VERSION.V2_1
        elif version == "3.0":
            return VERSION.V3
        elif version == "4.0":
            return VERSION.V4

    V2_1 = "2.1"
    V3 = "3.0"
    V4 = "4.0"


class SOURCES(enum.Enum):
    """
    Enum of sources supported sources
    """
    XML = "xml"
    JSON = "json"
    VCF = "vcf"
    CSV = "csv"
    HTML = "html"
