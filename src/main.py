# -*- coding: utf-8 -*-
import sys
import time
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
        # VARIABLES
        # CONEXION DE BOTONES
            
            
    def scanport(self):
        print("Escanear puerto serie") 
       
    def conectarport(self):
        print("Conectar puerto serie")
"""
Created on Sun Aug 17 17:29:13 2025

@author: Joaquin Cieri
"""
