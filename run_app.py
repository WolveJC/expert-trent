import os
import sys
import platform
import subprocess
from ui.main_window import DiskSimGUI

def get_resource_path(relative_path):
    """ 
    Permite encontrar archivos tanto en modo desarrollo como 
    cuando el programa esté empaquetado en un solo archivo .exe
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta del script actual
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class AppLauncher:
    def __init__(self):
        # Determinamos el nombre del motor según el Sistema Operativo
        self.engine_filename = "scheduler_engine"
        if platform.system() == "Windows":
            self.engine_filename += ".exe"
            
        # Obtenemos la ruta absoluta del motor C++ embebido
        self.engine_path = get_resource_path(os.path.join("core", self.engine_filename))
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

    def prepare_environment(self):
        """Asegura que las carpetas y permisos estén listos."""
        print(f"[System] Verificando entorno de simulación...")

        # 1. Crear carpeta de resultados si no existe
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"[System] Directorio de resultados creado: {self.results_dir}")

        # 2. Validar presencia del motor C++ (Embebido)
        if not os.path.exists(self.engine_path):
            print(f"\n[ERROR CRÍTICO] Motor no encontrado en: {self.engine_path}")
            print("Asegúrate de que el binario de C++ esté en la carpeta 'core/'.")
            return False

        # 3. Permisos de ejecución (Solo para Linux/macOS)
        if platform.system() != "Windows":
            try:
                subprocess.run(["chmod", "+x", self.engine_path], check=True)
            except Exception as e:
                print(f"[Aviso] No se pudo ajustar permisos al motor: {e}")

        return True

    def run(self):
        """Inicia la aplicación."""
        if self.prepare_environment():
            print("[System] Entorno validado. Lanzando GUI...")
            
            # Inicializamos la GUI
            # Nota: main_window.py ya tiene configurado el EngineSupervisor 
            # que buscará el motor en la ruta que establecimos.
            app = DiskSimGUI(engine_path=self.engine_path)
            
            try:
                app.mainloop()
            except KeyboardInterrupt:
                print("\n[System] Cierre solicitado por usuario.")
            finally:
                # Asegurar limpieza de procesos al salir
                if hasattr(app, 'supervisor'):
                    app.supervisor.stop_engine()
                print("[System] Procesos finalizados. Limpieza de memoria OK.")
        else:
            input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    launcher = AppLauncher()
    launcher.run()