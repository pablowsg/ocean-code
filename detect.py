import tkinter as tk
from ultralytics import YOLO
import cv2
import threading
import time
import pyttsx3  # Biblioteca para síntese de voz
from PIL import Image, ImageTk  # Biblioteca para manipulação de imagens
import requests  # Biblioteca para fazer requisições HTTP

# Inicializando o motor de síntese de voz (Inglês)
engine = pyttsx3.init()

# Configurando a voz para inglês (EN)
voices = engine.getProperty('voices')
for voice in voices:
    if "english" in voice.languages:  # Procura a voz em inglês
        engine.setProperty('voice', voice.id)
        break

# Dicionário global para manter as informações dos objetos detectados
objetos_detectados = {}
cache_detectados = {}  # Cache para evitar múltiplas contagens do mesmo objeto

# Tempo limite (em segundos) para recontar o mesmo objeto
TEMPO_LIMITE_RECONTAGEM = 2.0  # Ajuste conforme necessário

capturando = True  # Variável global para pausar/retomar detecção

# Função para consultar a API do Wikidata
def consultar_wikidata(nome_objeto):
    url = f"https://www.wikidata.org/w/rest.php/wikibase/v0/entities/search?search={nome_objeto}&language=en"
    response = requests.get(url)
    data = response.json()
    
    if 'search' in data and data['search']:
        item = data['search'][0]
        descricao = item.get('description', "No description available")
        uso = item.get('label', "No usage information available")
        return descricao, uso
    else:
        return "No description available", "No usage information available"

# Função que atualizará as informações na interface
def atualizar_info():
    for widget in frame_info.winfo_children():
        widget.destroy()  # Remove widgets anteriores

    # Exibe as informações armazenadas sobre os objetos detectados
    for obj, data in objetos_detectados.items():
        tk.Label(frame_info, text=f"Name: {obj}").pack()
        tk.Label(frame_info, text=f"What it is: {data['descricao']}").pack()
        tk.Label(frame_info, text=f"Purpose: {data['uso']}").pack()
        tk.Label(frame_info, text=f"Quantity: {data['quantidade']}").pack()
        tk.Label(frame_info, text="---").pack()

    # Exibe o número total de objetos detectados
    total_objetos = sum(data['quantidade'] for data in objetos_detectados.values())
    tk.Label(frame_info, text=f"Total objects detected: {total_objetos}").pack()

# Função para narrar em inglês
def narrar(texto):
    engine.say(texto)
    engine.runAndWait()

# Função para detectar objetos e mostrar na interface
def detectar():
    global objetos_detectados, cache_detectados, capturando
    cap = cv2.VideoCapture(1)  # Use 1 para o dispositivo de webcam correto

    while True:
        if capturando:  # Pausar a detecção se capturando for False
            ret, frame = cap.read()
            if ret:
                # Reduz a resolução para aumentar o desempenho
                frame = cv2.resize(frame, (640, 480))
                results = modelo(frame)

                # Processa as detecções para obter nomes e contagens de objetos
                for result in results[0].boxes:
                    if result.conf > 0.5:  # Filtrar por confiança mínima
                        classe = modelo.names[int(result.cls)]  # Obtém o nome da classe

                        agora = time.time()
                        if classe not in cache_detectados or (agora - cache_detectados[classe]) > TEMPO_LIMITE_RECONTAGEM:
                            # Atualiza o cache com o timestamp da detecção
                            cache_detectados[classe] = agora

                            if classe not in objetos_detectados:
                                # Se for a primeira vez que o objeto é detectado
                                descricao, uso = consultar_wikidata(classe)
                                objetos_detectados[classe] = {
                                    "descricao": descricao,
                                    "uso": uso,
                                    "quantidade": 1
                                }
                                # Narra o novo objeto detectado em inglês
                                threading.Thread(target=narrar, args=(f"New object detected: {classe},",)).start()
                            else:
                                # Se o objeto já foi detectado anteriormente, incrementa a contagem
                                objetos_detectados[classe]["quantidade"] += 1
                                # Narra que o objeto foi detectado novamente em inglês
                                threading.Thread(target=narrar, args=(f"{classe} detected again. Total: {objetos_detectados[classe]['quantidade']}.",)).start()

                # Mostra o frame com as detecções na tela
                frame = results[0].plot()  # Desenha as predições na imagem
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converte a imagem de BGR para RGB
                img = Image.fromarray(frame)  # Converte a imagem do OpenCV para PIL
                img_tk = ImageTk.PhotoImage(img)  # Converte a imagem para o formato que o Tkinter pode usar

                # Atualiza o Label com a nova imagem
                label_video.imgtk = img_tk
                label_video.configure(image=img_tk)

            time.sleep(0.1)  # Adiciona um pequeno delay para evitar alta utilização da CPU

            if cv2.waitKey(1) == ord('q'):
                break  # Encerra a captura se 'q' for pressionado

    cap.release()  # Libera a webcam
    cv2.destroyAllWindows()  # Fecha as janelas do OpenCV

# Função para pausar/retomar a detecção
def pausar_deteccao():
    global capturando
    capturando = not capturando  # Alterna entre pausar e retomar
    botao_pausar.config(text="Resume" if not capturando else "Pause")

# Função para limpar as detecções
def limpar_deteccoes():
    global objetos_detectados
    objetos_detectados = {}
    atualizar_info()

# Configurando o modelo YOLO
modelo = YOLO('yolov8m.pt')

# Configuração da interface gráfica
janela = tk.Tk()
janela.title("Object Detection")
janela.config(bg="white")  # Tema claro por padrão

# Frame para mostrar as informações dos objetos detectados
frame_info = tk.Frame(janela, bg="white")
frame_info.pack(side=tk.LEFT, padx=10, pady=10)

# Frame para exibir a imagem da câmera
frame_video = tk.Frame(janela, bg="white")
frame_video.pack(side=tk.RIGHT, padx=10, pady=10)

label_video = tk.Label(frame_video)
label_video.pack()

# Botões de controle
frame_controles = tk.Frame(janela, bg="white")
frame_controles.pack(side=tk.BOTTOM, padx=10, pady=10)

botao_iniciar = tk.Button(frame_controles, text="Start Detection", command=lambda: threading.Thread(target=detectar, daemon=True).start())
botao_iniciar.pack(pady=5)

botao_pausar = tk.Button(frame_controles, text="Pause", command=pausar_deteccao)
botao_pausar.pack(pady=5)

botao_limpar = tk.Button(frame_controles, text="Clear", command=limpar_deteccoes)
botao_limpar.pack(pady=5)

# Inicia a interface gráfica
janela.mainloop()
