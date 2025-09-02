class MetadataManager:
    def add_metadata(self, record):
        """Adiciona metadados ao registro."""
        record["metadata"] = {"verified": True}
        return record
