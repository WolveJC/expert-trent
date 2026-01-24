import time
import argparse
import os
from producer import ShmProducer
from collector import ShmCollector
from reference import ScanReference
from generators.scenarios import ScenarioGenerator
from analysis.plotter import PerformancePlotter
from analysis.reporter import ExperimentReporter

def run_simulation(args):
    """
    Ejecuta un experimento completo: Generación -> Inyección -> Recolección -> Validación.
    """
    # Asegurar que el directorio de resultados existe
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Inicialización de componentes
    try:
        producer = ShmProducer()
        collector = ShmCollector(log_file=args.output)
        reference = ScanReference()
        generator = ScenarioGenerator(max_cylinders=500)
    except Exception as e:
        print(f"[Sistema] Error crítico de inicialización: {e}")
        print("¿Está el motor C++ corriendo y la SHM creada?")
        return

    print(f"\n{'='*50}")
    print(f" EXPERIMENTO: {args.scenario.upper()} | ALGORITMO: {args.mode.upper()}")
    print(f"{'='*50}")

    # 2. Generación de Escenario Analítico
    scenarios = {
        "random": generator.random_requests,
        "locality": generator.locality_burst,
        "killer": generator.scan_killer
    }
    
    # Obtenemos las peticiones del generador
    requests = scenarios[args.scenario](count=args.batch_size)

    # 3. Fase de Inyección (Python -> SHM)
    initial_head = 0  # Punto de partida estático para validación
    print(f"[1/4] Inyectando {len(requests)} peticiones en SHM...")
    target_idx = producer.write_batch(requests)

    # 4. Fase de Espera y Sincronización
    print(f"[2/4] Sincronizando con Motor C++ (Esperando cons_idx >= {target_idx})...")
    start_time = time.perf_counter()
    
    # El collector observa la memoria compartida hasta que el motor avance
    success = collector.wait_for_completion(target_idx, timeout=args.timeout)
    end_time = time.perf_counter()

    if success:
        elapsed = (end_time - start_time) * 1000 # Convertir a ms
        print(f"[3/4] Motor respondió en {elapsed:.4f} ms.")
        
        # 5. Extracción de métricas
        metrics = collector.collect_metrics(
            batch_id=requests[0]['batch_id'], 
            algorithm=args.mode,
            elapsed_ms=elapsed
            )
        collector.save_to_csv()
        plotter = PerformancePlotter(args.output)
        reporter = ExperimentReporter(args.output)
        plotter.plot_latency_comparison()
        reporter.generate_summary()
        
        # 6. Validación cruzada
        if args.mode == "scan":
            ref_mov, _ = reference.calculate_scan(requests, initial_head)
        else:
            ref_mov, _ = reference.calculate_cscan(requests, initial_head, max_cyl=500)
            
        print(f"[4/4] VALIDACIÓN:")
        print(f"      - Movimiento Ref (Python): {ref_mov} cilindros")
        print(f"      - Resultado guardado en: {args.output}")
        print(f"\n[INFO] Compare este valor con el 'batch_movement' en el log de C++.")
    else:
        print(f"[ALERTA] Timeout tras {args.timeout}s. El motor no procesó el lote.")

    producer.close()
    collector.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador de Simulador de Disco")
    
    parser.add_argument("--mode", type=str, choices=["scan", "cscan"], default="scan")
    parser.add_argument("--scenario", type=str, choices=["random", "locality", "killer"], default="random")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--output", type=str, default="results/metrics.csv")
    parser.add_argument("--timeout", type=int, default=10, help="Segundos máximos de espera")

    args = parser.parse_args()
    run_simulation(args)