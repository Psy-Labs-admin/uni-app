import pandas as pd
import plotly.express as px

def generate_fee_visualizations(
    vol_df: pd.DataFrame,
    date_col: str = 'date',
    fee_col: str = 'fees_usd'
):
    """
    Упаковывает построение трёх интерактивных графиков по комиссиям:
      1. Daily Fees (линия)
      2. Cumulative Fees (кумулятивная линия)
      3. Calendar Heatmap (тепловая карта по дням недели и номерам недель)

    :param vol_df: DataFrame с колонкой дат и колонкой сборов
    :param date_col: имя колонки с датами (datetime или строка)
    :param fee_col: имя колонки с ежедневными комиссиями в USD
    :return: tuple(fig_daily, fig_cum, fig_heatmap)
    """
    df = vol_df.copy()
    # Приводим дату к datetime (если надо)
    df[date_col] = pd.to_datetime(df[date_col])

    # 1) Daily Fees
    fig_daily = px.line(
        df, x=date_col, y=fee_col,
        title='Daily Fees (USD)'
    )
    fig_daily.update_layout(
        xaxis_title='Date',
        yaxis_title='Fees (USD)',
        hovermode='x unified'
    )

    # 2) Cumulative Fees
    df['cum_fees'] = df[fee_col].cumsum()
    fig_cum = px.line(
        df, x=date_col, y='cum_fees',
        title='Cumulative Fees (USD)'
    )
    fig_cum.update_layout(
        xaxis_title='Date',
        yaxis_title='Cumulative Fees (USD)',
        hovermode='x unified'
    )

    # 3) Calendar Heatmap
    cal_df = df.set_index(date_col).asfreq('D', fill_value=0)
    cal_df['week'] = cal_df.index.isocalendar().week
    cal_df['weekday'] = cal_df.index.weekday  # Mon=0 … Sun=6
    heatmap_df = cal_df.pivot(
        index='weekday',
        columns='week',
        values=fee_col
    )
    fig_heatmap = px.imshow(
        heatmap_df,
        labels=dict(x='Week Number', y='Weekday', color='Fees (USD)'),
        title='Calendar Heatmap of Daily Fees (USD)'
    )
    fig_heatmap.update_yaxes(
        ticktext=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
        tickvals=list(range(7)),
        autorange='reversed'
    )

    return fig_daily, fig_cum, fig_heatmap
