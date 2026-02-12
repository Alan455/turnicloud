import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Mobile ---
st.set_page_config(page_title="Turni", page_icon="📅", layout="centered")

# --- CSS: Pulizia interfaccia ---
st.markdown("""
    <style>
    /* Nasconde menu e footer */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Riduce margini per sfruttare tutto lo schermo */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Migliora l'aspetto dei bottoni */
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Dati ---
OPZIONI = ["Mattina ☀️", "Pomeriggio 🌤️", "Sera 🌆", "Notte 🌙", "Ferie 🏖️", "Malattia 🤒", "Permesso 📝"]

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
            # Converte le date in stringa per Google Sheets
            df_in["Data"] = pd.to_datetime(df_in["Data"]).dt.strftime('%Y-%m-%d')
            conn.update(worksheet="Foglio1", data=df_in)
            return True
    except:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- 1. SEZIONE INSERIMENTO (Stile V2 - Comodo) ---
st.markdown("### 📅 Nuovo Turno")

with st.container():
    # Riga 1: Data e Tipo
    c1, c2 = st.columns([1, 1.5])
    with c1:
        data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    with c2:
        tipo_turno = st.selectbox("Tipo", OPZIONI)

    # Riga 2: Note e Bottone Salva
    c3, c4 = st.columns([2, 1])
    with c3:
        note_input = st.text_input("Note", placeholder="Es. cambio...")
    with c4:
        # Spaziatura per allineare il bottone all'input di testo
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        if st.button("➕ SALVA", type="primary"):
            df = gestisci_dati("read")
            # Puliamo l'emoji dal tipo per salvarlo pulito (opzionale, se vuoi)
            nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.rerun()

st.divider()

# --- 2. LISTA IN TABELLA (Compatta e Interattiva) ---
df = gestisci_dati("read")

if not df.empty:
    st.caption("📝 Storico Turni (Modifica direttamente qui sotto)")
    
    # Configurazione della tabella
    column_config = {
        "Data": st.column_config.DateColumn(
            "Data", 
            format="DD/MM/YYYY",  # Formato italiano
            width="small",
            required=True
        ),
        "Tipo": st.column_config.SelectboxColumn(
            "Tipo",
            options=OPZIONI,
            width="medium",
            required=True
        ),
        "Note": st.column_config.TextColumn(
            "Note",
            width="small"
        )
    }

    # EDITOR: Permette di modificare e cancellare righe
    df_modificato = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",       # Permette di aggiungere/togliere righe
        use_container_width=True, # Occupa tutto lo schermo
        hide_index=True,          # Nasconde i numeri 0,1,2...
        height=400                # Altezza fissa per scorrere bene
    )

    # Logica di salvataggio automatico se modifichi la tabella
    # (Controlla se il df modificato è diverso dall'originale)
    # Nota: Bisogna resettare l'indice per il confronto corretto
    if not df.reset_index(drop=True).equals(df_modificato.reset_index(drop=True)):
        if st.button("💾 Salva Modifiche Tabella", type="primary", use_container_width=True):
            gestisci_dati("write", df_modificato)
            st.toast("Tabella aggiornata!", icon="💾")
            st.rerun()
else:
    st.info("Nessun turno inserito.")
    
