from gedcom.element.element import Element

class DNAElement(Element):
    """Représente les informations ADN d'un individu."""
    def __init__(self, level, pointer, tag, value, crlf, multi_line=False):
        # Appeler le constructeur de la classe parente
        super().__init__(level, pointer, tag, value, crlf, multi_line)

        # Ajouter des attributs spécifiques à DNAElement
        self.matches = []  # Liste des matchs ADN