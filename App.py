import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import json
from datetime import datetime

st.set_page_config(
    page_title="Simulateur d'Arbitrage d'ETFs",
    page_icon="🔄",
    layout="wide"
)

ETFS_FILE_PATH = "etfs.csv"
BROKERS_FILE_PATH = "courtiers.json"

def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables CSS */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #ff6b35;
        --danger-color: #d62728;
        --background-light: #f8f9fa;
        --text-dark: #2c3e50;
        --border-radius: 12px;
        --shadow: 0 2px 12px rgba(0,0,0,0.1);
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Custom header */
    .custom-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
    }
    
    .custom-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .custom-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Card containers */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    
    .card-header {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.3rem;
        color: var(--text-dark);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: var(--border-radius);
        text-align: center;
        box-shadow: var(--shadow);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.9rem;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .status-excellent { background: #d4edda; color: #155724; }
    .status-good { background: #d1ecf1; color: #0c5460; }
    .status-moderate { background: #fff3cd; color: #856404; }
    .status-high { background: #f8d7da; color: #721c24; }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: var(--border-radius);
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: var(--shadow);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* DataFrames */
    .dataframe {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    
    /* Progress bars */
    .progress-container {
        background: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .progress-bar {
        height: 8px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Grille tarifaire */
    .grille-container {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .grille-header {
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_custom_header():
    st.markdown("""
    <div class="custom-header">
        <h1>🔄 Simulateur d'Arbitrage d'ETFs</h1>
        <p>Calculez la rentabilité du remplacement d'un ETF par un autre</p>
    </div>
    """, unsafe_allow_html=True)

def load_etfs_data():
    """Charge les données des ETFs depuis etfs.csv"""
    try:
        df = pd.read_csv(ETFS_FILE_PATH, delimiter=',')
        df['Ticker'] = df['Ticker'].str.strip()
        
        # Créer un dictionnaire avec les infos ETF
        etf_info = {}
        for _, row in df.iterrows():
            ticker = row['Ticker']
            
            # Convertir les frais en nombre (gérer les virgules et pourcentages)
            frais_str = str(row.get('Frais', '0')).strip()
            if frais_str.endswith('%'):
                frais_str = frais_str[:-1]  # Enlever le %
            frais_str = frais_str.replace(',', '.')  # Remplacer virgule par point
            
            try:
                expense_ratio = float(frais_str)
            except (ValueError, TypeError):
                expense_ratio = 0.0
            
            etf_info[ticker] = {
                'name': row.get('Nom du fonds', 'Nom inconnu'),
                'expense_ratio': expense_ratio,
                'isin': row.get('ISIN', 'ISIN inconnu')
            }
        
        return etf_info
    except Exception as e:
        st.error(f"Erreur lors du chargement des ETFs : {e}")
        return {}

def load_broker_structures():
    """Charge les structures de courtiers depuis le fichier JSON"""
    try:
        with open(BROKERS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Fichier {BROKERS_FILE_PATH} non trouvé")
        return {}
    except Exception as e:
        st.error(f"Erreur lors du chargement des courtiers : {e}")
        return {}

def get_etf_price(ticker):
    """Récupère le prix actuel d'un ETF via yfinance"""
    try:
        etf = yf.Ticker(ticker)
        hist = etf.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        else:
            return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération du prix pour {ticker}: {e}")
        return None

def calculate_fees(amount, broker_name, grille_name, broker_structures):
    """Calcule les frais selon la structure tarifaire"""
    if broker_name not in broker_structures or grille_name not in broker_structures[broker_name]["grilles"]:
        return 0
    
    grille = broker_structures[broker_name]["grilles"][grille_name]
    
    if grille["type"] == "simple":
        if grille["fee_type"] == "fixed":
            return grille["fee"]
        elif grille["fee_type"] == "percentage":
            return amount * grille["fee"] / 100
    
    elif grille["type"] == "paliers":
        for palier in grille["paliers"]:
            if palier["min"] <= amount < palier["max"]:
                if palier["fee_type"] == "fixed":
                    return palier["fee"]
                elif palier["fee_type"] == "percentage":
                    fee = amount * palier["fee"] / 100
                    return max(fee, palier.get("min_fee", 0))
    
    elif grille["type"] == "mixed":
        if amount <= grille["threshold"]:
            return grille["fixed"]
        else:
            return amount * grille["percentage"] / 100
    
    return 0

def calculate_total_transaction_fees(sell_amount, buy_amount, broker_name, grille_name, broker_structures):
    """Calcule les frais totaux : vente ETF1 + achat ETF2"""
    sell_fees = calculate_fees(sell_amount, broker_name, grille_name, broker_structures)
    buy_fees = calculate_fees(buy_amount, broker_name, grille_name, broker_structures)
    
    return {
        'sell_fees': sell_fees,
        'buy_fees': buy_fees,
        'total_fees': sell_fees + buy_fees
    }

def render_grille_display(grille_name, grille_data):
    """Affiche une grille tarifaire de manière lisible"""
    st.markdown(f"""
    <div class="grille-container">
        <div class="grille-header">📋 {grille_name}</div>
    """, unsafe_allow_html=True)
    
    if grille_data["type"] == "simple":
        if grille_data["fee_type"] == "fixed":
            st.write(f"• Frais fixe : {grille_data['fee']}€")
        elif grille_data["fee_type"] == "percentage":
            st.write(f"• Frais : {grille_data['fee']}%")
    
    elif grille_data["type"] == "paliers":
        for i, palier in enumerate(grille_data["paliers"]):
            min_val = f"{palier['min']}€" if palier['min'] > 0 else "0€"
            max_val = "et plus" if palier['max'] == float('inf') or palier['max'] > 999999999 else f"{palier['max']}€"
            
            if palier["fee_type"] == "fixed":
                st.write(f"• De {min_val} à {max_val} : {palier['fee']}€")
            elif palier["fee_type"] == "percentage":
                min_fee_text = f" (min {palier['min_fee']}€)" if 'min_fee' in palier else ""
                st.write(f"• De {min_val} à {max_val} : {palier['fee']}%{min_fee_text}")
    
    elif grille_data["type"] == "mixed":
        st.write(f"• Jusqu'à {grille_data['threshold']}€ : {grille_data['fixed']}€")
        st.write(f"• Au-delà de {grille_data['threshold']}€ : {grille_data['percentage']}%")
    
    st.markdown("</div>", unsafe_allow_html=True)

def calculate_replacement_profitability(etf1_shares, etf1_price, etf1_expense, 
                                      etf2_price, etf2_expense, transaction_fees_breakdown):
    """Calcule la rentabilité du remplacement avec frais détaillés"""
    
    # Montant de la vente ETF1
    sell_amount = etf1_shares * etf1_price
    
    # Montant net après vente (montant - frais de vente)
    net_amount_after_sell = sell_amount - transaction_fees_breakdown['sell_fees']
    
    # Pour le calcul des frais d'achat, on utilise le montant net disponible
    # car c'est ce montant qui sera investi dans l'ETF2
    buy_amount = net_amount_after_sell
    
    # Montant final disponible pour l'achat après déduction des frais d'achat
    final_amount_for_purchase = net_amount_after_sell - transaction_fees_breakdown['buy_fees']
    
    # Nombre d'ETF2 qu'on peut acheter avec le montant final
    etf2_shares = final_amount_for_purchase / etf2_price
    
    # Économie annuelle sur les frais de gestion
    # ETF1 : basé sur le montant initial investi
    annual_fee_etf1 = sell_amount * (etf1_expense / 100)
    # ETF2 : basé sur le montant final investi après tous les frais
    annual_fee_etf2 = final_amount_for_purchase * (etf2_expense / 100)
    annual_savings = annual_fee_etf1 - annual_fee_etf2
    
    # Temps pour rentabiliser (en années)
    total_transaction_cost = transaction_fees_breakdown['total_fees']
    if annual_savings > 0:
        payback_years = total_transaction_cost / annual_savings
        payback_months = payback_years * 12
    else:
        payback_years = float('inf')
        payback_months = float('inf')
    
    return {
        'sell_amount': sell_amount,
        'net_after_sell': net_amount_after_sell,
        'buy_amount': buy_amount,
        'final_amount_for_purchase': final_amount_for_purchase,
        'sell_fees': transaction_fees_breakdown['sell_fees'],
        'buy_fees': transaction_fees_breakdown['buy_fees'],
        'total_transaction_cost': total_transaction_cost,
        'etf2_shares': etf2_shares,
        'annual_fee_etf1': annual_fee_etf1,
        'annual_fee_etf2': annual_fee_etf2,
        'annual_savings': annual_savings,
        'payback_years': payback_years,
        'payback_months': payback_months
    }

def main():
    load_custom_css()
    render_custom_header()
    
    # Charger les données ETF et courtiers
    etfs_data = load_etfs_data()
    broker_structures = load_broker_structures()
    
    if not etfs_data:
        st.error("Impossible de charger les données des ETFs")
        return
    
    if not broker_structures:
        st.error("Impossible de charger les données des courtiers")
        return
    
    st.header("🎯 Configuration du Remplacement")
    
    # Section ETFs
    st.subheader("📊 ETFs")
    
    # ETF 1
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1.5])
    
    with col1:
        etf_tickers = [""] + list(etfs_data.keys())
        etf1_ticker = st.selectbox(
            "ETF 1 (à remplacer)",
            options=etf_tickers,
            format_func=lambda x: f"{x} ({etfs_data.get(x, {}).get('isin', 'N/A')}) - {etfs_data.get(x, {}).get('name', 'N/A')}" if x else "-- Sélectionnez un ETF --",
            key="etf1_select"
        )
    
    with col2:
        etf1_shares = st.number_input(
            "Nombre de parts",
            min_value=0,
            value=100,
            step=1,
            key="etf1_shares"
        )
    
    with col3:
        if etf1_ticker:
            etf1_price = get_etf_price(etf1_ticker)
            if etf1_price:
                st.metric("Prix", f"{etf1_price:.2f}€")
            else:
                st.metric("Prix", "N/A")
                etf1_price = 0
        else:
            st.metric("Prix", "N/A")
            etf1_price = 0
    
    with col4:
        if etf1_ticker:
            etf1_expense = etfs_data[etf1_ticker]['expense_ratio']
            st.metric("Frais gestion", f"{etf1_expense}%")
        else:
            st.metric("Frais gestion", "-%")
    
    # ETF 2
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1.5])
    
    with col1:
        etf2_ticker = st.selectbox(
            "ETF 2 (remplacement)",
            options=etf_tickers,
            format_func=lambda x: f"{x} ({etfs_data.get(x, {}).get('isin', 'N/A')}) - {etfs_data.get(x, {}).get('name', 'N/A')}" if x else "-- Sélectionnez un ETF --",
            key="etf2_select"
        )
    
    with col2:
        if etf1_ticker and etf2_ticker and etf1_price > 0:
            etf2_price = get_etf_price(etf2_ticker)
            if etf2_price:
                # Estimation approximative pour l'affichage (sera recalculée précisément plus tard)
                sell_amount = etf1_shares * etf1_price
                estimated_etf2_shares = (sell_amount * 0.95) / etf2_price  # Estimation avec 5% de frais
                st.metric("Parts (estimé)", f"{estimated_etf2_shares:.2f}")
            else:
                st.metric("Parts", "N/A")
                etf2_price = 0
        else:
            st.metric("Parts", "N/A")
            etf2_price = 0
    
    with col3:
        if etf2_ticker:
            if etf2_price:
                st.metric("Prix", f"{etf2_price:.2f}€")
            else:
                st.metric("Prix", "N/A")
        else:
            st.metric("Prix", "N/A")
    
    with col4:
        if etf2_ticker:
            etf2_expense = etfs_data[etf2_ticker]['expense_ratio']
            st.metric("Frais gestion", f"{etf2_expense}%")
        else:
            st.metric("Frais gestion", "-%")
    
    # Saut de ligne
    st.markdown("---")

    st.subheader("🏦 Choix du Courtier")
    
    col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1.5])
    
    with col1:
        broker_names = list(broker_structures.keys())
        if broker_names:
            selected_broker = st.selectbox(
                "Courtier",
                options=broker_names,
                key="broker_select"
            )
        else:
            st.warning("Aucun courtier configuré")
            selected_broker = None
    
    with col2:
        if selected_broker and selected_broker in broker_structures:
            grille_options = list(broker_structures[selected_broker]["grilles"].keys())
            if grille_options:
                selected_grille = st.selectbox(
                    "Grille tarifaire",
                    options=grille_options,
                    key="grille_select"
                )
            else:
                st.warning("Aucune grille configurée pour ce courtier")
                selected_grille = None
        else:
            st.selectbox("Grille tarifaire", options=[], key="grille_select_empty")
            selected_grille = None
    
    with col3:
        if selected_broker and selected_grille and etf1_shares > 0 and etf1_price > 0:
            sell_amount = etf1_shares * etf1_price
            # Estimation approximative pour l'affichage
            estimated_buy_amount = sell_amount * 0.95  # Estimation
            fees_breakdown = calculate_total_transaction_fees(
                sell_amount, estimated_buy_amount, selected_broker, selected_grille, broker_structures
            )
            total_fees = fees_breakdown['total_fees']
            fee_percentage = (total_fees / sell_amount) * 100 if sell_amount > 0 else 0
            st.metric("Frais totaux (%)", f"{fee_percentage:.2f}%")
        else:
            st.metric("Frais totaux (%)", "-%")
    
    with col4:
        if selected_broker and selected_grille and etf1_shares > 0 and etf1_price > 0:
            st.metric("Montant frais", f"{total_fees:.2f}€")
        else:
            st.metric("Montant frais", "0€")
    
    # Saut de ligne
    st.markdown("---")
    
    # Affichage de la grille sélectionnée
    if selected_broker and selected_grille:
        st.markdown("**📋 Grille tarifaire sélectionnée :**")
        grille_data = broker_structures[selected_broker]["grilles"][selected_grille]
        render_grille_display(selected_grille, grille_data)
    
    # Calcul et affichage des résultats
    if st.button("🚀 Calculer la Rentabilité", type="primary", use_container_width=True):
        
        if not all([etf1_ticker, etf2_ticker, etf1_price, etf2_price, etf1_shares > 0, selected_broker, selected_grille]):
            st.error("Veuillez remplir tous les champs nécessaires")
            return
        
        sell_amount = etf1_shares * etf1_price
        
        # Calcul itératif pour obtenir les bons frais
        # Premier calcul approximatif
        net_after_sell_approx = sell_amount * 0.95  # Estimation
        fees_breakdown = calculate_total_transaction_fees(
            sell_amount, net_after_sell_approx, selected_broker, selected_grille, broker_structures
        )
        
        # Recalcul plus précis
        net_after_sell_precise = sell_amount - fees_breakdown['sell_fees']
        fees_breakdown_final = calculate_total_transaction_fees(
            sell_amount, net_after_sell_precise, selected_broker, selected_grille, broker_structures
        )
        
        results = calculate_replacement_profitability(
            etf1_shares, etf1_price, etfs_data[etf1_ticker]['expense_ratio'],
            etf2_price, etfs_data[etf2_ticker]['expense_ratio'],
            fees_breakdown_final
        )
        
        st.markdown("---")
        st.header("📊 Résultats de l'Analyse")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**💰 Montant de vente**")
            st.markdown(f"# {results['sell_amount']:,.2f}€")
        
        with col2:
            st.markdown("**💸 Frais totaux**")
            st.markdown(f"# {results['total_transaction_cost']:,.2f}€")
        
        with col3:
            st.markdown("**📈 Économie annuelle**")
            color = "🟢" if results['annual_savings'] > 0 else "🔴"
            st.markdown(f"# {color} {results['annual_savings']:,.2f}€")
        
        with col4:
            st.markdown("**⏱️ Seuil de rentabilité**")
            if results['payback_months'] != float('inf'):
                if results['payback_months'] < 12:
                    st.markdown(f"# {results['payback_months']:.1f} mois")
                else:
                    st.markdown(f"# {results['payback_years']:.1f} ans")
            else:
                st.markdown("# ❌ Jamais")
        
        # Détails de l'opération
        st.subheader("🔍 Détail de l'Opération")
        
        details_data = {
            "Élément": [
                f"💼 Vente {etf1_shares:.2f} parts {etf1_ticker}",
                f"💸 Frais de vente",
                f"💰 Net après vente",
                f"💸 Frais d'achat",
                f"💰 Montant final pour achat",
                f"📊 Prix ETF2 ({etf2_ticker})",
                f"📈 Parts ETF2 obtenues"
            ],
            "Montant": [
                f"{results['sell_amount']:,.2f}€",
                f"-{results['sell_fees']:,.2f}€",
                f"{results['net_after_sell']:,.2f}€",
                f"-{results['buy_fees']:,.2f}€",
                f"{results['final_amount_for_purchase']:,.2f}€",
                f"{etf2_price:.2f}€/part",
                f"{results['etf2_shares']:.2f} parts"
            ]
        }
        
        details_df = pd.DataFrame(details_data)
        st.dataframe(details_df, use_container_width=True, hide_index=True)
        
        # Résumé des frais
        st.subheader("💸 Détail des Frais de Courtage")
        
        fees_summary_data = {
            "Type d'opération": ["Vente ETF1", "Achat ETF2", "Total"],
            "Montant de l'opération": [
                f"{results['sell_amount']:,.2f}€",
                f"{results['buy_amount']:,.2f}€",
                f"{results['sell_amount']:,.2f}€"
            ],
            "Frais": [
                f"{results['sell_fees']:,.2f}€",
                f"{results['buy_fees']:,.2f}€",
                f"{results['total_transaction_cost']:,.2f}€"
            ],
            "% du montant": [
                f"{(results['sell_fees']/results['sell_amount']*100):.3f}%",
                f"{(results['buy_fees']/results['buy_amount']*100):.3f}%",
                f"{(results['total_transaction_cost']/results['sell_amount']*100):.3f}%"
            ]
        }
        
        fees_summary_df = pd.DataFrame(fees_summary_data)
        st.dataframe(fees_summary_df, use_container_width=True, hide_index=True)
        
        # Comparaison des frais annuels
        st.subheader("📊 Comparaison des Frais Annuels")
        
        fees_data = {
            "ETF": [etf1_ticker, etf2_ticker, "Différence"],
            "Frais de gestion (%)": [
                f"{etfs_data[etf1_ticker]['expense_ratio']}%",
                f"{etfs_data[etf2_ticker]['expense_ratio']}%",
                f"{etfs_data[etf1_ticker]['expense_ratio'] - etfs_data[etf2_ticker]['expense_ratio']:+.2f}%"
            ],
            "Capital investi": [
                f"{results['sell_amount']:,.2f}€",
                f"{results['final_amount_for_purchase']:,.2f}€",
                f"{results['sell_amount'] - results['final_amount_for_purchase']:+,.2f}€"
            ],
            "Frais annuels (€)": [
                f"{results['annual_fee_etf1']:,.2f}€",
                f"{results['annual_fee_etf2']:,.2f}€",
                f"{results['annual_savings']:+,.2f}€"
            ]
        }
        
        fees_df = pd.DataFrame(fees_data)
        st.dataframe(fees_df, use_container_width=True, hide_index=True)
        
        # Recommandation
        st.subheader("🎯 Recommandation")
        if results['annual_savings'] > 0:
            if results['payback_months'] < 12:
                st.success(f"✅ **Recommandation : REMPLACER** - Rentable en {results['payback_months']:.1f} mois")
            elif results['payback_years'] < 6:
                st.warning(f"⚠️ **Recommandation : À CONSIDÉRER** - Rentable en {results['payback_years']:.1f} ans")
            else:
                st.error(f"❌ **Recommandation : NE PAS REMPLACER** - Rentable seulement après {results['payback_years']:.1f} ans")
        else:
            st.error("❌ **Ce remplacement n'est jamais rentable** - L'ETF2 a des frais plus élevés que l'ETF1")

if __name__ == "__main__":
    main()