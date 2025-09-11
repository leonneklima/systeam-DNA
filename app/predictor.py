import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

MODEL_PATH = "saved_model/fossil_classifier.h5"
LABELS_PATH = "model/labels.json"

# Carregar modelo
model = tf.keras.models.load_model(MODEL_PATH)

# Carregar labels
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    labels = json.load(f)

# Base de informações das espécies
INFO_ESPECIES = {
    "mammuthus_primigenius": "Mamutes eram grandes mamíferos da era do gelo, parentes próximos dos elefantes.",
    "tigre_dentes_de_sabre": "Predador do Pleistoceno, famoso por seus caninos enormes.",
    "preguica_gigante": "Gigantes do Pleistoceno, herbívoros que viviam em áreas abertas.",
}

def infos_especies(species_name: str):
    """Retorna informações sobre uma espécie específica"""
    return INFO_ESPECIES.get(species_name, "Informações não disponíveis.")

def predict_species(img_path: str):
    """Prediz a espécie com base na imagem fornecida"""
    # Preprocessar imagem
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    # Fazer predição
    prediction = model.predict(img_array)
    predicted_class = np.argmax(prediction[0])
    confidence = round(float(np.max(prediction)) * 100, 2)

    # Converter índice para nome da espécie
    print(f"DEBUG - Índice predito: {predicted_class}")
    print(f"DEBUG - Estrutura labels: {labels}")
    print(f"DEBUG - Tipo labels: {type(labels)}")
    
    if isinstance(labels, list):
        species_name = labels[predicted_class]
    elif isinstance(labels, dict):
        # Se labels for um dict com índices como chaves
        if str(predicted_class) in labels:
            species_name = labels[str(predicted_class)]
        elif predicted_class in labels:
            species_name = labels[predicted_class]
        else:
            # Se for dict com nomes como chaves, pegar por índice
            species_name = list(labels.keys())[predicted_class]
    else:
        species_name = f"classe_{predicted_class}"
    
    print(f"DEBUG - Nome da espécie identificada: {species_name}")

    # Obter informações da espécie
    descricao = infos_especies(species_name)

    return {
        "especie_provavel": species_name,
        "confianca": f"{confidence}%",
        "descricao": descricao
    }

# Exemplo de uso direto
if __name__ == "__main__":
    resultado = predict_species("data/test/mamute1.jpg")
    print("=== RESULTADO DA ANÁLISE ===")
    print(f"Espécie: {resultado['especie_provavel']}")
    print(f"Confiança: {resultado['confianca']}")
    print(f"Descrição: {resultado['descricao']}")
    print("="*30)