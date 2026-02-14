import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PAGINA MOBILE ---
st.set_page_config(page_title="Turni", page_icon="📱", layout="centered")

# --- CSS: OTTIMIZZAZIONE TOUCH ---
st.markdown("""
    <style>
    /* Nasconde header/footer inutili */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Spaziatura ottimizzata per le dita */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important; /* Spazio extra in basso per lo scroll */
    }
    
    /* Pulsanti grandi e facili da premere */
    div[data-testid="stButton"] button {
        width: 100%;
        height: 50px; /* Più alto per il dito */
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
    }
    
    /* Stile per i totali */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATI ---
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
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- TITOLO MINIMAL ---
st.markdown("### 📅 I Miei Turni")

# --- 1. NUOVO INSERIMENTO (Ottimizzato) ---
# Usiamo un container con bordo per evidenziare l'area di azione
with st.container(border=True):
    st.caption("Nuovo Inserimento")
    
    # DATA: Sempre default a OGGI
    col_data, col_note = st.columns([1, 1.5])
    with col_data:
        data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY", label_visibility="collapsed")
    with col_note:
        note_input = st.text_input("Note", placeholder="Note opzionali...", label_visibility="collapsed")

    # TIPO: Usiamo i PILLS (Pillole) o RADIO orizzontale
    # È molto più veloce del menu a tendina: un tocco e via.
    # Se st.pills non va (versione vecchia), usa st.radio
    try:
        tipo_turno = st.pills("Tipo", OPZIONI, selection_mode="single", label_visibility="collapsed")
    except AttributeError:
        tipo_turno = st.radio("Tipo", OPZIONI, horizontal=True, label_visibility="collapsed")

    # SPAZIO E BOTTONE
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    # Il bottone è disabilitato se non hai scelto il turno (Feedback visivo)
    if st.button("SALVA TURNO ✅", type="primary", disabled=(not tipo_turno)):
        df = gestisci_dati("read")
        nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
        gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
        st.toast(f"Salvato: {tipo_turno} il {data_input.strftime('%d/%m')}", icon="🎉")
        st.rerun()

# --- 2. DASHBOARD TOTALI (Compatta) ---
df = gestisci_dati("read")

if not df.empty:
    oggi = datetime.now()
    # Filtro mese corrente
    mask_mese = (pd.to_datetime(df["Data"]).dt.month == oggi.month) & (pd.to_datetime(df["Data"]).dt.year == oggi.year)
    df_mese = df[mask_mese]
    
    # Calcoli veloci
    tot_turni = len(df_mese)
    # Cerchiamo l'ultimo inserito per conferma visiva
    ultimo = df.iloc[0]
    txt_ultimo = f"{ultimo['Tipo']} ({ultimo['Data'].strftime('%d/%m')})"

    # Visualizzazione a 2 colonne
    k1, k2 = st.columns(2)
    k1.metric("Totale Mese", tot_turni)
    k2.metric("Ultimo Inserito", txt_ultimo)

    st.markdown("---")

    # --- 3. TABELLA STORICO ---
    st.caption("Modifica o Cancella qui sotto 👇")
    
    column_config = {
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True, width="small"),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=OPZIONI, required=True, width="medium"),
        "Note": st.column_config.TextColumn("Note", width="small")
    }

    df_modificato = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=350 # Altezza fissa per scorrere bene col dito
    )

    if st.button("💾 SALVA MODIFICHE TABELLA"):
        # Reset index serve per confrontare i dati ignorando l'ordine degli indici
        if not df.reset_index(drop=True).equals(df_modificato.reset_index(drop=True)):
            gestisci_dati("write", df_modificato)
            st.toast("Tabella Aggiornata!", icon="💾")
            st.rerun()
else:
    st.info("Inizia aggiungendo un turno sopra! 👆")
