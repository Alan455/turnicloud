import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Mobile ---
st.set_page_config(page_title="Turni App", page_icon="📱", layout="centered")

# --- CSS per nascondere elementi inutili e abbellire ---
st.markdown("""
    <style>
    /* Nasconde il menu in alto a destra e il footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Spaziatura più compatta per mobile */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Categorie con Emojis (Migliora lettura visiva) ---
OPZIONI_TURNI = {
    "Mattina": "☀️",
    "Pomeriggio": "🌤️",
    "Sera": "🌆",
    "Notte": "🌙",
    "Ferie": "Fn🏖️", # Fn = Ferie (Emoji per estetica)
    "Malattia": "Fn🤒",
    "Permesso": "Fn📝"
}
LISTA_TIPI = list(OPZIONI_TURNI.keys())

# --- Connessione Google ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    try:
        df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0)
        df = df.dropna(how="all")
        if "Note" not in df.columns: df["Note"] = ""
        df["Note"] = df["Note"].fillna("").astype(str)
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
        df = df.dropna(subset=["Data"])
        return df
    except:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

def salva_dati(df):
    try:
        df["Data"] = pd.to_datetime(df["Data"]).dt.strftime('%Y-%m-%d')
        df = df.sort_values(by="Data", ascending=False)
        conn.update(worksheet="Foglio1", data=df)
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

# --- UI PRINCIPALE ---

# 1. INTESTAZIONE (Semplice e pulita)
st.title("📅 I Miei Turni")

# 2. SEZIONE INSERIMENTO (Espandibile ma aperta di default)
# Usiamo un container con bordo per separarlo visivamente
with st.container(border=True):
    st.subheader("Nuovo Inserimento")
    
    # Riga 1: Data (con pulsanti rapidi "Oggi/Domani" sarebbe top, ma date_input è solido)
    data_input = st.date_input("Seleziona Data", datetime.today(), format="DD/MM/YYYY")
    
    # Riga 2: Tipo Turno con "Pills" (Bottoni cliccabili)
    # Se hai streamlit vecchio usa st.radio(..., horizontal=True)
    try:
        tipo_turno = st.pills("Tipo di Turno", LISTA_TIPI, selection_mode="single")
    except AttributeError:
        tipo_turno = st.radio("Tipo di Turno", LISTA_TIPI, horizontal=True)

    if not tipo_turno:
        st.caption("👆 Seleziona un turno per continuare")

    # Riga 3: Note
    note_input = st.text_input("Note (opzionale)", placeholder="Es. Cambio con Marco")

    # Riga 4: BOTTONE GIGANTE (Full width per pollice facile)
    if st.button("SALVA TURNO ✅", type="primary", use_container_width=True):
        if tipo_turno:
            df = carica_dati()
            nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
            df = pd.concat([df, nuova], ignore_index=True)
            salva_dati(df)
            st.toast("Salvato con successo!", icon="🎉")
            st.rerun()
        else:
            st.warning("Seleziona che tipo di turno hai fatto!")

# 3. STATISTICHE VELOCI (Mini dashboard)
df = carica_dati()
if not df.empty:
    mese_corr = datetime.now().month
    df["Data_dt"] = pd.to_datetime(df["Data"])
    df_mese = df[df["Data_dt"].dt.month == mese_corr]
    
    col1, col2 = st.columns(2)
    col1.metric("Turni questo mese", len(df_mese))
    # Calcola ultimo turno inserito
    ultimo_turno = df.iloc[0]
    col2.metric("Ultimo ins.", f"{ultimo_turno['Tipo']} ({ultimo_turno['Data'].strftime('%d/%m')})")

st.markdown("---")

# 4. LISTA TURNI A "SCHEDE" (Card View)
st.subheader("Storico Recente")

if not df.empty:
    # Mostriamo solo gli ultimi 15 per velocità
    for index, row in df.head(15).iterrows():
        
        # Scegliamo colore bordo/emoji in base al turno
        tipo = row['Tipo']
        emoji = OPZIONI_TURNI.get(tipo, "📅")
        
        # Creiamo la "Scheda"
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            
            with c1:
                # Icona grande
                st.markdown(f"<h2 style='text-align: center; margin:0;'>{emoji}</h2>", unsafe_allow_html=True)
            
            with c2:
                # Dati Turno
                data_fmt = row['Data'].strftime('%d/%m/%Y')
                # Giorni della settimana in ita (hack veloce)
                giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
                nome_giorno = giorni[row['Data'].weekday()]
                
                st.markdown(f"**{nome_giorno} {data_fmt}**")
                st.caption(f"{tipo} • {row['Note']}")
            
            with c3:
                # Tasto Cancella (Piccolo cestino)
                if st.button("🗑️", key=f"del_{index}"):
                    df = df.drop(index)
                    salva_dati(df)
                    st.rerun()
else:
    st.info("Nessun turno inserito.")

# 5. LINK ALLA MODALITÀ AVANZATA (Se serve modificare in massa)
with st.expander("🛠️ Modalità Tabella (Modifica/Correggi)"):
    st.caption("Usa questa tabella se devi modificare vecchi inserimenti.")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("Salva Modifiche Tabella"):
        salva_dati(edited)
        st.rerun()
        
