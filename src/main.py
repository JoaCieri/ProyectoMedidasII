# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-
import sys
import time
import re
import os
import serial
import numpy as np

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from serial.tools import list_ports

print("Proyecto Medición de Resistencias - Grupo 1")

# ------------------ utilidades locales ------------------
def _to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return float("nan")


class Ui(QMainWindow):

    def __init__(self):
        super().__init__()
        uic.loadUi('Interfaz.ui', self)

        # PARÁMETROS DE LA INTERFAZ
        self.showMaximized()
        self.cerrar_port.setEnabled(False)
        self.cerrar_port_2.setEnabled(False)
        self.proceso.setEnabled(False)

        # VARIABLES (respetadas)
        self.muestras_I = None
        self.muestras_V = None
        self.flag = 0
        self.flag1 = 0
        self.flag2 = 0
        self.flag3 = 0
        self.flag4 = 0
        self.Selector = 1

        # CONEXIÓN DE BOTONES (respetada)
        self.scan_port.clicked.connect(self.scanport)
        self.conectar.clicked.connect(self.conectarport1)
        self.conectar_2.clicked.connect(self.conectarport2)
        self.proceso.clicked.connect(self.iniciar_proceso)
        self.select_CBM.clicked.connect(self.CBM)
        self.select_TBM.clicked.connect(self.TBM)
        self.salir.clicked.connect(self.salir_ui)

    # ----------------------- Puertos -----------------------
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
        self.flag2 = 1
        self.cerrar_port.setEnabled(True)
        self.flag1 = 1

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

    # --------------------- Selector modo -------------------
    def CBM(self):
        self.selector = 0
        self.proceso.setEnabled(True)
        self.select_TBM.setEnabled(False)
        try:
            cant_muestras = int(self.Combobox_3.currentText())
        except Exception:
            cant_muestras = 10
        self.consola.setText('Cantidad de muestras: ' + str(cant_muestras))

    def TBM(self):
        self.selector = 1
        self.proceso.setEnabled(True)
        self.select_CBM.setEnabled(False)
        try:
            cant_muestras = int(self.Combobox_3.currentText())
        except Exception:
            cant_muestras = 10
        self.consola.setText('Cantidad de muestras: ' + str(cant_muestras))

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

    # ----------------------- Proceso -----------------------
    def iniciar_proceso(self):
        """
        Mantengo tu flujo por Selector, pero ambas ramas llaman
        a la medición dual para mostrar promedios.
        """
        if self.Selector == 0:
            self.medir_dos_y_mostrar_promedios()
        elif self.Selector == 1:
            self.medir_dos_y_mostrar_promedios()

    def medir_dos_y_mostrar_promedios(self):
        """
        Mide con UT61E+ y, si está disponible, con KEITHLEY 2110.
        Muestra los promedios en 'self.consola' usando setText.
        """
        try:
            cant = self._get_cant_mediciones(10)
            intervalo = 1.0

            # importar runner dual (robusto: agrega src si hace falta)
            SRC = os.path.abspath(os.path.join(os.path.dirname(__file__)))
            if SRC not in sys.path:
                sys.path.append(SRC)

            # dual_read_v4 expone run_dual y funciones de promedio
            from DMM.UT61ePlus.dual_read_v4 import (
                run_dual, promedio_keithley, promedio_ut61e
            )

            self.consola.setText("⏳ Midiendo UT61E+ y KEITHLEY…")
            KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS = run_dual(reads=cant, interval=intervalo)

            # promedios
            p_kei = promedio_keithley()
            p_ut =  promedio_ut61e()
            u_kei = (KEI_UNITS[0] if KEI_UNITS else "V")
            u_ut  = (UT_UNITS[0]  if UT_UNITS  else "V")

            msg = (
                f"Mediciones: {cant}\n"
                f"[KEITHLEY] Promedio: {p_kei:.6f} {u_kei}   (N={len(KEI_VEC)})\n"
                f"[UT61E+]  Promedio: {p_ut:.6f} {u_ut}   (N={len(UT_VEC)})"
            )
            self.consola.setText(msg)

        except Exception as e:
            self.consola.setText(f"Error en medición dual: {e}")

    # ------------------- Tus funciones ---------------------
    def calculo_TBM(self):
        pass

    # (si tenías calculo_CBM aquí, lo dejamos igual)
    def calculo_CBM(self):
        pass


# ================== util fuera de la clase ==================
def obtener_k_95(Vef):
    # Tabla de k (95%) de Student (se conserva)
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
        # valor más cercano en la tabla
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
