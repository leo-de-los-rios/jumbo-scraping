import json
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.jumbo.com.ar"
NAME_FILE = "categories.json"


def click_category(wait):
    category_div = wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                "div.vtex-menu-2-x-styledLinkContent.vtex-menu-2-x-styledLinkContent--header-category.flex.justify-between.nowrap",
            )
        )
    )
    category_div.click()


def get_sections(category):
    return category.find_elements(
        By.CSS_SELECTOR,
        "div.vtex-flex-layout-0-x-flexColChild.vtex-flex-layout-0-x-flexColChild--col-submenu.pb0",
    )[:-2]


def get_categories(wait):
    submenu_section = wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "section.vtex-menu-2-x-submenu.vtex-menu-2-x-submenu--department-menu.w-100.flex.justify-center.flex-column",
            )
        )
    )

    li_elements = submenu_section.find_elements(By.TAG_NAME, "li")[1:]
    return li_elements


def get_general_category(category):
    a_element = category.find_element(By.TAG_NAME, "a")
    name = a_element.text
    url = a_element.get_attribute("href")

    general_category = {
        "nombre": name,
        "url": url,
        "categorias": [],
    }

    return general_category


def get_category_subcategories(section):
    a_elements = section.find_elements(By.TAG_NAME, "a")
    category = a_elements[0]
    subcategories = []

    # Get subcategories
    for a_element in a_elements[1:]:
        name = a_element.text
        url = a_element.get_attribute("href")

        subcategory = {
            "nombre": name,
            "url": url,
        }

        subcategories.append(subcategory)

    category = {
        "nombre": category.text,
        "url": category.get_attribute("href"),
        "subcategorias": subcategories,
    }

    return category


def hover_category(action, category):
    action.move_to_element(category).perform()


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

        click_category(wait)

        categories = get_categories(wait)

        for category in categories:
            hover_category(action, category)
            time.sleep(0.1)

            general_category = get_general_category(category)

            sections = get_sections(category)

            categories = [get_category_subcategories(section) for section in sections]

            general_category["categorias"] = categories

            data["categorias_generales"].append(general_category)

        with open(NAME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print("Categorías guardadas en categories.json")

    except Exception as e:
        print("Ocurrió un error:", e)

    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()
