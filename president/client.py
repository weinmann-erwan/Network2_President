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
player_id = None  # ID du joueur

# Variable pour stocker la dernière carte jouée
last_played_card = None

def receive_data():
    """ Réception des données du serveur """
    global hand, is_my_turn, player_id, last_played_card
    buffer = ""  # Tampon pour accumuler les données reçues
    while True:
        try:
            data = client.recv(1024).decode()
            if data:
                buffer += data  # Ajouter les nouvelles données au tampon
                while True:
                    try:
                        # Tenter de décoder un message JSON complet
                        msg, index = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[index:]  # Supprimer le message traité du tampon
                        
                        # Traiter le message JSON
                        if "hand" in msg:
                            hand = msg["hand"]
                            print("Cartes reçues:", hand)
                        if "turn" in msg:
                            is_my_turn = msg["turn"]
                            print(f"Tour mis à jour : {is_my_turn}")
                        if "player_id" in msg:
                            player_id = msg["player_id"]
                            print(f"ID du joueur reçu : {player_id}")
                        if "played_card" in msg:
                            last_played_card = msg["played_card"]
                            print(f"Dernière carte jouée : {last_played_card}")
                            # Supprimer la carte jouée de la main si elle appartient au joueur
                            if last_played_card in hand:
                                hand.remove(last_played_card)
                    except json.JSONDecodeError:
                        # Si le message JSON n'est pas complet, attendre plus de données
                        break
        except Exception as e:
            print(f"Erreur dans receive_data: {e}")
            break

# Lancer le thread de réception
threading.Thread(target=receive_data, daemon=True).start()

def draw_turn_message():
    """ Affiche un message indiquant le tour et l'ID du joueur """
    font = pygame.font.Font(None, 36)
    if player_id is None:
        text = font.render("En attente de l'ID du joueur...", True, (255, 255, 0))
    elif is_my_turn:
        text = font.render(f"Joueur {player_id}: C'est à vous de jouer", True, (0, 255, 0))
    else:
        text = font.render(f"Joueur {player_id}: Au tour de l'adversaire", True, (255, 0, 0))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

def draw_last_played_card():
    """ Affiche la dernière carte jouée au centre du plateau """
    if last_played_card and last_played_card in card_images:
        x = WIDTH // 2 - CARD_WIDTH // 2
        y = HEIGHT // 2 - CARD_HEIGHT // 2
        screen.blit(card_images[last_played_card], (x, y))
        font = pygame.font.Font(None, 36)
        text = font.render("Dernière carte jouée", True, (0, 0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y - 40))

def draw_cards():
    """ Affiche les cartes du joueur """
    screen.fill(WHITE)
    draw_turn_message()  # Afficher le message de tour
    draw_last_played_card()  # Afficher la dernière carte jouée
    y = HEIGHT - CARD_HEIGHT - 20  # Ajuster la position verticale des cartes
    if len(hand) > 0:  # Vérifie que la main n'est pas vide
        spacing = min((WIDTH - 100) // len(hand), CARD_WIDTH + 10)  # Calculer l'espacement pour que toutes les cartes tiennent
        for i, card in enumerate(hand):
            x = 50 + i * spacing  # Espacement dynamique
            if card in card_images:
                screen.blit(card_images[card], (x, y))
                if i == selected_card_index:  # Dessiner un rectangle autour de la carte sélectionnée
                    pygame.draw.rect(screen, (0, 255, 0), (x, y, CARD_WIDTH, CARD_HEIGHT), 3)
            else:
                print(f"Carte non trouvée dans card_images: {card}")
    pygame.display.flip()


def send_card(card):
    """ Envoie une carte jouée au serveur """
    client.sendall(json.dumps({"play_card": card}).encode())


running = True
selected_card_index = 0  # Index de la carte sélectionnée

while running:
    if player_id is None:
        # Attendre que l'ID du joueur soit reçu
        pygame.time.delay(10)
        continue

    draw_cards()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                # Déplacer la sélection vers la gauche
                selected_card_index = (selected_card_index - 1) % len(hand)
                selected_card = hand[selected_card_index]
            elif event.key == pygame.K_RIGHT:
                # Déplacer la sélection vers la droite
                selected_card_index = (selected_card_index + 1) % len(hand)
                selected_card = hand[selected_card_index]
            elif event.key == pygame.K_RETURN:
                # Jouer la carte sélectionnée
                if selected_card:
                    send_card(selected_card)
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

pygame.quit()
client.close()
