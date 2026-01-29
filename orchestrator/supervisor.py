import subprocess
import sys
import os
import time
import platform
import shutil
from pathlib import Path

class EngineSupervisor:
    def __init__(self, bin_name="scheduler_engine", engine_path=None):
        self.os_type = platform.system()
        self.bin_name = f"{bin_name}.exe" if self.os_type == "Windows" else bin_name
        self.process = None
        self.is_running = False
        self.external_engine_path = engine_path 

    def _get_executable_path(self):
        """
        Detecta la ruta del binario priorizando la ruta externa inyectada.
        """
        if self.external_engine_path and os.path.exists(self.external_engine_path):
            return self.external_engine_path

        # Lógica de respaldo (Desarrollo o si falla la inyección)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS) / "core"
        else:
            base_path = Path(__file__).parent.parent / "core"

        exe_path = base_path / self.bin_name
        
        if not exe_path.exists():
            raise FileNotFoundError(f"Motor C++ no encontrado en: {exe_path}")
            
        return str(exe_path)

    def start_engine(self, algorithm="SCAN"):
        """Lanza el motor C++ y gestiona posibles errores de inicio."""
        try:
            exe_path = self._get_executable_path()
            
            # En Linux, asegurar que tiene permisos de ejecución
            if self.os_type != "Windows":
                os.chmod(exe_path, 0o755)

            # Lanzar el proceso
            # stdout/stderr se capturan para evitar que ensucien la consola de la GUI
            self.process = subprocess.Popen(
                [exe_path, "--algo", algorithm.upper()],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if self.os_type == "Windows" else 0
            )
            
            # Pequeña espera para verificar si el proceso no murió instantáneamente
            time.sleep(0.5)
            if self.process.poll() is not None:
                _, err = self.process.communicate()
                raise RuntimeError(f"El motor falló al iniciar: {err}")

            self.is_running = True
            print(f"[Supervisor] Motor C++ iniciado (PID: {self.process.pid})")
            
        except Exception as e:
            self.is_running = False
            raise RuntimeError(f"Error Crítico del Sistema: {str(e)}")

    def check_health(self):
        """Verifica si el motor sigue vivo."""
        if self.process and self.process.poll() is None:
            return True
        self.is_running = False
        return False

    def stop_engine(self):
        """Cierre limpio del motor."""
        if self.process:
            print("[Supervisor] Deteniendo motor C++...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self.is_running = False

    def cleanup_shm(self):
        """Limpia residuos de memoria compartida si el motor crashó."""
        if self.os_type == "Linux":
            shm_path = f"/dev/shm/disk_scheduler_shm"
            if os.path.exists(shm_path):
                try: os.remove(shm_path)
                except: pass