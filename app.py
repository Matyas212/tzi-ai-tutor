import streamlit as st
from google import genai
from google.genai import types

# Nastavení vzhledu stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")

st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# Inicializace klienta a nastavení systému
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTIONS = """
Jsi odborný výukový asistent (AI Tutor) pro vysokoškolský předmět "Teoretické základy informatiky I" (TZI I) na Přírodovědecké fakultě UJEP. 
Tvým cílem je pomáhat studentům pochopit matematické a informatické koncepty, procvičovat látku a připravit se na testy.

TVÁ OSOBNOST A TÓN:
- Jsi trpělivý, povzbuzující, stručný a matematicky přesný.
- Používáš jasný a srozumitelný jazyk. Matematické a logické výrazy píšeš přehledně v LaTeX formátu (např. $a \Rightarrow b$).

DIDAKTICKÁ PRAVIDLA (EXTRÉMNĚ DŮLEŽITÉ):
1. NIKDY nedávej studentovi kompletní řešení příkladu hned v první odpovědi, pokud tě o to explicitně nepožádá.
2. Vždy postupuj krok za krokem:
   - Nejprve zkontroluj, zda student rozumí definicím a předpokladům úlohy.
   - Polož mu naváděcí otázku nebo mu dej nápovědu pro první krok.
3. Pokud student udělá chybu:
   - Neříkej jen "To je špatně". 
   - Ukaž mu, ve kterém kroku úvaha selhala, vysvětli *proč* (připomeň příslušnou definici nebo větu z textu) a vyzvi ho k opravě.
4. Výroková logika (Negace, Obrácení, Obměna):
   - Při vysvětlování látky kolem výrokové logiky (negace, obrácení a obměna implikace) vysvětluj koncepty co nejjednodušeji a polopaticky.
   - Kdykoliv je to možné, používej pro srovnání těchto tvarů přehledné TABULKY, které studentům pomáhají látku lépe vizualizovat a pochopit.
5. Procvičování: Pokud student požádá o procvičování z konkrétní kapitoly, vygeneruj příklad odpovídající náročnosti úloh ze cvičení (ZM 1 až ZM 9).
6. Ilustrace z reálného života: Kdykoliv vysvětluješ nový teoretický pojem (např. ekvivalence, rozklad množiny, kartézský součin, relace, důkaz sporem), uveď kromě formální definice i krátký, názorný příměr z reálného života nebo z praxe v informatice pro lepší představivost.
"""

# Paměť konverzace v rámci jedné relace
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zobrazení historie konverzace
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Vstup pro dotaz uživatele
if prompt := st.chat_input("Zadej dotaz nebo požádej o procvičení..."):
    # Uložení a zobrazení dotazu
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generování odpovědi modelem Gemini
    with st.chat_message("assistant"):
        with st.spinner("AI Tutor přemýšlí..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[m["content"] for m in st.session_state.messages],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.7,
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
