import pandas as pd
import json

class ExperimentReporter:
    def __init__(self, csv_path="results/metrics.csv"):
        self.csv_path = csv_path

    def generate_summary(self):
        df = pd.read_csv(self.csv_path)
        
        # Agregamos estadísticas por algoritmo y escenario
        summary = df.groupby(['algorithm']).agg({
            'processing_time_ms': ['mean', 'min', 'max', 'std'],
            'batch_id': 'count'
        }).reset_index()

        summary.columns = ['Algoritmo', 'Media (ms)', 'Mín (ms)', 'Máx (ms)', 'Desviación', 'Total Pruebas']
        
        # Exportar a JSON para visualizadores externos
        summary_json = summary.to_json(orient='records')
        with open('results/summary_report.json', 'w') as f:
            f.write(summary_json)
        
        print("\n" + "="*30)
        print(" RESUMEN DE RENDIMIENTO")
        print("="*30)
        print(summary.to_string(index=False))