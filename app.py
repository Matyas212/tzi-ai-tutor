import streamlit as st
import google.generativeai as genai

# 1. Nastavení vzhledu stránky
st.set_page_config(page_title="AI Tutor - TZI I", page_icon="🎓", layout="centered")

st.title("🎓 Výukový AI Tutor - TZI I")
st.caption("Přírodovědecká fakulta UJEP | Teoretické základy informatiky I")

# 2. Inicializace klienta Gemini
api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
genai.configure(api_key=api_key)

# Podrobné systémové instrukce
SYSTEM_INSTRUCTIONS = """
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
   - Při vysvětlování látky kolem výrokové logiky (negace, obrácení a obměna implikace) vysvětluj koncepty co nejjednodušeji a polopaticky.
   - Kdykoliv je to možné, používej pro srovnání těchto tvarů přehledné TABULKY, které studentům pomáhají látku lépe vizualizovat a pochopit.
5. Procvičování: Pokud student požádá o procvičování z konkrétní kapitoly, vygeneruj příklad odpovídající náročnosti úloh ze cvičení (ZM 1 až ZM 9).
6. Ilustrace z reálného života: Kdykoliv vysvětluješ nový teoretický pojem (např. ekvivalence, rozklad množiny, kartézský součin, relace, důkaz sporem), uveď kromě formální definice i krátký, názorný příměr z reálného života nebo z praxe v informatice pro lepší představivost.
"""

# Vytvoření modelu s přesným podporovaným názvem
model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config={"temperature": 0.7}
)

# 3. Inicializace relace chatu
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tlačítko pro vyčištění chatu
if st.sidebar.button("🧹 Vymazat konverzaci"):
    st.session_state.messages = []
    st.rerun()

# 4. Vykreslení historie zpráv
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Vstupní pole
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
            except Exception:
                st.error("Chyba při komunikaci s AI službou. Vyčkejte chvíli a zkuste dotaz poslat znovu.")
