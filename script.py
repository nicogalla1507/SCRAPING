import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import pytesseract
import pandas as pd

class Autos:
    def __init__(self, base_url):  
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://taranto.specparts.shop/'  # Agregar el encabezado Referer
        })

    def conectar_pagina(self, pagina): 
        url = f"{self.base_url}{pagina}"  
        try:
            self.response = self.session.get(url)  
            self.response.raise_for_status()  
            print(f"Conexión exitosa a la página {pagina}.")
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con la página {pagina}: {e}")

    def parsear(self):
        if self.response.status_code == 200:
            self.sopa = BeautifulSoup(self.response.text, "html.parser")
        else:
            print("No se puede parsear, conexión no exitosa.")

    def buscar_datos(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Nico\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        
        lista_datos = []
        try:
            tipo_producto = self.sopa.find_all('h6', class_="p-1 fw-bold")
            codigo = self.sopa.find_all('h6', class_="p-2 color-theme fw-bold")
            
            if tipo_producto and codigo:
                print("Datos encontrados")
                
                for t, c in zip(tipo_producto, codigo):
                    datos_producto = {
                        'TIPO PRODUCTO': t.text.strip(),
                        'CODIGO': c.text.strip(),
                        'APLICACIONES': []  
                    }
                    
                    lista_datos.append(datos_producto)

                print("Datos procesados:", lista_datos)
                return lista_datos
            else:
                print("No se encontraron productos o códigos.")
                return None
                
        except AttributeError as e:
            print(f"Error al buscar datos en la página: {e}")
            return None

    def extraer_imagen(self, lista_datos):
        imagenes = self.sopa.find_all('div', class_="spec")
        if imagenes:
            for datos_producto in lista_datos:
                for img in imagenes:
                    imagen = img.find('img', class_="mw-100")
                    if imagen:
                        href = imagen.get('src')
                        if href:
                            try:
                                # Descargar la imagen con los headers necesarios para evitar el error 403
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                    'Referer': 'https://taranto.specparts.shop/'  # Referer para que el servidor permita la descarga
                                }
                                img_respuesta = self.session.get(href, headers=headers)
                                
                                if img_respuesta.status_code == 200:
                                    imagen2 = Image.open(BytesIO(img_respuesta.content))
                                    
                                    # Extraer texto de la imagen utilizando OCR
                                    texto = pytesseract.image_to_string(imagen2)
                                    print(f"Texto extraído de la imagen para el código {datos_producto['CODIGO']}: {texto}")
                                    
                                    aplicaciones = texto.split('\n')
                                    
                                    # Agregar todas las aplicaciones encontradas al producto
                                    datos_producto['APLICACIONES'].extend([app.strip() for app in aplicaciones if app.strip()])
                                    
                                    imagen2.close()
                                else:
                                    print(f"No se pudo descargar la imagen. Código de estado: {img_respuesta.status_code}")
                            except Exception as e:
                                print(f"Error al procesar la imagen: {e}")
        else:
            print("No se encontraron imágenes en la página.")

    def generar_df(self, lista_datos):
        datos_expandidos = []
        
        for producto in lista_datos:
            for aplicacion in producto['APLICACIONES']:
                datos_expandidos.append({
                    'TIPO PRODUCTO': producto['TIPO PRODUCTO'],
                    'CODIGO': producto['CODIGO'],
                    'APLICACION': aplicacion
                })
                
        return pd.DataFrame(datos_expandidos)

def main():
    base_url = "https://taranto.specparts.shop/products?page="
    auto = Autos(base_url)
    
    datos_totales = []
    
    for pagina in range(1, 49):  
        auto.conectar_pagina(pagina)
        auto.parsear()
        
        lista_datos = auto.buscar_datos()  
        if lista_datos:
            auto.extraer_imagen(lista_datos)
            datos_totales.extend(lista_datos)  

    # Crear el DataFrame con todos los datos extraídos
    df = auto.generar_df(datos_totales)
    print(df)

    # Exportar el DataFrame a un archivo Excel
    df.to_excel("productos_aplicaciones.xlsx", index=False)

main()
