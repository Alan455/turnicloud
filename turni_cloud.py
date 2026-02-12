import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Mobile ---
st.set_page_config(page_title="Turni", page_icon="📅", layout="centered")

# --- CSS: Pulizia interfaccia ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- OPZIONI PULITE (Senza Emoji nel testo per compatibilità) ---
# Queste sono le parole esatte che verranno salvate nel database
OPZIONI = ["Mattina", "Pomeriggio", "Sera", "Notte", "Ferie", "Malattia", "Permesso"]

conn = st.connection("gsheets", type=GSheetsConnection)

def gestisci_dati(mode="read", df_in=None):
    try:
        if mode == "read":
            # Leggiamo il foglio. Se manca qualche colonna, la ricreiamo vuota.
            df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0)
            
            # Controllo sicurezza colonne
            if "Tipo" not in df.columns: df["Tipo"] = ""
            if "Note" not in df.columns: df["Note"] = ""
            
            # Pulizia dati
            df["Note"] = df["Note"].fillna("").astype(str)
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
            return df.dropna(subset=["Data"]).sort_values(by="Data", ascending=False)
            
        elif mode == "write":
            # Salvataggio sicuro
            df_in["Data"] = pd.to_datetime(df_in["Data"]).dt.strftime('%Y-%m-%d')
            conn.update(worksheet="Foglio1", data=df_in)
            return True
    except Exception as e:
        st.error(f"Errore database: {e}")
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- 1. SEZIONE INSERIMENTO ---
st.markdown("### 📅 Nuovo Turno")

with st.container():
    c1, c2 = st.columns([1, 1.5])
    with c1:
        data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    with c2:
        tipo_turno = st.selectbox("Tipo", OPZIONI)

    c3, c4 = st.columns([2, 1])
    with c3:
        note_input = st.text_input("Note", placeholder="Es. cambio...")
    with c4:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        if st.button("➕ SALVA", type="primary"):
            df = gestisci_dati("read")
            nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.rerun()

st.divider()

# --- 2. TABELLA STORICO (Sicura) ---
df = gestisci_dati("read")

if not df.empty:
    st.caption("📝 Storico (Modifica qui sotto)")
    
    column_config = {
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=OPZIONI, required=True),
        "Note": st.column_config.TextColumn("Note")
    }

    df_modificato = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )

    # Confronto sicuro resettando l'indice per evitare falsi positivi
    if not df.reset_index(drop=True).equals(df_modificato.reset_index(drop=True)):
        if st.button("💾 Salva Modifiche Tabella", type="primary"):
            gestisci_dati("write", df_modificato)
            st.toast("Aggiornato!", icon="💾")
            st.rerun()
else:
    st.info("Nessun dato trovato.")
    
