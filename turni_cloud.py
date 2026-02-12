import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Configurazione Mobile ---
st.set_page_config(page_title="Turni", page_icon="⚡", layout="centered")

# --- CSS per Compattare al Massimo ---
st.markdown("""
    <style>
    /* Nasconde menu e footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Riduce i margini della pagina */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* Rende i bottoni "X" più piccoli e rossi */
    div[data-testid="stButton"] button {
        padding: 0px 10px;
        min-height: 35px;
    }
    
    /* Rende il testo delle colonne più compatto */
    p {
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Categorie & Emojis ---
OPZIONI_TURNI = {
    "Mattina": "☀️",
    "Pomeriggio": "🌤️",
    "Sera": "🌆",
    "Notte": "🌙",
    "Ferie": "🏖️",
    "Malattia": "🤒",
    "Permesso": "📝"
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

# Titolo minimal
st.markdown("### 📅 I Miei Turni")

# --- SEZIONE INSERIMENTO (Compatta) ---
with st.container():
    # Riga 1: Data e Tipo affiancati per risparmiare spazio verticale
    c1, c2 = st.columns([1, 1.5])
    with c1:
        data_input = st.date_input("Data", datetime.today(), format="DD/MM/YYYY", label_visibility="collapsed")
    with c2:
        tipo_turno = st.selectbox("Tipo", LISTA_TIPI, label_visibility="collapsed")

    # Riga 2: Note e Bottone sulla stessa linea
    c3, c4 = st.columns([2, 1])
    with c3:
        note_input = st.text_input("Note", placeholder="Note opzionali...", label_visibility="collapsed")
    with c4:
        if st.button("➕ SALVA", type="primary", use_container_width=True):
            df = carica_dati()
            nuova = pd.DataFrame([{"Data": data_input, "Tipo": tipo_turno, "Note": note_input}])
            df = pd.concat([df, nuova], ignore_index=True)
            salva_dati(df)
            st.toast("Salvato!", icon="✅")
            st.rerun()

st.divider()

# --- STORICO COMPATTO (Lista) ---
df = carica_dati()

if not df.empty:
    # Statistiche "Inline" (sulla stessa riga)
    mese_corr = datetime.now().month
    count = len(df[pd.to_datetime(df["Data"]).dt.month == mese_corr])
    st.caption(f"Totale turni questo mese: **{count}**")
    
    # Intestazione piccola
    st.markdown("**Ultimi Inserimenti:**")

    # Ciclo per stampare le righe
    for index, row in df.head(10).iterrows(): # Mostra solo ultimi 10 per non intasare
        
        tipo = row['Tipo']
        emoji = OPZIONI_TURNI.get(tipo, "▪️")
        data_fmt = row['Data'].strftime('%d/%m') # Solo giorno/mese (anno inutile)
        giorno_sett = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][row['Data'].weekday()]
        
        # --- LAYOUT RIGA COMPATTA ---
        # Col 1: Data (Piccola) | Col 2: Info Turno (Grande) | Col 3: Cancella (Piccolo)
        k1, k2, k3 = st.columns([1.2, 3, 0.8], vertical_alignment="center")
        
        with k1:
            # Data in grassetto, grigio scuro
            st.markdown(f"<span style='color:#555; font-size:0.9rem'><b>{data_fmt}</b><br><small>{giorno_sett}</small></span>", unsafe_allow_html=True)
            
        with k2:
            # Emoji + Tipo + Nota (tutto su una riga se possibile)
            nota_vis = f" <small style='color:gray'>({row['Note']})</small>" if row['Note'] else ""
            st.markdown(f"<span style='font-size:1rem'>{emoji} <b>{tipo}</b>{nota_vis}</span>", unsafe_allow_html=True)
            
        with k3:
            # Bottone X minimale
            if st.button("✕", key=f"del_{index}"):
                df = df.drop(index)
                salva_dati(df)
                st.rerun()
        
        # Linea sottile di separazione
        st.markdown("<hr style='margin: 0.3rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

    # Link per vedere tutto se serve
    with st.expander("Vedi tabella completa"):
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("Nessun dato.")
    
