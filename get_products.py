import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.jumbo.com.ar"


def parse_price(price_str):
    """
    Recibe un string de precio (ej.: "$1.181.499,15") y lo convierte a float.
    Se remueven el símbolo "$" y los separadores de miles.
    """
    price_str = price_str.replace("$", "").replace(" ", "")
    price_str = price_str.replace(".", "")
    price_str = price_str.replace(",", ".")
    try:
        return float(price_str)
    except ValueError:
        return 0.0


def ensure_page_loaded(driver, wait, url):
    """
    Verifica si la página cargó correctamente comprobando la existencia
    del div con id "Wpndialogcontainer". Si no aparece, se recarga la página
    hasta 3 veces. Retorna True si se logra cargar, o False en caso contrario.
    """
    attempts = 0
    while attempts < 3:
        try:
            # Espera hasta 5 segundos a que aparezca el elemento
            wait.until(EC.presence_of_element_located((By.ID, "Wpndialogcontainer")))
            # Si se encontró el elemento, se considera que la página cargó correctamente.
            return True
        except Exception:
            attempts += 1
            print(
                f"La página {url} no se cargó correctamente. Reintentando ({attempts}/3)..."
            )
            driver.refresh()
            time.sleep(2)
    return False


def extract_products_from_page(driver, wait):
    products = []
    # Espera breve para asegurar que la página cargue los productos
    time.sleep(2)
    # Localizar todos los productos en la página
    product_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "div.vtex-search-result-3-x-galleryItem.vtex-search-result-3-x-galleryItem--normal.vtex-search-result-3-x-galleryItem--grid.pa4",
    )
    print(f"Encontrados {len(product_elements)} productos en la página")
    for product in product_elements:
        try:
            # Extraer el nombre del producto desde el <h2>
            h2_element = product.find_element(By.TAG_NAME, "h2")
            product_name = h2_element.text.strip()

            # Extraer la URL del producto (del primer <a> que encuentre)
            a_element = product.find_element(By.TAG_NAME, "a")
            product_url = a_element.get_attribute("href").strip()

            # Extraer información de precios
            price_boxes = product.find_elements(
                By.CSS_SELECTOR,
                "div.vtex-flex-layout-0-x-flexColChild.vtex-flex-layout-0-x-flexColChild--shelf-main-price-box.pb0",
            )
            if not price_boxes:
                print("No se encontró el price box en el producto:", product_name)
                continue
            price_box = price_boxes[0]
            # Obtener el elemento <span> y solo sus hijos directos <div>
            price_span = price_box.find_element(By.TAG_NAME, "span")
            child_divs = price_span.find_elements(By.XPATH, "./div")

            if len(child_divs) == 1:
                # Sin descuento: el único div es el precio de lista
                price_text = child_divs[0].text.strip()
                precio_final = parse_price(price_text)
                precio_lista = parse_price(price_text)
            elif len(child_divs) >= 2:
                # Con descuento: el primer div es el precio final (con descuento)
                discount_price_text = child_divs[0].text.strip()
                precio_final = parse_price(discount_price_text)
                # El precio de lista se encuentra en el div siguiente al <span>
                list_price_elem = price_span.find_element(
                    By.XPATH, "following-sibling::div"
                )
                list_price_text = list_price_elem.text.strip()
                precio_lista = parse_price(list_price_text)
            else:
                precio_final = 0.0
                precio_lista = 0.0

            # SKU no especificado en la extracción, se asigna un valor dummy
            sku = "SKU-DUMMY"

            product_data = {
                "nombre": product_name,
                "SKU": sku,
                "precio_lista": precio_lista,
                "precio_final": precio_final,
                "url": product_url,
            }
            products.append(product_data)
        except Exception as e:
            print("Error extrayendo producto:", e)
            continue
    return products


def save_products(all_products):
    """Guarda el diccionario all_products en products.json."""
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=4, ensure_ascii=False)
    print(
        "Se ha actualizado products.json con",
        len(all_products["productos"]),
        "productos.",
    )


def main():
    # Cargar el archivo categories.json generado previamente
    try:
        with open("categories.json", "r", encoding="utf-8") as f:
            categories_data = json.load(f)
    except Exception as e:
        print("Error al cargar categories.json:", e)
        return

    # Inicializar Selenium WebDriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)

    all_products = {"productos": []}

    try:
        # Iterar sobre cada categoría general
        for general in categories_data.get("categorias_generales", []):
            # Iterar sobre cada categoría secundaria
            for cat in general.get("categorias", []):
                subcategorias = cat.get("subcategorias", [])
                if subcategorias:
                    for sub in subcategorias:
                        sub_url = sub.get("url")
                        print(
                            f"Accediendo a subcategoría: {sub.get('nombre')} | URL: {sub_url}"
                        )
                        driver.get(sub_url)
                        time.sleep(2)  # Esperar carga inicial de la página

                        # Verificar que la página cargó correctamente
                        if not ensure_page_loaded(driver, wait, sub_url):
                            print(
                                f"No se pudo cargar correctamente la subcategoría: {sub.get('nombre')}. Se pasa al siguiente."
                            )
                            continue

                        products = extract_products_from_page(driver, wait)
                        all_products["productos"].extend(products)
                        # Guardado incremental
                        save_products(all_products)
                else:
                    # Si no hay subcategorías, procesar la URL de la categoría secundaria
                    cat_url = cat.get("url")
                    print(
                        f"Accediendo a categoría sin subcategorías: {cat.get('nombre')} | URL: {cat_url}"
                    )
                    driver.get(cat_url)
                    time.sleep(2)

                    if not ensure_page_loaded(driver, wait, cat_url):
                        print(
                            f"No se pudo cargar correctamente la categoría: {cat.get('nombre')}. Se pasa al siguiente."
                        )
                        continue

                    products = extract_products_from_page(driver, wait)
                    all_products["productos"].extend(products)
                    save_products(all_products)

        print("Extracción de productos completada.")
    except Exception as e:
        print("Error durante la extracción de productos:", e)
    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()
