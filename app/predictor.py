import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

MODEL_PATH = "saved_model/fossil_classifier.h5"
LABELS_PATH = "model/labels.json"

model = tf.keras.models.load_model(MODEL_PATH)

with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = json.load(f)

def predict_species(img_path: str):
    img = image.load_img(img_path, target_size=(128, 128))  # Redimensiona
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0

    prediction = model.predict(img_array)
    predicted_class = np.argmax(prediction[0])
    confidence = round(float(np.max(prediction)) * 100, 2)

    species_name = labels[str(predicted_class)]

    return {
        "especie_provavel": species_name,
        "confianca": f"{confidence}%",
        "descricao": infos_especies(species_name)
    }

def infos_especies(species_name: str):
  
    info = {
        "mamute": "Mamutes eram grandes mamíferos da era do gelo, parentes próximos dos elefantes.",
        "tigre_dentes_de_sabre": "Predador do Pleistoceno, famoso por seus caninos enormes.",
        "preguica_gigante": "Gigantes do Pleistoceno, herbívoros que viviam em áreas abertas.",
    }
    return info.get(species_name, "Informações não disponíveis.")
