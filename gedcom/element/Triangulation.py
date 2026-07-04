from gedcom.element.element import Element

class TriangulationElement(Element):
    """Représente une triangulation entre plusieurs individus."""
    def __init__(self, level, pointer, tag, value, crlf, multi_line=False):
        super().__init__(level, pointer, tag, value, crlf, multi_line)

        