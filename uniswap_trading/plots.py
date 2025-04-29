import pandas as pd
import plotly.express as px

def generate_fee_visualizations_hourly(
    vol_df: pd.DataFrame,
    date_col: str = 'datetime',
    fee_col: str = 'fees_usd'
):
    df = vol_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # 1) Hourly Fees
    fig_hourly = px.line(
        df, x=date_col, y=fee_col,
        title='Hourly Fees (USD)'
    )
    fig_hourly.update_layout(
        xaxis_title='Datetime',
        yaxis_title='Fees (USD)',
        hovermode='x unified'
    )

    # 2) Cumulative Fees
    df = df.sort_values(by=date_col)
    df['cum_fees'] = df[fee_col].cumsum()
    fig_cum = px.line(
        df, x=date_col, y='cum_fees',
        title='Cumulative Fees (USD)'
    )
    fig_cum.update_layout(
        xaxis_title='Datetime',
        yaxis_title='Cumulative Fees (USD)',
        hovermode='x unified'
    )

    # 3) Heatmap by Weekday vs Hour
    #  — сначала агрегируем (суммируем) все записи, у которых одна и та же метка часа
    cal_ser = (
        df
        .set_index(date_col)[fee_col]
        .groupby(level=0).sum()
        .asfreq('H', fill_value=0)
    )
    # теперь превращаем Series в DataFrame и расчитываем день недели и час
    cal_df = cal_ser.to_frame(name=fee_col)
    cal_df['weekday'] = cal_df.index.weekday
    cal_df['hour']    = cal_df.index.hour

    # pivot: строки — дни недели, столбцы — часы
    heatmap_df = cal_df.pivot_table(
        index='weekday',
        columns='hour',
        values=fee_col,
        fill_value=0
    )

    weekday_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    fig_heatmap = px.imshow(
        heatmap_df,
        labels=dict(x='Hour of Day', y='Weekday', color='Fees (USD)'),
        title='Heatmap of Hourly Fees by Weekday',
        aspect='auto'
    )
    fig_heatmap.update_xaxes(
        tickmode='array',
        tickvals=list(range(24)),
        ticktext=[f"{h}:00" for h in range(24)]
    )
    fig_heatmap.update_yaxes(
        tickmode='array',
        tickvals=list(range(7)),
        ticktext=weekday_names,
        autorange='reversed'
    )

    return fig_hourly, fig_cum, fig_heatmap
