import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Estrema ---
st.set_page_config(page_title="Turni", page_icon="⚡", layout="centered")

# --- CSS: Rimozione Spazi Vuoti (Aggressive) ---
st.markdown("""
    <style>
    /* Nasconde tutto l'inutile */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Margini al minimo storico */
    .block-container {
        padding-top: 0.5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Riduce spazio tra gli elementi */
    div[data-testid="stVerticalBlock"] { gap: 0.3rem; }
    
    /* Input più compatti */
    .stDateInput, .stSelectbox, .stTextInput { margin-bottom: -15px !important; }
    
    /* Bottone 'X' rosso e minuscolo */
    div[data-testid="stButton"] button {
        background-color: #ffeded;
        color: red;
        border: none;
        padding: 0px 5px;
        min-height: 25px;
        height: 25px;
        line-height: 1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Dati ---
OPZIONI = {"Mattina": "☀️", "Pomeriggio": "🌤️", "Sera": "🌆", "Notte": "🌙", "Ferie": "🏖️", "Malattia": "🤒"}
LISTA_TIPI = list(OPZIONI.keys())

conn = st.connection("gsheets", type=GSheetsConnection)

def gestisci_dati(mode="read", df_in=None):
    try:
        if mode == "read":
            df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0).dropna(how="all")
            if "Note" not in df.columns: df["Note"] = ""
            df["Note"] = df["Note"].fillna("").astype(str)
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
            return df.dropna(subset=["Data"]).sort_values(by="Data", ascending=False)
        elif mode == "write":
            df_in["Data"] = pd.to_datetime(df_in["Data"]).dt.strftime('%Y-%m-%d')
            conn.update(worksheet="Foglio1", data=df_in)
            return True
    except:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- UI ULTRA COMPATTA ---

# 1. INSERIMENTO (Griglia 2x2 senza etichette)
with st.container():
    c1, c2 = st.columns([1.2, 1.5], gap="small")
    with c1:
        # CORREZIONE QUI: Rimesso YYYY obbligatorio per evitare crash
        data = st.date_input("D", datetime.today(), format="DD/MM/YYYY", label_visibility="collapsed")
    with c2:
        tipo = st.selectbox("T", LISTA_TIPI, label_visibility="collapsed")

    c3, c4 = st.columns([2, 0.8], gap="small")
    with c3:
        note = st.text_input("N", placeholder="Note...", label_visibility="collapsed")
    with c4:
        if st.button("➕", type="primary", use_container_width=True):
            df = gestisci_dati("read")
            nuova = pd.DataFrame([{"Data": data, "Tipo": tipo, "Note": note}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.rerun()

st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)

# 2. LISTA MICRO (Una riga per turno)
df = gestisci_dati("read")

if not df.empty:
    st.caption(f"Storico ({len(df)})")
    
    for i, row in df.head(15).iterrows():
        # Layout: Data | Emoji+Tipo | X
        k1, k2, k3 = st.columns([0.8, 2, 0.4], gap="small", vertical_alignment="center")
        
        with k1:
            # QUI la visualizzazione resta compatta (solo Giorno/Mese)
            st.markdown(f"**{row['Data'].strftime('%d/%m')}**")
        
        with k2:
            emoji = OPZIONI.get(row['Tipo'], "▪️")
            txt_nota = f"<span style='color:gray; font-size:0.8em'> ({row['Note']})</span>" if row['Note'] else ""
            st.markdown(f"{emoji} {row['Tipo']}{txt_nota}", unsafe_allow_html=True)
            
        with k3:
            if st.button("x", key=f"d_{i}"):
                gestisci_dati("write", df.drop(i))
                st.rerun()
else:
    st.write("Lista vuota")
    
