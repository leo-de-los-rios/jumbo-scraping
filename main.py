import json
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.jumbo.com.ar"


def main():
    # Configuración del driver (se asume que chromedriver está en el PATH)
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)
    action = ActionChains(driver)

    data = {"categorias_generales": []}

    try:
        # Navegar a la página principal
        driver.get(BASE_URL)

        time.sleep(5)

        # Hacer clic en el div que despliega el menú de categorías principal
        category_div = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "div.vtex-menu-2-x-styledLinkContent.vtex-menu-2-x-styledLinkContent--header-category.flex.justify-between.nowrap",
                )
            )
        )
        category_div.click()

        # Esperar a que aparezca la sección del menú
        submenu_section = wait.until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "section.vtex-menu-2-x-submenu.vtex-menu-2-x-submenu--department-menu.w-100.flex.justify-center.flex-column",
                )
            )
        )

        # Obtener todos los elementos <li> de la sección
        li_elements = submenu_section.find_elements(By.TAG_NAME, "li")

        # Iterar desde el segundo <li> hasta el último
        for idx, li in enumerate(li_elements):
            if idx == 0:
                continue  # Saltamos el primer li

            if idx == 4:
                pass

            try:
                # Realizar mouse hover sobre el <li> para desplegar su contenido
                action.move_to_element(li).perform()
                time.sleep(1)  # Ajustar si es necesario

                # === Procesar el primer div (categoría general) ===
                divs_in_li = li.find_elements(By.TAG_NAME, "div")
                if not divs_in_li:
                    print(f"No se encontraron divs en el li número {idx}")
                    continue

                general_div = divs_in_li[0]
                categoria_nombre = general_div.text.strip()
                a_general = general_div.find_element(By.TAG_NAME, "a")
                href_reducido = a_general.get_attribute("href").strip()
                if href_reducido.startswith("/"):
                    href_completa = BASE_URL + href_reducido
                else:
                    href_completa = href_reducido

                # Se arma la categoría general con una lista vacía para "categorias"
                general_category = {
                    "nombre": categoria_nombre,
                    "url": href_completa,
                    "categorias": [],
                }

                # === Procesar el segundo div (categorías secundarias y subcategorías) ===
                # Buscar divs con la clase indicada
                second_divs = li.find_elements(
                    By.CSS_SELECTOR,
                    "div.pr9.items-stretch.vtex-flex-layout-0-x-stretchChildrenWidth.flex",
                )
                for second_div in second_divs:
                    # Dentro de cada div, buscar los <li> con la clase específica
                    sub_li_elements = second_div.find_elements(
                        By.CSS_SELECTOR,
                        "li.vtex-menu-2-x-menuItem.vtex-menu-2-x-menuItem--item-submenu-list-custom.list.vtex-menu-2-x-menuItem.vtex-menu-2-x-menuItem--item-submenu-list-custom",
                    )
                    for sub_li in sub_li_elements:
                        try:
                            # Dentro de cada sub_li se tienen dos componentes: un div y un nav.
                            # El div contiene el nombre y el link de la categoría secundaria.
                            category_div = sub_li.find_element(By.TAG_NAME, "div")
                            category_name = category_div.text.strip()
                            a_category = category_div.find_element(By.TAG_NAME, "a")
                            href_cat = a_category.get_attribute("href").strip()
                            if href_cat.startswith("/"):
                                category_url = BASE_URL + href_cat
                            else:
                                category_url = href_cat

                            try:
                                # El nav contiene las subcategorías.
                                nav_element = sub_li.find_element(By.TAG_NAME, "nav")
                                sub_li_items = nav_element.find_elements(
                                    By.TAG_NAME, "li"
                                )
                            except:
                                sub_li_items = []
                            subcategorias = []
                            for sub_item in sub_li_items:
                                try:
                                    a_sub = sub_item.find_element(By.TAG_NAME, "a")
                                    sub_name = a_sub.text.strip()
                                    sub_href = a_sub.get_attribute("href").strip()
                                    if sub_href.startswith("/"):
                                        sub_url = BASE_URL + sub_href
                                    else:
                                        sub_url = sub_href
                                    subcategorias.append(
                                        {"nombre": sub_name, "url": sub_url}
                                    )
                                except Exception as e:
                                    print(f"Error extrayendo subcategoría en li: {e}")
                                    continue

                            # Agregar la categoría secundaria con sus subcategorías
                            general_category["categorias"].append(
                                {
                                    "nombre": category_name,
                                    "url": category_url,
                                    "subcategorias": subcategorias,
                                }
                            )

                        except Exception as e:
                            print(
                                f"Error procesando un sub-li en el li número {idx}: {e}"
                            )
                            continue

                # Agregar la categoría general (con sus subcategorías) al listado principal
                data["categorias_generales"].append(general_category)

            except Exception as e:
                print(f"Error procesando el li número {idx}: {e}")
                continue

        # Almacenar el JSON en un archivo categories.json
        with open("categories.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print("Información extraída y almacenada en categories.json:")
        print(json.dumps(data, indent=4, ensure_ascii=False))

    except Exception as e:
        print("Ocurrió un error:", e)

    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()
