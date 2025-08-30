# -*- coding: utf-8 -*-
import sys
import time
import re
import serial
import numpy as np

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from PyQt5.QtCore import *
from PyQt5.QtGui import *

print("Proyecto Medición de Resistencias - Grupo 1")

class Ui(QMainWindow):

    def __init__(self):
        super().__init__()
        uic.loadUi('Interfaz.ui', self)   
            
        # PARAMETROS DE LA INTERFAZ
        self.showMaximized()
        self.cerrar_port.setEnabled(False)
        self.cerrar_port_2.setEnabled(False)
        self.proceso.setEnabled(False)
        
        # VARIABLES
        
        self.muestras_I = None
        self.muestras_V = None
        self.flag = 0
        self.flag1 = 0
        self.flag2 = 0
        self.flag3 = 0
        self.flag4 = 0
        self.CBM_f = 0
        self.TBM_f = 0
        
        # CONEXION DE BOTONES
        self.scan_port.clicked.connect(self.scanport)
        self.conectar.clicked.connect(self.conectarport1) 
        self.conectar_2.clicked.connect(self.conectarport2) 
        self.proceso.clicked.connect(self.iniciar_proceso)
        self.select_CBM.clicked.connect(self.CBM)
        self.select_TBM.clicked.connect(self.TBM)
        
        #self.salir.clicked.connect(self.salir)
            
    def scanport(self):
        print("Escanear puerto serie") 
        def puertos_seriales():
            ports = ['COM%s' % (i + 1) for i in range(256)]
            encontrados = []
            for port in ports:
                try:
                    s = serial.Serial(port)
                    s.close()
                    encontrados = port
                except (OSError, serial.SerialException):
                    pass
            return encontrados

        puertoencontrado = str(puertos_seriales())
        self.etiqueta.setText('Puertos disponibles: ' + puertoencontrado)
        
    def conectarport1(self):
        print("Conectar puerto serie 1")
        port = self.Combobox.currentText()
        
        baudrate = 115200
        self.ard1 = serial.Serial(port=port, baudrate=baudrate)
        self.etiqueta.setText("Puerto 1 conectado a: " + port)
        self.conectar.setEnabled(False)
        #self.proceso.setEnabled(True)
        self.flag2 = 1
        self.cerrar_port.setEnabled(True)
        self.flag1 = 1
        #self.etiqueta.setText('Puerto NO conectado')
        
    def conectarport2(self):
        print("Conectar puerto serie 2")
        port = self.Combobox_2.currentText()
        
        baudrate = 115200
        self.ard2 = serial.Serial(port=port, baudrate=baudrate)
        self.etiqueta.setText("Puerto 2 conectado a: " + port)
        self.conectar_2.setEnabled(False)
        #self.proceso.setEnabled(True)
        self.flag4 = 1
        self.cerrar_port_2.setEnabled(True)
        self.flag3 = 1
        
        if self.flag4 and self.flag2:
            self.select_CBM.setEnabled(True) 
            self.select_TBM.setEnabled(True) 
            
        #self.etiqueta.setText('Puerto NO conectado')
        
    def salir(self):
        self.close()
        
    def CBM(self):
        self.CBM_f=1
        self.proceso.setEnabled(True)
        self.select_TBM.setEnabled(False)

    def TBM(self):
        self.TBM_f=1
        self.proceso.setEnabled(True)
        self.select_CBM.setEnabled(False)        
    
    
    def iniciar_proceso(self):
        # amperímetro en self.ard1, voltímetro en self.ard2
        if (not hasattr(self, "ard1") or self.ard1 is None or not self.ard1.is_open or
            not hasattr(self, "ard2") or self.ard2 is None or not self.ard2.is_open):
            return

        if not self.ard1.timeout or self.ard1.timeout <= 0:
            self.ard1.timeout = 1.0
        if not self.ard2.timeout or self.ard2.timeout <= 0:
            self.ard2.timeout = 1.0

        try:
            self.ard1.reset_input_buffer(); self.ard1.reset_output_buffer()
            self.ard2.reset_input_buffer(); self.ard2.reset_output_buffer()
        except:
            pass

        vals_I, vals_V = [], []

        for i in range(5):
            vI, vV = None, None
            t0 = time.time()
            # ventana de hasta 2 s para capturar el par casi simultáneo
            while (time.time() - t0) < 2.0 and (vI is None or vV is None):
                if vI is None:
                    raw1 = self.ard1.readline()
                    if raw1:
                        try:
                            vI = float(raw1.decode("ascii", errors="ignore").strip().replace(",", "."))
                        except:
                            pass
                if vV is None:
                    raw2 = self.ard2.readline()
                    if raw2:
                        try:
                            vV = float(raw2.decode("ascii", errors="ignore").strip().replace(",", "."))
                        except:
                            pass

            if vI is not None: vals_I.append(vI)
            if vV is not None: vals_V.append(vV)

            self.etiqueta.setText(f"Muestra {i+1}/5  I:{vI}  V:{vV}")
            QApplication.processEvents()
            if i < 4:
                time.sleep(1)

        self.muestras_I = np.array(vals_I, dtype=float)
        self.muestras_V = np.array(vals_V, dtype=float)

        # Si ya definiste calcular_R_incertidumbre(), lo invocás acá:
        res = getattr(self, "calcular_R_incertidumbre", None)
        if callable(res):
            out = res()
            if out is not None:
                R, U95 = out
                self.etiqueta.setText(f"Listo.\nR = {R:.6g} Ω\nU95 (95%) = ±{U95:.6g} Ω")
                return

        self.etiqueta.setText("Listo.")

    def calcular_R_incertidumbre(self):
        pass
        #PROCESAMIENTO MATEMATICO ESTADISTICO  

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
