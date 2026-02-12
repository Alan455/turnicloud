import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# --- Configurazione Pagina ---
st.set_page_config(page_title="Gestione Turni Auto", page_icon="⚡", layout="wide")

FILE_DATA = "turni_lavoro.csv"

# --- Categorie ---
CATEGORIE_LAVORO = ["Mattina", "Pomeriggio", "Sera", "Notte"]
CATEGORIE_ASSENZA = ["Ferie", "Malattia", "Ima", "Permesso"]
TUTTE_OPZIONI = CATEGORIE_LAVORO + CATEGORIE_ASSENZA

# --- Funzioni di Supporto ---
def carica_dati():
    if not os.path.exists(FILE_DATA):
        return pd.DataFrame({
            "Data": pd.Series(dtype='datetime64[ns]'),
            "Tipo": pd.Series(dtype='str'),
            "Note": pd.Series(dtype='str')
        })
    try:
        df = pd.read_csv(FILE_DATA)
        
        # Gestione valori vuoti e tipi
        if "Note" in df.columns:
            df["Note"] = df["Note"].fillna("").astype(str)
        else:
            df["Note"] = ""
            
        # Conversione Data sicura
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        return df
    except Exception as e:
        st.error(f"Errore lettura file: {e}")
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

def salva_dati(df):
    try:
        # Assicuriamoci che la data sia corretta e ordiniamo
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        df = df.sort_values(by="Data", ascending=False)
        df.to_csv(FILE_DATA, index=False)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

# --- SIDEBAR: Inserimento Rapido ---
st.sidebar.header("➕ Nuovo Inserimento")

with st.sidebar.form("nuovo_turno_form", clear_on_submit=True):
    data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    tipo_turno = st.selectbox("Tipo", TUTTE_OPZIONI)
    note_input = st.text_input("Note")
    submitted = st.form_submit_button("Aggiungi")

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
        st.toast("✅ Turno aggiunto e salvato!", icon="💾")
        # Non serve rerun qui perché il form ricarica la pagina

st.sidebar.divider()

# --- SIDEBAR: Filtri ---
st.sidebar.subheader("📊 Filtro Mese")
mese_corrente = datetime.now().month
anno_corrente = datetime.now().year
col_m, col_a = st.sidebar.columns(2)
with col_m:
    mese_sel = st.selectbox("Mese", range(1, 13), index=mese_corrente-1)
with col_a:
    anno_sel = st.number_input("Anno", value=anno_corrente)

# --- CORPO PRINCIPALE ---
st.title("⚡ Gestione Turni (Auto-Save)")

# 1. Caricamento Iniziale
df = carica_dati()

# --- Sezione Statistiche ---
if not df.empty:
    df_calc = df.copy()
    df_calc["Data"] = pd.to_datetime(df_calc["Data"])
    
    # Filtro
    mask = (df_calc["Data"].dt.month == mese_sel) & (df_calc["Data"].dt.year == anno_sel)
    df_filtrato = df_calc.loc[mask]
    
    # Calcolo Semplificato (Totale Giornate)
    counts = df_filtrato['Tipo'].value_counts()
    
    lavorati = sum(counts.get(k, 0) for k in CATEGORIE_LAVORO)
    malattia = counts.get("Malattia", 0)
    ima = counts.get("Ima", 0)
    ferie = counts.get("Ferie", 0)
    
    totale_giornate = lavorati + malattia + ima + ferie

    # Visualizzazione Unica
    st.info(f"Riepilogo **{mese_sel}/{anno_sel}**")
    st.metric("TOTALE GIORNATE", totale_giornate, help="Include Lavoro, Malattia, Ima, Ferie")

else:
    st.info("Nessun dato. Inizia dalla barra laterale.")

st.divider()

# --- Sezione Editor Automatico ---
st.subheader("✏️ Modifica / Elimina")
st.caption("Modifica le celle o cancella le righe (seleziona e premi CANC). Il salvataggio è automatico.")

if not df.empty:
    # Editor Config
    column_config = {
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=TUTTE_OPZIONI, required=True),
        "Note": st.column_config.TextColumn("Note", default="")
    }

    # EDITOR INTERATTIVO
    # Quando modifichi qualcosa qui, Streamlit ricarica lo script e restituisce il nuovo dataframe in 'df_modificato'
    df_modificato = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_turni"
    )

    # --- LOGICA AUTO-SALVATAGGIO ---
    # Confrontiamo il dataframe caricato dal disco (df) con quello modificato dall'utente (df_modificato)
    # Dobbiamo resettare l'indice per essere sicuri che il confronto sia corretto
    if not df.reset_index(drop=True).equals(df_modificato.reset_index(drop=True)):
        salva_dati(df_modificato)
        st.toast("Modifiche salvate automaticamente!", icon="✅")
        # Opzionale: un rerun assicura che le statistiche si aggiornino istantaneamente
        # ma potrebbe causare un leggero "sfarfallio". Se ti dà fastidio, rimuovi la riga sotto.
        # st.rerun()

        