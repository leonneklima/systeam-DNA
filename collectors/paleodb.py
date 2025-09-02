class PaleoDBCollector:
    def __init__(self, session):
        self.session = session

    def fetch(self, species):
        """Simula coleta de dados no PaleoDB."""
        return [{"species": species, "source": "PaleoDB", "data": f"Registro de {species}"}]
