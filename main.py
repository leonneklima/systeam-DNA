from collectors.paleodb import PaleoDBCollector
from collectors.gbif import GBIFCollector
from collectors.fallback import FallbackCollector
from processing.images import ImageProcessor
from processing.metadata import MetadataManager
from utils.session import create_session

def main():
    session = create_session()
    species_list = ["Mammuthus primigenius", "Smilodon fatalis"]

    paleo = PaleoDBCollector(session)
    gbif = GBIFCollector(session)
    fallback = FallbackCollector(session)

    image_processor = ImageProcessor()
    metadata_manager = MetadataManager()

    all_records = []

    for species in species_list:
        try:
            records = paleo.fetch(species)
            if not records:
                records = gbif.fetch(species)
        except Exception:
            records = fallback.fetch(species)

        # processa resultados
        for record in records:
            record = image_processor.process(record)
            record = metadata_manager.add_metadata(record)
            all_records.append(record)

    # mostra saída
    for r in all_records:
        print(r)

if __name__ == "__main__":
    main()
