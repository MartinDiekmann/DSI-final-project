import warnings
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
import numpy as np
import math
from statsmodels.nonparametric.smoothers_lowess import lowess

st.set_page_config(layout='wide')

st.title('Krebsinzidenz, Mortalität und Risikofaktoren für Deutschland')
st.subheader("Epidemiologische Analyse & Interpretation :chart_with_downwards_trend:")


##################################################################
# Daten laden
##################################################################

@st.cache_data
def load_data():

    df_cancer_w = pd.read_csv('Krebsdaten_w.csv', sep=';', decimal=',')
    df_cancer_w = df_cancer_w.rename(columns={'Unnamed: 0': 'Jahr'}).sort_values('Jahr',ascending=True).drop(columns='Unnamed: 22')

    df_cancer_m = pd.read_csv('Krebsdaten_m.csv', sep=';', decimal=',')
    df_cancer_m = df_cancer_m.rename(columns={'Unnamed: 0': 'Jahr'}).sort_values('Jahr', ascending=True).drop(columns='Unnamed: 22')


    df_cancer_mort_w = pd.read_csv('Krebsdaten_Mortalität_w.csv', sep=';',  decimal=',')
    df_cancer_mort_w = df_cancer_mort_w.rename(columns={'Unnamed: 0': 'Jahr'}).sort_values('Jahr', ascending=True).drop(columns='Unnamed: 22')

    df_cancer_mort_m = pd.read_csv('Krebsdaten_Mortalität_m.csv', sep=';',  decimal=',')
    df_cancer_mort_m = df_cancer_mort_m.rename(columns={'Unnamed: 0': 'Jahr'}).sort_values('Jahr', ascending=True).drop(columns='Unnamed: 22')

    df_riscfactors_w= pd.read_csv('risk_factors_w.csv', sep=',')
    df_riscfactors_m= pd.read_csv('risk_factors_m.csv', sep=',')

    return df_cancer_w, df_cancer_m, df_cancer_mort_w, df_cancer_mort_m, df_riscfactors_w, df_riscfactors_m

df_cancer_w, df_cancer_m, df_cancer_mort_w, df_cancer_mort_m, df_riscfactors_w, df_riscfactors_m = load_data()

####################################################################
# Pills  
####################################################################

bereich = st.pills("Auswahl der Analyse: ",['Inzidenz', 'Mortalität','Risikofaktoren', 'Zusammenhang'])

###########################################################################################################
################### Inzidenz ##############################################################################
###########################################################################################################

if bereich == 'Inzidenz':
    
    st.info(':bulb: **Inzidenz**: Die Inzidenz ist ein Ausdruck aus der medizinischen Statistik, der die Häufigkeit von Neuerkrankungen beschreibt. Unter Inzidenz versteht man die Anzahl neu aufgetretener Krankheitsfälle innerhalb einer definierten Population in einem oder bezogen auf einen bestimmten Zeitraum. ' \
    'Der Begriff "Inzidenz" wird darüber hinaus auch generell als Maß für die Häufigkeit eines bestimmten Merkmals bzw. Ereignisses verwendet.')

    st.info(':bulb: **Alterstandardisierung**:  Die altersstandardisierte Rate ist eine Messgröße aus der Statistik. Sie gibt an, wie viele Erkrankungsfälle oder Sterbefälle auf 100.000 Personen entfallen wären, wenn der Altersaufbau der Bevölkerung dem einer definierten Standardbevölkerung entsprochen hätte.' \
    'Es finden bei der Verwendung der altersstandardisierten Rate auch die jeweils in der Bevölkerung vorhandenen Gesundheitsverhältnisse Berücksichtigung. Durch Altersstandardisierung ist ein Vergleich von Daten von unterschiedlichen Jahren oder Regionen ohne Verzerrungen möglich.')

    df_cancertyps_w= df_cancer_w.copy()
    df_cancertyps_m= df_cancer_m.copy()

    cancertyps_w = df_cancertyps_w.columns.drop('Jahr')
    cancertyps_m = df_cancertyps_m.columns.drop('Jahr')

    cancertyps_all = sorted(set(cancertyps_w).union(set(cancertyps_m)))


    default_typ = 'Krebs gesamt (C00-C97 ohne C44)'
    activ_index = cancertyps_all.index(default_typ)
    
    fig = go.Figure()

    # für Frauen

    for typ in cancertyps_w:
        fig.add_trace(go.Scatter(x=df_cancertyps_w['Jahr'],
                                y = df_cancertyps_w[typ], 
                                mode='lines+markers', 
                                name=F'{typ} (Frauen)', 
                                visible=(typ==default_typ)))
        
    # für Männer

    for typ in cancertyps_m:
        fig.add_trace(go.Scatter(x=df_cancertyps_m['Jahr'],
                                y = df_cancertyps_m[typ], 
                                mode='lines+markers', 
                                name=F'{typ} (Männer)', 
                                visible=(typ==default_typ)))


    # Drop Down Menü

    buttons = []

    for typ in cancertyps_all:
        visible_arr = [False] * (len(cancertyps_w) + len(cancertyps_m))

        if typ in cancertyps_w:
            id_w = list(cancertyps_w).index(typ)
            visible_arr[id_w] = True
        
        
        if typ in cancertyps_m:
            id_m = len(cancertyps_w) + list(cancertyps_m).index(typ)
            visible_arr[id_m] = True
        

        buttons.append(
            dict(
                label=typ,
                method='update',
                args=[{'visible': visible_arr},
                    {'title': f'Zeitverlauf der altersstandardisierten Krebsinzidenz: {typ}'}]
            )
        )


    fig.update_layout(
        autosize=False,
        width=1600,
        height=800,
        updatemenus=[dict(active=activ_index, buttons=buttons)],
        title=f'Zeitverlauf der altersstandardisierten Krebsinzidenz: {default_typ}',
        xaxis_title='Jahr',
        yaxis_title='Inzidenz pro 100.000 Einwohner',
        template='plotly_white')
    
    st.plotly_chart(fig, use_container_width=True)

    ##################################################################################################################
    # Trendanalyse
    ##################################################################################################################

    st.subheader("Trendanalyse der Krebsinzidenzen in Deutschland")
    auswahl_typ = st.selectbox("Krebsart für die Trendanalyse wählen: ", cancertyps_all, index = activ_index)

    def trendanalyse(df, typ):
        y = df[typ]
        X = sm.add_constant(df['Jahr'])
        model = sm.OLS(y,X).fit()

        slope = model.params['Jahr']
        p_value = model.pvalues["Jahr"]
        conf_intervall = model.conf_int().loc['Jahr']

        # Prozentuale Veränderung
        dekade = slope * 10
        baseline = y.iloc[0]
        perc_dekade = (dekade/baseline)*100
        
        return slope, p_value, conf_intervall, perc_dekade
    
    col1, col2 = st.columns(2)

    #Frauen
    if auswahl_typ in cancertyps_w:
        slope_w, p_value_w, conf_intervall_w, perc_dekade_w = trendanalyse (df_cancertyps_w, auswahl_typ)

        with col1:
            st.markdown("**Frauen**")
            st.write(f'Steigung: {round(slope_w,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_w[0],2)}, {round(conf_intervall_w[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_w,2)} %')
            st.write(f'p-Wert: {round(p_value_w,4)}')
    
    #Männer

    if auswahl_typ in cancertyps_m:
        slope_m, p_value_m, conf_intervall_m, perc_dekade_m = trendanalyse (df_cancertyps_m, auswahl_typ)

        with col2:
            st.markdown("**Männer**")
            st.write(f'Steigung: {round(slope_m,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_m[0],2)}, {round(conf_intervall_m[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_m,2)} %')
            st.write(f'p-Wert: {round(p_value_m,4)}')

    ######################################################################################
    # Automatische Interpretation
    ######################################################################################

    st.subheader('Interpretation der statistischen Kennzahlen')

    interpretation = ''

    if auswahl_typ in cancertyps_w:
        if p_value_w < 0.05:
            interpretation += "Bei Frauen liegt ein statistisch signifikanter Trend vor. "
        else:
            interpretation += "Bei Frauen liegt kein statistisch signifikanter Trend vor. "


    if auswahl_typ in cancertyps_m:
        if p_value_m < 0.05:
            interpretation += "Bei Männern liegt ein statistisch signifikanter Trend vor. "
    else:
            interpretation += "Bei Männern liegt kein statistisch signifikanter Trend vor. "           


    def trend_direction(slope, tol=1e-9):
        if math.isclose(slope,0,abs_tol=tol):
            return "stabil"
        elif slope > 0:
            return 'steigend'
        else:
            return 'fallend'


    if auswahl_typ in cancertyps_w and auswahl_typ in cancertyps_m:
        
        dir_w = trend_direction(slope_w)
        dir_m = trend_direction(slope_m)

        # Fall 1: beide stabil
        if dir_w =="stabil" and dir_m == "stabil":
            interpretation += "Bei beiden Geschlechtern zeigt sich kein relevanter Trend."
        
        # Fall 2: gegenläufiger Trend
        elif dir_w != dir_m and "stabil" not in (dir_w,dir_m):
            if dir_w == "steigend":
                interpretation += "Bei Frauen steigt die Fallzahl, während sie bei Männern sinkt."
            else:
                interpretation += "Bei Männern steigt die Fallzahl, während sie bei Frauen sinkt."

        # Fall 3: gleicher Richtungstrend
        elif dir_w == dir_m:
            if math.isclose(slope_w, slope_m, rel_tol=1e-6):
                interpretation += "Die Trendstärke ist bei beiden Geschlechtern vergleichbar."
            elif abs(slope_w) > abs(slope_m):
                if dir_w == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Frauen. "
                else: 
                    interpretation += "Der Rückgang ist stärker bei Frauen. "
            else:
                if dir_m == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Männern. "
                else:
                    interpretation += "Der Rückgang ist stärker bei Männern. "

        # Fall 4: ein Geschlecht stabil
        else:
            if dir_w == "stabil":
                interpretation += "Bei Frauen zeigt sich kein relevanter Trend, während sich bei Männern eine Veränderung zeigt."
            else: 
                interpretation += "Bei Männern zeigt sich kein relevanter Trend, während sich bei Frauen eine Veränderung zeigt."

    st.info(interpretation)

#############################################################################################
################################# Mortalität ################################################
#############################################################################################

elif bereich == 'Mortalität':

    st.info(':bulb: **Mortalität**: Die Mortalität ist die Anzahl der Todesfälle in einem bestimmten Zeitraum, bezogen auf 100.000 Individuen einer Population. Als Zeitraum wird in der Regel 1 Jahr definiert.' )


    df_cancertyps_mort_w= df_cancer_mort_w.copy()
    df_cancertyps_mort_m= df_cancer_mort_m.copy()

    cancertyps_mort_w = df_cancertyps_mort_w.columns.drop('Jahr')
    cancertyps_mort_m = df_cancertyps_mort_m.columns.drop('Jahr')

    cancertyps_mort_all = sorted(set(cancertyps_mort_w).union(set(cancertyps_mort_m)))

    default_typ = 'Krebs gesamt (C00-C97 ohne C44)'
    activ_index = cancertyps_mort_all.index(default_typ)


    fig = go.Figure()

    # für Frauen

    for typ in cancertyps_mort_w:
        fig.add_trace(go.Scatter(x=df_cancertyps_mort_w['Jahr'],
                                y = df_cancertyps_mort_w[typ], 
                                mode='lines+markers', 
                                name=F'{typ} (Frauen)', 
                                visible=(typ==default_typ)))
        
    # für Männer

    for typ in cancertyps_mort_m:
        fig.add_trace(go.Scatter(x=df_cancertyps_mort_m['Jahr'],
                                y = df_cancertyps_mort_m[typ], 
                                mode='lines+markers', 
                                name=F'{typ} (Männer)', 
                                visible=(typ==default_typ)))


    # Drop Down Menü

    buttons = []

    for typ in cancertyps_mort_all:
        visible_arr = [False] * (len(cancertyps_mort_w) + len(cancertyps_mort_m))

        if typ in cancertyps_mort_w:
            id_w = list(cancertyps_mort_w).index(typ)
            visible_arr[id_w] = True
        
        
        if typ in cancertyps_mort_m:
            id_m = len(cancertyps_mort_w) + list(cancertyps_mort_m).index(typ)
            visible_arr[id_m] = True
        

        buttons.append(
            dict(
                label=typ,
                method='update',
                args=[{'visible': visible_arr},
                    {'title': f'Zeitverlauf der altersstandardisierten Krebsmortalität: {typ}'}]
            )
        )

    fig.update_layout(
        autosize=False,
        width=1600,
        height=800,
        updatemenus=[dict(active=activ_index, buttons=buttons)],
        title=f'Zeitverlauf der altersstandardisierten Krebsinzmortalität: {default_typ}',
        xaxis_title='Jahr',
        yaxis_title='Mortalitätsrate pro 100.000 Einwohner',
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    #####################################################################################################
    # Trendanalyse
    ####################################################################################################

    st.subheader("Trendanalyse der Krebsmortalität in Deutschland")
    auswahl_typ = st.selectbox("Krebsart für die Trendanalyse wählen: ", cancertyps_mort_all, index = activ_index)

    def trendanalyse(df, typ):
        y = df[typ]
        X = sm.add_constant(df['Jahr'])
        model = sm.OLS(y,X).fit()

        slope = model.params['Jahr']
        p_value = model.pvalues["Jahr"]
        conf_intervall = model.conf_int().loc['Jahr']

        # Prozentuale Veränderung
        dekade = slope * 10
        baseline = y.iloc[0]
        perc_dekade = (dekade/baseline)*100
        
        return slope, p_value, conf_intervall, perc_dekade
    
    col1, col2 = st.columns(2)

    #Frauen
    if auswahl_typ in cancertyps_mort_w:
        slope_w, p_value_w, conf_intervall_w, perc_dekade_w = trendanalyse (df_cancertyps_mort_w, auswahl_typ)

        with col1:
            st.markdown("**Frauen**")
            st.write(f'Steigung: {round(slope_w,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_w[0],2)}, {round(conf_intervall_w[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_w,2)} %')
            st.write(f'p-Wert: {round(p_value_w,4)}')
    

    #Männer

    if auswahl_typ in cancertyps_mort_m:
        slope_m, p_value_m, conf_intervall_m, perc_dekade_m = trendanalyse (df_cancertyps_mort_m, auswahl_typ)

        with col2:
            st.markdown("**Männer**")
            st.write(f'Steigung: {round(slope_m,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_m[0],2)}, {round(conf_intervall_m[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_m,2)} %')
            st.write(f'p-Wert: {round(p_value_m,4)}')

    #####################################################################################################################
    # Automatische Interpretation
    #####################################################################################################################

    st.subheader('Interpretation der statitischen Kennzahlen')

    interpretation = ''

    if auswahl_typ in cancertyps_mort_w:
        if p_value_w < 0.05:
            interpretation += "Bei Frauen liegt ein statistisch signifikanter Trend vor. "
        else:
            interpretation += "Bei Frauen liegt kein statistisch signifikanter Trend vor. "


    if auswahl_typ in cancertyps_mort_m:
        if p_value_m < 0.05:
            interpretation += "Bei Männern liegt ein statistisch signifikanter Trend vor. "
        else:
            interpretation += "Bei Männern liegt kein statistisch signifikanter Trend vor. "           

    def trend_direction(slope, tol=1e-9):
        if math.isclose(slope,0,abs_tol=tol):
            return "stabil"
        elif slope > 0:
            return 'steigend'
        else:
            return 'fallend'


    if auswahl_typ in cancertyps_mort_w and auswahl_typ in cancertyps_mort_m:
        
        dir_w = trend_direction(slope_w)
        dir_m = trend_direction(slope_m)

        # Fall 1: beide stabil
        if dir_w =="stabil" and dir_m == "stabil":
            interpretation += "Bei beiden Geschlechtern zeigt sich kein relevanter Trend."
        
        # Fall 2: gegenläufiger Trend
        elif dir_w != dir_m and "stabil" not in (dir_w,dir_m):
            if dir_w == "steigend":
                interpretation += "Bei Frauen steigt die Fallzahl, während sie bei Männern sinkt."
            else:
                interpretation += "Bei Männern steigt die Fallzahl, während sie bei Frauen sinkt."

        # Fall 3: gleicher Richtungstrend
        elif dir_w == dir_m:
            if math.isclose(slope_w, slope_m, rel_tol=1e-6):
                interpretation += "Die Trendstärke ist bei beiden Geschlechtern vergleichbar."
            elif abs(slope_w) > abs(slope_m):
                if dir_w == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Frauen. "
                else: 
                    interpretation += "Der Rückgang ist stärker bei Frauen. "
            else:
                if dir_m == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Männern. "
                else:
                    interpretation += "Der Rückgang ist stärker bei Männern. "

        # Fall 4: ein Geschlecht stabil
        else:
            if dir_w == "stabil":
                interpretation += "Bei Frauen zeigt sich kein relevanter Trend, während sich bei Männern eine Veränderung zeigt."
            else: 
                interpretation += "Bei Männern zeigt sich kein relevanter Trend, während sich bei Frauen eine Veränderung zeigt."

    st.info(interpretation)


#################################################################################################################
####################### Risikofaktoren ##########################################################################
#################################################################################################################

elif bereich == 'Risikofaktoren':

    st.info(':bulb: **Multikausalität**: Die Multikausalität bei Krebs bezeichnet das Konzept, dass eine Krebserkrankung nicht durch eine einzige Ursache entsteht, sondern das Resultat des Zusammenspiels mehrerer verschiedener Faktoren ist. Anstatt einer monokausalen Ursache wirken verschiedene innere und äußere Faktoren zusammen, die zu einer Schädigung des Erbguts (DNA) und letztlich zur unkontrollierten Zellteilung führen. ')

    df_riscfactors_w= pd.read_csv('risk_factors_w.csv', sep=',')
    df_riscfactors_m= pd.read_csv('risk_factors_m.csv', sep=',')

    riscfactors_w = df_riscfactors_w.columns.drop('Jahr')
    riscfactors_m = df_riscfactors_m.columns.drop('Jahr')

    riscfactors_all = sorted(set(riscfactors_w).union(set(riscfactors_m)))


    fig = go.Figure()

    # für Frauen

    for factor in riscfactors_w:
        fig.add_trace(go.Scatter(x=df_riscfactors_w['Jahr'],
                                y =df_riscfactors_w[factor], 
                                mode='lines+markers', 
                                name=F'{factor} (Frauen)', 
                                visible=(factor == riscfactors_all[0])))
        
    # für Männer

    for factor in riscfactors_m:
        fig.add_trace(go.Scatter(x=df_riscfactors_m['Jahr'],
                                y =df_riscfactors_m[factor], 
                                mode='lines+markers', 
                                name=F'{factor} (Männer)', 
                                visible=(factor == riscfactors_all[0])))


    # Drop Down Menü

    buttons = []

    for factor in riscfactors_all:
        visible_arr = []

        for f in riscfactors_w:
            visible_arr.append(f == factor)
        
        
        for f in riscfactors_m:
            visible_arr.append(f == factor)
        

        y_title = ('Durchschnittlicher Alkoholkonsum täglich (in g)' if factor == 'Alkoholkonsum_avg_täglich(g)' else 'Feinstaubkonzentration (PM2.5)' if factor == 'Feinstaubkonzentration (PM2.5)' else 'Altersandardisierte Prävalenz (%)')

        buttons.append(dict(
                label=factor,
                method='update',
                args=[{'visible': visible_arr},
                        {'title': f'Zeitverlauf Risikofaktor: {factor}',
                        'yaxis': {'title': y_title}}
                ]
        ))

    fig.update_layout(
        autosize=False,
        width=1600,
        height=800,
        updatemenus=[dict(active=0, buttons=buttons)],
        title=f'Zeitverlauf Risikofaktor: {riscfactors_all[0]}',
        xaxis_title='Jahr',
        yaxis_title='Altersandardisierte Prävalenz (%)',
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    #####################################################################################################
    # Trendanalyse
    ####################################################################################################

    st.subheader("Trendanalyse für ausgewählte Krebsrisikofakotren in Deutschland")
    auswahl_typ = st.selectbox("Krebsart für die Trendanalyse wählen: ", riscfactors_all)

    def trendanalyse(df, typ):
        y = df[typ].dropna()
        X = sm.add_constant(df['Jahr'][y.index])
        model = sm.OLS(y,X).fit()

        slope = model.params['Jahr']
        p_value = model.pvalues["Jahr"]
        conf_intervall = model.conf_int().loc['Jahr']

        # Prozentuale Veränderung
        dekade = slope * 10
        baseline = y.iloc[0]
        perc_dekade = (dekade/baseline)*100 if baseline != 0 else np.nan
        
        return slope, p_value, conf_intervall, perc_dekade
    
    col1, col2 = st.columns(2)

    #Frauen
    if auswahl_typ in riscfactors_w:
        slope_w, p_value_w, conf_intervall_w, perc_dekade_w = trendanalyse (df_riscfactors_w, auswahl_typ)

        with col1:
            st.markdown("**Frauen**")
            st.write(f'Steigung: {round(slope_w,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_w[0],2)}, {round(conf_intervall_w[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_w,2)} %')
            st.write(f'p-Wert: {round(p_value_w,4)}')
    

    #Männer

    if auswahl_typ in riscfactors_m:
        slope_m, p_value_m, conf_intervall_m, perc_dekade_m = trendanalyse (df_riscfactors_m, auswahl_typ)

        with col2:
            st.markdown("**Männer**")
            st.write(f'Steigung: {round(slope_m,2)} Fälle pro Jahr.')
            st.write(f'95% CI: [{round(conf_intervall_m[0],2)}, {round(conf_intervall_m[1],2)}]')
            st.write(f'Veränderung pro Dekade: {round(perc_dekade_m,2)} %')
            st.write(f'p-Wert: {round(p_value_m,4)}')

    #####################################################################################################################
    # Automatische Interpretation
    #####################################################################################################################

    st.subheader('Interpretation der statitischen Kennzahlen')

    interpretation = ''

    if auswahl_typ in riscfactors_w:
        if p_value_w < 0.05:
            interpretation += "Bei Frauen liegt ein statistisch signifikanter Trend vor. "
        else:
            interpretation += "Bei Frauen liegt kein statistisch signifikanter Trend vor. "


    if auswahl_typ in riscfactors_m:
        if p_value_m < 0.05:
            interpretation += "Bei Männern liegt ein statistisch signifikanter Trend vor. "
        else:
            interpretation += "Bei Männern liegt kein statistisch signifikanter Trend vor. "           

    def trend_direction(slope, tol=1e-9):
        if math.isclose(slope,0,abs_tol=tol):
            return "stabil"
        elif slope > 0:
            return 'steigend'
        else:
            return 'fallend'


    if auswahl_typ in riscfactors_w and auswahl_typ in riscfactors_m:
        
        dir_w = trend_direction(slope_w)
        dir_m = trend_direction(slope_m)

        # Fall 1: beide stabil
        if dir_w =="stabil" and dir_m == "stabil":
            interpretation += "Bei beiden Geschlechtern zeigt sich kein relevanter Trend."
        
        # Fall 2: gegenläufiger Trend
        elif dir_w != dir_m and "stabil" not in (dir_w,dir_m):
            if dir_w == "steigend":
                interpretation += "Bei Frauen steigt die Fallzahl, während sie bei Männern sinkt."
            else:
                interpretation += "Bei Männern steigt die Fallzahl, während sie bei Frauen sinkt."

        # Fall 3: gleicher Richtungstrend
        elif dir_w == dir_m:
            if math.isclose(slope_w, slope_m, rel_tol=1e-6):
                interpretation += "Die Trendstärke ist bei beiden Geschlechtern vergleichbar."
            elif abs(slope_w) > abs(slope_m):
                if dir_w == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Frauen. "
                else: 
                    interpretation += "Der Rückgang ist stärker bei Frauen. "
            else:
                if dir_m == "steigend":
                    interpretation += "Der Anstieg ist stärker bei Männern. "
                else:
                    interpretation += "Der Rückgang ist stärker bei Männern. "

        # Fall 4: ein Geschlecht stabil
        else:
            if dir_w == "stabil":
                interpretation += "Bei Frauen zeigt sich kein relevanter Trend, während sich bei Männern eine Veränderung zeigt."
            else: 
                interpretation += "Bei Männern zeigt sich kein relevanter Trend, während sich bei Frauen eine Veränderung zeigt."

    st.info(interpretation)

#################################################################################################################
#################### Zusammenhänge ##############################################################################
#################################################################################################################

elif bereich == 'Zusammenhang':
    df_w = df_cancer_w.copy().set_index('Jahr')
    df_m = df_cancer_m.copy().set_index('Jahr')
    df_rf_w = df_riscfactors_w.copy().set_index('Jahr')
    df_rf_m = df_riscfactors_m.copy().set_index('Jahr')

    jahr_gesamt_w = df_w.index.intersection(df_rf_w.index)
    jahr_gesamt_m = df_m.index.intersection(df_rf_m.index)

    df_w = df_w.loc[jahr_gesamt_w]
    df_rf_w = df_rf_w.loc[jahr_gesamt_w]
    df_m = df_m.loc[jahr_gesamt_m]
    df_rf_m = df_rf_m.loc[jahr_gesamt_m]

    # Prozentuale Veränderungen berechnen (Delta in %)
    df_w_pct = df_w.pct_change().dropna()*100
    df_rf_w_pct = df_rf_w.pct_change().dropna()*100
    df_m_pct = df_m.pct_change().dropna()*100
    df_rf_m_pct = df_rf_m.pct_change().dropna()*100

    # Korrelationsmatrix Frauen
    corr_w = pd.concat([df_w_pct,df_rf_w_pct], axis=1).corr().loc[df_w_pct.columns,df_rf_w_pct.columns]

    # Korrelationsmatrix Männer
    corr_m = pd.concat([df_m_pct,df_rf_m_pct], axis=1).corr().loc[df_m_pct.columns,df_rf_m_pct.columns]

    
    st.info(':bulb: **Korrelation**: Eine Korrelation misst die Stärke einer statistischen Beziehung von zwei Variablen zueinander. \n\n'
            'Bei einer positiven Korrelation gilt „je mehr ..., desto mehr ...“, bei einer negativen Korrelation „je mehr ..., desto weniger ...“. Korrelationen sind immer ungerichtet, das heißt, sie enthalten keine Information darüber, welche Variable eine andere bedingt.\n\n' \
    'Beispiel : Eine negative Korrelation besteht etwa zwischen der Variable „aktuelles Alter“ und „verbleibende Lebenserwartung“. Je höher das aktuelle Alter einer Person, je niedriger ist die durchschnittliche verbleibende Lebenserwartung.  \n\n' \
    'Die Stärke des statistischen Zusammenhangs wird mit dem Korrelationskoeffizienten (r) ausgedrückt, der zwischen -1 und +1 liegt:\n'
    '- **r = -1**: starker negativer Zusammenhang\n'
    '- **|r| < 0.5**: schwacher negativer bzw. positiver Zusammenhang\n '
    '- **r = 1**: starker positiver Zusammenhang\n\n'
    'Die Art eines gerichteten Zusammenhangs wird durch die Regression beschrieben.\n\n ' \
    ':rotating_light: **Wichtig**: Korrelationen sind ein Hinweis aber kein Beweis für Kausalitäten (bewiesene Ursachen- und Wirkungszusammenhänge). ')


    # Heatmap Frauen

    st.subheader("Frauen: Korrelation jährlicher prozentualer Veränderungen Krebsarten vs. Risikofaktoren")

    fig_w = go.Figure(data=go.Heatmap(
        z = corr_w.values,
        x = corr_w.columns,
        y = corr_w.index,
        colorscale='RdBu_r',
        zmid = 0,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Korrelationskoeffizient")
    ))
    fig_w.update_layout(width=1000, height=600, template='plotly_white')
    st.plotly_chart(fig_w, use_container_width=True)


    # Heatmap Männer

    st.subheader("Männer: Korrelation jährlicher prozentualer Veränderungen Krebsarten vs. Risikofaktoren")
    fig_m = go.Figure(data=go.Heatmap(
        z = corr_m.values,
        x = corr_m.columns,
        y = corr_m.index,
        colorscale='RdBu_r',
        zmid = 0,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Korrelationskoeffizient")
    ))
    fig_m.update_layout(width=1000, height=600, template='plotly_white')
    st.plotly_chart(fig_m, use_container_width=True)

    # Scatterplot für visuelle Kontrolle
    st.subheader("Scatterplots zur visuellen Trendkontrolle")
    geschlecht = st.radio("Geschlecht auswählen: ", ["Frauen", "Männer"])

    if geschlecht == "Frauen":
        df_cancer_sel = df_w
        df_rf_sel = df_rf_w

    else: 
        df_cancer_sel = df_m
        df_rf_sel = df_rf_m
    
    krebs_auswahl = st.selectbox("Krebsart wählen :", df_cancer_sel.columns)
    rf_auswahl = st.selectbox("Risikofaktor wählen :", df_rf_sel.columns)

    fig_2 = go.Figure()

    fig_2.add_trace(go.Scatter(
        x = df_rf_sel[rf_auswahl],
        y = df_cancer_sel[krebs_auswahl],
        mode = 'markers',
        name = 'Beobachtungen'
    ))

    # LOWESS Trendlinie

    x = df_rf_sel[rf_auswahl]
    y = df_cancer_sel[krebs_auswahl]

    sorted_id = np.argsort(x)
    x_sorted = x.iloc[sorted_id]
    y_sorted = y.iloc[sorted_id]

    frac = st.slider("Glättung der Trendlinie: ", 0.1, 0.9, 0.5, 0.1)
    lowess_result = lowess(y_sorted,x_sorted, frac=frac)

    fig_2.add_trace(go.Scatter(
        x = lowess_result[:,0],
        y = lowess_result[:,1],
        mode = 'lines',
        name = 'LOWESS Trendlinie',
        line = dict(color = 'red', width = 3)
    ))

    fig_2.update_layout(
    title=f'Zusammenhang ({geschlecht}): {krebs_auswahl} vs. {rf_auswahl}',
    xaxis_title=rf_auswahl,
    yaxis_title=krebs_auswahl,
    template='plotly_white'
)    
    st.plotly_chart(fig_2, use_container_width=True)

    st.markdown('Kennwerte der LOWESS-Trendlinie')
    startwert = lowess_result[0,1]
    endwert = lowess_result[-1,1]
    delta = endwert - startwert
    delta_perc = (delta/startwert)*100 if startwert != 0 else np.nan

    st.write(f'Veränderung im Zeitraum: {delta:.2f} Fälle')
    st.write(f'Prozentuale Veränderung: {delta_perc:.2f} %')

    st.info(
        ':bulb: **LOWESS**: LOWESS (Locally Weighted Scatterplot Smoothing) ist eine nichtparametrische Regressionsmethode, die lokal gewichtete Regressionen verwendet, um Trends in Datenpunkten zu glätten. Im Gegensatz zu globalen Modellen wie der linearen Regression werden hier lokale Modelle anhand von Nachbarschaften von Datenpunkten berechnet, wobei nähere Punkte stärker gewichtet werden. '
        ' Die Lowess-Kurve dient lediglich der explorativen Visualisierung möglicher nicht-linearer Zusammenhänge. '
    )
    
    st.info(
        ':rotating_light: **Hinweis**: Krebs ist immer multikausal, d.h. das Risiko, Krebs zu bekommen, hängt von mehreren Risikofaktoren ab. Daher sind die gezeigten Zusammenhänge bzgl. des Krebsrisikos kaum zu interpretieren. Zudem sind diese Korrelationen und Trends rein explorativ, da die Datengrundlage nur 20 Datensätze umfasst. '
        'Statistische Signifikanz sollte nicht interpretiert werden. '
        'Ausreißer können stark beeinflussen. '
        
    )
