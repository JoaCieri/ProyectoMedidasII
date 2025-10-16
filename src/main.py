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
from serial.tools import list_ports

print("Proyecto Medición de Resistencias - Grupo 1")

def _es_volt(u: str) -> bool:
    return str(u).strip().upper().startswith("V")

def _es_corr(u: str) -> bool:
    return str(u).strip().upper().startswith("A")

def _to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return float("nan")

def _armar_vectores_VI(KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS):
    n = min(len(KEI_VEC), len(KEI_UNITS), len(UT_VEC), len(UT_UNITS))
    v_vec, i_vec = [], []
    for kv, ku, uv, uu in zip(KEI_VEC[:n], KEI_UNITS[:n], UT_VEC[:n], UT_UNITS[:n]):
        kvf, uvf = _to_float(kv), _to_float(uv)
        # Voltaje por unidad
        v_val = kvf if _es_volt(ku) else (uvf if _es_volt(uu) else float("nan"))
        # Corriente por unidad
        i_val = kvf if _es_corr(ku) else (uvf if _es_corr(uu) else float("nan"))
        v_vec.append(v_val)
        i_vec.append(i_val)
    return v_vec, i_vec



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
        self.Selector = 1
    
        
        # CONEXION DE BOTONES
        self.scan_port.clicked.connect(self.scanport)
        self.conectar.clicked.connect(self.conectarport1) 
        self.conectar_2.clicked.connect(self.conectarport2) 
        self.proceso.clicked.connect(self.iniciar_proceso)
        self.select_CBM.clicked.connect(self.CBM)
        self.select_TBM.clicked.connect(self.TBM)        
        self.salir.clicked.connect(self.salir_ui)
            
    def scanport(self):
        puertos = [p.device for p in list_ports.comports()]
        disponibles = ", ".join(puertos) if puertos else "ninguno"
        self.etiqueta.setText(f"Puertos disponibles: {disponibles}")
        
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
        self.flag4 = 1
        self.cerrar_port_2.setEnabled(True)
        self.flag3 = 1
        
        if self.flag4 and self.flag2:
            self.select_CBM.setEnabled(True) 
            self.select_TBM.setEnabled(True) 
        
    def salir_ui(self):
        self.close()
        
    def CBM(self):
        self.selector=0
        self.proceso.setEnabled(True)
        self.select_TBM.setEnabled(False)
        cant_muestras = int(self.Combobox_3.currentText())
        self.consola.setText('Cantidad de muestras: ' + str(cant_muestras))
        cant_muestras = 0
        
              
    def TBM(self):
        self.selector=1
        self.proceso.setEnabled(True)
        self.select_CBM.setEnabled(False) 
        cant_muestras = int(self.Combobox_3.currentText())
        self.consola.setText('Cantidad de muestras: ' + str(cant_muestras))
        cant_muestras = 0
        
    def _get_cant_mediciones(self, default=10):
        """
        Intenta obtener la cantidad de mediciones desde distintos widgets comunes.
        Acepta QComboBox (currentText) o QSpinBox (value). Si no encuentra nada,
        devuelve 'default'.
        """
        candidatos = [
            "Combobox_3", "comboBox_3", "comboBox", "ComboBox",
            "cb_muestras", "CB_muestras", "cmbMuestras",
            "spinBox_muestras", "SpinBox_muestras", "spinBox", "SpinBox",
        ]
        for name in candidatos:
            if hasattr(self, name):
                w = getattr(self, name)
                # QComboBox
                if hasattr(w, "currentText"):
                    try:
                        return int(w.currentText())
                    except Exception:
                        pass
                # QSpinBox / QDoubleSpinBox
                if hasattr(w, "value"):
                    try:
                        return int(w.value())
                    except Exception:
                        pass
        return int(default)

    
    def iniciar_proceso(self):
        if self.Selector == 0:
            self.medir_ut_y_mostrar_promedio()
            
            
        elif self.Selector == 1:
            self.medir_ut_y_mostrar_promedio()
        
            
                

    def medir_ut_y_mostrar_promedio(self):
        """
        Mide SOLO con UT61E+ usando DMM/UT61ePlus/dual_read_v3.run_dual,
        calcula el promedio y lo muestra en el QTextEdit 'consola'.
        """
        try:
            # 1) Cantidad de mediciones robusta
            cant_mediciones = self._get_cant_mediciones(default=10)
            intervalo_s = 1.0
    
            # 2) Import del módulo (ruta a 'src' por si no estás lanzando como paquete)
            import sys, os
            sys.path.append(r"C:\Users\setup\OneDrive\Desktop\otros\UTN\ProyectoMedidasII\src")
            from DMM.UT61ePlus.dual_read_v3 import run_dual
    
            # 3) Ejecutar medición
            self.consola.setText("Midiendo con UT61E+...")
            UT_VEC, UT_UNITS = run_dual(reads=cant_mediciones, interval=intervalo_s)  # tu run_dual devuelve (UT_VEC, UT_UNITS) en mi versión; si en la tuya devuelve 4, ajusta abajo
    
            # Si tu run_dual devuelve 4 elementos (KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS), descomenta:
            # _, _, UT_VEC, UT_UNITS = run_dual(reads=cant_mediciones, interval=intervalo_s)
    
            # 4) Promedio seguro
            def _to_float(x):
                try:
                    return float(str(x).replace(",", "."))
                except Exception:
                    return float("nan")
    
            valores = [_to_float(v) for v in UT_VEC if str(v).strip()]
            unidad  = (UT_UNITS[0] if UT_UNITS else "").strip()
    
            if not valores:
                self.consola.setText("[UT61E+] No se obtuvieron valores válidos.")
                return
    
            prom = sum(valores) / len(valores)
            self.consola.setText(
                f"[UT61E+] Mediciones: {len(valores)}\n"
                f"[UT61E+] Promedio: {prom:.6f} {unidad}\n"                
            )
    
        except ModuleNotFoundError as e:
            self.consola.setText(
                "No se pudo importar DMM/UT61ePlus/dual_read_v3.py\n"
                "Asegurate de instalar 'hidapi' en el MISMO entorno y que la ruta a 'src' esté en sys.path.\n"
                f"Detalle: {e}"
            )
        except Exception as e:
            self.consola.setText(f"Error en la medición UT61E+: {e}")

                                    
    
    def calculo_TBM(self):
        pass
    
    def obtener_k_95(Vef):
        # Tabla de k (95%) de Student
        k_table = {
            1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57,
            6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23,
            11: 2.20, 12: 2.18, 13: 2.16, 14: 2.14, 15: 2.13,
            16: 2.12, 17: 2.11, 18: 2.10, 19: 2.09, 20: 2.09,
            25: 2.06, 30: 2.04
            }    
        
        if Vef >= 30:  
            # Cuando Vef >= 30 se usa aproximadamente k=2
            return 2.0
        else:
            # Buscar el valor más cercano en la tabla
            grados = min(k_table.keys(), key=lambda x: abs(x - int(round(Vef))))
            return k_table[grados]

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
