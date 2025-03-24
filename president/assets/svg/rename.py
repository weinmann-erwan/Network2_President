import os

# Obtient le chemin du dossier courant (où se trouve le script)
folder_path = os.getcwd()

# Mot à remplacer et son remplacement
old_word = "queen"
new_word = "Q"

# Parcours tous les fichiers du dossier
for filename in os.listdir(folder_path):
    print(filename)
    if filename.endswith(".svg") and old_word in filename:
        new_filename = filename.replace(old_word, new_word)
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_filename)
        
        os.rename(old_file, new_file)
        print(f'Renommé : {filename} -> {new_filename}')

print("Renommage terminé !")
