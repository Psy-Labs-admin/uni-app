# import plotly.express as px
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import plotly.graph_objects as go
# from itertools import cycle

# def plot_combined_ranges_and_actions(collected, strategy):
#     fig = go.Figure()

#     # Цена ETH/BTC
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Price"], mode="lines",
#         name="ETH/BTC Price", line=dict(color="black")
#     ))

#     # Зоны покоя
#     fig.add_trace(go.Scatter(
#         x=collected["Time"] + collected["Time"][::-1],
#         y=collected["Rest Zone High 1"] + collected["Rest Zone Low 1"][::-1],
#         fill='toself', fillcolor='rgba(128,128,128,0.15)',
#         line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 1", showlegend=True
#     ))
#     fig.add_trace(go.Scatter(
#         x=collected["Time"] + collected["Time"][::-1],
#         y=collected["Rest Zone High 2"] + collected["Rest Zone Low 2"][::-1],
#         fill='toself', fillcolor='rgba(160,160,160,0.25)',
#         line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 2", showlegend=True
#     ))

#     # Диапазоны
#     fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range Low"],
#         mode="lines", name="Primary Range", line=dict(color="blue", dash="dot")))
#     fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range High"],
#         mode="lines", name=None, showlegend=False, line=dict(color="blue", dash="dot")))

#     fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Secondary Range Low"],
#         mode="lines", name="Secondary Range", line=dict(color="green", dash="dot")))
#     fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Secondary Range High"],
#         mode="lines", name=None, showlegend=False, line=dict(color="green", dash="dot")))

#     # Действия стратегии
#     log_df = pd.DataFrame(strategy.log)
#     log_df["step"] = log_df.index

#     # event_colors = {
#     #     "initialize": "blue",
#     #     "in_rest_zone": "gray",
#     #     "rebalance": "orange",
#     #     "move_range": "green"
#     # }

#     for event in log_df["event"].unique():
#         subset = log_df[log_df["event"] == event]
#         fig.add_trace(go.Scatter(
#             x=subset["step"], y=subset["price"], mode="markers",
#             name=event
#         ))

#     fig.update_layout(
#         title="Uniswap V3 Strategy — Диапазоны, Зоны Покоя и Лог Действий",
#         xaxis_title="Шаг/Время",
#         yaxis_title="Цена ETH/BTC",
#         height=750,
#         legend_title="Элементы"
#     )
#     fig.show()


# def plot_strategy_ranges(collected):
#     fig = go.Figure()

#     # Цена
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Price"], mode="lines",
#         name="ETH/BTC Price", line=dict(color="black")
#     ))

#     # Заливка зон покоя
#     fig.add_trace(go.Scatter(
#         x=collected["Time"] + collected["Time"][::-1],
#         y=collected["Rest Zone High 1"] + collected["Rest Zone Low 1"][::-1],
#         fill='toself', fillcolor='rgba(128,128,128,0.15)',
#         line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 1", showlegend=True
#     ))
#     fig.add_trace(go.Scatter(
#         x=collected["Time"] + collected["Time"][::-1],
#         y=collected["Rest Zone High 2"] + collected["Rest Zone Low 2"][::-1],
#         fill='toself', fillcolor='rgba(160,160,160,0.25)',
#         line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 2", showlegend=True
#     ))

#     # Границы диапазонов одной линией
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Primary Range Low"], mode="lines",
#         name="Primary Range", line=dict(color="blue", dash="dot")
#     ))
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Primary Range High"], mode="lines",
#         showlegend=False, line=dict(color="blue", dash="dot")
#     ))
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Secondary Range Low"], mode="lines",
#         name="Secondary Range", line=dict(color="green", dash="dot")
#     ))
#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Secondary Range High"], mode="lines",
#         showlegend=False, line=dict(color="green", dash="dot")
#     ))

#     fig.update_layout(
#         title="Uniswap V3 Strategy Simulation — Диапазоны и Зоны Покоя (Интерактив)",
#         xaxis_title="Время",
#         yaxis_title="Цена ETH/BTC",
#         height=700,
#         legend_title="Уровни"
#     )
#     fig.show()


# def plot_actions(strategy):  
#     log_df = pd.DataFrame(strategy.log)
#     log_df["step"] = log_df.index
    
#     fig = px.scatter(
#         log_df,
#         x="step",
#         y="price",
#         color="event",
#         hover_data=["event", "price", "sigma"],
#         title="Интерактивный лог действий стратегии Uniswap V3",
#         labels={"step": "Шаг", "price": "Цена ETH/BTC"},
#         color_discrete_map={
#             "initialize": "blue",
#             "in_rest_zone": "gray",
#             "rebalance": "orange",
#             "move_range": "green"
#         }
#     )
    
#     fig.update_traces(marker=dict(size=6, opacity=0.8))
#     fig.update_layout(legend_title_text='Событие', height=600)
#     fig.show()


# def plot_strategy_vs_hodl(strategy_usd, hodl_usd):
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(y=strategy_usd, mode='lines', name='Strategy Portfolio (USD)'))
#     fig.add_trace(go.Scatter(y=hodl_usd, mode='lines', name='HODL Portfolio (USD)', line=dict(dash='dash')))

#     fig.update_layout(
#         title='Сравнение стратегии и HODL в USD',
#         xaxis_title='Шаг',
#         yaxis_title='Стоимость портфеля в USD',
#         height=500
#     )
#     fig.show()


# def plot_wallet_and_price(collected):
#     import plotly.graph_objects as go
#     from plotly.subplots import make_subplots

#     # Нормализуем ETH и BTC к их максимуму (или к начальному значению)
#     eth_scaled = [v / max(collected["ETH"]) for v in collected["ETH"]]
#     btc_scaled = [v / max(collected["BTC"]) for v in collected["BTC"]]

#     fig = make_subplots(
#         rows=1, cols=1,
#         shared_xaxes=True,
#         specs=[[{"secondary_y": True}]],
#         subplot_titles=("Нормализованный баланс ETH/BTC и курс ETH/BTC",)
#     )

#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=eth_scaled,
#         mode="lines", name="ETH (норм.)", line=dict(color="purple")
#     ), row=1, col=1, secondary_y=False)

#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=btc_scaled,
#         mode="lines", name="BTC (норм.)", line=dict(color="orange")
#     ), row=1, col=1, secondary_y=False)

#     fig.add_trace(go.Scatter(
#         x=collected["Time"], y=collected["Price"],
#         mode="lines", name="ETH/BTC Price", line=dict(color="black", dash="dot")
#     ), row=1, col=1, secondary_y=True)

#     fig.update_layout(
#         title="Нормализованные активы в портфеле и курс ETH/BTC",
#         height=500
#     )
#     fig.update_yaxes(title_text="ETH / BTC (норм.)", secondary_y=False)
#     fig.update_yaxes(title_text="ETH/BTC цена", secondary_y=True)
#     fig.show()
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from itertools import cycle

from price_simulation import simulate_prices
from simulation import run_simulation
from strategy import UniswapV4Strategy


def plot_ranges(collected: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price"))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range Low"], mode="lines", name="Primary Range Low", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range High"], mode="lines", name="Primary Range High", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected.get("Secondary Range Low"), mode="lines", name="Secondary Range Low", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected.get("Secondary Range High"), mode="lines", name="Secondary Range High", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=collected["Time"]+collected["Time"][::-1], y=collected["Rest Zone High 1"]+collected["Rest Zone Low 1"][::-1], fill='toself', fillcolor='rgba(128,128,128,0.15)', line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 1"))
    fig.add_trace(go.Scatter(x=collected["Time"]+collected["Time"][::-1], y=collected["Rest Zone High 2"]+collected["Rest Zone Low 2"][::-1], fill='toself', fillcolor='rgba(160,160,160,0.25)', line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 2"))
    fig.update_layout(title="ETH/BTC Price and Strategy Ranges with Rest Zones", xaxis_title="Time", yaxis_title="Price", height=600)
    return fig


def plot_combined_ranges_and_actions(collected: dict, strategy) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price", line=dict(color="black")))
    fig.add_trace(go.Scatter(x=collected["Time"]+collected["Time"][::-1], y=collected["Rest Zone High 1"]+collected["Rest Zone Low 1"][::-1], fill='toself', fillcolor='rgba(128,128,128,0.15)', line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 1"))
    fig.add_trace(go.Scatter(x=collected["Time"]+collected["Time"][::-1], y=collected["Rest Zone High 2"]+collected["Rest Zone Low 2"][::-1], fill='toself', fillcolor='rgba(160,160,160,0.25)', line=dict(color='rgba(0,0,0,0)'), name="Rest Zone 2"))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range Low"], mode="lines", name="Primary Range", line=dict(color="blue", dash="dot")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Primary Range High"], mode="lines", showlegend=False, line=dict(color="blue", dash="dot")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Secondary Range Low"], mode="lines", name="Secondary Range", line=dict(color="green", dash="dot")))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Secondary Range High"], mode="lines", showlegend=False, line=dict(color="green", dash="dot")))
    log_df = pd.DataFrame(strategy.log)
    log_df["step"] = log_df.index
    for event in log_df["event"].unique():
        subset = log_df[log_df["event"] == event]
        fig.add_trace(go.Scatter(x=subset["step"], y=subset["price"], mode="markers", name=event))
    fig.update_layout(title="Ranges, Rest Zones and Strategy Actions", xaxis_title="Step", yaxis_title="Price", height=750)
    return fig


def plot_strategy_vs_hodl(strategy_usd: list, hodl_usd: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=strategy_usd, mode='lines', name='Strategy Portfolio (USD)'))
    fig.add_trace(go.Scatter(y=hodl_usd, mode='lines', name='HODL Portfolio (USD)', line=dict(dash='dash')))
    fig.update_layout(title='Strategy vs HODL in USD', xaxis_title='Step', yaxis_title='Portfolio Value (USD)', height=500)
    return fig


def plot_wallet_and_price(collected: dict) -> go.Figure:
    eth_scaled = [v / max(collected["ETH"]) for v in collected["ETH"]]
    btc_scaled = [v / max(collected["BTC"]) for v in collected["BTC"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=collected["Time"], y=eth_scaled, mode="lines", name="ETH (scaled)"))
    fig.add_trace(go.Scatter(x=collected["Time"], y=btc_scaled, mode="lines", name="BTC (scaled)"))
    fig.add_trace(go.Scatter(x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price", line=dict(dash="dot")))
    fig.update_layout(title="Normalized Wallet vs Price", xaxis_title="Time", yaxis_title="Value (normalized)", height=500)
    return fig


def main():
    st.title("Uniswap V4 Strategy Simulation Web Service")

    # Sidebar inputs
    st.sidebar.header("Simulation Parameters")
    start_price_eth = st.sidebar.number_input("Start ETH Price", value=2000.0)
    start_price_btc = st.sidebar.number_input("Start BTC Price", value=30000.0)
    start_price_unk = st.sidebar.number_input("Start UNK Price", value=2000.0)
    rho = st.sidebar.number_input("Correlation (rho)", min_value=-1.0, max_value=1.0, value=0.0)
    vol_eth = st.sidebar.number_input("ETH Volatility (std dev)", value=0.01)
    vol_btc = st.sidebar.number_input("BTC Volatility (std dev)", value=0.015)
    vol_unk = st.sidebar.number_input("UNK Volatility (std dev)", value=0.02)
    trend_eth = st.sidebar.number_input("ETH Trend", value=0.0)
    trend_btc = st.sidebar.number_input("BTC Trend", value=0.0)
    trend_unk = st.sidebar.number_input("UNK Trend", value=0.0)
    n_steps = st.sidebar.number_input("Number of Steps", value=100, step=1)

    st.sidebar.header("Strategy Parameters")
    epsilon_ticks = st.sidebar.number_input("Epsilon Ticks", value=30, step=1)
    range_ticks = st.sidebar.number_input("Range Ticks", value=300, step=1)
    alpha = st.sidebar.number_input("Alpha (Liquidity Shift)", value=0.33)
    lambda_ = st.sidebar.number_input("Lambda (EWMA)", value=0.9)
    initial_eth = st.sidebar.number_input("Initial ETH", value=1000.0)
    initial_btc = st.sidebar.number_input("Initial BTC", value=20.0)

    if st.sidebar.button("Run Simulation"):
        # Generate prices
        df_prices = simulate_prices(
            start_price_eth=start_price_eth,
            start_price_btc=start_price_btc,
            start_price_unk=start_price_unk,
            rho=rho,
            sigma_eth=vol_eth,
            sigma_btc=vol_btc,
            sigma_unk=vol_unk,
            trend_eth=trend_eth,
            trend_btc=trend_btc,
            trend_unk=trend_unk,
            T=int(n_steps),
            seed=None
        )
        prices_ratio = df_prices["ETH/BTC"].tolist()
        eth_prices = df_prices["ETH"].tolist()
        btc_prices = df_prices["BTC"].tolist()

        # Run strategy simulation
        strategy = UniswapV4Strategy(
            epsilon_ticks, range_ticks, alpha, lambda_,
            initial_eth, initial_btc
        )
        collected, strat_obj, strat_usd, hodl_usd = run_simulation(
            prices_ratio, eth_prices, btc_prices,
            strategy, initial_eth, initial_btc
        )

        # Final values
        final_strat_value = strat_usd[-1] if isinstance(strat_usd, list) else strat_usd
        final_hodl_value = hodl_usd[-1] if isinstance(hodl_usd, list) else hodl_usd

        # Display metrics
        st.subheader("Performance Metrics")
        st.write(f"Final Strategy Value: **{final_strat_value:.2f} USD**")
        st.write(f"Final HODL Value: **{final_hodl_value:.2f} USD**")

        # Dataframe
        st.subheader("Collected Data")
        st.dataframe(pd.DataFrame(collected))

        # Visualizations
        st.subheader("Visualization Options")
        if st.checkbox("Price & Strategy Ranges"):
            st.plotly_chart(plot_ranges(collected), use_container_width=True)
        if st.checkbox("Ranges & Actions"):
            st.plotly_chart(plot_combined_ranges_and_actions(collected, strat_obj), use_container_width=True)
        if st.checkbox("Strategy vs HODL"):
            st.plotly_chart(plot_strategy_vs_hodl(strat_usd, hodl_usd), use_container_width=True)
        if st.checkbox("Normalized Wallet & Price"):
            st.plotly_chart(plot_wallet_and_price(collected), use_container_width=True)


if __name__ == "__main__":
    main()
