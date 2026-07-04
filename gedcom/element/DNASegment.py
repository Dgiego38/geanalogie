from gedcom.element.element import Element

class DNASegmentElement(Element):
    def __init__(self, level, pointer, tag, value, crlf, multi_line=False):
        super().__init__(level, pointer, tag, value, crlf, multi_line)
        self.chromosome = None  # Numéro du chromosome
        self.start_pos = None  # Position de début du segment
        self.end_pos = None  # Position de fin du segment
        self.cm = None  # Centimorgans du segment
        self.pct = None  # Pourcentage d'ADN partagé dans ce segment
        self.snp = None  # Nombre de SNPs dans ce segment
