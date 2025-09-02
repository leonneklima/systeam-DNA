class ImageProcessor:
    def process(self, record):
        """Simula processamento de imagem relacionado ao fóssil."""
        record["image_processed"] = True
        return record
