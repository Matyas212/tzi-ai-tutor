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

# Funkce pro vyčištění textu - odstraní uvozovky kódového bloku (backticks) z matematických výrazů
def clean_latex(text: str) -> str:
    # Odstraní uvozovky kódových bloků kolem dolarů, např. `$p \Rightarrow q$` -> $p \Rightarrow q$
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    # Odstraní samostatné uvozovky u čísel v tabulkách/textu
    text = re.sub(r'`(\d+)`', r'\1', text)
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

# Podrobné systémové instrukce + studijní materiály
SYSTEM_INSTRUCTIONS = f"""
Jsi odborný výukový asistent (AI Tutor) pro vysokoškolský předmět "Teoretické základy informatiky I" (TZI I) na Přírodovědecké fakultě UJEP. 
Tvým cílem je pomáhat studentům pochopit matematické a informatické koncepty, procvičovat látku a připravit se na testy.

PRAVIDLA PRO MATEMATICKÝ ZÁPIS A FORMÁTOVÁNÍ (EXTRÉMNĚ DŮLEŽITÉ):
1. VŠECHNY matematické symboly, výrokové formule, šipky, proměnné a relace MUSÍŠ psát POUZE v platném LaTeXu uzavřeném v dolarech!
   - Správně: $p \\Rightarrow q$, $p \\land \\neg q$, $p \\iff q$, $x \\in \\mathbb{{R}}$, $\\forall x$, $\\exists x$.
   - Samostatný vzorec na novém řádku: $$p \\Rightarrow q$$
2. NIKDY nepoužívej zpětné uvozovky (backticks `) kolem matematiky, formulí ani čísel! Píše se $p \\Rightarrow q$, NIKDY NE `$p \\Rightarrow q$`.
3. PŘESNOST ZÁPISU: Všechny výrokové znaky, konjunkce ($\\land$), disjunkce ($\\lor$), negace ($\\neg$), implikace ($\\Rightarrow$), ekvivalence ($\\iff$) a kvantifikátory přepisuj přesně tak, jak jsou v zadání a skriptech.

DIDAKTICKÁ PRAVIDLA:
1. NIKDY nedávej studentovi kompletní řešení příkladu hned v první odpovědi, pokud tě o to explicitně nepožádá.
2. Vždy postupuj krok za krokem:
   - Nejprve zkontroluj, zda student rozumí definicím a předpokladům úlohy.
   - Polož mu naváděcí otázku nebo mu dej nápovědu pro první krok.
3. Pokud student udělá chybu:
   - Neříkej jen "To je špatně". 
   - Ukaž mu, ve kterém kroku úvaha selhala, vysvětli *proč* a vyzvi ho k opravě.
4. Výroková logika (Negace, Obrácení, Obměna):
   - Při vysvětlování látky kolem výrokové logiky používaj pro srovnání tvarů přehledné TABULKY.
5. Procvičování: Pokud student požádá o procvičování z konkrétní kapitoly, vygeneruj příklad přesně podle formátu úloh ze cvičení (ZM 1 až ZM 9).

DŮLEŽITÉ - STUDIJNÍ MATERIÁLY K PŘEDMĚTU:
Všechny svoje odpovědi, příklady a nápovědy primárně čerpej z následujících nahraných podkladů:
{STUDY_MATERIALS if STUDY_MATERIALS else "Strojově dostupné podklady v PDF formátu nebyly nahrány, vycházej z obecných osnov předmětu TZI I na UJEP."}
"""

# Vytvoření modelu
model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.7}
)

# 4. Inicializace relace chatu
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tlačítko pro vyčištění chatu
if st.sidebar.button("🧹 Vymazat konverzaci"):
    st.session_state.messages = []
    st.rerun()

# 5. Vykreslení historie zpráv
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
                response = model.generate_content(prompt)
                # Vyčištění odpovědi od nechtěných uvozovek kódového bloku
                answer = clean_latex(response.text)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Pevný výpis chyby API: {e}")
