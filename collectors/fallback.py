class FallbackCollector:
    def __init__(self, session):
        self.session = session

    def fetch(self, species):
        """Coleta alternativa caso outras falhem."""
        return [{"species": species, "source": "Fallback", "data": f"Registro genérico de {species}"}]
