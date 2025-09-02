class GBIFCollector:
    def __init__(self, session):
        self.session = session

    def fetch(self, species):
        """Simula coleta de dados no GBIF."""
        return [{"species": species, "source": "GBIF", "data": f"Registro de {species}"}]
