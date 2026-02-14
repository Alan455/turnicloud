import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE MOBILE ---
st.set_page_config(page_title="Turni App", page_icon="📱", layout="centered")

# --- 2. CSS "APP STYLE" (Il trucco per la grafica) ---
st.markdown("""
    <style>
    /* Nasconde menu standard */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Spaziatura ottimizzata per smartphone */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Stile Bottoni: Arrotondati e Moderni */
    div[data-testid="stButton"] button {
        border-radius: 12px;
        height: 45px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Stile delle Card (Tessere) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 15px;
        background-color: #ffffff;
        /* box-shadow: 0 1px 3px rgba(0,0,0,0.05); Rimosso per pulizia */
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATI ---
OPZIONI = ["Mattina", "Pomeriggio", "Sera", "Notte", "Ferie", "Malattia", "Ima"]

# Mappa icone per un look grafico migliore
ICONE = {
    "Mattina": "☀️", "Pomeriggio": "🌤️", "Sera": "🌆", 
    "Notte": "🌙", "Ferie": "🏖️", "Malattia": "🤒", "Ima": "🏥"
}

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
    except Exception:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

# --- UI: HEADER ---
st.markdown("### 👋 Ciao, ecco i tuoi turni")

# --- UI: HERO SECTION (Riepilogo Mese) ---
df = gestisci_dati("read")
oggi = datetime.now()

if not df.empty:
    mask_mese = (pd.to_datetime(df["Data"]).dt.month == oggi.month) & (pd.to_datetime(df["Data"]).dt.year == oggi.year)
    turni_mese = len(df[mask_mese])
    
    # Card Riepilogo in alto (Stile Widget)
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.caption(f"Totale {oggi.strftime('%B').capitalize()}")
            st.markdown(f"<h1 style='margin: -10px 0 0 0;'>{turni_mese}</h1>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='text-align: right; font-size: 2rem;'>📅</div>", unsafe_allow_html=True)
        
        # Barra di "progresso" mese (estetica)
        giorni_nel_mese = 31 # Semplificazione visiva
        progresso = min(turni_mese / giorni_nel_mese, 1.0)
        st.progress(progresso)

st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

# --- UI: AZIONE (Inserimento Flottante) ---
with st.expander("➕ AGGIUNGI NUOVO TURNO", expanded=True):
    # Riga 1
    c_date, c_type = st.columns([1.2, 1.5])
    with c_date:
        d_in = st.date_input("Data", datetime.today(), format="DD/MM/YYYY", label_visibility="collapsed")
    with c_type:
        t_in = st.selectbox("Tipo", OPZIONI, label_visibility="collapsed")
    
    # Riga 2
    c_note, c_btn = st.columns([2, 1])
    with c_note:
        n_in = st.text_input("Note", placeholder="Note...", label_visibility="collapsed")
    with c_btn:
        if st.button("SALVA", type="primary"):
            nuova = pd.DataFrame([{"Data": d_in, "Tipo": t_in, "Note": n_in}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.rerun()

# --- UI: LISTA "APP STYLE" (Ultime 10 Attività) ---
st.caption("ULTIMI INSERIMENTI")

if not df.empty:
    for i, row in df.head(10).iterrows():
        # Creiamo una "Card" per ogni turno
        with st.container(border=True):
            # Layout a griglia: Icona | Info | Tasto Cancella
            k1, k2, k3 = st.columns([0.7, 3, 0.5])
            
            with k1:
                # Icona grande centrata
                icona = ICONE.get(row['Tipo'], "📅")
                st.markdown(f"<div style='font-size: 1.8rem; text-align: center;'>{icona}</div>", unsafe_allow_html=True)
            
            with k2:
                # Data e Tipo
                data_str = row['Data'].strftime('%d/%m')
                giorno = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][row['Data'].weekday()]
                
                # HTML per formattazione precisa
                st.markdown(f"""
                <div style='line-height: 1.2;'>
                    <span style='font-weight: bold; font-size: 1rem;'>{row['Tipo']}</span>
                    <br>
                    <span style='color: gray; font-size: 0.8rem;'>{giorno} {data_str}</span>
                    <span style='color: #888; font-size: 0.8rem; font-style: italic;'> {row['Note']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with k3:
                # Bottone Cancella invisibile ma cliccabile
                if st.button("✕", key=f"del_{i}"):
                    gestisci_dati("write", df.drop(i))
                    st.rerun()

    # Link per vedere tutto
    if st.button("Vedi storico completo (Tabella)"):
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("Nessun turno. Aggiungine uno sopra!")
