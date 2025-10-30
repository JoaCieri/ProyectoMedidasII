# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-
import sys
import time
import re
import os
import serial
import numpy as np
import statistics
import math
from decimal import Decimal

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
        #self.showMaximized()
        self.proceso.setEnabled(False)

        # VARIABLES (respetadas)
        self.muestras_I = None
        self.muestras_V = None
        self.cant_muestras = 0
        self.flag = 0
        self.flag1 = 0
        self.flag2 = 0
        self.flag3 = 0
        self.flag4 = 0
        self.selector = 1
        
        self.vector_V = np.array([], dtype=float)
        self.vector_I = np.array([], dtype=float)
        
        #PRUEBA        
        #self.vector_V = [21.985 , 21.985 , 21.985 , 21.985 , 21.985]
        #self.vector_I = [2.196e-3, 2.197e-3, 2.196e-3, 2.197e-3, 2.196e-3]
        
        # CONEXIÓN DE BOTONES 

        self.proceso.clicked.connect(self.iniciar_proceso)
        self.boton_medir.clicked.connect(self.medir_dos_y_mostrar_promedios)
        self.select_CBM.clicked.connect(self.CBM)
        self.select_TBM.clicked.connect(self.TBM)
        self.salir.clicked.connect(self.salir_ui)

    # ----------------------- Salida -----------------------
    
    def salir_ui(self):
        self.close()

    # --------------------- Selector modo -------------------
    def CBM(self):
        self.selector = 0
        self.proceso.setEnabled(True)
        try:
            self.cant_muestras = int(self.Combobox_3.currentText())
        except Exception:
            self.cant_muestras = 10
        self.consola.setText('Metodo CBM con Cantidad de muestras = ' + str(self.cant_muestras))

    def TBM(self):
        self.selector = 1
        self.proceso.setEnabled(True)
        try:
            self.cant_muestras = int(self.Combobox_3.currentText())
        except Exception:
            self.cant_muestras = 10
        self.consola.setText('Metodo TBM con Cantidad de muestras = ' + str(self.cant_muestras))


    # ----------------------- Prueba -----------------------
    def medir(self):
        """
        Lee ambos multímetros una sola vez y muestra las lecturas en la consola.
        Guarda los valores en self.vector_V y self.vector_I.
        """
        try:
            cant = self.cant_muestras   
            intervalo = 1.0

            SRC = os.path.abspath(os.path.join(os.path.dirname(__file__)))
            if SRC not in sys.path:
                sys.path.append(SRC)

            from DMM.UT61ePlus.dual_read_v4 import run_dual

            self.consola.setText("⏳ Midiendo...")

            KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS = run_dual(reads=cant, interval=intervalo)

            # Asumimos: UT61E+ = I, KEITHLEY = V
            N = min(len(UT_VEC), len(KEI_VEC))
            self.vector_I = np.array(UT_VEC[:N], dtype=float)
            self.vector_V = np.array(KEI_VEC[:N], dtype=float)

            # Imprimir resultados en consola
            texto = "📊 Mediciones realizadas:\n"
            for i in range(N):
                texto += f"{i+1:02d}) V = {self.vector_V[i]:.6f} V   |   I = {self.vector_I[i]:.6f} A\n"

            self.consola.setText(texto)

        except Exception as e:
            self.consola.setText(f"⚠ Error en medición: {e}")
    
    # ----------------------- Proceso -----------------------
    def iniciar_proceso(self):
        """
        Mantengo tu flujo por Selector, pero ambas ramas llaman
        a la medición dual para mostrar promedios.
        """
        self.medir_dos_y_mostrar_promedios()
        self.calculo()


    def medir_dos_y_mostrar_promedios(self):
        """
        Mide con UT61E+ y, si está disponible, con KEITHLEY 2110.
        Muestra los promedios en 'self.consola' usando setText.
        """
        try:
            cant = self.cant_muestras
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
            
            N = min(len(UT_VEC), len(KEI_VEC))  # por si difieren en longitud
            
            self.vector_I = np.array(UT_VEC[:N], dtype=float)
            self.vector_V = np.array(KEI_VEC[:N], dtype=float)

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
    def calculo(self):
        
        ra = 0.45   # resistencia del amperímetro (ohm)
        rv = 10e6   # resistencia del voltímetro (ohm)
        fuente_instru_v= 5e-2/math.sqrt(3) #[%]
        fuente_instru_i= 8e-2/math.sqrt(3) #[%]
        fuente_rv= 5 #[%]
        fuente_ra= 5 #[%]
        cuenta_v=5
        cuenta_i=20
        eps = 1e-12  # umbral numérico
        
        if self.selector == 0: #CBM
            media_i_cbm = statistics.mean(self.vector_I)
            entero_i_cbm = cuatro_dig_sig(media_i_cbm)         
            media_v_cbm = statistics.mean(self.vector_V)         
            media_r_cbm = media_v_cbm / media_i_cbm
            
            # Corrección por RA (voltímetro mide R+RA, amperímetro en serie)
            rcorr_cbm = media_r_cbm - ra
            
            if abs(1.0 - (ra/media_r_cbm)) < eps or abs(1.0 - (media_r_cbm/ra)) < eps:
                mensaje = "⚠️ CBM: Rm ≈ RA → sensibilidades enormes. Revisar configuración."
                print(mensaje)
                self.consola.setText(mensaje)
                raise ValueError(mensaje)
            
            # Desvíos (repetibilidad)
            desvio_i_cbm = statistics.stdev(self.vector_I)
            desvio_v_cbm = statistics.stdev(self.vector_V)
            
            rep_v_cbm = (desvio_v_cbm*100)/(math.sqrt(len(self.vector_V))*media_v_cbm)
            rep_i_cbm = (desvio_i_cbm*100)/(math.sqrt(len(self.vector_I))*media_i_cbm)
            
            entero_v_cbm = cuatro_dig_sig(media_v_cbm)

            cuenta_v_cbm = (cuenta_v*100)/(math.sqrt(3)*entero_v_cbm)
            cuenta_i_cbm = (cuenta_i*100)/(math.sqrt(3)*entero_i_cbm)  
            
            Coef_sens_vind_cbm = 1/(1-(ra/media_r_cbm))
            Coef_sens_iind_cbm = 1/((ra/media_r_cbm)-1)
            Coef_sens_ra_cbm = 1/(1-(media_r_cbm/ra))
            
            f_v_cbm       = pow(Coef_sens_vind_cbm*rep_v_cbm,2)
            f_ins_v_cbm   = pow(Coef_sens_vind_cbm*fuente_instru_v,2)
            f_cuenta_v_cbm= pow(Coef_sens_vind_cbm*cuenta_v_cbm,2)
            f_i_cbm       = pow(Coef_sens_iind_cbm*rep_i_cbm,2)
            f_ins_i_cbm   = pow(Coef_sens_iind_cbm*fuente_instru_i,2)
            f_cuenta_i_cbm= pow(Coef_sens_iind_cbm*cuenta_i_cbm,2)
            f_ra_cbm      = pow((fuente_ra*Coef_sens_ra_cbm)/math.sqrt(3),2)
                        
            Uc_cbm = math.sqrt(
                f_v_cbm + f_ins_v_cbm + f_cuenta_v_cbm +
                f_i_cbm + f_ins_i_cbm + f_cuenta_i_cbm +
                f_ra_cbm
            )
            
            Vef_cbm = pow(Uc_cbm,4)/((pow(f_v_cbm,2)/len(self.vector_V)) + (pow(f_i_cbm,2)/len(self.vector_I)))
            print("Vef= ", Vef_cbm)
            
            K_cbm = obtener_k_95(Vef_cbm)
            
            U_exp_cbm = K_cbm * Uc_cbm
            U_exp_abs = rcorr_cbm * U_exp_cbm / 100.0
        
            print(f"R: {rcorr_cbm} Ω ± {U_exp_abs} Ω  (±{U_exp_cbm} %)")
            self.consola.setText(f"R = {rcorr_cbm:.4f} Ω ± {U_exp_abs:.4f} Ω  (±{U_exp_cbm:.2f} %)")
            
            print("Media de I CBM =", media_i_cbm)
            print("recortado=", entero_i_cbm)
            print("Media de V CBM =", media_v_cbm)
            print("Media de R =", media_r_cbm)
            print("Entero V=", entero_v_cbm)            
            print("Cuenta V=", cuenta_v_cbm)
            print("Cuenta I=", cuenta_i_cbm)
            print("1=", f_v_cbm)
            print("2=", f_ins_v_cbm)
            print("3=", f_cuenta_v_cbm)
            print("4=", f_i_cbm)
            print("5=", f_ins_i_cbm)
            print("6=", f_cuenta_i_cbm)
            print("7=", f_ra_cbm)
            print("Uc =", Uc_cbm)
            
        elif self.selector == 1: #TBM
        
            media_i_tbm = statistics.mean(self.vector_I)
            entero_i = cuatro_dig_sig(media_i_tbm)
            media_v_tbm = statistics.mean(self.vector_V)
            
            media_r_tbm=media_v_tbm/media_i_tbm
            
            errorm_tbm = (-media_r_tbm)/rv
            rcorr_tbm=media_r_tbm/(1+errorm_tbm)
            
            desvio_i_tbm = statistics.stdev(self.vector_I)
            desvio_v_tbm = statistics.stdev(self.vector_V)
            
            if abs(1.0 - (media_r_tbm/rv)) < eps:
                mensaje = "⚠️ TBM: Rm ≈ Rv → sensibilidades enormes. Revisar configuración."
                print(mensaje)
                self.consola.setText(mensaje)
                raise ValueError(mensaje)
        
            rep_v_tbm = (desvio_v_tbm*100)/(math.sqrt(len(self.vector_V))*media_v_tbm)   
            rep_i_tbm = (desvio_i_tbm*100)/(math.sqrt(len(self.vector_I))*media_i_tbm) 
            
            entero_v = cuatro_dig_sig(media_v_tbm)
                    
            cuenta_v_tbm=(cuenta_v*100)/(math.sqrt(3)*entero_v) 
            cuenta_i_tbm=(cuenta_i*100)/(math.sqrt(3)*entero_i)
            
            Coef_sens_vind_tbm=1/(1-(media_r_tbm/rv))
            Coef_sens_iind_tbm=1/((media_r_tbm/rv)-1)
            Coef_sens_rv_tbm=1/(1-(rv/media_r_tbm))
            
            f_v=pow(Coef_sens_vind_tbm*rep_v_tbm,2)
            f_ins_v=pow(Coef_sens_vind_tbm*fuente_instru_v,2)
            f_cuenta_v=pow(Coef_sens_vind_tbm*cuenta_v_tbm,2)
            f_i=pow(Coef_sens_iind_tbm*rep_i_tbm,2)
            f_ins_i=pow(Coef_sens_iind_tbm*fuente_instru_i,2)
            f_cuenta_i=pow(Coef_sens_iind_tbm*cuenta_i_tbm,2)
            f_rv=pow((fuente_rv*Coef_sens_rv_tbm)/math.sqrt(3),2)            
            
            Uc= math.sqrt(f_v+f_ins_v+f_cuenta_v+f_i+f_ins_i+f_cuenta_i+f_rv)
            
            Vef = pow(Uc,4)/((pow(f_v, 2)/(len(self.vector_V)))+(pow(f_i, 2)/(len(self.vector_I))))             
            K_tbm = obtener_k_95(Vef)
            
            U_exp_tbm = K_tbm * Uc
            U_exp_abs = rcorr_tbm * U_exp_tbm / 100.0
        
            print(f"R: {rcorr_tbm} Ω ± {U_exp_abs} Ω  (±{U_exp_tbm} %)")
            self.consola.setText(f"R = {rcorr_tbm:.4f} Ω ± {U_exp_abs:.4f} Ω  (±{U_exp_tbm:.2f} %)")

            print("Media de I TBM =", media_i_tbm)
            print("recortado=", entero_i)
            print("Media de V TBM =", media_v_tbm)
            print("Media de R =", media_r_tbm)
            print("Entero V=", entero_v)
            print("Cuenta V=", cuenta_v_tbm)
            print("Cuenta I=", cuenta_i_tbm)   
            print("1=", f_v)
            print("2=", f_ins_v)
            print("3=", f_cuenta_v)
            print("4=", f_i)
            print("5=", f_ins_i)
            print("6=", f_cuenta_i)
            print("7=", f_rv)
            print("Uc =", Uc)
            print("Vef= ", Vef)
            
                        
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
    gl = max(1, int(round(Vef)))        # 👈 clamp a 1
    grados = min(k_table.keys(), key=lambda x: abs(x - gl))
    return k_table[grados]

def cuatro_dig_sig(x):
    s = f"{x:.15g}".replace(".", "").lstrip("0")
    return int((s[:4] or "1"))

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
