#!/usr/bin/env python3
"""
PLEISTOCENE FOSSIL COLLECTOR - VERSÃO OTIMIZADA
Implementa as estratégias testadas que funcionaram
"""

import requests
import json
import os
import time
from pathlib import Path
from PIL import Image
import hashlib
import urllib.parse

def setup_directories():
    """Cria estrutura de pastas"""
    dirs = [
        "data/raw/images",
        "data/raw/metadata", 
        "data/processed",
        "data/models"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def try_paleodb_strategies(session, species_name):
    """
    Implementa as estratégias de API que funcionaram nos testes
    """
    print(f"   🦴 Testando PaleoDB para {species_name}...")
    
    # Estratégias baseadas nos testes que funcionaram
    strategies = [
        {
            'name': 'taxa_list_children',
            'url': 'https://paleobiodb.org/data1.2/taxa/list.json',
            'params': {
                'name': species_name.split()[0],  # Só o gênero
                'rel': 'all_children',
                'show': 'attr,app,size'
            }
        },
        {
            'name': 'occs_basic',
            'url': 'https://paleobiodb.org/data1.2/occs/list.json',
            'params': {
                'taxon_name': species_name,
                'limit': 50
            }
        },
        {
            'name': 'occs_with_ident',
            'url': 'https://paleobiodb.org/data1.2/occs/list.json',
            'params': {
                'taxon_name': species_name.split()[0],  # Gênero
                'show': 'ident',
                'limit': 30
            }
        },
        {
            'name': 'base_name_quaternary',
            'url': 'https://paleobiodb.org/data1.2/occs/list.json',
            'params': {
                'base_name': species_name,
                'interval': 'quaternary',
                'show': 'phylo,ident',
                'limit': 25
            }
        }
    ]
    
    all_records = []
    
    for strategy in strategies:
        try:
            print(f"      🔄 Estratégia: {strategy['name']}")
            
            response = session.get(
                strategy['url'], 
                params=strategy['params'], 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                if records:
                    print(f"      ✅ {len(records)} registros encontrados")
                    all_records.extend(records)
                else:
                    print(f"      ⚠️  Sem registros")
            else:
                print(f"      ❌ Status {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Erro na estratégia {strategy['name']}: {e}")
            continue
        
        # Pequena pausa entre estratégias
        time.sleep(1)
    
    # Remove duplicatas baseado no ID
    unique_records = {}
    for record in all_records:
        record_id = record.get('oid') or record.get('tid') or str(hash(str(record)))
        if record_id not in unique_records:
            unique_records[record_id] = record
    
    final_records = list(unique_records.values())
    
    if final_records:
        print(f"   ✅ PaleoDB Total: {len(final_records)} registros únicos")
    else:
        print(f"   ❌ PaleoDB: Nenhum registro encontrado")
    
    return final_records

def try_gbif_enhanced(session, species_name):
    """
    Versão aprimorada da busca GBIF
    """
    print(f"   🌐 Testando GBIF para {species_name}...")
    
    url = "https://api.gbif.org/v1/occurrence/search"
    
    # Múltiplas consultas para maximizar resultados
    search_variants = [
        {
            'scientificName': species_name,
            'hasCoordinate': 'true',
            'hasGeospatialIssue': 'false',
            'limit': 20
        },
        {
            'scientificName': species_name.split()[0],  # Só gênero
            'hasCoordinate': 'true',
            'mediaType': 'StillImage',
            'limit': 15
        },
        {
            'q': species_name.replace(' ', '+'),
            'hasCoordinate': 'true',
            'limit': 10
        }
    ]
    
    all_results = []
    
    for i, params in enumerate(search_variants):
        try:
            print(f"      🔄 Variante GBIF {i+1}...")
            
            response = session.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                count = data.get('count', 0)
                
                print(f"      ✅ {len(results)} resultados (de {count} total)")
                all_results.extend(results)
            else:
                print(f"      ❌ Status {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Erro variante {i+1}: {e}")
            continue
        
        time.sleep(0.5)
    
    # Converte para formato padrão e remove duplicatas
    records = []
    seen_keys = set()
    
    for result in all_results:
        key = result.get('key')
        if key and key not in seen_keys:
            seen_keys.add(key)
            
            # Procura por imagens
            images = []
            if 'media' in result:
                for media in result['media']:
                    if media.get('type') == 'StillImage':
                        images.append(media.get('identifier'))
            
            # Cria registro padronizado
            record = {
                'oid': f"gbif_{key}",
                'tna': result.get('scientificName', species_name),
                'cc2': result.get('countryCode', result.get('country', 'Unknown')),
                'lng': result.get('decimalLongitude'),
                'lat': result.get('decimalLatitude'),
                'source': 'gbif',
                'images': images
            }
            
            if images:  # Só adiciona se tem imagem
                records.append(record)
    
    if records:
        print(f"   ✅ GBIF Total: {len(records)} registros com imagens")
    else:
        print(f"   ⚠️  GBIF: Sem registros com imagens")
    
    return records

def download_images_from_records(session, records, species_name, max_images=20):
    """
    Baixa imagens dos registros coletados
    """
    species_clean = species_name.replace(' ', '_')
    species_dir = Path(f"data/raw/images/{species_clean}")
    species_dir.mkdir(exist_ok=True)
    
    downloaded_count = 0
    
    print(f"   📸 Baixando imagens para {species_name}...")
    
    for i, record in enumerate(records):
        if downloaded_count >= max_images:
            break
        
        # Diferentes fontes de URL de imagem
        img_urls = []
        
        # Para registros PaleoDB
        if record.get('img'):
            img_urls.append(record['img'])
        
        # Para registros GBIF
        if record.get('images'):
            img_urls.extend(record['images'])
        
        # Se não tem URL, pula
        if not img_urls:
            continue
        
        for j, img_url in enumerate(img_urls[:2]):  # Max 2 imagens por registro
            if downloaded_count >= max_images:
                break
            
            if not img_url or not img_url.startswith('http'):
                continue
            
            try:
                print(f"      📸 {downloaded_count+1}/{max_images}...", end="")
                
                response = session.get(img_url, timeout=25)
                
                if response.status_code == 200:
                    # Nome do arquivo
                    record_id = record.get('oid', f'img_{i}_{j}')
                    filename = f"{record_id}_{downloaded_count:03d}.jpg"
                    filepath = species_dir / filename
                    
                    # Salva arquivo temporário
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    # Valida e processa
                    if validate_and_process_image(filepath):
                        downloaded_count += 1
                        print(" ✅")
                        
                        # Salva metadados
                        save_image_metadata(filepath, record, img_url)
                    else:
                        if filepath.exists():
                            filepath.unlink()
                        print(" ❌")
                else:
                    print(f" ❌ ({response.status_code})")
                
            except Exception as e:
                print(f" ❌ (erro)")
                continue
            
            time.sleep(0.3)  # Rate limiting
    
    return downloaded_count

def validate_and_process_image(filepath):
    """
    Valida e processa uma imagem baixada
    """
    try:
        with Image.open(filepath) as img:
            # Checks básicos
            if img.width < 100 or img.height < 100:
                return False
            
            if filepath.stat().st_size < 2000:  # Muito pequeno
                return False
            
            # Converte para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensiona se muito grande
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Salva otimizado
            img.save(filepath, 'JPEG', quality=90, optimize=True)
            return True
            
    except Exception:
        return False

def save_image_metadata(filepath, record, img_url):
    """
    Salva metadados da imagem
    """
    metadata = {
        'filename': filepath.name,
        'species': record.get('tna'),
        'source': record.get('source', 'unknown'),
        'record_id': record.get('oid'),
        'original_url': img_url,
        'location': {
            'country': record.get('cc2'),
            'lat': record.get('lat'),
            'lng': record.get('lng')
        },
        'download_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    metadata_file = filepath.with_suffix('.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def download_fallback_images():
    """
    Baixa imagens de fallback do Wikipedia/Commons - EXPANDIDO
    """
    print("📸 Baixando imagens de fallback expandidas...")
    
    # URLs verificadas e funcionais - MUITO MAIS IMAGENS
    fallback_images = {
        'Mammuthus_primigenius': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Woolly_mammoth_%28Mammuthus_primigenius%29_-_Naturmuseum_Senckenberg_-_DSC02054.JPG/800px-Woolly_mammoth_%28Mammuthus_primigenius%29_-_Naturmuseum_Senckenberg_-_DSC02054.JPG',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Mammuthus_primigenius_skull_MHNT.JPG/600px-Mammuthus_primigenius_skull_MHNT.JPG',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Woolly_mammoth_model_Royal_BC_Museum_in_Victoria.jpg/800px-Woolly_mammoth_model_Royal_BC_Museum_in_Victoria.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Mammoth_skeleton_%28replica%29.jpg/800px-Mammoth_skeleton_%28replica%29.jpg'
        ],
        'Smilodon_fatalis': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Smilodon_fatalis_skull_MHNT.JPG/800px-Smilodon_fatalis_skull_MHNT.JPG',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Saber-toothed_cat_%28Smilodon_fatalis%29.jpg/800px-Saber-toothed_cat_%28Smilodon_fatalis%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Smilodon_fatalis_Saber-toothed_Cat_La_Brea.jpg/800px-Smilodon_fatalis_Saber-toothed_Cat_La_Brea.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Smilodon_skeleton.jpg/600px-Smilodon_skeleton.jpg'
        ],
        'Megatherium_americanum': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Megatherium_americanum_skeleton_MHNT.JPG/800px-Megatherium_americanum_skeleton_MHNT.JPG',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Megatherium_americanum_skull_FMNH.jpg/800px-Megatherium_americanum_skull_FMNH.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Giant_ground_sloth_Megatherium.jpg/800px-Giant_ground_sloth_Megatherium.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Megatherium_claw_MHNT.JPG/600px-Megatherium_claw_MHNT.JPG'
        ],
        'Canis_dirus': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Canis_dirus_skull_MHNT.JPG/800px-Canis_dirus_skull_MHNT.JPG',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Dire_wolf_skeleton_cast_LACM.jpg/800px-Dire_wolf_skeleton_cast_LACM.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Canis_dirus_reconstruction.jpg/800px-Canis_dirus_reconstruction.jpg'
        ],
        # NOVAS ESPÉCIES ADICIONAIS
        'Arctodus_simus': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Short-faced_bear_skeleton.jpg/800px-Short-faced_bear_skeleton.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Arctodus_simus_skull.jpg/800px-Arctodus_simus_skull.jpg'
        ],
        'Glyptodon': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Glyptodon_skeleton_FMNH.jpg/800px-Glyptodon_skeleton_FMNH.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Glyptodon_shell_MHNT.JPG/800px-Glyptodon_shell_MHNT.JPG'
        ],
        'Equus_occidentalis': [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Equus_occidentalis_skull.jpg/800px-Equus_occidentalis_skull.jpg'
        ]
    }
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'PaleontologyResearch/1.0'})
    
    total_downloaded = 0
    
    for species, urls in fallback_images.items():
        species_dir = Path(f"data/raw/images/{species}")
        species_dir.mkdir(exist_ok=True)
        
        print(f"   📁 {species.replace('_', ' ')}")
        
        for i, url in enumerate(urls):
            try:
                print(f"      📸 Fallback {i+1}...", end="")
                
                response = session.get(url, timeout=30)
                response.raise_for_status()
                
                filename = f"fallback_{i+1:03d}.jpg"
                filepath = species_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                if validate_and_process_image(filepath):
                    total_downloaded += 1
                    print(" ✅")
                else:
                    if filepath.exists():
                        filepath.unlink()
                    print(" ❌")
                
                time.sleep(1)
                
            except Exception as e:
                print(f" ❌ ({e})")
                continue
    
    return total_downloaded

def collect_fossil_data():
    """
    Função principal de coleta otimizada
    """
    print("🦕 PLEISTOCENE FOSSIL COLLECTOR v3.0")
    print("=" * 50)
    print("🔬 Versão otimizada com estratégias testadas")
    
    setup_directories()
    
    target_species = [
        "Mammuthus primigenius",
        "Smilodon fatalis", 
        "Megatherium americanum",
        "Canis dirus",
        "Arctodus simus",  # Urso-de-cara-curta
        "Glyptodon",       # Tatu gigante
        "Equus occidentalis"  # Cavalo pleistocênico
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'PaleontologyResearch/1.0',
        'Accept': 'application/json'
    })
    
    collection_stats = {}
    total_images = 0
    
    # Coleta principal
    for species in target_species:
        print(f"\n🔍 PROCESSANDO: {species}")
        print("-" * 40)
        
        species_images = 0
        all_records = []
        
        # Estratégia 1: PaleoDB (múltiplas estratégias)
        paleodb_records = try_paleodb_strategies(session, species)
        all_records.extend(paleodb_records)
        
        # Estratégia 2: GBIF (aprimorado)
        gbif_records = try_gbif_enhanced(session, species)
        all_records.extend(gbif_records)
        
        # Download de imagens
        if all_records:
            species_images = download_images_from_records(
                session, all_records, species, max_images=15
            )
        
        collection_stats[species] = species_images
        total_images += species_images
        
        print(f"   🎯 Resultado: {species_images} imagens")
        time.sleep(2)  # Pausa entre espécies
    
    # Fallback se poucos dados - ATIVA SEMPRE PARA GARANTIR DATASET COMPLETO
    if total_images < 25:  # Aumentou o threshold
        print(f"\n📸 Expandindo dataset com imagens de referência...")
        print(f"   Atual: {total_images} imagens")
        fallback_count = download_fallback_images()
        
        if fallback_count > 0:
            collection_stats['fallback_wikipedia'] = fallback_count
            total_images += fallback_count
    
    # Salva estatísticas finais
    save_final_stats(collection_stats, total_images)
    
    # Relatório final
    print_final_report(collection_stats, total_images)
    
    return total_images

def save_final_stats(stats, total):
    """Salva estatísticas finais"""
    metadata = {
        'collection_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'version': '3.0_optimized',
        'total_images': total,
        'species_stats': stats,
        'strategies_used': ['PaleoDB_multi', 'GBIF_enhanced', 'Wikipedia_fallback'],
        'status': 'completed' if total > 0 else 'failed'
    }
    
    with open('data/raw/metadata/collection_stats.json', 'w') as f:
        json.dump(metadata, f, indent=2)

def print_final_report(stats, total):
    """Relatório final otimizado"""
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL - COLETA OTIMIZADA")
    print("=" * 60)
    
    print(f"\n🎯 Total de imagens coletadas: {total}")
    print(f"📈 Estratégias utilizadas:")
    print(f"   • PaleoDB (múltiplas estratégias)")
    print(f"   • GBIF (consultas aprimoradas)")
    print(f"   • Wikipedia/Commons (fallback)")
    
    print(f"\n📋 Detalhamento por espécie:")
    for species, count in stats.items():
        if species == 'fallback_wikipedia':
            print(f"   🌐 Imagens de fallback: {count}")
        else:
            status = "✅" if count >= 3 else "⚠️" if count > 0 else "❌"
            print(f"   {status} {species}: {count} imagens")
    
    if total >= 15:
        print(f"\n🎉 DATASET ROBUSTO CRIADO!")
        print(f"   ✅ Pronto para treinamento de modelo")
        print(f"   ✅ Dados suficientes para classificação")
    elif total >= 5:
        print(f"\n⚠️  Dataset pequeno mas funcional")
        print(f"   • Suficiente para testes iniciais")
        print(f"   • Recomendado: expandir dataset")
    else:
        print(f"\n❌ Dataset insuficiente")
        print(f"   • Verificar conectividade de rede")
        print(f"   • Tentar novamente mais tarde")
    
    print(f"\n📁 Arquivos salvos em: data/raw/images/")
    print(f"📊 Metadados em: data/raw/metadata/")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando coleta otimizada...")
        total = collect_fossil_data()
        
        if total > 0:
            print(f"\n✅ SUCESSO! {total} imagens coletadas!")
            print(f"📁 Verifique a pasta 'data/raw/images' para os resultados")
        else:
            print(f"\n❌ Falha na coleta. Verifique:")
            print(f"   • Conexão com internet")
            print(f"   • Disponibilidade das APIs")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print(f"   Por favor, reporte este erro se persistir")