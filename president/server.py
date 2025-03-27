import socket
import threading
import json
import random

# Configuration du serveur
HOST = "127.0.0.1"  
PORT = 5555  
clients = []
deck = [f"{v}{c}" for v in "23456789TJQKA" for c in "CKTP"]  # Cartes disponibles
current_turn = 0  # Index of the current player's turn
played_cards = []  # Cards played on the table
MAX_PLAYERS = 2  # Nombre maximum de joueurs
passes = []  # Déplacer l'initialisation des passes ici, au niveau global
cards_played_by_value = {}  # Dictionnaire pour compter les cartes jouées par valeur

def broadcast(message):
    """ Envoie un message à tous les joueurs """
    for client in clients:
        client.sendall(message.encode())

def validate_move(cards, last_cards):
    """ Valide si le coup est valide et renvoie un tuple (valide, message) """
    # Toutes les cartes doivent avoir la même valeur
    if len(set(card[0] for card in cards)) != 1:
        return False, "Vous devez jouer des cartes de même valeur !"
        
    # Si aucune carte n'a été jouée, le coup est valide
    if not last_cards:
        return True, ""
        
    # Le nombre de cartes jouées doit correspondre au dernier coup
    if len(cards) != len(last_cards):
        return False, f"Vous devez jouer {len(last_cards)} carte(s) !"
        
    # La valeur des cartes doit être supérieure à la dernière carte jouée
    values = "3456789TJQKA2"  # "2" est la carte la plus forte
    if values.index(cards[0][0]) < values.index(last_cards[0][0]) and cards[0][0] != "2":
        return False, "Vous devez jouer une carte plus forte que la précédente !"
        
    return True, ""

def notify_turn():
    """ Notifie les joueurs du tour actuel """
    for i, client in enumerate(clients):
        if i == current_turn:
            client.sendall(json.dumps({"turn": True}).encode())
        else:
            client.sendall(json.dumps({"turn": False}).encode())

def check_winner():
    """ Vérifie si un joueur a gagné """
    for i, client in enumerate(clients):
        if not hands[i]:  # Si la main d'un joueur est vide
            broadcast(json.dumps({"winner": i}))  # Notifier tous les joueurs du gagnant
            print(f"Le joueur {i} a gagné !")  # Message pour le débogage
            return True
    return False

def distribute_cards():
    """ Distribue toutes les cartes entre les joueurs """
    global hands, passes, cards_played_by_value  # Ajouter cards_played_by_value
    random.shuffle(deck)
    hands = [deck[i::len(clients)] for i in range(len(clients))]  # Répartir toutes les cartes entre les joueurs
    passes = [False] * len(clients)  # Initialiser les passes pour tous les joueurs
    cards_played_by_value = {}  # Initialiser le compteur de cartes par valeur
    
    for i, client in enumerate(clients):
        client.sendall(json.dumps({"hand": hands[i]}).encode())
    global current_turn
    current_turn = random.randint(0, len(clients) - 1)  # Choisir un joueur aléatoire pour commencer
    print(f"Le joueur {current_turn} commence.")  # Ajout d'un message pour le débogage
    notify_turn()

def handle_client(client, addr):
    """ Gère un joueur connecté """
    print(f"Connexion de {addr}")
    clients.append(client)

    # Envoyer l'ID du joueur au client
    player_id = len(clients) - 1  # L'ID du joueur est basé sur l'ordre de connexion
    client.sendall(json.dumps({"player_id": player_id}).encode())

    if len(clients) == MAX_PLAYERS:
        print("Tous les joueurs sont connectés. Distribution des cartes...")
        distribute_cards()

    global current_turn, played_cards, hands, passes, cards_played_by_value  # Ajouter cards_played_by_value

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break

            data = json.loads(msg)
            if "play_cards" in data:
                cards = data["play_cards"]
                if clients[current_turn] == client:
                    valid_move, error_msg = validate_move(cards, played_cards[-1] if played_cards else [])
                    if valid_move:
                        played_cards.append(cards)
                        reset_game = False
                        
                        for card in cards:
                            hands[current_turn].remove(card)  # Retirer les cartes jouées de la main
                            
                            # Compter les cartes jouées par valeur
                            card_value = card[0]
                            cards_played_by_value.setdefault(card_value, 0)
                            cards_played_by_value[card_value] += 1
                            
                            # Vérifier si 4 cartes de cette valeur ont été jouées
                            if cards_played_by_value.get(card_value) == 4:
                                reset_game = True
                                print(f"4 cartes {card_value} ont été jouées. Réinitialisation du jeu.")
                                
                        broadcast(json.dumps({"played_cards": cards, "player": addr[1]}))  # Diffuser les cartes jouées
                        
                        if check_winner():  # Vérifier si un joueur a gagné
                            return  # Arrêter la gestion du client si le jeu est terminé
                            
                        if reset_game or cards[0][0] == "2":  # Si un "2" est joué ou 4 cartes identiques
                            played_cards = []  # Réinitialiser les cartes jouées
                            cards_played_by_value = {}  # Réinitialiser le compteur de cartes
                            broadcast(json.dumps({"reset": True}))  # Notifier les clients de la réinitialisation
                            current_turn = clients.index(client)  # Le joueur qui a joué commence
                            notify_turn()
                        else:
                            passes = [False] * len(clients)  # Réinitialiser les passes
                            current_turn = (current_turn + 1) % len(clients)
                            notify_turn()
                    else:
                        client.sendall(json.dumps({"error": error_msg}).encode())
                else:
                    client.sendall(json.dumps({"error": "Ce n'est pas votre tour de jouer !"}).encode())
            elif "pass" in data:
                if clients[current_turn] == client:
                    passes[current_turn] = True
                    client.sendall(json.dumps({"error": "Vous avez passé votre tour."}).encode())  # Message de confirmation
                    print(f"Player {current_turn} passed. Passes status: {passes}")  # Debug info
                    current_turn = (current_turn + 1) % len(clients)
                    if all(passes):  # Si tous les joueurs ont passé
                        played_cards = []  # Réinitialiser les cartes jouées
                        cards_played_by_value = {}  # Réinitialiser le compteur de cartes
                        broadcast(json.dumps({"reset": True}))  # Notifier les clients de la réinitialisation
                        passes = [False] * len(clients)  # Réinitialiser les passes
                        print("All players passed. Game reset. Next player:", current_turn)  # Debug info
                    notify_turn()  # Notifier les joueurs du nouveau tour
                else:
                    client.sendall(json.dumps({"error": "Ce n'est pas votre tour de jouer !"}).encode())
            print(f"Message reçu de {addr}: {msg}")
        except:
            break

    print(f"Déconnexion de {addr}")
    clients.remove(client)
    client.close()

def start_server():
    """ Lance le serveur """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_PLAYERS)
    print(f"Serveur en écoute sur {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client, addr)).start()

if __name__ == "__main__":
    start_server()
