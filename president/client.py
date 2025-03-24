import pygame
import socket
import threading
import json
import os

# Configuration du client
HOST = "127.0.0.1"  
PORT = 5555  
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Initialisation de Pygame
pygame.init()
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Président - Jeu Multijoueur")

# Couleurs
WHITE = (255, 255, 255)

# Charger les images des cartes
# Charger les images des cartes
CARD_WIDTH, CARD_HEIGHT = 100, 150  # Taille des cartes
card_images = {}

# Charger les images depuis le dossier "assets/cards/" contenant des fichiers PNG
card_folder = "assets/png"  # Dossier contenant les fichiers PNG
for filename in os.listdir(card_folder):
    if filename.endswith(".png"):  # Charger uniquement les fichiers PNG
        card_name = filename[:-4]  # Supprime le .png
        path = os.path.join(card_folder, filename)
        try:
            # Charger l'image
            card_image = pygame.image.load(path).convert_alpha()
            
            # Créer une surface avec un fond blanc
            card_surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            card_surface.fill(WHITE)
            
            # Dessiner l'image de la carte sur la surface avec le fond blanc
            card_surface.blit(pygame.transform.scale(card_image, (CARD_WIDTH, CARD_HEIGHT)), (0, 0))
            
            # Ajouter la carte avec fond blanc au dictionnaire
            card_images[card_name] = card_surface
        except Exception as e:
            print(f"Erreur lors du chargement de {filename}: {e}")
            
# Variables du jeu
hand = []  # Main du joueur
selected_card = None  # Carte sélectionnée par le joueur
is_my_turn = False  # Indique si c'est le tour du joueur

def receive_data():
    """ Réception des données du serveur """
    global hand, is_my_turn
    while True:
        try:
            data = client.recv(1024).decode()
            if data:
                msg = json.loads(data)
                if "hand" in msg:
                    hand = msg["hand"]
                    print("Cartes reçues:", hand)
                if "turn" in msg:
                    is_my_turn = msg["turn"]
        except Exception as e:
            print(f"Erreur dans receive_data: {e}")
            break

# Lancer le thread de réception
threading.Thread(target=receive_data, daemon=True).start()

def draw_turn_message():
    """ Affiche un message indiquant le tour """
    font = pygame.font.Font(None, 36)
    if is_my_turn:
        text = font.render("C'est à vous de jouer", True, (0, 255, 0))
    else:
        text = font.render("Au tour de l'adversaire", True, (255, 0, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

def draw_cards():
    """ Affiche les cartes du joueur """
    screen.fill(WHITE)
    draw_turn_message()  # Afficher le message de tour
    y = HEIGHT - CARD_HEIGHT - 20  # Ajuster la position verticale des cartes
    if len(hand) > 0:  # Vérifie que la main n'est pas vide
        spacing = min((WIDTH - 100) // len(hand), CARD_WIDTH + 10)  # Calculer l'espacement pour que toutes les cartes tiennent
        for i, card in enumerate(hand):
            x = 50 + i * spacing  # Espacement dynamique
            if card in card_images:
                screen.blit(card_images[card], (x, y))
                if selected_card == card:
                    pygame.draw.rect(screen, (0, 255, 0), (x, y, CARD_WIDTH, CARD_HEIGHT), 3)
            else:
                print(f"Carte non trouvée dans card_images: {card}")
    pygame.display.flip()

def send_card(card):
    """ Envoie une carte jouée au serveur """
    client.sendall(json.dumps({"play_card": card}).encode())

running = True
while running:
    draw_cards()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            for i, card in enumerate(hand):
                card_x = 50 + i * (CARD_WIDTH + 10)
                if card_x <= x <= card_x + CARD_WIDTH and HEIGHT - 180 <= y <= HEIGHT - 180 + CARD_HEIGHT:
                    selected_card = card
                    send_card(card)
                    break

pygame.quit()
client.close()
