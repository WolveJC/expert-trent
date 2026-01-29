import time
import argparse
import os
import sys
from orchestrator.supervisor import EngineSupervisor
from orchestrator.producer import ShmProducer
from orchestrator.collector import ShmCollector
from orchestrator.reference import ScanReference
from orchestrator.generators.scenarios import ScenarioGenerator
from orchestrator.analysis.plotter import PerformancePlotter
from orchestrator.analysis.reporter import ExperimentReporter

def run_simulation(args):
    """
    Ejecuta el experimento gestionando el ciclo de vida del motor C++.
    """
    # 1. Inicialización del Supervisor (El 'niñero' del proceso C++)
    supervisor = EngineSupervisor()
    
    try:
        # Limpiar residuos de ejecuciones previas (vital en Linux)
        supervisor.cleanup_shm()
        
        # Lanzar el motor C++ de forma invisible
        print(f"[Sistema] Iniciando motor C++ para modo: {args.mode.upper()}...")
        supervisor.start_engine(algorithm=args.mode)
        
        # 2. Conexión a la infraestructura de datos
        # Esperamos un momento a que el motor cree la SHM
        time.sleep(0.2) 
        producer = ShmProducer()
        collector = ShmCollector(log_file=args.output)
        reference = ScanReference()
        generator = ScenarioGenerator(max_cylinders=500)

    except Exception as e:
        # Aquí capturamos el error y evitamos el Traceback feo
        print(f"\n[ERROR CRÍTICO] No se pudo inicializar el entorno: {e}")
        if supervisor.is_running:
            supervisor.stop_engine()
        return

    print(f"\n{'='*50}")
    print(f" EXPERIMENTO: {args.scenario.upper()} | ALGORITMO: {args.mode.upper()}")
    print(f"{'='*50}")

    # 3. Generación de Escenario
    scenarios = {
        "random": generator.random_requests,
        "locality": generator.locality_burst,
        "killer": generator.scan_killer
    }
    requests = scenarios[args.scenario](count=args.batch_size)

    # 4. Fase de Inyección
    initial_head = 0
    print(f"[1/4] Inyectando {len(requests)} peticiones en SHM...")
    target_idx = producer.write_batch(requests)

    # 5. Sincronización con el Motor
    print(f"[2/4] Sincronizando (Esperando respuesta del motor)...")
    start_time = time.perf_counter()
    success = collector.wait_for_completion(target_idx, timeout=args.timeout)
    end_time = time.perf_counter()

    # 6. Procesamiento de Resultados
    if success:
        elapsed = (end_time - start_time) * 1000
        print(f"[3/4] Motor respondió exitosamente en {elapsed:.4f} ms.")
        
        metrics = collector.collect_metrics(
            batch_id=requests[0]['batch_id'], 
            algorithm=args.mode,
            elapsed_ms=elapsed
        )
        collector.save_to_csv()
        
        # Generación de reportes automáticos
        try:
            reporter = ExperimentReporter(args.output)
            reporter.generate_summary()
            plotter = PerformancePlotter(args.output)
            plotter.plot_latency_comparison()
        except Exception as e:
            print(f"[Aviso] No se pudieron generar gráficas: {e}")

        # Validación técnica
        if args.mode == "scan":
            ref_mov, _ = reference.calculate_scan(requests, initial_head)
        else:
            ref_mov, _ = reference.calculate_cscan(requests, initial_head, max_cyl=500)
            
        print(f"[4/4] VALIDACIÓN FINAL:")
        print(f"      - Movimiento Teórico: {ref_mov} cilindros")
        print(f"      - Reporte guardado en: results/summary_report.json")
    else:
        print(f"[ALERTA] Timeout: El motor C++ no respondió. Revise los logs.")

    # 7. Clausura Limpia (VITAL)
    print("\n[Sistema] Finalizando procesos y liberando memoria...")
    producer.close()
    collector.close()
    supervisor.stop_engine()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador de Simulador de Disco")
    parser.add_argument("--mode", type=str, choices=["scan", "cscan"], default="scan")
    parser.add_argument("--scenario", type=str, choices=["random", "locality", "killer"], default="random")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--output", type=str, default="results/metrics.csv")
    parser.add_argument("--timeout", type=int, default=10)

    args = parser.parse_args()
    
    # Crear carpeta de resultados si no existe
    os.makedirs("results", exist_ok=True)
    
    run_simulation(args)