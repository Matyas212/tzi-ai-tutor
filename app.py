import streamlit as st
import google.generativeai as genai
import os
import glob
from pypdf import PdfReader

# 1. Nastavení vzhledu stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")

st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Inicializace klienta Gemini
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

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

TVÁ OSOBNOST A TÓN:
- Jsi trpělivý, povzbuzující, stručný a matematicky přesný.
- Používáš jasný a srozumitelný jazyk. Matematické a logické výrazy píšeš přehledně v LaTeX formátu (např. $a \\Rightarrow b$).

DIDAKTICKÁ PRAVIDLA (EXTRÉMNĚ DŮLEŽITÉ):
1. NIKDY nedávej studentovi kompletní řešení příkladu hned v první odpovědi, pokud tě o to explicitně nepožádá.
2. Vždy postupuj krok za krokem:
   - Nejprve zkontroluj, zda student rozumí definicím a předpokladům úlohy.
   - Polož mu naváděcí otázku nebo mu dej nápovědu pro první krok.
3. Pokud student udělá chybu:
   - Neříkej jen "To je špatně". 
   - Ukaž mu, ve kterém kroku úvaha selhala, vysvětli *proč* (připomeň příslušnou definici nebo větu z textu) a vyzvi ho k opravě.
4. Výroková logika (Negace, Obrácení, Obměna):
   - Při vysvětlování látky kolem výrokové logiky vysvětluj koncepty co nejjednodušeji a polopaticky.
   - Kdykoliv je to možné, používej pro srovnání těchto tvarů přehledné TABULKY.
5. Procvičování: Pokud student požádá o procvičování z konkrétní kapitoly, vygeneruj příklad odpovídající náročnosti úloh ze cvičení (ZM 1 až ZM 9).
6. Ilustrace z reálného života: Kdykoliv vysvětluješ nový teoretický pojem, uveď kromě formální definice i krátký příměr z reálného života.

DŮLEŽITÉ - STUDIJNÍ MATERIÁLY K PŘEDMĚTU:
Všechny svoje odpovědi, příklady a nápovědy primárně čerpej z následujících nahraných podkladů:
{STUDY_MATERIALS if STUDY_MATERIALS else "Strojově dostupné podklady v PDF formátu nebyly nahrány, vycházej z obecných osnov předmětu TZI I na UJEP."}
"""

# Vytvoření modelu s lehkou bezplatnou verzí Lite
model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest"",
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
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Pevný výpis chyby API: {e}")
