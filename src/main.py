# -*- coding: utf-8 -*-
import sys
import time
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
        self.proceso.setEnabled(False)
        
        # VARIABLES
        
        self.flag = 0
        self.flag1 = 0
        self.flag2 = 0
        
        # CONEXION DE BOTONES
        self.scan_port.clicked.connect(self.scanport)
        self.conectar.clicked.connect(self.conectarport)    
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
        
    def conectarport(self):
        print("Conectar puerto serie")
        port = self.Combobox.currentText()
        
        baudrate = 115200
        self.ard = serial.Serial(port=port, baudrate=baudrate)
        self.etiqueta.setText("Puerto conectado a: " + port)
        self.conectar.setEnabled(False)
        self.proceso.setEnabled(True)
        self.flag2 = 1
        self.cerrar_port.setEnabled(True)
        self.flag1 = 1
        #self.etiqueta.setText('Puerto NO conectado')
        
    def salir(self):
        self.close()
        
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
