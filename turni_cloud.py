import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Turni App", page_icon="📅", layout="centered")

# --- CSS: RENDERE I BOTTONI "CELLE DI CALENDARIO" ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Stile Griglia Calendario */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.2rem; /* Spazio minimo tra i giorni */
    }
    
    /* Bottoni dei giorni */
    div[data-testid="stButton"] button {
        width: 100%;
        padding: 0px;
        height: 50px; /* Altezza fissa per quadrati */
        border-radius: 8px;
        border: 1px solid #eee;
        font-weight: bold;
        font-size: 14px;
    }
    
    /* Giorno Selezionato (Evidenziato) */
    .selected-day {
        border: 2px solid #ff4b4b !important;
        background-color: #ffebeb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- STATO E COSTANTI ---
OPZIONI = ["Mattina", "Pomeriggio", "Sera", "Notte", "Ferie", "Malattia", "Ima"]
ICONE = {
    "Mattina": "☀️", "Pomeriggio": "🌤️", "Sera": "🌆", 
    "Notte": "🌙", "Ferie": "🏖️", "Malattia": "🤒", "Ima": "🏥"
}

if 'anno_view' not in st.session_state:
    st.session_state.anno_view = datetime.now().year
if 'mese_view' not in st.session_state:
    st.session_state.mese_view = datetime.now().month
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None # Nessun giorno selezionato all'inizio

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONI ---
def gestisci_dati(mode="read", df_in=None):
    try:
        if mode == "read":
            df = conn.read(worksheet="Foglio1", usecols=[0, 1, 2], ttl=0)
            if "Tipo" not in df.columns: df["Tipo"] = ""
            if "Note" not in df.columns: df["Note"] = ""
            df["Note"] = df["Note"].fillna("").astype(str)
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce').dt.date
            return df.dropna(subset=["Data"])
        elif mode == "write":
            df_in["Data"] = pd.to_datetime(df_in["Data"]).dt.strftime('%Y-%m-%d')
            conn.update(worksheet="Foglio1", data=df_in)
            return True
    except:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

def naviga_mese(delta):
    m = st.session_state.mese_view + delta
    y = st.session_state.anno_view
    if m > 12: m, y = 1, y + 1
    elif m < 1: m, y = 12, y - 1
    st.session_state.mese_view = m
    st.session_state.anno_view = y
    st.session_state.selected_date = None # Reset selezione al cambio mese

# --- UI: NAVIGAZIONE ---
c_prev, c_title, c_next = st.columns([1, 4, 1], vertical_alignment="center")
with c_prev:
    if st.button("◀", key="prev"): naviga_mese(-1); st.rerun()
with c_next:
    if st.button("▶", key="next"): naviga_mese(1); st.rerun()
with c_title:
    # Nome Mese
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
        nome = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y').capitalize()
    except:
        nome = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y')
    st.markdown(f"<h3 style='text-align: center; margin:0;'>{nome}</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- UI: GRIGLIA CALENDARIO (CLICCABILE) ---
df = gestisci_dati("read")

# Intestazione giorni
giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
cols = st.columns(7)
for i, g in enumerate(giorni):
    cols[i].markdown(f"<div style='text-align:center; font-size:12px; color:gray'>{g}</div>", unsafe_allow_html=True)

# Generazione Griglia
cal_matrix = calendar.monthcalendar(st.session_state.anno_view, st.session_state.mese_view)

# Mappa rapida {giorno: (emoji, tipo, nota)}
turni_mese = {}
mask = (pd.to_datetime(df["Data"]).dt.year == st.session_state.anno_view) & \
       (pd.to_datetime(df["Data"]).dt.month == st.session_state.mese_view)
for _, row in df[mask].iterrows():
    turni_mese[row["Data"].day] = (ICONE.get(row["Tipo"], ""), row["Tipo"], row["Note"])

# Disegno i bottoni
for week in cal_matrix:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("") # Cella vuota
        else:
            # Contenuto bottone
            emoji = turni_mese.get(day, ("", "", ""))[0]
            label = f"{day}\n{emoji}"
            
            # Tasto Cliccabile
            # Se clicchi, salviamo quel giorno in session_state
            if cols[i].button(label, key=f"btn_{day}"):
                st.session_state.selected_date = date(st.session_state.anno_view, st.session_state.mese_view, day)
                st.rerun()

# --- UI: PANNELLO MODIFICA (Compare solo se clicchi) ---
if st.session_state.selected_date:
    sel_dt = st.session_state.selected_date
    st.markdown("---")
    st.markdown(f"#### ✏️ Modifica: {sel_dt.strftime('%d/%m/%Y')}")
    
    # Cerchiamo se esiste già un turno in quel giorno
    turno_esistente = df[df["Data"] == sel_dt]
    
    # Valori di default
    def_tipo = None
    def_note = ""
    esiste = False
    
    if not turno_esistente.empty:
        esiste = True
        def_tipo = turno_esistente.iloc[0]["Tipo"]
        def_note = turno_esistente.iloc[0]["Note"]
        # Se il tipo nel file non è nella lista (es. vecchio), fallback
        if def_tipo not in OPZIONI: def_tipo = None 

    # Form di Modifica
    with st.container(border=True):
        tipo_sel = st.pills("Tipo", OPZIONI, selection_mode="single", default=def_tipo)
        note_sel = st.text_input("Note", value=def_note)
        
        c_salva, c_elimina = st.columns(2)
        
        with c_salva:
            if st.button("💾 SALVA", type="primary"):
                # 1. Rimuovi vecchio se c'era
                df = df[df["Data"] != sel_dt]
                # 2. Aggiungi nuovo
                if tipo_sel:
                    nuova = pd.DataFrame([{"Data": sel_dt, "Tipo": tipo_sel, "Note": note_sel}])
                    df = pd.concat([df, nuova], ignore_index=True)
                    gestisci_dati("write", df)
                    st.toast("Salvato!", icon="✅")
                    st.rerun()
                else:
                    st.warning("Seleziona un tipo!")

        with c_elimina:
            if esiste:
                if st.button("🗑️ ELIMINA"):
                    df = df[df["Data"] != sel_dt] # Filtra via quel giorno
                    gestisci_dati("write", df)
                    st.toast("Eliminato!", icon="🗑️")
                    st.session_state.selected_date = None # Chiudi pannello
                    st.rerun()
            else:
                st.write("") # Spazio vuoto se non c'è nulla da eliminare

else:
    # Messaggio guida se non hai cliccato nulla
    st.markdown("---")
    st.caption("👆 Tocca un giorno nel calendario per aggiungere o modificare un turno.")
    
