# -*- coding: utf-8 -*-
import sys
import time
import numpy as np

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from serial.tools import list_ports
from ut61eplus.dmm import DMM

print("Proyecto Medición de Resistencias - Grupo 1")

class Ui(QMainWindow):

    def __init__(self):
        super().__init__()
        uic.loadUi('Interfaz.ui', self)   
            
        # PARAMETROS DE LA INTERFAZ
        self.showMaximized()
        self.cerrar_port.setEnabled(False)
        self.proceso.setEnabled(False)
        
        # VARIABLES
        
        self.flag = 0
        self.flag1 = 0
        self.flag2 = 0
        self.muestras_I = None
        
        # CONEXION DE BOTONES
        self.scan_port.clicked.connect(self.scanport)
        self.conectar.clicked.connect(self.conectarport)
        self.proceso.clicked.connect(self.iniciar_proceso)
        #self.salir.clicked.connect(self.salir)
            
    def scanport(self):
        pass

    def conectarport(self):
        pass
        
    def salir(self):
        self.close()
        
    def iniciar_proceso(self):
        """Lee 5 mediciones del multímetro, 1s entre cada una, y las guarda en self.ultimas_mediciones"""
        if not hasattr(self, "ard") or self.ard is None or not self.ard.is_open:
            return  # seguridad, por si el puerto no está abierto

        self.ard.reset_input_buffer()
        self.ard.reset_output_buffer()

        valores = []
        for i in range(5):
            raw = self.ard.readline().decode("ascii", errors="ignore").strip()
            try:
                # reemplazo de coma por punto en caso de que el multímetro envíe con coma
                valor = float(raw.replace(",", "."))
                valores.append(valor)
            except:
                continue  # si no se puede parsear, ignora y sigue

            self.etiqueta.setText(f"Medición {i+1}/5: {valor}")
            QApplication.processEvents()
            if i < 4:
                time.sleep(1)

        self.muestras_I = np.array(valores, dtype=float)
        self.consola.setText(f"Listo. Lecturas: {self.ultimas_mediciones}")

        
# ================== EJECUCIÓN ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)   # Crear la aplicación
    window = Ui()                  # Crear la ventana
    window.show()                  # Mostrar la ventana
    sys.exit(app.exec_())          # Ejecutar el loop de eventos        
        
"""
Created on Sun Aug 17 17:29:13 2025

@author: Joaquin Cieri
"""

