import pandas as pd
import streamlit as st
import uuid
import math
import datetime

# --- CONFIGURAREA PAGINII ---
st.set_page_config(page_title="Calculator Termic & Radiatoare PRO", page_icon="️", layout="wide")

# --- INITIALIZAREA st.session_state (Memoria aplicatiei) ---
if 'elemente_anvelopa_salvate' not in st.session_state: st.session_state.elemente_anvelopa_salvate = {"Perete Exterior BCA (exemplu)": 0.28, "Planseu peste subsol (exemplu)": 0.35}
if 'elemente_vitrate_salvate' not in st.session_state: st.session_state.elemente_vitrate_salvate = {"Fereastra Tripan (PVC)": 1.1, "Fereastra Bipan (PVC)": 1.8, "Usa exterioara (izolata)": 1.6}
if 'straturi' not in st.session_state: st.session_state.straturi = []
if 'proiect' not in st.session_state: st.session_state.proiect = {}
if 'elemente_curente' not in st.session_state: st.session_state.elemente_curente = []
if 'punti_curente' not in st.session_state: st.session_state.punti_curente = []
if 'locatie_selectata' not in st.session_state: st.session_state.locatie_selectata = "București (II)"
if 'temp_ext' not in st.session_state: st.session_state.temp_ext = -15

# --- BAZE DE DATE COMPLETE ---
materiale_constructii = {
    "BCA (350 kg/m³)": {"lambda": 0.11}, "Caramida Porotherm N+F": {"lambda": 0.26}, "Caramida plina": {"lambda": 0.70}, "Caramida eficienta (BKS)": {"lambda": 0.35},
    "Beton armat (2400 kg/m³)": {"lambda": 1.75}, "Beton simplu (2200 kg/m³)": {"lambda": 1.40},
    "Polistiren expandat (EPS 80)": {"lambda": 0.040}, "Polistiren extrudat (XPS)": {"lambda": 0.035}, "Vata minerala bazaltica": {"lambda": 0.038}, "Vata minerala de sticla": {"lambda": 0.042}, "Spuma poliuretanica (PIR)": {"lambda": 0.022},
    "Tencuiala ciment-var": {"lambda": 0.87}, "Tencuiala decorativa": {"lambda": 0.70}, "Gips-carton": {"lambda": 0.25},
    "Sapa ciment": {"lambda": 1.40}, "Parchet laminat": {"lambda": 0.17}, "Lemn (ex. OSB)": {"lambda": 0.13}, "Strat de aer neventilat": {"lambda": 0.16},
}
stratificatii_uzuale = {
    "Perete Exterior BCA": [{'material': 'Tencuiala ciment-var', 'grosime_cm': 2.0}, {'material': 'BCA (350 kg/m³)', 'grosime_cm': 30.0}, {'material': 'Polistiren expandat (EPS 80)', 'grosime_cm': 15.0}, {'material': 'Tencuiala decorativa', 'grosime_cm': 0.5}],
    "Perete Exterior Cărămidă": [{'material': 'Tencuiala ciment-var', 'grosime_cm': 2.0}, {'material': 'Caramida Porotherm N+F', 'grosime_cm': 25.0}, {'material': 'Vata minerala bazaltica', 'grosime_cm': 15.0}, {'material': 'Tencuiala decorativa', 'grosime_cm': 0.5}],
    "Acoperiș Terasă": [{'material': 'Gips-carton', 'grosime_cm': 1.25}, {'material': 'Beton armat (2400 kg/m³)', 'grosime_cm': 20.0}, {'material': 'Polistiren extrudat (XPS)', 'grosime_cm': 20.0}]
}
debite_aer_normate = {"bucatarie": 1.19, "baie": 1, "camara": 1, "camera tehnica": 0.79, "debara": 1, "dormitor": 0.792, "hol": 0.792, "living": 0.792, "sufragerie": 0.792, "birou": 0.792, "default": 0.5}
spatii_adiacente = {"Exterior": {"b": 1.0}, "Sol": {"b": 0.5}, "Subsol neincalzit": {"b": 0.5}, "Pod neincalzit": {"b": 0.7}, "Camera adiacenta incalzita": {"b": 0.0}}
temperaturi_standard = {"dormitor": 20, "living": 20, "baie": 22, "bucatarie": 18, "hol": 18, "default": 20}
zone_climatice = {
    "Manual": -15, "București (II)": -15, "Constanța (I)": -12, "Iași (III)": -18, "Cluj-Napoca (III)": -18, "Timișoara (II)": -15, "Brașov (IV)": -21, "Craiova (II)": -15,
    "Galați (II)": -15, "Ploiești (II)": -15, "Oradea (II)": -15, "Brăila (II)": -15, "Arad (II)": -15, "Pitești (III)": -18, "Sibiu (III)": -18, "Bacău (III)": -18,
    "Târgu Mureș (III)": -18, "Baia Mare (III)": -18, "Buzău (II)": -15, "Botoșani (III)": -18, "Satu Mare (III)": -18, "Râmnicu Vâlcea (III)": -18, "Suceava (III)": -18,
    "Piatra Neamț (III)": -18, "Drobeta-Turnu Severin (II)": -15, "Focșani (II)": -15, "Târgu Jiu (III)": -18, "Tulcea (I)": -12, "Târgoviște (III)": -18, "Slatina (II)": -15,
    "Hunedoara (III)": -18, "Zalău (III)": -18, "Sfântu Gheorghe (IV)": -21, "Vaslui (III)": -18, "Călărași (II)": -15, "Alba Iulia (III)": -18, "Giurgiu (II)": -15, "Miercurea Ciuc (IV)": -21
}
coeficienti_montaj_radiator = {"Montare liberă pe perete": 1.0, "Cu poliță deasupra": 1.05, "În nișă de perete": 1.10, "În mască integrală": 1.25}

# --- FUNCTII UTILITARE ---
def calculeaza_u(straturi):
    R_total = 0.13 + 0.04; 
    for strat in straturi: R_total += (strat["grosime_cm"] / 100.0) / materiale_constructii.get(strat["material"], {"lambda": 999})["lambda"]
    return 1 / R_total if R_total > 0 else 0
def incarca_stratificatie(nume): st.session_state.straturi = stratificatii_uzuale[nume]

# --- INTERFATA STREAMLIT ---
st.title("️ Calculator Profesional: Necesar Termic & Dimensionare Radiatoare")
tab_titles = ["1. 🏛️ Bibliotecă Elemente", "2. 🏗️ Calcul Încăpere", "3. 📊 Centralizatoare", "4. 🌡️ Dimensionare Radiatoare", "5. 📝 Generare Memoriu"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

with tab1: # BIBLIOTECA DE ELEMENTE
    st.header("Creează și Gestionează Biblioteca de Elemente")
    col1, col2 = st.columns([1,1])
    with col1:
        with st.container(border=True):
            st.subheader("Creează Element Nou")
            nume_element_nou = st.text_input("Nume element (ex: Perete Exterior, Fereastră Tripan)")
            is_vitrat = st.checkbox("Bifează dacă este element vitrat (fereastră, ușă)")
            if is_vitrat:
                u_val_manual = st.number_input("Introdu valoarea U [W/m²K] direct", value=1.1, format="%.3f")
                if st.button("💾 Salvează Element Vitrat", type="primary", use_container_width=True):
                    if nume_element_nou: st.session_state.elemente_vitrate_salvate[nume_element_nou] = u_val_manual; st.success(f"Elementul '{nume_element_nou}' a fost salvat!")
                    else: st.warning("Introdu un nume.")
            else:
                with st.expander("Încarcă Stratificații Uzuale (Exemple)"):
                    c1,c2,c3=st.columns(3); c1.button("Perete BCA", on_click=incarca_stratificatie, args=("Perete Exterior BCA",), use_container_width=True); c2.button("Perete Cărămidă", on_click=incarca_stratificatie, args=("Perete Exterior Cărămidă",), use_container_width=True); c3.button("Terasă", on_click=incarca_stratificatie, args=("Acoperiș Terasă",), use_container_width=True)
                if st.button("➕ Adaugă Strat Nou", use_container_width=True): st.session_state.straturi.append({'material': 'Polistiren expandat (EPS 80)', 'grosime_cm': 10.0})
                for i, strat in enumerate(st.session_state.straturi):
                    cols = st.columns([3, 2]); st.session_state.straturi[i]['material'] = cols[0].selectbox(f"Material Strat {i+1}", list(materiale_constructii.keys()), key=f"mat_{i}", index=max(0, list(materiale_constructii.keys()).index(strat['material']) if strat.get('material') in materiale_constructii else 0))
                    st.session_state.straturi[i]['grosime_cm'] = cols[1].number_input(f"Grosime [cm]", min_value=0.1, value=float(strat.get('grosime_cm', 10.0)), key=f"gros_{i}")
                if st.session_state.straturi:
                    U_val = calculeaza_u(st.session_state.straturi)
                    st.metric(label="Coeficient U calculat", value=f"{U_val:.3f} W/m²K")
                    if st.button("💾 Salvează Element de Anvelopă", type="primary", use_container_width=True):
                        if nume_element_nou: st.session_state.elemente_anvelopa_salvate[nume_element_nou] = U_val; st.success(f"Elementul '{nume_element_nou}' a fost salvat!")
                        else: st.warning("Introdu un nume.")
    with col2:
        with st.container(border=True):
            st.subheader("Elemente de Anvelopă Salvate"); [st.code(f"{nume}: U = {u_val:.3f} W/m²K") for nume, u_val in st.session_state.elemente_anvelopa_salvate.items()]
        with st.container(border=True):
            st.subheader("Elemente Vitrate Salvate"); [st.code(f"{nume}: U = {u_val:.3f} W/m²K") for nume, u_val in st.session_state.elemente_vitrate_salvate.items()]

with tab2: # CALCUL PE INCAPERE
    st.header("Definește o Încăpere și Calculează Pierderile")
    with st.container(border=True):
        st.subheader("📍 1. Setări Generale Proiect")
        locatie_selectata = st.selectbox("Selectează Zona Climatică", options=list(zone_climatice.keys()), index=list(zone_climatice.keys()).index(st.session_state.locatie_selectata))
        st.session_state.locatie_selectata = locatie_selectata; temp_ext = zone_climatice[locatie_selectata]; st.session_state.temp_ext = temp_ext
        st.info(f"Temperatura exterioară de calcul pentru **{locatie_selectata}** este: **{temp_ext}°C**")
    
    with st.container(border=True):
        st.subheader("🏠 2. Date Generale Încăpere")
        c1, c2, c3, c4 = st.columns(4)
        nume_incapere = c1.text_input("Nume Încăpere", f"Incăpere {len(st.session_state.proiect) + 1}")
        temp_int = c2.number_input("Temp. interioară [°C]", value=20.0)
        lungime = c3.number_input("Lungime [m]", value=4.0, min_value=0.1); latime = c4.number_input("Lățime [m]", value=3.5, min_value=0.1)
        inaltime = st.number_input("Înălțime [m]", value=2.7, min_value=0.1)
        tip_incapere = next((k for k in temperaturi_standard if k in nume_incapere.lower()), "default")
        if abs(temp_int - temperaturi_standard[tip_incapere]) > 2: st.warning(f"⚠️ Atenție: Temperatura standard pentru '{tip_incapere.capitalize()}' este de {temperaturi_standard[tip_incapere]}°C.")

    st.subheader("🧱 3. Elemente de Anvelopă (Pereți, Planșee)")
    tip_adauga = st.selectbox("Asistent Adăugare Elemente", ["Adaugă Pardoseală/Tavan (L x l)", "Adaugă Perete (pe Lungime L x H)", "Adaugă Perete (pe lățime l x H)", "Adaugă Element Manual"])
    if st.button("➕ Adaugă Element Anvelopă", use_container_width=True): 
        arie_sugerata = 10.0
        if "Pardoseală" in tip_adauga: arie_sugerata = lungime * latime
        elif "Lungime" in tip_adauga: arie_sugerata = lungime * inaltime
        elif "lățime" in tip_adauga: arie_sugerata = latime * inaltime
        st.session_state.elemente_curente.append({'id': uuid.uuid4(), 'tip_el': list(st.session_state.elemente_anvelopa_salvate.keys())[0], 'spatiu_adj': 'Exterior', 'arie_tot': arie_sugerata, 'vitraje': [], 'temp_adj_dif': False, 'temp_adj_val': 18.0})
    
    for el in st.session_state.elemente_curente:
        with st.container(border=True):
            c1,c2,c3=st.columns([2,1,1]); el['tip_el'] = c1.selectbox("Element", list(st.session_state.elemente_anvelopa_salvate.keys()), key=f"sel_{el['id']}"); el['spatiu_adj'] = c2.selectbox("Spațiu Adiacent", list(spatii_adiacente.keys()), key=f"spa_{el['id']}"); el['arie_tot'] = c3.number_input("Arie Totală [m²]", value=el['arie_tot'], min_value=0.1, key=f"ar_{el['id']}"); 
            if el['spatiu_adj'] == "Camera adiacenta incalzita":
                el['temp_adj_dif'] = st.checkbox("Temperatură diferită?", key=f"check_{el['id']}", value=el['temp_adj_dif'])
                if el['temp_adj_dif']: el['temp_adj_val'] = st.number_input("Temp. adiacentă [°C]", value=el['temp_adj_val'], key=f"temp_adj_{el['id']}")
            with st.expander("Adaugă Ferestre/Uși în acest element"):
                if st.button("➕ Vitraj", key=f"add_v_{el['id']}"): el['vitraje'].append({'id': uuid.uuid4(), 'tip_v': list(st.session_state.elemente_vitrate_salvate.keys())[0], 'L': 1.2, 'H': 1.4})
                for vitraj in el['vitraje']: cv1,cv2,cv3=st.columns([2,1,1]); vitraj['tip_v']=cv1.selectbox("Tip Vitraj", list(st.session_state.elemente_vitrate_salvate.keys()), key=f"v_tip_{vitraj['id']}"); vitraj['L']=cv2.number_input("Lățime [m]", value=vitraj['L'], min_value=0.1, key=f"v_l_{vitraj['id']}"); vitraj['H']=cv3.number_input("Înălțime [m]", value=vitraj['H'], min_value=0.1, key=f"v_h_{vitraj['id']}");

    st.subheader("🧊 4. Punți Termice")
    if st.button("➕ Adaugă Punte Termică", use_container_width=True):
        st.session_state.punti_curente.append({'id': uuid.uuid4(), 'descr': 'Contur fereastră', 'lungime': 5.2, 'psi': 0.04})
    for pt in st.session_state.punti_curente:
        with st.container(border=True):
            c1,c2,c3 = st.columns(3); pt['descr'] = c1.text_input("Descriere", value=pt['descr'], key=f"pt_d_{pt['id']}"); pt['lungime'] = c2.number_input("Lungime [m]", value=pt['lungime'], min_value=0.1, key=f"pt_l_{pt['id']}"); pt['psi'] = c3.number_input("Valoare Psi [W/mK]", value=pt['psi'], format="%.3f", help="Ex: Colț=0.05", key=f"pt_psi_{pt['id']}");

    st.subheader("🏁 5. Finalizare Calcul Încăpere")
    if st.button("✅ Calculează și Adaugă Încăperea în Proiect", type="primary", use_container_width=True):
        tip_incapere_vent = next((k for k in debite_aer_normate if k in nume_incapere.lower()), "default"); V = lungime*latime*inaltime; n = debite_aer_normate[tip_incapere_vent]
        Q_vent = 0.34 * V * n * (temp_int - temp_ext)
        Q_trans_anvelopa = 0; centralizator = []
        for el in st.session_state.elemente_curente:
            b = spatii_adiacente[el['spatiu_adj']]['b']; delta_T = temp_int - temp_ext
            if el['spatiu_adj'] == "Camera adiacenta incalzita":
                if el['temp_adj_dif']: delta_T = temp_int - el['temp_adj_val']; b = 1.0
                else: delta_T = 0
            arie_vitraje = sum(v['L']*v['H'] for v in el['vitraje']); arie_neta = el['arie_tot'] - arie_vitraje; U = st.session_state.elemente_anvelopa_salvate[el['tip_el']]
            Q_el = b * U * arie_neta * delta_T; Q_trans_anvelopa += Q_el
            centralizator.append({'Element': el['tip_el'], 'Arie [m²]': arie_neta, 'U': U, 'b': b, 'ΔT': delta_T, 'Q_Transmisie [W]': Q_el})
            for v in el['vitraje']:
                U_v = st.session_state.elemente_vitrate_salvate[v['tip_v']]; arie_v = v['L']*v['H']
                Q_v = b * U_v * arie_v * delta_T; Q_trans_anvelopa += Q_v
                centralizator.append({'Element': v['tip_v'], 'Arie [m²]': arie_v, 'U': U_v, 'b': b, 'ΔT': delta_T, 'Q_Transmisie [W]': Q_v})
        Q_punti = sum(pt['lungime'] * pt['psi'] * (temp_int - temp_ext) for pt in st.session_state.punti_curente)
        Q_trans_total = Q_trans_anvelopa + Q_punti; Q_total = Q_trans_total + Q_vent
        st.session_state.proiect[nume_incapere] = {'Q_Vent': Q_vent, 'Q_Trans_Anvelopa': Q_trans_anvelopa, 'Q_Punti': Q_punti, 'Q_Trans_Total': Q_trans_total, 'Q_Total': Q_total, 'centralizator': centralizator, 'temp_int': temp_int}
        st.session_state.elemente_curente, st.session_state.punti_curente = [], []; st.success(f"Încăperea '{nume_incapere}' a fost adăugată cu un necesar total de {Q_total:.0f} W."); st.rerun()

with tab3: # CENTRALIZATOARE
    st.header("Vizualizare Rezultate Proiect")
    if not st.session_state.proiect: st.warning("Niciun calcul efectuat. Adaugă o încăpere din Tab-ul 2.")
    else:
        st.subheader("Rezumat pe Încăperi")
        rezumat_data = [{'Încăpere': nume, 'Transmisie Anvelopă [W]': date['Q_Trans_Anvelopa'], 'Punți Termice [W]': date['Q_Punti'], 'Total Transmisie [W]': date['Q_Trans_Total'], 'Ventilație [W]': date['Q_Vent'], 'Necesar Total [W]': date['Q_Total']} for nume, date in st.session_state.proiect.items()]
        df_rezumat = pd.DataFrame(rezumat_data)
        coloane_format = [col for col in df_rezumat.columns if col != 'Încăpere']
        st.dataframe(df_rezumat.style.format("{:.0f}", subset=coloane_format))
        st.metric("Necesar Total Clădire", f"{df_rezumat['Necesar Total [W]'].sum():.0f} W")
        with st.expander("Vezi Centralizatorul Detaliat (pentru Verificare)"):
            full_centralizator = []; 
            for nume, date in st.session_state.proiect.items():
                for row in date['centralizator']: new_row = row.copy(); new_row['Încăpere'] = nume; full_centralizator.append(new_row)
            df_centralizator = pd.DataFrame(full_centralizator); st.dataframe(df_centralizator.style.format("{:.2f}", subset=['Arie [m²]', 'U', 'b', 'ΔT', 'Q_Transmisie [W]']))
            st.download_button("Descarcă Centralizator Detaliat (.csv)", df_centralizator.to_csv(index=False).encode('utf-8'), "centralizator_detaliat.csv")

with tab4: # DIMENSIONARE RADIATOARE
    st.header("Ghid pentru Dimensionarea Radiatoarelor")
    if not st.session_state.proiect: st.warning("Calculează necesarul termic pentru a putea dimensiona radiatoarele.")
    else:
        with st.container(border=True):
            st.subheader("Pasul 1: Setează Parametrii Sistemului de Încălzire")
            st.info("**Agent Termic:** Apa caldă care circulă prin instalație. Temperaturile sale definesc cât de 'fierbinte' este radiatorul.")
            c1, c2 = st.columns(2); temp_tur = c1.number_input("Temperatură Tur [°C]", value=75.0); temp_retur = c2.number_input("Temperatură Retur [°C]", value=65.0)
        st.subheader("Pasul 2: Alege Radiatorul pentru Fiecare Cameră")
        rezultate_radiatoare = []
        for nume, date in st.session_state.proiect.items():
            with st.container(border=True):
                st.markdown(f"#### {nume} (Necesar: **{date['Q_Total']:.0f} W**)")
                c1,c2 = st.columns(2)
                delta_T_ref = c1.number_input("ΔT de Referință (din catalog)", value=50.0, min_value=1.0, key=f"dt_ref_{nume}", help="Puterea din fișa tehnică este dată pentru un ΔT standard (de obicei 50K sau 60K).")
                mod_montaj = c2.selectbox("Mod de montare", list(coeficienti_montaj_radiator.keys()), key=f"montaj_{nume}", help="Un radiator acoperit pierde din eficiență. Coeficientul compensează.")
                temp_medie_agent = (temp_tur + temp_retur) / 2; delta_T_proiect = temp_medie_agent - date['temp_int']; coef_montaj = coeficienti_montaj_radiator[mod_montaj]
                if delta_T_proiect <= 0: delta_T_proiect = 0.1
                putere_necesara_catalog = date['Q_Total'] * math.pow((delta_T_ref / delta_T_proiect), 1.3) * coef_montaj
                st.metric("🎯 Putere Necesară (la ΔT ref din catalog)", f"{putere_necesara_catalog:.0f} W")
                st.info(f"**Explicație:** Pentru a acoperi **{date['Q_Total']:.0f} W** cu ΔT proiect = {delta_T_proiect:.1f}°C, ai nevoie de un radiator care în fișa tehnică (la ΔT ref = {delta_T_ref}°C) are o putere de **{putere_necesara_catalog:.0f} W**.")
                rezultate_radiatoare.append({'Încăpere': nume, 'Necesar Termic [W]': date['Q_Total'], 'Putere Necesară Catalog [W]': putere_necesara_catalog})
        if st.button("Generează Lista de Radiatoare", use_container_width=True, type="primary"):
            df_radiatoare = pd.DataFrame(rezultate_radiatoare); st.dataframe(df_radiatoare.style.format("{:.0f}", subset=['Necesar Termic [W]', 'Putere Necesară Catalog [W]']))
            st.download_button("Descarcă Lista (.csv)", df_radiatoare.to_csv(index=False).encode('utf-8'), "lista_radiatoare.csv")

with tab5: # GENERARE MEMORIU
    st.header("Generare Memoriu Tehnic de Specialitate")
    if not st.session_state.proiect: st.warning("Finalizează calculul pentru a putea genera memoriul.")
    else:
        st.info("Completează datele de mai jos, apoi apasă butonul pentru a genera textul memoriului. Poți apoi să-l copiezi și să-l lipești într-un editor text (ex: Microsoft Word) pentru a-l salva ca PDF.")
        c1, c2 = st.columns(2)
        st.session_state.beneficiar = c1.text_input("Nume Beneficiar", value=st.session_state.get('beneficiar', ''))
        st.session_state.proiectant = c2.text_input("Nume Proiectant / Întocmit", value=st.session_state.get('proiectant', ''))
        if st.button("🚀 Generează Textul Memoriului", type="primary", use_container_width=True):
            df_rezumat_final = pd.DataFrame([{'Încăpere': nume, 'Transmisie Anvelopă [W]': date['Q_Trans_Anvelopa'], 'Punți Termice [W]': date['Q_Punti'], 'Ventilație [W]': date['Q_Vent'], 'Necesar Total [W]': date['Q_Total']} for nume, date in st.session_state.proiect.items()])
            total_cladire = df_rezumat_final['Necesar Total [W]'].sum(); data_azi = datetime.date.today().strftime("%d.%m.%Y")
            locatie_memoriu = st.session_state.locatie_selectata; temp_ext_memoriu = st.session_state.temp_ext
            memoriu = f"""
## MEMORIU TEHNIC - INSTALAȚII TERMICE

**1. DATE GENERALE**
- **Proiect:** Calculul necesarului de căldură
- **Beneficiar:** {st.session_state.beneficiar if st.session_state.beneficiar else "_________________________"}
- **Amplasament:** {locatie_memoriu}
- **Data:** {data_azi}

**2. OBIECTUL PROIECTULUI**
Prezentul memoriu tehnic are ca obiect descrierea soluției de încălzire și calculul necesarului de căldură pentru imobilul situat în {locatie_memoriu}. Calculul s-a efectuat în conformitate cu prevederile normativului SR 12831.

**3. BAZA DE CALCUL**
- **Normativ de referință:** SR 12831 - Performanța energetică a clădirilor.
- **Temperatură exterioară de calcul:** {temp_ext_memoriu}°C (conform SR 1907 pentru zona climatică {locatie_memoriu}).
- **Temperaturi interioare de proiectare:** Conform tabelului de rezultate.
- **Regim de funcționare:** Permanent.

**4. REZULTATELE CALCULULUI NECESARULUI DE CĂLDURĂ**
În urma analizei, s-au obținut următoarele sarcini termice pentru fiecare încăpere:

| Încăpere | Transmisie [W] | Punți Termice [W] | Ventilație [W] | **Necesar Total [W]** |
|---|---|---|---|---|
"""
            for index, row in df_rezumat_final.iterrows(): memoriu += f"| {row['Încăpere']} | {row['Transmisie Anvelopă [W]']:.0f} | {row['Punți Termice [W]']:.0f} | {row['Ventilație [W]']:.0f} | **{row['Necesar Total [W]']:.0f}** |\n"
            memoriu += f"""| **TOTAL CLĂDIRE** | - | - | - | **{total_cladire:.0f}** |

**5. CONCLUZII**
Necesarul total de căldură pentru clădire este de **{total_cladire:.0f} W**. Sursa de căldură (centrală termică, pompă de căldură etc.) va trebui să aibă o putere nominală cel puțin egală cu această valoare.

**Întocmit,**
{st.session_state.proiectant if st.session_state.proiectant else "_________________________"}
"""
            st.code(memoriu, language="markdown"); st.success("Memoriul a fost generat! Copiază textul de mai sus.")