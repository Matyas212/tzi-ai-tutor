import streamlit as st
import google.generativeai as genai
import glob
import re
from pypdf import PdfReader
from PIL import Image

# 1. Konfigurace stránky Streamlit
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")
st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Inicializace API klíče
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

def clean_latex(text: str) -> str:
    # Odstranění zbloudilých kódových bloků kolem dollarů
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    text = re.sub(r'`(\d+)`', r'\1', text)
    text = text.replace('\u2009', ' ')
    # Ošetření překlepů tokenizéru
    text = text.replace("konjunkcija", "konjunkce")
    return text

# 3. Načtení podkladových materiálů kurzu (PDF skripta)
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

# 4. Systémové instrukce se striktními didaktickými a jazykovými pravidly
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
- ZÁKAZ ODKAZŮ NA ČÍSLA ÚLOH: NIKDY se neodkazujte na konkrétní čísla úloh či sad (např. neuvádějte "v úloze 3", "v sadě ZM 4"). Odkazujte se pouze na věcná matematická témata.
- LATEXOVÁ PRAVIDLA:
  * Matematické vzorce vkládejte striktně mezi dolary ($...$).
  * Běžný text NIKDY nevkládejte dovnitř dollarů. Mezi vzorcem a textem musí být vždy zřetelná mezera a uzavřený dollar, aby nedošlo k slití textu do matematického fontu.

DIDAKTICKÉ VEDENÍ:
- Sokratovská metoda: Veďte studenta po jednotlivých krocích, nepředávejte hotová řešení hned v první odpovědi.
- NEPŘIJÍMEJTE VÁGNÍ ODPOVĚDI: Pokud student odpoví neúplně nebo nepřesně, neoznačujte odpověď jako zcela správnou. Vlídně jej vyzvěte k upřesnění chybějící části.
- POKUD STUDENT NAHRAJE FOTKU / OBRÁZEK: Analyzujte jeho postup, najděte přesné místo první chyby a otázkou jej navedte na správný směr.

STUDIJNÍ PODKLADY PŘEDMĚTU:
{STUDY_MATERIALS}
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.15}
)

# 5. Inicializace stavu relace
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# 6. Postranní panel: Přílohy a export do HTML s MathJaxem
with st.sidebar:
    st.header("📎 Příloha studenta")
    uploaded_file = st.file_uploader("Nahrajte fotku / zadání (PNG, JPG)", type=["png", "jpg", "jpeg"])
    student_image = None
    if uploaded_file is not None:
        student_image = Image.open(uploaded_file)
        st.image(student_image, caption="Nahraná příloha", use_container_width=True)
    
    st.divider()
    st.header("💾 Uložení konverzace")
    
    # Sestavení samostatné HTML stránky s MathJax skriptem
    html_export = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Záznam konzultace - AI Tutor TZI I</title>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    max-width: 820px;
    margin: 40px auto;
    padding: 0 20px;
    background-color: #f8fafc;
    color: #1e293b;
  }
  h2 {
    color: #0f172a;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 12px;
  }
  .message {
    margin-bottom: 24px;
    padding: 16px 20px;
    border-radius: 8px;
  }
  .user {
    background-color: #ffffff;
    border-left: 5px solid #ef4444;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .assistant {
    background-color: #f1f5f9;
    border-left: 5px solid #2563eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .sender {
    font-weight: 700;
    margin-bottom: 8px;
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .user .sender { color: #b91c1c; }
  .assistant .sender { color: #1d4ed8; }
  .content { white-space: pre-wrap; word-wrap: break-word; }
</style>
</head>
<body>
<h2>🎓 Záznam konzultace: Teoretické základy informatiky I</h2>
"""

    for m in st.session_state.messages:
        role_class = "user" if m["role"] == "user" else "assistant"
        role_label = "👤 Student" if m["role"] == "user" else "🤖 AI Tutor"
        content_escaped = m["content"].replace("<", "&lt;").replace(">", "&gt;")
        html_export += f"""
<div class="message {role_class}">
  <div class="sender">{role_label}</div>
  <div class="content">{content_escaped}</div>
</div>
"""

    html_export += """
</body>
</html>
"""

    st.download_button(
        label="📥 Stáhnout přehledný záznam (.html)",
        data=html_export,
        file_name="konverzace_tutor_tzi.html",
        mime="text/html",
        disabled=(len(st.session_state.messages) == 0)
    )
    
    if st.button("🧹 Nová konverzace (Vymazat)"):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

# 7. Vykreslení historie zpráv
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. Zpracování uživatelského vstupu
prompt = st.chat_input("Zadejte svůj dotaz nebo odpověď k příkladu...")

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
