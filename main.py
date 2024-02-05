import argparse
import requests
from bs4 import BeautifulSoup
import sys
import time
from colorama import Fore, Style
from token_config import URL_TOKEN
import os
from static.banner import display_banner
import socks
import socket
from tqdm import tqdm
from tabulate import tabulate
import shutil


# Configure the socket to use Tor
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # 9050 is default Tor port
socket.socket = socks.socksocket

# Display banner on startup
banner_lines = display_banner()
for line in banner_lines:
    print(Fore.RED + line + Style.RESET_ALL)
    time.sleep(0.1)

# def get_terminal_width():
#     """Get the current width of the terminal."""
#     rows, columns = os.popen('stty size', 'r').read().split()
#     return int(columns)

def get_terminal_width():
    """Get the current width of the terminal."""
    # shutil.get_terminal_size() returns a tuple (columns, lines)
    columns, lines = shutil.get_terminal_size(fallback=(80, 20))
    return columns

def adjust_table_width(table_instance):
    """Ajuste la largeur du tableau en fonction de la largeur du terminal."""
    largeur_terminal = get_terminal_width()
    num_colonnes = len(table_instance[0])
    # Utilise colorama pour formater le texte de l'en-tête en gras
    format_en_tete = f"{Fore.GREEN}{Style.BRIGHT}{{:<{largeur_terminal}}}{Style.RESET_ALL}"
    # Ajoute une ligne supérieure du rectangle
    ligne_superieure = "+" + "-" * (largeur_terminal - 2) + "+"
    print(f"{Fore.GREEN}{ligne_superieure}{Style.RESET_ALL}")
    # Calcule la largeur maximale pour chaque colonne
    largeurs_max_colonnes = [max(len(str(row[i])) for row in table_instance) for i in range(num_colonnes)]
    # Définit une largeur minimale fixe
    largeur_colonne_fixe = 5
    # Ajuste la largeur de la colonne dynamiquement
    largeurs_colonnes_ajustees = [max(largeurs_max_colonnes[i], largeur_colonne_fixe) for i in range(num_colonnes)]
    # Crée une chaîne de format pour ajuster les largeurs des colonnes
    format_str = "|".join([f"{{:<{largeurs_colonnes_ajustees[i]}}}" for i in range(num_colonnes)])
    # Imprime le tableau avec les largeurs des colonnes ajustées et l'en-tête formaté en gras
    print(f"{Fore.GREEN}|{Style.RESET_ALL}{format_en_tete.format(format_str.format(*table_instance[0]))}", end="")
    # Ajoute une ligne inférieure du rectangle
    ligne_inferieure = "+" + "-" * (largeur_terminal - 3) + "+"
    print(f"{Fore.GREEN}{ligne_inferieure}{Style.RESET_ALL}")
    for row in table_instance[1:]:
        print(format_str.format(*row))



def pass_the_captcha():
    """Handles the CAPTCHA challenge for the given onion website."""
    url_index = "http://4wbwa6vcpvcr3vvf4qkhppgy56urmjcj2vagu2iqgp3z656xcmfdbiqd.onion/"
    req = requests.get(url_index, verify=False, proxies={'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'})
    soup = BeautifulSoup(req.text, "html.parser")
    get_captcha = soup.find('pre').text
    get_id = soup.find('input', {'name': 'id'}).get('value')
    print(get_captcha)

    captcha = input("Enter the captcha: ")
    url_captcha = "{}captcha".format(url_index)

    datas = {
        "captcha": captcha,
        "id": get_id
    }

    req_captcha = requests.post(url_captcha, verify=False, data=datas, proxies={'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'})
    with open("token_config.py", "w") as replace_token:
        replace_token.write("""URL_TOKEN = "{}" """.format(req_captcha.url.split("=")[-1]))
    main(req_captcha.url.split("=")[-1])

def main(URL_TOKEN, max_results=None):
    """Main function to scrape and display data from the onion website."""
    
    animation = "|/-\\"
    # Filter out parameters that are empty
    filtered_params = {key: value for key, value in params.items() if value}
    search_url = "http://4wbwa6vcpvcr3vvf4qkhppgy56urmjcj2vagu2iqgp3z656xcmfdbiqd.onion/search?" + "&".join(f"{key}={value}" for key, value in filtered_params.items())
    search_url += "&s={}&r=*any*&g=*any*".format(URL_TOKEN)
    
    # Use the Tor proxy for the request
    with requests.Session() as session:
        session.verify = False
        session.proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
        response = session.get(search_url, allow_redirects=True)

    soup = BeautifulSoup(response.content, 'html.parser')
    
    start_time = time.time()
    while True:
        for i in range(4):
            time.sleep(0.2)
            sys.stdout.write("\rSearching " + animation[i % len(animation)])
            sys.stdout.flush()

        print() 

        if time.time() - start_time > 0: 
            break
        
    # Handle CAPTCHA if presented
    if "fill" in response.text:
        # Use tqdm for the progress bar
        for _ in tqdm(range(10), desc="Processing before CAPTCHA", unit="step"):
            time.sleep(0.1)
        pass_the_captcha()
    else:
        table = soup.find('table')
        table = soup.find('table')
        if table:
            headers = [th.text.strip() for th in table.find_all('th')]
            data = []
            max_header_length = max(len(header.strip()) for header in headers)

            for row in table.find_all('tr')[1:]:
                row_data = [td.text.strip() for td in row.find_all('td')]
                data.append(row_data)
                if max_results is not None and len(data) >= max_results:
                    break

            table_instance = [headers] + data
            adjust_table_width(table_instance)
            print("\nDirect Link to Facebook profile:\n")
            for row in data:
                fb_url = f"https://www.facebook.com/profile.php?id={row[0]}"
                print(fb_url)
        else:
            print("\nNo results found.")


if __name__ == '__main__':
    # Parse arguments from the command line
    parser = argparse.ArgumentParser(description='Tool to search for information in a Facebook dump')
    parser.add_argument('-i', '--id', help='ID')
    parser.add_argument('-f', '--firstname', help='First name')
    parser.add_argument('-l', '--lastname', help='Last name')
    parser.add_argument('-t', '--phone', help='Phone number')
    parser.add_argument('-w', '--work', help='Work')
    parser.add_argument('-o', '--location', help='Location')
    parser.add_argument('-m', '--max-results', type=int, help='Maximum number of results to display')
    args = parser.parse_args()

    # Check if any arguments were provided
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    # Create a dictionary with all the provided search parameters
    params = {
        'i': args.id if args.id else '',
        'f': args.firstname if args.firstname else '',
        'l': args.lastname if args.lastname else '',
        't': args.phone if args.phone else '',
        'w': args.work if args.work else '',
        'o': args.location if args.location else ''
    }
    main(URL_TOKEN, max_results=args.max_results)
