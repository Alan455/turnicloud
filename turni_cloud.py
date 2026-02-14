import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE FULL SCREEN ---
# CAMBIAMENTO FONDAMENTALE: layout="wide" usa tutto lo schermo
st.set_page_config(page_title="Turni App", page_icon="📅", layout="wide")

# --- CSS: RIMUOVERE BORDI E MARGINI ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 1. FORZARE I MARGINI AL MINIMO ASSOLUTO */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 5px !important;  /* Quasi zero margine a sinistra */
        padding-right: 5px !important; /* Quasi zero margine a destra */
        max-width: 100% !important;
    }
    
    /* 2. GESTIONE COLONNE SU MOBILE */
    div[data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0px !important;
        padding: 0px !important;
    }
    
    /* 3. GRIGLIA ORRIZONTALE FORZATA */
    div[data-testid="stHorizontalBlock"] {
        gap: 2px !important;
    }
    
    /* 4. BOTTONI QUADRATI E COMPATTI */
    div[data-testid="stButton"] button {
        width: 100% !important;
        padding: 0px !important;
        height: 55px !important; /* Altezza fissa */
        border-radius: 6px !important;
        font-size: 11px !important;
        line-height: 1.1 !important;
        margin: 0px !important;
        white-space: pre-wrap !important; /* Per mandare a capo l'emoji */
    }
    
    /* Testo intestazione giorni (Lun, Mar...) molto piccolo */
    div[data-testid="stMarkdownContainer"] p {
        font-size: 10px !important;
        margin-bottom: 0px !important;
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
    st.session_state.selected_date = None

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
    st.session_state.selected_date = None

# --- HEADER NAVIGAZIONE ---
c_prev, c_title, c_next = st.columns([1, 6, 1], gap="small", vertical_alignment="center")

with c_prev:
    if st.button("◀", key="prev"): naviga_mese(-1); st.rerun()
with c_next:
    if st.button("▶", key="next"): naviga_mese(1); st.rerun()
with c_title:
    # Nome Mese
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
        nome = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y').upper()
    except:
        nome = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y')
    st.markdown(f"<h4 style='text-align: center; margin:0;'>{nome}</h4>", unsafe_allow_html=True)

st.write("") # Spacer

# --- CALENDARIO GRIGLIA ---
df = gestisci_dati("read")

# 1. Intestazione Giorni
giorni = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
cols_header = st.columns(7)
for i, g in enumerate(giorni):
    cols_header[i].markdown(f"<div style='text-align:center; font-size:9px; font-weight:bold; color:#888'>{g}</div>", unsafe_allow_html=True)

# 2. Matrice Giorni
cal_matrix = calendar.monthcalendar(st.session_state.anno_view, st.session_state.mese_view)
turni_mese = {}
mask = (pd.to_datetime(df["Data"]).dt.year == st.session_state.anno_view) & \
       (pd.to_datetime(df["Data"]).dt.month == st.session_state.mese_view)

for _, row in df[mask].iterrows():
    turni_mese[row["Data"].day] = ICONE.get(row["Tipo"], "")

# 3. Disegno Bottoni
for week in cal_matrix:
    # Gap "small" aiuta a tenere i bottoni vicini
    cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            emoji = turni_mese.get(day, "")
            # Se c'è l'emoji metto quella, altrimenti il numero
            label = f"{day}\n{emoji}" if emoji else f"{day}"
            
            # Se è il giorno selezionato, usiamo type="primary" per evidenziarlo
            is_selected = (st.session_state.selected_date and 
                           st.session_state.selected_date.day == day and 
                           st.session_state.selected_date.month == st.session_state.mese_view)
            
            tipo_btn = "primary" if is_selected else "secondary"
            
            if cols[i].button(label, key=f"btn_{day}", type=tipo_btn):
                st.session_state.selected_date = date(st.session_state.anno_view, st.session_state.mese_view, day)
                st.rerun()

# --- MODALE MODIFICA (BOTTOM SHEET) ---
if st.session_state.selected_date:
    sel_dt = st.session_state.selected_date
    st.markdown("---")
    st.markdown(f"**Modifica {sel_dt.strftime('%d/%m')}**")
    
    turno_esistente = df[df["Data"] == sel_dt]
    def_tipo = None
    def_note = ""
    
    if not turno_esistente.empty:
        def_tipo = turno_esistente.iloc[0]["Tipo"]
        def_note = turno_esistente.iloc[0]["Note"]
        if def_tipo not in OPZIONI: def_tipo = None 

    # Controlli
    c_sel, c_note = st.columns([1, 1.5])
    with c_sel:
        # Selectbox è meglio di pills in spazi stretti
        tipo_sel = st.selectbox("Tipo", OPZIONI, index=OPZIONI.index(def_tipo) if def_tipo else 0, label_visibility="collapsed")
    with c_note:
        note_sel = st.text_input("Note", value=def_note, placeholder="Note...", label_visibility="collapsed")
        
    st.write("")
    
    # Bottoni Azione
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💾 SALVA", type="primary", use_container_width=True):
            df = df[df["Data"] != sel_dt] 
            nuova = pd.DataFrame([{"Data": sel_dt, "Tipo": tipo_sel, "Note": note_sel}])
            gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.session_state.selected_date = None
            st.rerun()
    with b2:
        if not turno_esistente.empty:
            if st.button("🗑️ ELIMINA", use_container_width=True):
                df = df[df["Data"] != sel_dt]
                gestisci_dati("write", df)
                st.toast("Cancellato!", icon="🗑️")
                st.session_state.selected_date = None
                st.rerun()
        else:
            if st.button("CHIUDI", use_container_width=True):
                st.session_state.selected_date = None
                st.rerun()
                
