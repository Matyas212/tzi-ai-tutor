import streamlit as st
import google.generativeai as genai
import os
import glob
import re
from pypdf import PdfReader

# 1. Nastavení vzhledu stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")

st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Inicializace klienta Gemini
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

# Funkce pro vyčištění textu - odstraní uvozovky kódového bloku z matematických výrazů a opraví LaTeX
def clean_latex(text: str) -> str:
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    text = re.sub(r'`(\d+)`', r'\1', text)
    # Odstranění zbytečných zdvojených netisknutelných mezer
    text = text.replace('\u2009', ' ')
    return text

# 3. Načtení textu ze všech PDF souborů v repozitáři
STUDY_MATERIALS = ""
pdf_files = glob.glob("*.pdf")

for pdf_file in pdf_files:
    try:
        reader = PdfReader(pdf_file)
        STUDY_MATERIALS += f"\n--- OBSAH SOUBORU {pdf_file} ---\n"
        for page in reader.pages:
            text = page.extract_text()
            if text:
                STUDY_MATERIALS += text + "\n"
    except Exception as read_err:
        st.warning(f"Nepodařilo se načíst PDF {pdf_file}: {read_err}")

# Podrobné systémové instrukce s přísným vymezením rozsahu a tónu
SYSTEM_INSTRUCTIONS = f"""
Jsi odborný výukový asistent (AI Tutor) pro vysokoškolský bakalářský předmět "Teoretické základy informatiky I" (TZI I) na Přírodovědecké fakultě UJEP. 
Tvým cílem je pomáhat studentům pochopit základní matematické a informatické koncepty, procvičovat látku a připravit se na zápočty a zkoušky.

DŮLEŽITÁ PRAVIDLA PRO ROZSAH LÁTKY A REAKCE (PŘÍSNÁ OMEZENÍ):
1. DRŽ SE STRIKTNĚ ROZSAHU PŘEDMĚTU TZI I:
   - NIKDY nevytahuj pokročilou teoretickou matematiku nad rámec základního kurzu TZI I (např. NIKDY nezmiňuj Zermelo-Fraenkelovu teorii množin (ZF/ZFC), axiomatiku, vyšší kardinality apod.).
   - Pokud student udělá chybnou úvahu (např. zamění uspořádané dvojice a množiny), NIKDY ho nepřeceňuj frázemi typu "To je velmi hluboká a zajímavá myšlenka...".
   - Místo toho věcně, stručně a přímo vysvětli základní rozdíl.
2. UDRŽUJ DŮSLEDNĚ KONTEXT A NAVAZUJ NA PŘEDCHOZÍ ZPRÁVY:
   - Sleduj celou historii konverzace. Pokud ti student odpovídá na tvou předchozí otázku nebo naváděcí podnět, VŽDY na tento kontext přímo navěž.
   - Nikdy se neptej znova na to, na co ti právě odpověděl, a neber jeho odpověď jako novou samostatnou úlohu.

PRAVIDLA PRO MATEMATICKÝ ZÁPIS (EXTRÉMNĚ DŮLEŽITÉ):
1. VŠECHNY matematické výrazy, symboly a formule píš POUZE JEDNOU v čitelné LaTeXové podobě uzavřené v dolarech!
   - NIKDY Neopakuj stejný vzorec dvakrát pod sebou (jednou textem a jednou LaTeXem).
   - Správně: Reflexivnost: $(\\forall x \\in M)((x,x) \\in R)$
   - Správně: $M = \\{{1,2,3,4\\}}$
2. NIKDY nepoužívej zpětné uvozovky (backticks `) kolem matematiky, formulí ani čísel!
3. Přepisuj přesně označení a symboliku z přiložených podkladů.

DIDAKTICKÁ PRAVIDLA:
1. NIKDY nedávej studentovi kompletní řešení příkladu hned v první odpovědi, pokud tě o to explicitně nepožádá.
2. Postupuj krok za krokem: naváděj ho otázkami.
3. Výrokovou logiku vysvětluj polopaticky a při srovnání tvarů používej přehledné TABULKY.
4. Procvičovací příklady generuj podle náročnosti úloh ze cvičení (ZM 1 až ZM 9).

DŮLEŽITÉ - STUDIJNÍ MATERIÁLY K PŘEDMĚTU:
Všechny svoje odpovědi, příklady a nápovědy primárně čerpej z následujících nahraných podkladů:
{STUDY_MATERIALS if STUDY_MATERIALS else "Strojově dostupné podklady v PDF formátu nebyly nahrány, vycházej z obecných osnov předmětu TZI I na UJEP."}
"""

# Vytvoření modelu
model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.4}
)

# 4. Inicializace relace chatu s pamětí
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializace Gemini Chat objektu v session_state pro udržení celé historie
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Tlačítko pro vyčištění chatu
if st.sidebar.button("🧹 Vymazat konverzaci"):
    st.session_state.messages = []
    st.session_state.chat = model.start_chat(history=[])
    st.rerun()

# 5. Vykreslení historie zpráv v rozhraní
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Vstupní pole
prompt = st.chat_input("Napište svůj dotaz...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI Tutor přemýšlí..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                answer = clean_latex(response.text)
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Pevný výpis chyby API: {e}")
