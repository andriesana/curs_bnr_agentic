import os
from curs_bnr.config import REPORTS_DIR
import pandas as pd
import plotly.graph_objects as go
from typing import (
    Optional
)


def plot_forecast_results(
    y_true: pd.Series,
    df_pred: pd.DataFrame,
    model_name: str,
    reports_dir: str = str(REPORTS_DIR),
    y_hist: Optional[pd.Series] = None
) -> str:
    """
    Generează un grafic interactiv Plotly pentru vizualizarea performanței modelului de prognoză.
    Afișează datele reale, valorile prezise și intervalul de încredere (shading).

    Args:
        y_true (pd.Series): Valorile reale din setul de test (Hold-out).
        df_pred (pd.DataFrame): Dataframe cu coloanele 'pred_mean', 'conf_lower', 'conf_upper'.
        model_name (str): Numele modelului utilizat (pentru titlu).
        reports_dir (str): Folderul unde se va salva graficul HTML.
        y_hist (Optional[pd.Series]): Date istorice suplimentare pentru context vizual (opțional).

    Returns:
        str: Calea către fișierul HTML salvat.
    """
    # 1. Verificare riguroasă a structurii DataFrame-ului de predicție
    required_cols = ['pred_mean', 'conf_lower', 'conf_upper']
    if not all(col in df_pred.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_pred.columns]
        raise ValueError(f"Eroare structură df_pred: Lipsesc coloanele {missing}")

    fig = go.Figure()

    # 2. Adăugare context istoric (dacă este furnizat)
    if y_hist is not None:
        fig.add_trace(go.Scatter(
            x=y_hist.index,
            y=y_hist.values,
            mode='lines',
            name='Historical Rate',
            line=dict(color='lightgrey', dash='dot'),
            showlegend=True
        ))

    # 3. Adăugare date reale (Test Set)
    fig.add_trace(go.Scatter(
        x=y_true.index,
        y=y_true.values,
        mode='lines+markers',
        name='Actual Rate (Test)',
        line=dict(color='DarkSlateGrey', width=2),
        showlegend=True
    ))

    # 4. Adăugare Interval de Încredere (Shading)
    # Marginea superioară (invizibilă, baza pentru fill)
    fig.add_trace(go.Scatter(
        x=df_pred.index,
        y=df_pred['conf_upper'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Marginea inferioară + fill spre cea superioară
    fig.add_trace(go.Scatter(
        x=df_pred.index,
        y=df_pred['conf_lower'],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(65, 105, 225, 0.2)', # RoyalBlue cu opacitate 20%
        name='95% Confidence Interval',
        showlegend=True,
        hoverinfo='skip'
    ))

    # 5. Adăugare Predicție (Mean)
    fig.add_trace(go.Scatter(
        x=df_pred.index,
        y=df_pred['pred_mean'],
        mode='lines+markers',
        name=f'Predicted Rate ({model_name})',
        line=dict(color='RoyalBlue', width=3),
        showlegend=True
    ))

    # 6. Setări layout (Aesthetics & Interaction)
    fig.update_layout(
        title=dict(
            text=f"GBP/RON Exchange Rate Forecast Evaluation<br><sup>Best Model: {model_name}</sup>",
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Date",
        yaxis_title="Rate (GBP/RON)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        template="plotly_white",
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        )
    )

    # 7. Salvare în folderul reports/
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    output_path = os.path.join(reports_dir, "forecast_plot.html")
    fig.write_html(output_path)

    print(f"[PLOT] [SUCCESS] Graficul interactiv a fost salvat in: {output_path}")
    
    return output_path
