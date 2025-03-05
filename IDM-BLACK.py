import os
import threading
import requests
import tkinter as tk
from tkinter import filedialog, ttk
import time
import sys

class DownloadManager:
    def __init__(self, root):
        self.root = root
        self.root.title("IDM BLACK")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        self.root.configure(bg="#d4d0c8")
        self.monitor_clipboard()
        self.root.bind("<Control-y>", self.reset_app)

        self.file_size = 0
        self.downloaded = 0
        self.is_paused = False
        self.is_cancelled = False
        self.num_connections = 4
        
        tk.Label(root, text="URL del archivo:", bg="#d4d0c8", font=("Tahoma", 10)).place(x=20, y=20)
        self.entry_url = tk.Entry(root, width=50)
        self.entry_url.place(x=150, y=20)
        
        tk.Label(root, text="Guardar en:", bg="#d4d0c8", font=("Tahoma", 10)).place(x=20, y=60)
        self.entry_path = tk.Entry(root, width=40)
        self.entry_path.place(x=150, y=60)
        self.btn_browse = tk.Button(root, text="Examinar", command=self.browse_location)
        self.btn_browse.place(x=400, y=58)
        
        self.btn_size = tk.Button(root, text="Ver tamaño", command=self.get_file_size)
        self.btn_size.place(x=150, y=90)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, length=300)
        self.progress_bar.place(x=150, y=130)
        self.progress_label = tk.Label(root, text="0%", bg="#d4d0c8", font=("Tahoma", 10))
        self.progress_label.place(x=460, y=130)
        
        self.speed_label = tk.Label(root, text="Velocidad: 0 KB/s", bg="#d4d0c8", font=("Tahoma", 10))
        self.speed_label.place(x=150, y=160)
        
        self.downloaded_label = tk.Label(root, text="Descargado: 0 MB", bg="#d4d0c8", font=("Tahoma", 10))
        self.downloaded_label.place(x=150, y=180)

        self.time_remaining_label = tk.Label(root, text="Tiempo restante: --", bg="#d4d0c8", font=("Tahoma", 10))
        self.time_remaining_label.place(x=150, y=220)
        
        self.connections_label = tk.Label(root, text=f"Conexiones: {self.num_connections}", bg="#d4d0c8", font=("Tahoma", 10))
        self.connections_label.place(x=150, y=200)
        
        self.btn_download = tk.Button(root, text="Descargar", command=self.start_download, width=10)
        self.btn_download.place(x=50, y=245)
        
        self.btn_pause = tk.Button(root, text="Pausar", command=self.pause_download, width=10)
        self.btn_pause.place(x=150, y=245)
        
        self.btn_cancel = tk.Button(root, text="Cancelar", command=self.cancel_download, width=10, state=tk.DISABLED)
        self.btn_cancel.place(x=250, y=245)
        
        self.btn_delete = tk.Button(root, text="Eliminar Archivo", command=self.delete_file, width=15)
        self.btn_delete.place(x=350, y=245)

        self.version_label = tk.Label(root, text="Versión 1.0.0", bg="#d4d0c8", font=("Tahoma", 8))
        self.version_label.place(x=420, y=280)  # Ajusta la posición según necesites


    def monitor_clipboard(self):
        try:
             clipboard_content = self.root.clipboard_get()
             if clipboard_content.startswith("http"):  # Verifica si es un enlace
                 self.entry_url.delete(0, tk.END)
                 self.entry_url.insert(0, clipboard_content)
        except tk.TclError:
            pass  # Puede fallar si el portapapeles está vacío o inaccesible

        self.root.after(1000, self.monitor_clipboard)  # Verifica cada segundo

        
    def browse_location(self):
        folder_selected = filedialog.askdirectory()
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, folder_selected)
    
    def get_file_size(self):
        url = self.entry_url.get()
        response = requests.head(url, allow_redirects=True)
        if 'Content-Length' in response.headers:
            self.file_size = int(response.headers['Content-Length'])
            self.speed_label.config(text=f"Tamaño del archivo: {self.file_size / (1024 * 1024):.2f} MB")
        else:
            self.speed_label.config(text="No se pudo obtener el tamaño del archivo")
    
    def start_download(self):
        self.is_paused = False
        self.is_cancelled = False
        self.downloaded = 0
        self.btn_cancel.config(state=tk.NORMAL)
        threading.Thread(target=self.download_file).start()
    
    def download_file(self):
        url = self.entry_url.get()
        path = self.entry_path.get()
        file_name = os.path.join(path, url.split('/')[-1])
        
        response = requests.get(url, stream=True)
        self.file_size = int(response.headers.get('content-length', 0))
        
        if self.file_size == 0:
            self.speed_label.config(text="Error: Tamaño de archivo desconocido")
            return
        
        start_time = time.time()
        
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 100):  # Chunk aumentado
                if self.is_cancelled:
                    os.remove(file_name)
                    return
                while self.is_paused:
                    time.sleep(0.5)
                if chunk:
                    file.write(chunk)
                    self.downloaded += len(chunk)
                    elapsed_time = time.time() - start_time
                    speed = (self.downloaded / 1024) / elapsed_time if elapsed_time > 0 else 0
                    self.update_progress(speed)
        
        self.btn_cancel.config(state=tk.DISABLED)
    
    def update_progress(self, speed):
        if self.file_size == 0:
            return
        progress = (self.downloaded / self.file_size) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.2f}%")
        self.speed_label.config(text=f"Velocidad: {speed:.2f} KB/s")
        self.downloaded_label.config(text=f"Descargado: {self.downloaded / (1024 * 1024):.2f} MB")
        self.root.update_idletasks()
        remaining_size = self.file_size - self.downloaded
        remaining_time = (remaining_size / 1024) / speed if speed > 0 else 0  # Tiempo en segundos
        minutes, seconds = divmod(int(remaining_time), 60)
        self.time_remaining_label.config(text=f"Tiempo restante: {minutes}m {seconds}s")

    
    def pause_download(self):
        self.is_paused = not self.is_paused
        self.btn_pause.config(text="Reanudar" if self.is_paused else "Pausar")
    
    def cancel_download(self):
        self.is_cancelled = True
        self.btn_cancel.config(state=tk.DISABLED)
    
    def delete_file(self):
        file_path = self.entry_path.get()
        if os.path.exists(file_path):
            os.remove(file_path)
            print("Archivo eliminado")
        else:
            print("No hay archivo para eliminar")

    def reset_app(self, event=None):
        self.root.destroy()
        python = sys.executable
        os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManager(root)
    root.mainloop()
