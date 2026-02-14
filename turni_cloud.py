import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Turni App", page_icon="📅", layout="centered")

# --- CSS: MAGIC FIX PER MOBILE ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Riduce i margini generali */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 5rem !important;
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
    }
    
    /* --- CSS PER FORZARE LA GRIGLIA SU MOBILE --- */
    @media (max-width: 640px) {
        /* Impedisce alle colonne di andare a capo (stacking) */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 2px !important; /* Spazio piccolissimo tra i bottoni */
        }
        
        /* Permette alle colonne di diventare piccolissime */
        div[data-testid="column"] {
            flex: 1 !important;
            width: auto !important;
            min-width: 0px !important;
        }
        
        /* Stile Bottoni Mobile: Testo piccolo, niente padding */
        div[data-testid="stButton"] button {
            padding: 0px !important;
            font-size: 10px !important; /* Testo piccolo per farci stare l'emoji */
            height: 45px !important;
            line-height: 1.2 !important;
            white-space: pre-wrap !important; /* Permette all'emoji di andare a capo se serve */
        }
        
        /* Nasconde i giorni della settimana testuali se troppo piccoli, 
           o li fa molto piccoli */
        div[data-testid="stMarkdownContainer"] p {
            font-size: 10px !important;
        }
    }
    
    /* Stile Desktop (Normale) */
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 6px;
        border: 1px solid #ddd;
        font-weight: bold;
    }
    
    /* Giorno Selezionato */
    div[data-testid="stButton"] button:focus {
        border-color: #ff4b4b;
        background-color: #ffebeb;
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

# --- UI: NAVIGAZIONE ---
# Usiamo gap="small" per tenere i tasti vicini
c_prev, c_title, c_next = st.columns([1, 4, 1], gap="small", vertical_alignment="center")

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

st.write("") # Spaziatura minima

# --- UI: GRIGLIA CALENDARIO ---
df = gestisci_dati("read")

# 1. Intestazione Giorni (Lun Mar...)
giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
cols_header = st.columns(7)
for i, g in enumerate(giorni):
    # Riduciamo il font al minimo per mobile
    cols_header[i].markdown(f"<div style='text-align:center; font-size:11px; font-weight:bold; color:#666'>{g}</div>", unsafe_allow_html=True)

# 2. Dati Turni
cal_matrix = calendar.monthcalendar(st.session_state.anno_view, st.session_state.mese_view)

turni_mese = {}
mask = (pd.to_datetime(df["Data"]).dt.year == st.session_state.anno_view) & \
       (pd.to_datetime(df["Data"]).dt.month == st.session_state.mese_view)
for _, row in df[mask].iterrows():
    turni_mese[row["Data"].day] = ICONE.get(row["Tipo"], "")

# 3. Disegno Griglia
for week in cal_matrix:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("") # Vuoto
        else:
            emoji = turni_mese.get(day, "")
            # Se c'è l'emoji, mettiamo solo quella (più visibile su mobile)
            # Altrimenti solo il numero del giorno
            if emoji:
                label = f"{day}\n{emoji}"
            else:
                label = f"{day}"
            
            if cols[i].button(label, key=f"btn_{day}"):
                st.session_state.selected_date = date(st.session_state.anno_view, st.session_state.mese_view, day)
                st.rerun()

# --- UI: PANNELLO MODIFICA ---
if st.session_state.selected_date:
    sel_dt = st.session_state.selected_date
    st.markdown("---")
    
    # Intestazione pannello
    st.markdown(f"#### ✏️ {sel_dt.strftime('%d/%m')} - Modifica")
    
    turno_esistente = df[df["Data"] == sel_dt]
    def_tipo = None
    def_note = ""
    esiste = False
    
    if not turno_esistente.empty:
        esiste = True
        def_tipo = turno_esistente.iloc[0]["Tipo"]
        def_note = turno_esistente.iloc[0]["Note"]
        if def_tipo not in OPZIONI: def_tipo = None 

    # Box Modifica
    with st.container(border=True):
        # Usiamo selectbox che è più sicuro su mobile rispetto a pills in spazi stretti
        tipo_sel = st.selectbox("Tipo Turno", OPZIONI, index=OPZIONI.index(def_tipo) if def_tipo else 0, label_visibility="collapsed")
        note_sel = st.text_input("Note", value=def_note, placeholder="Note...")
        
        st.write("") # Spazio
        
        c_salva, c_elimina = st.columns(2)
        with c_salva:
            if st.button("💾 SALVA", type="primary"):
                df = df[df["Data"] != sel_dt] # Rimuovi vecchio
                nuova = pd.DataFrame([{"Data": sel_dt, "Tipo": tipo_sel, "Note": note_sel}])
                gestisci_dati("write", pd.concat([df, nuova], ignore_index=True))
                st.toast("Salvato!", icon="✅")
                st.session_state.selected_date = None
                st.rerun()

        with c_elimina:
            if esiste:
                if st.button("🗑️ ELIMINA"):
                    df = df[df["Data"] != sel_dt]
                    gestisci_dati("write", df)
                    st.toast("Eliminato!", icon="🗑️")
                    st.session_state.selected_date = None
                    st.rerun()
                    
