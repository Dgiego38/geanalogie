from gedcom.element.element import Element

class DNAMatchElement(Element):
    def __init__(self, level, pointer, tag, value, crlf, multi_line=False):
        super().__init__(level, pointer, tag, value, crlf, multi_line)
        self.match_id = value  # ID de l'individu qui match
        self.segments = []  # Liste des segments d'ADN partagés
        self.shared_cm = None  # Centimorgans partagés
        self.shared_pct = None  # Pourcentage d'ADN partagé