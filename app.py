import streamlit as st
import google.generativeai as genai
import glob
import re
from pypdf import PdfReader
from PIL import Image
from supabase import create_client, Client

# 1. Konfigurace stránky Streamlit
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")
st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Připojení k databázi Supabase
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

def save_message(username, role, content):
    if supabase:
        try:
            supabase.table("chat_history").insert({
                "username": username,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            st.error(f"Chyba uložení do databáze: {e}")

def load_history(username):
    if supabase:
        try:
            # Načte historii seřazenou chronologicky podle ID
            response = supabase.table("chat_history").select("*").eq("username", username).order("id").execute()
            return response.data
        except Exception as e:
            st.error(f"Chyba načtení z databáze: {e}")
    return []

# 3. Inicializace API klíče Gemini
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

def clean_latex(text: str) -> str:
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    text = re.sub(r'`(\d+)`', r'\1', text)
    text = text.replace('\u2009', ' ')
    text = text.replace("konjunkcija", "konjunkce")
    return text

# 4. Načtení podkladových materiálů kurzu
STUDY_MATERIALS = ""
for pdf_file in glob.glob("*.pdf"):
    try:
        reader = PdfReader(pdf_file)
        STUDY_MATERIALS += f"\n--- MATERIÁL {pdf_file} ---\n"
        for page in reader.pages:
            t = page.extract_text()
            if t:
                STUDY_MATERIALS += t + "\n"
    except Exception:
        pass

# 5. Systémové instrukce
SYSTEM_INSTRUCTIONS = f"""
Jste odborný vysokoškolský AI Tutor pro předmět "Teoretické základy informatiky I" (TZI I) na Přírodovědecké fakultě UJEP.

KOMUNIKACE A JAZYK:
- DŮSLEDNĚ VYKAT: Se studentem vždy jednejte zdvořile a výhradně v jednotném VYKÁNÍ (žádné tykání ani střídání tvarů).
- ČESKÁ GRAMATIKA: Dbejte na bezchybnou češtinu, vyvarujte se zkomolenin (např. pište výhradně "konjunkce", nikoli "konjunkcija").
- JEDNOTNÁ TERMINOLOGIE:
  * Vlastnosti relací nazývejte výhradně: reflexivita, symetrie, tranzitivita, slabá antisymetrie.
  * Formální logika:
    - Negace implikace (p => q) je konjunkce: p a zároveň ne-q (p ∧ ¬q).
    - Obrácení implikace (konverze) je: q => p.
    - Obměna implikace (kontrapozice) je: ¬q => ¬p. NIKDY nezaměňujte obměnu a obrácení!

MATEMATICKÁ PŘESNOST A FORMÁT:
- DŮSLEDNOST U MNOŽIN: Pokud množina obsahuje jako prvek jinou množinu (např. B = {{2, 3, {{4, 5}}}}), tento vnitřní prvek je jedním nerozdělitelným celkem! Nikdy prvky nevysypávejte do {{2, 3, 4, 5}}.
- ZÁKAZ ODKAZŮ NA ČÍSLA ÚLOH: NIKDY se neodkazujte na konkrétní čísla úloh či sad. Odkazujte se pouze na věcná matematická témata.
- LATEXOVÁ PRAVIDLA:
  * Matematické vzorce vkládejte striktně mezi dolary ($...$).
  * Běžný text NIKDY nevkládejte dovnitř dollarů. Mezi vzorcem a textem musí být vždy zřetelná mezera a uzavřený dollar.

DIDAKTICKÉ VEDENÍ:
- Sokratovská metoda: Veďte studenta po jednotlivých krocích, nepředávejte hotová řešení hned v první odpovědi.
- NEPŘIJÍMEJTE VÁGNÍ ODPOVĚDI: Pokud student odpoví neúplně nebo nepřesně, vlídně jej vyzvěte k upřesnění chybějící části.
- POKUD STUDENT NAHRAJE FOTKU / OBRÁZEK: Analyzujte jeho postup, najděte přesné místo první chyby a otázkou jej navedte na správný směr.

STUDIJNÍ PODKLADY PŘEDMĚTU:
{STUDY_MATERIALS}
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.15}
)

# 6. Přihlášení studenta
if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.info("👋 Vítejte! Pro načtení nebo uložení vaší konverzace zadejte svou přezdívku či ID.")
    username_input = st.text_input("Vaše přezdívka (např. JanN, student01):")
    if st.button("Vstoupit do aplikace") and username_input:
        st.session_state.username = username_input.strip()
        st.rerun()
    st.stop() # Zastaví vykreslování chatu, dokud se student nepodepíše

# 7. Načtení paměti a inicializace chatu po přihlášení
if "messages" not in st.session_state:
    db_messages = load_history(st.session_state.username)
    st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in db_messages]

if "chat" not in st.session_state:
    gemini_history = []
    for m in st.session_state.messages:
        gemini_role = "user" if m["role"] == "user" else "model"
        gemini_history.append({"role": gemini_role, "parts": [m["content"]]})
    
    st.session_state.chat = model.start_chat(history=gemini_history)

# 8. Postranní panel
with st.sidebar:
    st.markdown(f"👤 **Přihlášený student:** `{st.session_state.username}`")
    if st.button("🚪 Odhlásit se"):
        st.session_state.username = None
        st.session_state.messages = []
        del st.session_state.chat
        st.rerun()

    st.divider()
    st.header("📎 Příloha studenta")
    uploaded_file = st.file_uploader("Nahrajte fotku / zadání (PNG, JPG)", type=["png", "jpg", "jpeg"])
    student_image = None
    if uploaded_file is not None:
        student_image = Image.open(uploaded_file)
        st.image(student_image, caption="Nahraná příloha", use_container_width=True)
    
    st.divider()
    st.header("💾 Uložení konverzace")
    # Zde zůstává váš kód pro export HTML nezměněn... (zkráceno pro přehlednost, vložte sem původní HTML export blok)
    if st.button("🧹 Vymazat historii tohoto chatu"):
        if supabase:
            supabase.table("chat_history").delete().eq("username", st.session_state.username).execute()
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

# 9. Vykreslení historie zpráv
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 10. Zpracování uživatelského vstupu
prompt = st.chat_input("Zadejte svůj dotaz nebo odpověď k příkladu...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.username, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI Tutor formuluje odpověď..."):
            try:
                if student_image:
                    content_payload = [prompt, student_image]
                else:
                    content_payload = prompt

                response = st.session_state.chat.send_message(content_payload)
                ans = clean_latex(response.text)
                st.markdown(ans)
                
                st.session_state.messages.append({"role": "assistant", "content": ans})
                save_message(st.session_state.username, "assistant", ans)
                
            except Exception as e:
                st.error(f"Chyba při komunikaci: {e}")
