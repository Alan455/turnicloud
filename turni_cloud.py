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
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 2rem !important;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 8px;
    }
    /* Stile per i box dei totali */
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- OPZIONI ---
OPZIONI = ["Mattina", "Pomeriggio", "Sera", "Notte", "Ferie", "Malattia", "Ima"]

conn = st.connection("gsheets", type=GSheetsConnection)

def gestisci_dati(mode="read", df_in=None):
    try:
        if mode == "read":
            df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0)
            if "Tipo" not in df.columns: df["Tipo"] = ""
            if "Note" not in df.columns: df["Note"] = ""
            df["Note"] = df["Note"].fillna("").astype(str)
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
            return df.dropna(subset=["Data"]).sort_values(by="Data", ascending=False)
        elif mode == "write":
            df_in["Data"] = pd.to_datetime(df_in["Data"]).dt.strftime('%Y-%m-%d')
            conn.update(worksheet="Foglio1", data=df_in)
            return True
    except Exception as e:
        st.error(f"Errore database: {e}")
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- 1. SEZIONE INSERIMENTO ---
st.markdown("### ➕ Nuovo Turno")
with st.container():
    c1, c2 = st.columns([1, 1.5])
    with c1:
        data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    with c2:
        tipo_turno = st.selectbox("Tipo", OPZIONI)

    c3, c4 = st.columns([2, 1])
    with c3:
        note_input = st.text_input("Note", placeholder="Note...")
    with c4:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        if st.button("SALVA"):
            df = gestisci_dati("read")
            nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.rerun()

st.divider()

# --- 2. NUOVA SEZIONE: TOTALI TURNI ---
df = gestisci_dati("read")

if not df.empty:
    st.markdown("### 📊 Riepilogo Mese Corrente")
    
    # Filtriamo i dati per il mese e anno attuale
    oggi = datetime.now()
    df_mese = df[
        (pd.to_datetime(df["Data"]).dt.month == oggi.month) & 
        (pd.to_datetime(df["Data"]).dt.year == oggi.year)
    ]
    
    # Calcolo totali
    totale_giorni = len(df_mese)
    # Escludiamo Ferie, Malattia e Ima dal conteggio dei turni "lavorati" effettivi se vuoi, 
    # oppure mostriamo tutto. Qui mostro il totale righe nel mese.
    
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("Giorni totali", totale_giorni)
    
    # Mostriamo il dettaglio in un piccolo expander per non occupare spazio
    with st.expander("Dettaglio turni"):
        conteggio = df_mese["Tipo"].value_counts()
        for opzione in OPZIONI:
            qta = conteggio.get(opzione, 0)
            if qta > 0:
                st.write(f"**{opzione}**: {qta}")

    st.divider()

    # --- 3. TABELLA STORICO ---
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

    if st.button("💾 Salva Modifiche Tabella", type="primary"):
        if not df.reset_index(drop=True).equals(df_modificato.reset_index(drop=True)):
            gestisci_dati("write", df_modificato)
            st.toast("Aggiornato!", icon="💾")
            st.rerun()
else:
    st.info("Nessun turno inserito.")
    
