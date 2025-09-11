import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import os
from pathlib import Path

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
    "smilodon": "Smilodon, conhecido como tigre dentes-de-sabre, foi um predador feroz do Pleistoceno com caninos de até 28cm.",
    "smilodon_fatalis": "Smilodon fatalis era um felino pré-histórico famoso por seus enormes dentes caninos e força muscular.",
}

def infos_especies(species_name: str):
    """Retorna informações sobre uma espécie específica"""
    return INFO_ESPECIES.get(species_name, "Informações não disponíveis.")

def predict_species(img_path: str):
    """Prediz a espécie com base na imagem fornecida"""
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(img_path):
            return {"erro": f"Arquivo não encontrado: {img_path}"}
        
        # Preprocessar imagem
        img = image.load_img(img_path, target_size=(128, 128))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Fazer predição
        prediction = model.predict(img_array)
        predicted_class = np.argmax(prediction[0])
        confidence = round(float(np.max(prediction)) * 100, 2)
        
        # DEBUG: Mostrar todas as probabilidades
        print("\n🔬 DEBUG - Probabilidades por classe:")
        for i, prob in enumerate(prediction[0]):
            classe_nome = "desconhecida"
            if isinstance(labels, list) and i < len(labels):
                classe_nome = labels[i]
            elif isinstance(labels, dict):
                if str(i) in labels:
                    classe_nome = labels[str(i)]
                elif i in labels:
                    classe_nome = labels[i]
            print(f"  Classe {i} ({classe_nome}): {prob*100:.2f}%")

        # Converter índice para nome da espécie
        if isinstance(labels, list):
            species_name = labels[predicted_class]
        elif isinstance(labels, dict):
            if str(predicted_class) in labels:
                species_name = labels[str(predicted_class)]
            elif predicted_class in labels:
                species_name = labels[predicted_class]
            else:
                species_name = list(labels.keys())[predicted_class]
        else:
            species_name = f"classe_{predicted_class}"

        # Verificar se a confiança é baixa
        confianca_baixa = confidence < 70
        aviso = ""
        if confianca_baixa:
            aviso = " ⚠️ CONFIANÇA BAIXA - Resultado pode estar incorreto!"

        # Obter informações da espécie
        descricao = infos_especies(species_name)

        return {
            "especie_provavel": species_name,
            "confianca": f"{confidence}%{aviso}",
            "descricao": descricao,
            "arquivo_analisado": os.path.basename(img_path),
            "todas_probabilidades": {
                f"classe_{i}": f"{prob*100:.2f}%" 
                for i, prob in enumerate(prediction[0])
            }
        }
    
    except Exception as e:
        return {"erro": f"Erro ao processar imagem: {str(e)}"}

def analisar_imagem_interativo():
    """Interface interativa para análise de imagens"""
    print("🧬 === ANALISADOR DE DNA FÓSSIL === 🦴")
    print("Digite o caminho da imagem ou arraste o arquivo aqui:")
    print("(Digite 'sair' para encerrar)")
    print("-" * 50)
    
    while True:
        # Solicitar caminho da imagem
        caminho = input("\n📁 Caminho da imagem: ").strip()
        
        if caminho.lower() in ['sair', 'exit', 'quit']:
            print("👋 Encerrando o analisador...")
            break
        
        if not caminho:
            print("❌ Por favor, digite um caminho válido!")
            continue
        
        # Remover aspas se houver (caso o usuário copie com aspas)
        caminho = caminho.strip('"').strip("'")
        
        print("\n🔬 Analisando imagem...")
        resultado = predict_species(caminho)
        
        print("\n" + "="*40)
        if "erro" in resultado:
            print(f"❌ {resultado['erro']}")
        else:
            print("✅ RESULTADO DA ANÁLISE")
            print(f"📷 Arquivo: {resultado['arquivo_analisado']}")
            print(f"🦴 Espécie: {resultado['especie_provavel']}")
            print(f"📊 Confiança: {resultado['confianca']}")
            print(f"📝 Descrição: {resultado['descricao']}")
        print("="*40)

def listar_imagens_disponiveis():
    """Lista imagens disponíveis nas pastas comuns"""
    pastas_comuns = ["data/test", "images", "fotos", ".", "test"]
    extensoes = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    imagens_encontradas = []
    
    for pasta in pastas_comuns:
        if os.path.exists(pasta):
            for arquivo in os.listdir(pasta):
                if any(arquivo.lower().endswith(ext) for ext in extensoes):
                    caminho_completo = os.path.join(pasta, arquivo)
                    imagens_encontradas.append(caminho_completo)
    
    return imagens_encontradas

def menu_principal():
    """Menu principal do analisador"""
    while True:
        print("\n🧬 === ANALISADOR DE DNA FÓSSIL ===")
        print("1. 📁 Analisar imagem específica")
        print("2. 📋 Ver imagens disponíveis")
        print("3. 🔄 Análise rápida (última imagem)")
        print("4. ❌ Sair")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == "1":
            analisar_imagem_interativo()
        
        elif opcao == "2":
            imagens = listar_imagens_disponiveis()
            if imagens:
                print(f"\n📋 Encontradas {len(imagens)} imagens:")
                for i, img in enumerate(imagens, 1):
                    print(f"  {i}. {img}")
                
                try:
                    escolha = int(input(f"\nEscolha uma imagem (1-{len(imagens)}) ou 0 para voltar: "))
                    if 1 <= escolha <= len(imagens):
                        resultado = predict_species(imagens[escolha-1])
                        print("\n" + "="*40)
                        if "erro" in resultado:
                            print(f"❌ {resultado['erro']}")
                        else:
                            print("✅ RESULTADO DA ANÁLISE")
                            print(f"📷 Arquivo: {resultado['arquivo_analisado']}")
                            print(f"🦴 Espécie: {resultado['especie_provavel']}")
                            print(f"📊 Confiança: {resultado['confianca']}")
                            print(f"📝 Descrição: {resultado['descricao']}")
                        print("="*40)
                except ValueError:
                    print("❌ Opção inválida!")
            else:
                print("❌ Nenhuma imagem encontrada nas pastas comuns!")
        
        elif opcao == "3":
            # Análise da primeira imagem encontrada
            imagens = listar_imagens_disponiveis()
            if imagens:
                print(f"🔬 Analisando: {imagens[0]}")
                resultado = predict_species(imagens[0])
                print("\n" + "="*40)
                if "erro" in resultado:
                    print(f"❌ {resultado['erro']}")
                else:
                    print("✅ RESULTADO DA ANÁLISE")
                    print(f"📷 Arquivo: {resultado['arquivo_analisado']}")
                    print(f"🦴 Espécie: {resultado['especie_provavel']}")
                    print(f"📊 Confiança: {resultado['confianca']}")
                    print(f"📝 Descrição: {resultado['descricao']}")
                print("="*40)
            else:
                print("❌ Nenhuma imagem encontrada!")
        
        elif opcao == "4":
            print("👋 Encerrando o analisador...")
            break
        
        else:
            print("❌ Opção inválida! Escolha entre 1-4.")

# Execução principal
if __name__ == "__main__":
    # Você pode escolher qual modo usar:
    
    # Modo 1: Menu interativo completo
    menu_principal()
    
    # Modo 2: Interface simples (descomente a linha abaixo e comente a anterior)
    # analisar_imagem_interativo()
    
    # Modo 3: Análise direta (como era antes, mas melhorada)
    # resultado = predict_species("data/test/mamute1.jpg")
    # print(resultado)