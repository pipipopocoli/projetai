import pdb
import time
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import h5py


def login(driver, wait, username, password):
    """
    Se connecte au site en naviguant vers la page Login.
    IDs utilisés :
      - Nom d'utilisateur : "txtUserName"
      - Mot de passe : "txtPassword"
      - Bouton de connexion : "btnLogin"
    """
    login_url = "https://soletlab.adaptiveliteracy.com:8443/Login.aspx"
    driver.get(login_url)
    
    # Attendre que le champ du nom d'utilisateur soit présent
    user_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
    user_field.clear()
    user_field.send_keys(username)
    
    # Remplir le champ du mot de passe
    pwd_field = driver.find_element(By.ID, "txtPassword")
    pwd_field.clear()
    pwd_field.send_keys(password)
    
    # Cliquer sur le bouton de connexion
    login_button = driver.find_element(By.ID, "btnLogin")
    login_button.click()
    
    # Attendre que l'URL contienne "Grid/Coh-MetrixMytext.aspx" pour confirmer la connexion
    wait.until(EC.url_contains("Grid/Coh-MetrixMytext.aspx"))

# Créer un répertoire temporaire unique pour le profil utilisateur
temp_profile_dir = tempfile.mkdtemp()

chrome_options = Options()
chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")  # Utiliser "new" pour la dernière version headless, ou "--headless" si nécessaire

# Initialisation du driver Chrome avec les options configurées
driver = webdriver.Chrome(options=chrome_options)
print("first wait...")
wait = WebDriverWait(driver, 15)

login_username = "leonardsauve@gmail.com"
login_password = "RARS3075"
login(driver, wait, login_username, login_password)
pdb.set_trace()
# Accéder à la page "My Text" pour l'ajout du texte
url = "https://soletlab.adaptiveliteracy.com:8443/Grid/Coh-MetrixMytext.aspx"
driver.get(url)
print("second wait...")
time.sleep(3)  # Pause pour permettre le chargement complet de la page

# Remplissage du formulaire

# Remplir le champ "Titre de l'article"
title_field = wait.until(EC.presence_of_element_located((By.ID, "txtTitle")))
title_field.clear()
title_field.send_keys("Titre de l'article")
pdb.set_trace() 
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
with h5py.File("sample_data/2012_vol1_1.h5", "r") as inf:
    sample_text = inf[inf.keys()[0]].asstr()[()]

text_area.send_keys(sample_text)
pdb.set_trace() 
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

driver.quit()

shutil.rmtree(temp_profile_dir, ignore_errors=True)


