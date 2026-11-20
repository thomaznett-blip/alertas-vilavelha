import math

class ResolvedorGeofencing:
    def __init__(self, raio_alerta_padrao_km=0.5):
        self.raio_alerta_padrao_km = raio_alerta_padrao_km

    def calcular_distancia_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0 # Raio médio da Terra em km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        # Fórmula matemática pura de Haversine
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 3)

    def verificar_moradores_no_perimetro(self, coordenadas_incidente, lista_moradores):
        lat_inc, lon_inc = coordenadas_incidente
        moradores_afetados = []

        for morador in lista_moradores:
            dist = self.calcular_distancia_haversine(lat_inc, lon_inc, morador["lat"], morador["lon"])
            if dist <= self.raio_alerta_padrao_km:
                morador_com_distancia = morador.copy()
                morador_com_distancia["distancia_km"] = dist
                moradores_afetados.append(morador_com_distancia)

        return moradores_afetados

if __name__ == "__main__":
    print("--- [TESTE LAB] Inicializando Módulo de Geofencing da ThomasinfoTech ---")
    alagamento_itaparica = (-20.3621, -40.2894)
    
    moradores_vv = [
        {"id": "MOR-01 - Perto do Quiosque", "lat": -20.3625, "lon": -40.2890}, 
        {"id": "MOR-02 - Duas quadras atrás", "lat": -20.3650, "lon": -40.2910}, 
        {"id": "MOR-03 - Centro de Vila Velha", "lat": -20.3294, "lon": -40.2944} 
    ]
    
    geofence = ResolvedorGeofencing(raio_alerta_padrao_km=0.5)
    afetados = geofence.verificar_moradores_no_perimetro(alagamento_itaparica, moradores_vv)
    
    print(f"\nAlagamento detectado em Itaparica {alagamento_itaparica}")
    print(f"Total de moradores notificados no raio de 500m: {len(afetados)}")
    for m in afetados:
        print(f" -> Notificação enviada para: {m['id']} (Distância: {m['distancia_km']} km)")