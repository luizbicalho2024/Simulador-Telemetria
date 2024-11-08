import streamlit as st
import time

st.markdown("## Simulador de Comandos para Suntech e-Trac")
#st.sidebar.markdown("## Simulador de Comandos para Suntech e-Trac")

st.text_input("Insira o Serial: ", key="serial")

left_column, right_column = st.columns(2)

with left_column:
    comandos = st.radio(
        'Comandos: ',
        ("IP e APN Suntech e-Trac", "Disable ZIP", "Protocolo TCP/IP", 'Tempo de Comunicação', 'Eventos', 'NPTs'))
    
    if comandos == "IP e APN Suntech e-Trac":
        apns = st.radio(
            'APNs: ',
            ("Allcom", "M2data", "Virtueyes"))
        
        if apns == "Allcom":
            st.write('Segue código:')
            st.write(f"ST300NTW;{st.session_state.serial};02;1;allcom.claro.com.br;allcom;allcom;54.94.190.167;9601;35.198.41.183;9601;;")
        elif apns == "M2data" :
            st.write('Segue código:')
            st.write(f"ST300NTW;{st.session_state.serial};02;1;m2data.claro.com.br;claro;claro;54.94.190.167;9601;35.198.41.183;9601;;")
        elif apns == "Virtueyes" :
            st.write('Segue código:')
            st.write(f"ST300NTW;{st.session_state.serial};02;1;virtueyes.claro.com.br;veye;veye;54.94.190.167;9601;35.198.41.183;9601;;")
    elif comandos == "Disable ZIP":
        st.write('Segue código:')
        st.write(f'ST300SVC;{st.session_state.serial};02;1;180;0;0;0;1;1;0;1;0;0;1;0')
    elif comandos == 'Protocolo TCP/IP' :
        st.write('Segue código:')
        st.write(f'ST300ADP;{st.session_state.serial};02;T;T;1;;0;0;0;0;0;0')
    elif comandos == 'Tempo de Comunicação':
        veiculo = st.radio(
            'Tipo de Veículo: ',
            ("Carro", "Moto"))
        if veiculo == "Carro":
            st.write('Segue código:')
            st.write(f'ST300RPT;{st.session_state.serial};02;3600;120;3600;1;0;600;0;0;0')
        else:
            st.write('Segue código:')
            st.write(f'ST300RPT;{st.session_state.serial};02;0;60;3600;1;0;0;0;0;0')
    elif comandos == "Eventos":
        st.write('Segue código:')
        st.write(f'ST300EVT;{st.session_state.serial};02;0;10;0;12;3;9;30;20;0;1;7;1;1;0;0;0;0;0;0;9;9;0;0;0')
    elif comandos == "NPTs":
        st.write('Segue código:')
        st.write(f'ST300NPT;{st.session_state.serial};02;20.0;1;30;0;1;500;300;5;10;100;10;180;100;1')