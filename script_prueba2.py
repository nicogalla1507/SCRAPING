import requests
from bs4 import BeautifulSoup

url_base = f"https://taranto.specparts.shop/products?page=1"
lista_valores_marca = []
response = requests.get(url_base)
if response.status_code == 200:
    print("EXITO")
    sopa  = BeautifulSoup(response.text,"html.parser")
    
        