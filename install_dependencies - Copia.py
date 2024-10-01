import os
import subprocess
import sys

# Função para instalar pacotes do requirements.txt
def instalar_dependencias():
    try:
        # Verifica se o pip está instalado
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        # Instala os pacotes listados no requirements.txt
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependências instaladas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")

if __name__ == "__main__":
    instalar_dependencias()
