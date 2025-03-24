import socket
import threading
import json
import random

# Configuration du serveur
HOST = "0.0.0.0"  
PORT = 5555  
clients = []
deck = [f"{v}{c}" for v in "23456789TJQKA" for c in "CKTP"]  # Cartes disponibles
current_turn = 0  # Index of the current player's turn
played_cards = []  # Cards played on the table
MAX_PLAYERS = 2  # Nombre maximum de joueurs

def broadcast(message):
    """ Envoie un message à tous les joueurs """
    for client in clients:
        client.sendall(message.encode())

def validate_move(card, last_card):
    """ Valide si le coup est valide """
    # Exemple simple : la carte doit être plus forte que la dernière carte jouée
    values = "23456789TJQKA"
    return values.index(card[0]) > values.index(last_card[0])

def notify_turn():
    """ Notifie les joueurs du tour actuel """
    for i, client in enumerate(clients):
        if i == current_turn:
            client.sendall(json.dumps({"turn": True}).encode())
        else:
            client.sendall(json.dumps({"turn": False}).encode())

def distribute_cards():
    """ Distribue toutes les cartes entre les joueurs """
    random.shuffle(deck)
    hands = [deck[i::len(clients)] for i in range(len(clients))]  # Répartir toutes les cartes entre les joueurs
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

    global current_turn, played_cards

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break

            data = json.loads(msg)
            if "play_card" in data:
                card = data["play_card"]
                if clients[current_turn] == client:
                    if not played_cards or validate_move(card, played_cards[-1]):
                        played_cards.append(card)
                        broadcast(json.dumps({"played_card": card, "player": addr[1]}))  # Diffuser la carte jouée
                        current_turn = (current_turn + 1) % len(clients)
                        notify_turn()
                    else:
                        client.sendall(json.dumps({"error": "Invalid move"}).encode())
                else:
                    client.sendall(json.dumps({"error": "Not your turn"}).encode())
            print(f"Message reçu de {addr}: {msg}")
            broadcast(msg)
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
