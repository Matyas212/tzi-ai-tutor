import streamlit as st
import google.generativeai as genai
import os
import glob
import re
from pypdf import PdfReader
from PIL import Image

# 1. Nastavení stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")
st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Inicializace Gemini klienta
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

def clean_latex(text: str) -> str:
    text = re.sub(r'`(\$[^`]+\$)`', r'\1', text)
    text = re.sub(r'`(\d+)`', r'\1', text)
    text = text.replace('\u2009', ' ')
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not cleaned_lines or stripped != cleaned_lines[-1].strip():
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

# 3. Načtení interních studijních materiálů
STUDY_MATERIALS = ""
for pdf_file in glob.glob("*.pdf"):
    try:
        reader = PdfReader(pdf_file)
        STUDY_MATERIALS += f"\n--- PODKLAD {pdf_file} ---\n"
        for page in reader.pages:
            t = page.extract_text()
            if t:
                STUDY_MATERIALS += t + "\n"
    except Exception as e:
        pass

# 4. Didaktické a systémové instrukce
SYSTEM_INSTRUCTIONS = f"""
Jsi odborný výukový asistent (AI Tutor) pro vysokoškolský kurz "Teoretické základy informatiky I" (TZI I) na Přírodovědecké fakultě UJEP.

DIDAKTICKÉ A OBSAHOVÉ ZÁSADY:
1. SOKRATOVSKÉ VEDENÍ:
   - Nikdy neposkytuj kompletní řešení ihned v první odpovědi.
   - Veď studenta po dílčích logických krocích a ověřuj pochopení kontrolními otázkami.
   - Pokud student nahraje fotografii/obrázek svého postupu, analyzuj jeho zápis, přesně lokalizuj první chybu a naved ho k její opravě.
2. ZÁKAZ ODKAZŮ NA ČÍSLA ÚLOH:
   - NIKDY se neodkazuj na konkrétní číslování úloh nebo sad (např. neříkej "v úloze 3", "v sadě ZM 4").
   - Odkazuj se výhradně na konkrétní matematická témata (např. "při negaci kvantifikovaných výroků", "u relací ekvivalence").
3. VĚCNOST A ROZSAH:
   - Drž se látky bakalářského kurzu TZI I. Nevytahuj axiomatickou teorii množin (ZF/ZFC).
   - Při chybě studenta odpověz věcně a přímo, bez frází typu "To je hluboká myšlenka".
4. FORMÁTOVÁNÍ:
   - Veškeré matematické výrazy piš výhradně v LaTeXu ohraničeném dolary ($...$). Nezdvojuj vzorce.

STUDIJNÍ PODKLADY PŘEDMĚTU:
{STUDY_MATERIALS}
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-lite-latest",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.2}
)

# 5. Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# 6. Postranní panel - Nahrání souboru a správa
with st.sidebar:
    st.header("📎 Příloha studenta")
    uploaded_file = st.file_uploader(
        "Nahrajte fotku postupu / zadání (PNG, JPG)", 
        type=["png", "jpg", "jpeg"]
    )
    student_image = None
    if uploaded_file is not None:
        student_image = Image.open(uploaded_file)
        st.image(student_image, caption="Nahraná příloha", use_container_width=True)
    
    if st.button("🧹 Vymazat konverzaci"):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

# 7. Vykreslení historie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. Zpracování vstupu
prompt = st.chat_input("Napište svůj dotaz nebo se zeptejte k nahranému obrázku...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI Tutor analyzuje zadání..."):
            try:
                # Pokud student nahrál obrázek, odešle se společně s textem
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
                st.error(f"Chyba při komunikaci s modelem: {e}")
