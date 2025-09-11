# systeam-DNA/model/train.py

import os
import json
import tensorflow as tf
from cnn_model import create_model

# Diretórios
DATA_DIR = "data/images"
MODEL_DIR = "saved_model"
LABELS_FILE = "model/labels.json"

# Configurações
IMG_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 10

def main():
    # 1. Carregar dataset
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,   # 20% para validação
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    # ⚠️ Capturar as classes ANTES de transformar
    class_names = train_ds.class_names
    print("📂 Classes detectadas:", class_names)

    # Salvar mapeamento {id: nome}
    os.makedirs(os.path.dirname(LABELS_FILE), exist_ok=True)
    with open(LABELS_FILE, "w") as f:
        json.dump({i: name for i, name in enumerate(class_names)}, f)

    # 2. Normalizar pixels (0-255 → 0-1)
    train_ds = train_ds.map(lambda x, y: (x / 255.0, y))
    val_ds = val_ds.map(lambda x, y: (x / 255.0, y))

    # Melhorar performance com cache e prefetch
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # 3. Criar modelo
    model = create_model(num_classes=len(class_names))

    # 4. Treinar
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    # 5. Salvar modelo treinado
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(os.path.join(MODEL_DIR, "fossil_classifier.h5"))
    print("✅ Treinamento concluído! Modelo salvo em", MODEL_DIR)

if __name__ == "__main__":
    main()
