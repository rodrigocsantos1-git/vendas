import pdfplumber
import re
import json
import sqlite3

# Let's map each of the 29 unique items with precision
catalog_data = {
    # 1. Sabonetes Tododia 5x90g
    "2832": {
        "nome_revista": "Tododia Sabonete em Barra Noz Pecã e Cacau 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73, # na compra de 4 un (pág 144)
        "pagina_revista": 143,
        "detalhes": "Página 143: Código (2832), 03 pts, R$ 34,90"
    },
    "72147": {
        "nome_revista": "Tododia Sabonete em Barra Alecrim e Sálvia 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73,
        "pagina_revista": 144,
        "detalhes": "Página 144: Código (72147), 03 pts, R$ 34,90 (Promoção 4 un por R$ 28,73 cada)"
    },
    "214468": {
        "nome_revista": "Tododia Sabonete em Barra Jambo Rosa e Flor de Caju 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": None,
        "pagina_revista": 140,
        "detalhes": "Página 140: Código (214468), 03 pts, R$ 34,90"
    },
    "2829": {
        "nome_revista": "Tododia Sabonete em Barra Macadâmia 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73,
        "pagina_revista": 143,
        "detalhes": "Página 143: Código (2829), 03 pts, R$ 34,90"
    },
    "87512": {
        "nome_revista": "Tododia Sabonete em Barra Amora Vermelha e Jabuticaba 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73,
        "pagina_revista": 144,
        "detalhes": "Página 144: Código (87512), 03 pts, R$ 34,90"
    },
    "7733": {
        "nome_revista": "Tododia Sabonete em Barra Tamarindo e Canela 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73,
        "pagina_revista": 143,
        "detalhes": "Linha Tododia Sabonetes Puro Vegetal 5x90g: R$ 34,90"
    },
    "121969": {
        "nome_revista": "Tododia Sabonete em Barra Camomila e Lavanda 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": None,
        "pagina_revista": 139,
        "detalhes": "Página 139: Código (121969), 03 pts, R$ 34,90"
    },
    "205939": {
        "nome_revista": "Tododia Sabonete em Barra Morango e Baunilha Dourada 5x90g",
        "preco_revista_tabela": 34.90,
        "preco_revista_promo": 28.73,
        "pagina_revista": 144,
        "detalhes": "Página 144: Código (205939), 03 pts, R$ 34,90"
    },
    "114464": {
        "nome_revista": "Tododia Sabonete em Barra Sortidos Coleção 5x90g",
        "preco_revista_tabela": 42.90,
        "preco_revista_promo": None,
        "pagina_revista": 144,
        "detalhes": "Linha Tododia Caixa Especial Sabonetes Sortidos: R$ 42,90"
    },
    
    # 2. Perfumaria
    "95560": {
        "nome_revista": "Essencial Supreme Masculino Deo Parfum 100ml",
        "preco_revista_tabela": 279.90,
        "preco_revista_promo": None,
        "pagina_revista": 71,
        "detalhes": "Página 71: Código (95560), 21 pts, R$ 279,90"
    },
    "76423": {
        "nome_revista": "Essencial Exclusivo Feminino Deo Parfum 100ml",
        "preco_revista_tabela": 279.90,
        "preco_revista_promo": None,
        "pagina_revista": 63,
        "detalhes": "Página 63: Código (76423), 21 pts, R$ 279,90"
    },
    "72468": {
        "nome_revista": "K Max Masculino Deo Parfum 100ml",
        "preco_revista_tabela": 299.90,
        "preco_revista_promo": None,
        "pagina_revista": 83,
        "detalhes": "Página 83: Código (72468), 22 pts, R$ 299,90"
    },
    "108401": {
        "nome_revista": "Kaiak Urbe Masculino Desodorante Colônia 100ml",
        "preco_revista_tabela": 189.90,
        "preco_revista_promo": None,
        "pagina_revista": 82,
        "detalhes": "Página 82: Código (108401), 14 pts, R$ 189,90"
    },
    "17049": {
        "nome_revista": "Essencial Oud Vanilla Feminino Deo Parfum 100ml",
        "preco_revista_tabela": 289.90,
        "preco_revista_promo": None,
        "pagina_revista": 67,
        "detalhes": "Página 67: Código (17049), 21 pts, R$ 289,90"
    },
    "102412": {
        "nome_revista": "Naturé Colônia Infantil Pula-Corda 100ml",
        "preco_revista_tabela": 99.90,
        "preco_revista_promo": None,
        "pagina_revista": 173,
        "detalhes": "Página 173: Colônia infantil Naturé 100ml, R$ 99,90"
    },

    # 3. Hidratantes & Cuidados Corporais
    "180469": {
        "nome_revista": "Tododia Desodorante Hidratante Corporal Iluminador Dourado Acerola e Hibisco 150ml",
        "preco_revista_tabela": 54.90,
        "preco_revista_promo": None,
        "pagina_revista": 134,
        "detalhes": "Página 134: Código (180469), 04 pts, R$ 54,90"
    },
    "174614": {
        "nome_revista": "Tododia Desodorante Hidratante Corporal Cereja Negra e Jabuticaba 400ml",
        "preco_revista_tabela": 78.90,
        "preco_revista_promo": None,
        "pagina_revista": 135,
        "detalhes": "Página 135: Hidratante Corporal Tododia 400ml, 06 pts, R$ 78,90"
    },
    "21307": {
        "nome_revista": "Tododia Óleo Desodorante Hidratante Bifásico Corporal Cereja e Avelã 120ml",
        "preco_revista_tabela": 63.90,
        "preco_revista_promo": None,
        "pagina_revista": 136,
        "detalhes": "Página 136: Óleo bifásico corporal Tododia 120ml, R$ 63,90"
    },
    "18978": {
        "nome_revista": "Tododia Refil Sabonete Líquido Cereja e Avelã 300ml",
        "preco_revista_tabela": 38.40,
        "preco_revista_promo": None,
        "pagina_revista": 139,
        "detalhes": "Linha Tododia Refil Sabonete Líquido Corporal 300ml, R$ 38,40"
    },
    "189409": {
        "nome_revista": "Tododia Desodorante Antitranspirante Roll-on Manga Rosa e Água de Coco 70ml",
        "preco_revista_tabela": 29.90,
        "preco_revista_promo": 23.90, # Promoção pág 162
        "pagina_revista": 162,
        "detalhes": "Página 162: Código (189409), R$ 29,90 (Promoção no ciclo R$ 23,90)"
    },
    "146888": {
        "nome_revista": "Essencial Exclusivo Feminino Desodorante Spray Corporal 100ml",
        "preco_revista_tabela": 72.90,
        "preco_revista_promo": None,
        "pagina_revista": 33,
        "detalhes": "Linha Essencial Desodorante Corporal Perfumado Spray 100ml, R$ 72,90"
    },

    # 4. Cuidados para as Mãos
    "174169": {
        "nome_revista": "Essencial Exclusivo Creme Hidratante para Mãos 40g",
        "preco_revista_tabela": 47.40,
        "preco_revista_promo": None,
        "pagina_revista": 33,
        "detalhes": "Linha Essencial Creme Desodorante Hidratante para Mãos 40g, R$ 47,40"
    },
    "194826": {
        "nome_revista": "Luna Fascinante Creme Hidratante para Mãos 40g",
        "preco_revista_tabela": 45.40,
        "preco_revista_promo": None,
        "pagina_revista": 27,
        "detalhes": "Linha Luna Creme Hidratante para Mãos 40g, R$ 45,40"
    },
    "194822": {
        "nome_revista": "Essencial Ato Feminino Creme Hidratante para Mãos 40g",
        "preco_revista_tabela": 50.50,
        "preco_revista_promo": None,
        "pagina_revista": 27,
        "detalhes": "Linha Essencial Ato Creme Hidratante para Mãos 40g, R$ 50,50"
    },

    # 5. Mamãe e Bebê
    "92796": {
        "nome_revista": "Mamãe e Bebê Sabonete em Barra com Saboneteira / 2x100g",
        "preco_revista_tabela": 31.10,
        "preco_revista_promo": None,
        "pagina_revista": 168,
        "detalhes": "Página 168: Sabonete em Barra Vegetal Mamãe e Bebê 100g, R$ 31,10"
    },
    "135049": {
        "nome_revista": "Mamãe e Bebê Clássico Loção Hidratante Corporal 100ml",
        "preco_revista_tabela": 37.50,
        "preco_revista_promo": None,
        "pagina_revista": 168,
        "detalhes": "Página 168: Hidratante Mamãe e Bebê 100ml, R$ 37,50"
    },
    "140689": {
        "nome_revista": "Mamãe e Bebê Loção Hidratante Papai e Bebê / Pele Sensível 100ml",
        "preco_revista_tabela": 37.50,
        "preco_revista_promo": None,
        "pagina_revista": 168,
        "detalhes": "Página 168: Hidratante Mamãe e Bebê 100ml, R$ 37,50"
    },

    # 6. Infantil Naturé & Cabelos Lumina
    "102417": {
        "nome_revista": "Naturé Sabonete Líquido Infantil 250ml",
        "preco_revista_tabela": 37.90,
        "preco_revista_promo": None,
        "pagina_revista": 174,
        "detalhes": "Página 174: Código (102417), 03 pts, R$ 37,90"
    },
    "147418": {
        "nome_revista": "Lumina Condicionador / Máscara Nutrição e Brilho 250ml",
        "preco_revista_tabela": 79.90,
        "preco_revista_promo": None,
        "pagina_revista": 185,
        "detalhes": "Página 185: Código (147418), 06 pts, R$ 79,90"
    }
}

print(f"Catalog mapping prepared for all {len(catalog_data)} products.")
