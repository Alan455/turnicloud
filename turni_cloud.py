import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Pagina ---
st.set_page_config(page_title="Turni Cloud ☁️", page_icon="📱", layout="wide")

# --- Categorie ---
CATEGORIE_LAVORO = ["Mattina", "Pomeriggio", "Sera", "Notte"]
CATEGORIE_ASSENZA = ["Ferie", "Malattia", "Ima", "Permesso"]
TUTTE_OPZIONI = CATEGORIE_LAVORO + CATEGORIE_ASSENZA

# --- Connessione a Google Sheets ---
# Questo crea il collegamento usando i segreti che hai impostato
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    try:
        # Scarica i dati aggiornati dal foglio Google
        df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0)
        # Pulisce i dati vuoti se ce ne sono
        df = df.dropna(how="all")
        
        # Gestione formati
        if "Note" not in df.columns: df["Note"] = ""
        df["Note"] = df["Note"].fillna("").astype(str)
        
        # Converte la data (Google a volte la manda come stringa, a volte come oggetto)
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
        
        # Rimuove righe con date non valide
        df = df.dropna(subset=["Data"])
        
        return df
    except Exception as e:
        st.error(f"Errore connessione Google: {e}")
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

def salva_dati(df):
    try:
        # Ordina per data decrescente
        df["Data"] = pd.to_datetime(df["Data"]).dt.strftime('%Y-%m-%d')
        df = df.sort_values(by="Data", ascending=False)
        
        # Aggiorna tutto il foglio Google
        conn.update(worksheet="Foglio1", data=df)
        st.toast("Salvato su Google Drive!", icon="☁️")
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

# --- SIDEBAR: Inserimento ---
st.sidebar.header("➕ Nuovo Turno")
with st.sidebar.form("nuovo_turno_form", clear_on_submit=True):
    data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    tipo_turno = st.selectbox("Tipo", TUTTE_OPZIONI)
    note_input = st.text_input("Note")
    submitted = st.form_submit_button("Invia al Cloud")

    if submitted:
        df_current = carica_dati()
        nuova_riga = pd.DataFrame([{
            "Data": data_input, 
            "Tipo": tipo_turno, 
            "Note": str(note_input)
        }])
        
        if df_current.empty:
            df_updated = nuova_riga
        else:
            df_updated = pd.concat([df_current, nuova_riga], ignore_index=True)
            
        salva_dati(df_updated)
        # Ricarica forzata per vedere subito i dati aggiornati
        st.rerun() 

st.sidebar.divider()

# --- FILTRI ---
st.sidebar.subheader("📅 Periodo")
mese_corrente = datetime.now().month
anno_corrente = datetime.now().year
c1, c2 = st.sidebar.columns(2)
mese_sel = c1.selectbox("Mese", range(1, 13), index=mese_corrente-1)
anno_sel = c2.number_input("Anno", value=anno_corrente)

# --- CORPO PRINCIPALE ---
st.title("📱 Turni Online (Google Sheets)")

df = carica_dati()

if not df.empty:
    # --- Statistiche ---
    df_calc = df.copy()
    df_calc["Data"] = pd.to_datetime(df_calc["Data"])
    mask = (df_calc["Data"].dt.month == mese_sel) & (df_calc["Data"].dt.year == anno_sel)
    df_filt = df_calc.loc[mask]

    # Contatori
    counts = df_filt['Tipo'].value_counts()
    lavorati = sum(counts.get(k, 0) for k in CATEGORIE_LAVORO)
    assenze = sum(counts.get(k, 0) for k in ["Malattia", "Ima", "Ferie"])
    
    st.info(f"Riepilogo **{mese_sel}/{anno_sel}**")
    col1, col2 = st.columns(2)
    col1.metric("Giorni Lavorati", lavorati)
    col2.metric("Giorni Assenza", assenze) # Malattia+Ima+Ferie

    st.divider()

    # --- EDITOR ---
    st.caption("Modifica qui sotto. Il salvataggio su Google richiede qualche secondo.")
    
    # Configurazione colonne
    column_config = {
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=TUTTE_OPZIONI, required=True),
        "Note": st.column_config.TextColumn("Note")
    }

    df_modificato = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_cloud"
    )

    # Logica di Salvataggio Manuale (Più sicuro col cloud)
    if st.button("💾 Salva Modifiche su Google Drive", type="primary"):
        salva_dati(df_modificato)
        st.rerun()

else:
    st.warning("Il foglio Google sembra vuoto o non raggiungibile.")