class ParserIncidentes:
    def __init__(self):
        self.palavras_criticas = ["intransitavel", "intransitável", "alagado", "coberto", "roda", "enchente"]
        self.palavras_medias = ["meio-fio", "calçada", "calcada", "subindo", "canela"]

    def extrair_severidade(self, texto):
        texto_limpo = texto.lower()
        if any(palavra in texto_limpo for palavra in self.palavras_criticas):
            return 5
        elif any(palavra in texto_limpo for palavra in self.palavras_medias):
            return 3
        return 1

if __name__ == "__main__":
    print("--- [TESTE LAB] Inicializando Parser de Texto da ThomasinfoTech ---")
    parser = ParserIncidentes()
    
    relato_1 = "A Avenida em Itaparica está totalmente intransitável, a água cobriu tudo."
    relato_2 = "Tem um pouco de água subindo no meio-fio da rua."
    
    print(f"Relato 1 -> Nível de Severidade Calculado: {parser.extrair_severidade(relato_1)}")
    print(f"Relato 2 -> Nível de Severidade Calculado: {parser.extrair_severidade(relato_2)}")