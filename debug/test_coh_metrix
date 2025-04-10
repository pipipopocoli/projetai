import time
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Créer un répertoire temporaire unique pour le profil utilisateur
temp_profile_dir = tempfile.mkdtemp()

chrome_options = Options()
chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")  # Utiliser "new" pour la dernière version headless, ou "--headless" si nécessaire

try:
    # Initialisation du driver Chrome avec les options configurées
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    # Accéder à la page "My Text" pour l'ajout du texte
    url = "https://soletlab.adaptiveliteracy.com:8443/Grid/Coh-MetrixMytext.aspx"
    driver.get(url)
    time.sleep(3)  # Pause pour permettre le chargement complet de la page

    # Remplissage du formulaire

    # Remplir le champ "Titre de l'article"
    title_field = wait.until(EC.presence_of_element_located((By.ID, "txtTitle")))
    title_field.clear()
    title_field.send_keys("Titre de l'article")

    # Indiquer le grade (ici "X")
    grade_field = driver.find_element(By.ID, "txtGrade")
    grade_field.clear()
    grade_field.send_keys("X")

    # Sélectionner le style "PeerReview Paper"
    style_dropdown = driver.find_element(By.ID, "ddlStyle")
    Select(style_dropdown).select_by_visible_text("PeerReview Paper")

    # Cocher l'option "Text Excerpt"
    text_excerpt_checkbox = driver.find_element(By.ID, "chkTextExcerpt")
    if not text_excerpt_checkbox.is_selected():
        text_excerpt_checkbox.click()

    # Insérer le texte à analyser dans la zone dédiée
    text_area = driver.find_element(By.ID, "txtContent")
    text_area.clear()
    sample_text = (
        "Votre texte en format clair ici. Ceci est un exemple de contenu textuel pour l'analyse Coh-Metrix. "
        "Ajoutez le texte complet que vous souhaitez analyser."
    )
    text_area.send_keys(sample_text)

    # Soumettre le formulaire
    submit_button = driver.find_element(By.ID, "btnSubmit")
    submit_button.click()
    time.sleep(5)  # Attente pour que l'analyse soit effectuée

    # Actualiser pour récupérer les résultats
    refresh_button = wait.until(EC.element_to_be_clickable((By.ID, "btnRefresh")))
    refresh_button.click()
    time.sleep(5)  # Attente pour que les résultats se mettent à jour

    # Extraction du Flesch-Kincaid Grade
    try:
        fk_grade_elem = driver.find_element(By.ID, "lblFleschKincaidGrade")
        fk_grade = fk_grade_elem.text
    except Exception as e:
        fk_grade = "Non trouvé"
        print("Erreur lors de l'extraction du Flesch-Kincaid Grade:", e)

    # Extraction des données graphiques (si disponibles en texte)
    try:
        graph_data_elem = driver.find_element(By.ID, "divGraphData")
        graph_data = graph_data_elem.text
    except Exception as e:
        graph_data = "Non trouvé"
        print("Erreur lors de l'extraction des données graphiques:", e)

    print("Flesch-Kincaid Grade:", fk_grade)
    print("Données graphiques:", graph_data)

except Exception as main_e:
    print("Erreur lors de l'initialisation ou de l'exécution:", main_e)
finally:
    # Fermer le driver et supprimer le répertoire temporaire
    try:
        driver.quit()
    except Exception:
        pass
    shutil.rmtree(temp_profile_dir, ignore_errors=True)


