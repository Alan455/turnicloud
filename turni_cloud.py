import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE E CSS ---
st.set_page_config(page_title="Turni App", page_icon="📅", layout="centered")

st.markdown("""
    <style>
    /* Nasconde elementi inutili */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Ottimizzazione Mobile */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Stile Bottoni */
    div[data-testid="stButton"] button {
        border-radius: 10px;
        height: 45px;
        font-weight: bold;
    }
    
    /* Stile Calendario */
    div[data-testid="stDataFrame"] {
        font-size: 16px; 
    }
    
    /* --- CORREZIONE COLORI --- */
    .summary-box {
        background-color: #262730; /* Sfondo Scuro (Grigio/Nero Streamlit) */
        border: 1px solid #4b4b4b; /* Bordino grigio */
        color: white !important;   /* Testo BIANCO forzato */
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
        font-size: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3); /* Ombretta per staccarlo */
    }
    
    /* Se vuoi un tocco di colore, scommenta questa riga sotto per farlo blu: */
    /* .summary-box { background-color: #0e1117; border: 1px solid #1f77b4; } */

    </style>
    """, unsafe_allow_html=True)

# --- 2. COSTANTI ---
OPZIONI = ["Mattina", "Pomeriggio", "Sera", "Notte", "Ferie", "Malattia", "Ima"]
ICONE = {
    "Mattina": "☀️", "Pomeriggio": "🌤️", "Sera": "🌆", 
    "Notte": "🌙", "Ferie": "🏖️", "Malattia": "🤒", "Ima": "🏥"
}

conn = st.connection("gsheets", type=GSheetsConnection)

if 'anno_view' not in st.session_state:
    st.session_state.anno_view = datetime.now().year
if 'mese_view' not in st.session_state:
    st.session_state.mese_view = datetime.now().month

# --- 3. FUNZIONI ---
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
    except:
        return pd.DataFrame(columns=["Data", "Tipo", "Note"])

def cambio_mese(delta):
    m = st.session_state.mese_view + delta
    y = st.session_state.anno_view
    if m > 12: m, y = 1, y + 1
    elif m < 1: m, y = 12, y - 1
    st.session_state.mese_view = m
    st.session_state.anno_view = y

def crea_calendario_df(anno, mese, df_turni):
    cal = calendar.monthcalendar(anno, mese)
    grid = []
    
    mask = (pd.to_datetime(df_turni["Data"]).dt.year == anno) & (pd.to_datetime(df_turni["Data"]).dt.month == mese)
    df_mese = df_turni[mask]
    
    giorni_map = {}
    for _, row in df_mese.iterrows():
        giorni_map[row["Data"].day] = ICONE.get(row["Tipo"], "•")

    for week in cal:
        row_str = []
        for day in week:
            if day == 0:
                row_str.append("")
            else:
                emoji = giorni_map.get(day, "")
                row_str.append(f"{day} {emoji}" if emoji else f"{day}")
        grid.append(row_str)
    return pd.DataFrame(grid, columns=["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"])

# --- 4. INTERFACCIA ---

# Navigazione
c_prev, c_title, c_next = st.columns([1, 3, 1], vertical_alignment="center")
with c_prev:
    if st.button("◀", key="p"): cambio_mese(-1); st.rerun()
with c_next:
    if st.button("▶", key="n"): cambio_mese(1); st.rerun()
with c_title:
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
        nome_mese = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y').capitalize()
    except:
        nome_mese = date(st.session_state.anno_view, st.session_state.mese_view, 1).strftime('%B %Y')
    st.markdown(f"<h3 style='text-align: center; margin:0;'>{nome_mese}</h3>", unsafe_allow_html=True)

# --- RIEPILOGO CONTEGGI (SFONDO SCURO) ---
df_completo = gestisci_dati("read")
mask_mese = (pd.to_datetime(df_completo["Data"]).dt.year == st.session_state.anno_view) & \
            (pd.to_datetime(df_completo["Data"]).dt.month == st.session_state.mese_view)
df_mese_corr = df_completo[mask_mese]

if not df_mese_corr.empty:
    totale = len(df_mese_corr)
    conteggi = df_mese_corr["Tipo"].value_counts()
    
    dettaglio_str = ""
    for tipo, count in conteggi.items():
        icona = ICONE.get(tipo, "")
        if icona:
            dettaglio_str += f"<span style='white-space: nowrap; margin: 0 5px;'>{icona} <b>{count}</b></span>"
            
    # Box ad alto contrasto
    st.markdown(f"""
        <div class="summary-box">
            <div style="font-size: 14px; opacity: 0.8; margin-bottom: 5px;">TOTALE TURNI</div>
            <div style="font-size: 28px; font-weight: bold; margin-bottom: 10px;">{totale}</div>
            <div style="font-size: 16px; border-top: 1px solid #555; padding-top: 10px;">{dettaglio_str}</div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("Nessun turno inserito in questo mese.")

# --- CALENDARIO ---
df_cal = crea_calendario_df(st.session_state.anno_view, st.session_state.mese_view, df_completo)
st.table(df_cal)

# --- INSERIMENTO ---
with st.expander("➕ Aggiungi / Modifica Turno", expanded=False):
    c1, c2 = st.columns([1, 1.5])
    with c1:
        d_in = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
    with c2:
        try:
            t_in = st.pills("Tipo", OPZIONI, selection_mode="single", default="Mattina")
        except AttributeError:
            t_in = st.selectbox("Tipo", OPZIONI)
        if not t_in: t_in = "Mattina" 
    
    c3, c4 = st.columns([2, 1])
    with c3:
        n_in = st.text_input("Note", placeholder="Opzionale...")
    with c4:
        st.markdown("<div style='margin-top: 29px'></div>", unsafe_allow_html=True)
        if st.button("SALVA", type="primary"):
            nuova = pd.DataFrame([{"Data": d_in, "Tipo": t_in, "Note": n_in}])
            gestisci_dati("write", pd.concat([df_completo, nuova], ignore_index=True))
            st.toast("Salvato!", icon="✅")
            st.rerun()
            
