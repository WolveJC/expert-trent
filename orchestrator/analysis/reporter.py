import pandas as pd
import json

class ExperimentReporter:
    def __init__(self, csv_path="results/metrics.csv"):
        self.csv_path = csv_path

    def generate_summary(self):
        try:
            df = pd.read_csv(self.csv_path)
            
            # Aumentamos la precisión en la agregación
            summary = df.groupby(['algorithm']).agg({
                'processing_time_ms': ['mean', 'min', 'max', 'std'],
                'batch_id': 'count'
            }).reset_index()

            summary.columns = ['Algoritmo', 'Media (ms)', 'Mín (ms)', 'Máx (ms)', 'Desviación', 'Total Pruebas']
            
            # Exportar a JSON asegurando que no se pierdan decimales
            # records orient es perfecto para tablas en CustomTkinter
            summary_dict = summary.to_dict(orient='records')
            
            with open('results/summary_report.json', 'w') as f:
                json.dump(summary_dict, f, indent=4)
            
            return summary
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return None