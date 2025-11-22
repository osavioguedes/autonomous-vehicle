"""
Sistema Central de Gestão da Mina
Ponto de entrada para interface gráfica
"""

import sys
from src.central.mine_management import main

if __name__ == "__main__":
    print("="*70)
    print("SISTEMA CENTRAL DE GESTÃO DA MINA".center(70))
    print("="*70)
    print("\nIniciando interface gráfica...\n")
    
    main()
