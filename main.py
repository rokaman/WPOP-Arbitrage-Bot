import asyncio
from orchestrator import AgentOrchestrator


async def main():
    agent = AgentOrchestrator()
    query = "monedas+plata"

    # Ejecutamos la búsqueda y el pipeline de arbitraje
    results = await agent.run_search_pipeline(query=query, max_price=30.0)

    if not results:
        print("[!] No se encontraron resultados o no superaron los criterios de análisis.")
        return

    print("\n" + "=" * 50)
    print("      RESULTADOS DEL ANÁLISIS DE ARBITRAJE")
    print("=" * 50)

    for result in results:
        # 1. Control de seguridad: ignorar elementos nulos
        if result is None:
            continue

        # 2. Extraer item y análisis según la estructura devuelta por el orquestador
        if hasattr(result, "item"):
            item = result.item
            analysis = getattr(result, "analysis", None)
            melt_value = getattr(result, "melt_value", 0.0)
            margen = getattr(result, "margen_chollo", 0.0)
            es_chollo = getattr(result, "es_chollo", False)
        else:
            item = result
            analysis = None
            melt_value, margen, es_chollo = 0.0, 0.0, False

        if not item:
            continue

        # 3. Mostrar el reporte en consola
        print(f"\n[ITEM] {item.titulo} | {item.precio} EUR")
        print(f"URL: {item.url_anuncio}")

        if analysis:
            print(f"Moneda detectada: {analysis.moneda_detectada}")
            print(f"Peso: {analysis.peso_g}g | Ley: {analysis.ley}")
            print(f"Melt value (valor fundicion): {melt_value:.2f} EUR")
            print(f"Margen: {margen:.1f}%")
            print(f"Es chollo: {'SI' if es_chollo else 'NO'}")
        
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())