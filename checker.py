import re
import os
import shutil

# Checar Estrutura de Pastas (Somente pasta Clientes por Enquanto)
current_dir = os.getcwd()
files = os.listdir(current_dir)
excluded_dirs = ['AAA --- NAO CLIENTE', 'AAA ---- CONSULTAS', "checker.py", ".DS_Store", ".checker.py.swp"]
filtered_files = [file for file in files if file not in excluded_dirs]
file_array = filtered_files
pattern = r'\(\d+\)$'

# Folder Size:
# Checar se há arquivos muito grande dentro das pastas 
folder_sizes = {}
for folder in file_array:
    folder_path = os.path.join(current_dir, folder)
    if os.path.isdir(folder_path):
        folder_size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                folder_size += os.path.getsize(file_path)
        folder_sizes[folder] = int(folder_size / (1024 * 1024))  # Convert bytes to megabytes without decimals

#print("Dez Maiores Pastas - Atenção:")
#sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)
#for folder, size in sorted_folders[:10]:
#    print(f"{folder}: {size} MegaBytes")

# Modelos Replacer  
source_folder = './AAA --- NAO CLIENTE/ZMODELOS'
destination_folder = './AAA --- NAO CLIENTE/MODELOST'
# Get the list of files and folders in the source folder
files = os.listdir(source_folder)

# Iterate over each file/folder and copy it to the destination folder
for file in files:
    print(file)
    source_path = os.path.join(source_folder, file)
    destination_path = os.path.join(destination_folder, file)
    
    # Check if it's a directory
    if os.path.isdir(source_path):
        shutil.copytree(source_path, destination_path)
    else:
        shutil.copy2(source_path, destination_path)

print("Files and folders copied successfully!")







def check(pattern, lines):
    for line in lines:
        matches = re.findall(pattern, line)
        if not matches:
            print(line.strip())

print("Pastas em Desconformidade (Clientes): ")
check(pattern, file_array)

