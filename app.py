import streamlit as st
import google.generativeai as genai
import glob
import re
from pypdf import PdfReader
from PIL import Image

# 1. Konfigurace stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")
st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. API Klíč
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

def clean_latex(text: str) -> str:
    # Oprava případných zbloudilých kódových bloků kolem dollarů
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    text = re.sub(r'`(\d+)`', r'\1', text)
    text = text.replace('\u2009', ' ')
    # Ošetření překlepů typu konjunkcija
    text = text.replace("konjunkcija", "konjunkce")
    return text

# 3. Načtení podkladů z PDF
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

# 4. Systémové instrukce se striktními pravidly
SYSTEM_INSTRUCTIONS = f"""
Jste odborný vysokoškolský AI Tutor pro předmět "Teoretické základy informatiky I" (TZI I) na PřF UJEP.

KOMUNIKACE A JAZYK:
- DŮSLEDNĚ VYKAT: Se studentem vždy jednejte zdvořile a výhradně v jednotném VYKÁNÍ (žádné tykání ani střídání tvarů).
- ČESKÁ GRAMATIKA: Dbejte na bezchybnou češtinu, vyvarujte se zkomolenin (např. pište výhradně "konjunkce", nikoli "konjunkcija").
- JEDNOTNÁ TERMINOLOGIE:
  * Vlastnosti relací nazývejte výhradně: reflexivita, symetrie, tranzitivita, slabá antisymetrie.
  * Formální logika:
    - Negace implikace (p => q) je konjunkce: p a zároveň ne-q (p ∧ ¬q).
    - Obrácení implikace (konverze) je: q => p (případně ¬p => ¬q je negace předpokladu i závěru).
    - Obměna implikace (kontrapozice) je: ¬q => ¬p. NIKDY nezaměňujte obměnu a obrácení!

MATEMATICKÁ PŘESNOST A FORMÁT:
- DŮSLEDNOST U MNOŽIN: Pokud množina obsahuje jako prvek jinou množinu (např. B = {{2, 3, {{4, 5}}}}), tento vnitřní prvek je jedním celkem! Nikdy prvky nevysypávejte do {{2, 3, 4, 5}}.
- ODKAZY: NIKDY se neodkazujte na konkrétní čísla úloh či sad (např. neuvádějte "v úloze 3", "v sadě ZM 4"). Odkazujte se pouze na věcná témata.
- LATEXOVÁ PRAVIDLA:
  * Matematické vzorce vkládejte striktně mezi dolary ($...$).
  * Běžný text NIKDY nevkládejte dovnitř dollarů. Mezi vzorcem a textem musí být vždy zřetelná mezera a uzavřený dollar, aby nedošlo k slití textu do matematického fontu.

DIDAKTICKÉ VEDENÍ:
- Sokratovská metoda: Veďte studenta po jednotlivých krocích, nepředávejte hotová řešení hned.
- NEPŘIJÍMEJTE VÁGNÍ ODPOVĚDI: Pokud student odpoví neúplně nebo nepřesně, neoznačujte odpověď jako zcela správnou. Vlídně jej vyzvěte k upřesnění chybějící části.

STUDIJNÍ PODKLADY ZM 1 AŽ ZM 9:
{STUDY_MATERIALS}
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.15}
)

# 5. Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# 6. Postranní panel: Přílohy a ukládání historie
with st.sidebar:
    st.header("📎 Příloha studenta")
    uploaded_file = st.file_uploader("Nahrajte fotku / zadání (PNG, JPG)", type=["png", "jpg", "jpeg"])
    student_image = None
    if uploaded_file is not None:
        student_image = Image.open(uploaded_file)
        st.image(student_image, caption="Nahraná příloha", use_container_width=True)
    
    st.divider()
    st.header("💾 Uložení konverzace")
    
    # Příprava konverzace pro export do textu
    chat_export = ""
    for m in st.session_state.messages:
        role_label = "Student" if m["role"] == "user" else "AI Tutor"
        chat_export += f"{role_label}:\n{m['content']}\n\n" + ("-"*40) + "\n\n"
    
    st.download_button(
        label="📥 Stáhnout konverzaci (.txt)",
        data=chat_export,
        file_name="konverzace_tutor_tzi.txt",
        mime="text/plain",
        disabled=(len(st.session_state.messages) == 0)
    )
    
    if st.button("🧹 Nová konverzace (Vymazat)"):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

# 7. Zobrazení dosavadního chatu
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. Vstup uživatele
prompt = st.chat_input("Zadejte svůj dotaz nebo odpověď...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
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
                st.rerun()
            except Exception as e:
                st.error(f"Chyba při komunikaci: {e}")
