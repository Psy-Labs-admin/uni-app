import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from price_simulation import simulate_prices
from simulation import run_simulation
from strategy import UniswapV4Strategy
from produce_fees import produce_fees
from plots import generate_fee_visualizations

# --- Plotting Functions with Hover and Unified Mode ---

def plot_ranges(collected: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price",
        hovertemplate="Time: %{x}<br>Price: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Primary Range Low"], mode="lines", name="Primary Range Low",
        line=dict(dash="dash"), hovertemplate="Time: %{x}<br>Low: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Primary Range High"], mode="lines", name="Primary Range High",
        line=dict(dash="dash"), hovertemplate="Time: %{x}<br>High: %{y:.4f}<extra></extra>"
    ))
    low2 = collected.get("Secondary Range Low")
    high2 = collected.get("Secondary Range High")
    if low2 and high2:
        fig.add_trace(go.Scatter(
            x=collected["Time"], y=low2, mode="lines", name="Secondary Range Low",
            line=dict(dash="dot"), hovertemplate="Time: %{x}<br>Low2: %{y:.4f}<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=collected["Time"], y=high2, mode="lines", showlegend=False,
            line=dict(dash="dot"), hovertemplate="Time: %{x}<br>High2: %{y:.4f}<extra></extra>"
        ))
    fig.add_trace(go.Scatter(
        x=collected["Time"] + collected["Time"][::-1],
        y=collected["Rest Zone High 1"] + collected["Rest Zone Low 1"][::-1],
        fill='toself', fillcolor='rgba(128,128,128,0.15)', line=dict(color='rgba(0,0,0,0)'),
        name="Rest Zone 1", hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"] + collected["Time"][::-1],
        y=collected["Rest Zone High 2"] + collected["Rest Zone Low 2"][::-1],
        fill='toself', fillcolor='rgba(160,160,160,0.25)', line=dict(color='rgba(0,0,0,0)'),
        name="Rest Zone 2", hoverinfo='skip'
    ))
    fig.update_layout(
        title="ETH/BTC Price and Strategy Ranges with Rest Zones",
        xaxis_title="Time",
        yaxis_title="Price",
        height=600,
        hovermode='x unified'
    )
    return fig


def plot_combined_ranges_and_actions(collected: dict, strategy) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price",
        line=dict(color="black"), hovertemplate="Step: %{x}<br>Price: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"] + collected["Time"][::-1],
        y=collected["Rest Zone High 1"] + collected["Rest Zone Low 1"][::-1],
        fill='toself', fillcolor='rgba(128,128,128,0.15)', line=dict(color='rgba(0,0,0,0)'),
        name="Rest Zone 1", hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"] + collected["Time"][::-1],
        y=collected["Rest Zone High 2"] + collected["Rest Zone Low 2"][::-1],
        fill='toself', fillcolor='rgba(160,160,160,0.25)', line=dict(color='rgba(0,0,0,0)'),
        name="Rest Zone 2", hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Primary Range Low"], mode="lines", name="Primary Range",
        line=dict(color="blue", dash="dot"), hovertemplate="Step: %{x}<br>Primary Low: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Primary Range High"], mode="lines", showlegend=False,
        line=dict(color="blue", dash="dot"), hovertemplate="Step: %{x}<br>Primary High: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Secondary Range Low"], mode="lines", name="Secondary Range",
        line=dict(color="green", dash="dot"), hovertemplate="Step: %{x}<br>Secondary Low: %{y:.4f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Secondary Range High"], mode="lines", showlegend=False,
        line=dict(color="green", dash="dot"), hovertemplate="Step: %{x}<br>Secondary High: %{y:.4f}<extra></extra>"
    ))
    log_df = pd.DataFrame(strategy.log)
    log_df["step"] = log_df.index
    for event in log_df["event"].unique():
        subset = log_df[log_df["event"] == event]
        fig.add_trace(go.Scatter(
            x=subset["step"], y=subset["price"], mode="markers", name=event,
            hovertemplate=f"Event: {event}<br>Step: %{{x}}<br>Price: %{{y:.4f}}<extra></extra>"
        ))
    fig.update_layout(
        title="Ranges, Rest Zones and Strategy Actions",
        xaxis_title="Step",
        yaxis_title="Price",
        height=750,
        hovermode='x unified'
    )
    return fig


def plot_strategy_vs_hodl(strategy_usd: list, hodl_usd: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=strategy_usd, mode='lines+markers', name='Strategy Portfolio (USD)',
        hovertemplate="Step: %{x}<br>Value: $%{y:.2f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        y=hodl_usd, mode='lines+markers', name='HODL Portfolio (USD)', line=dict(dash='dash'),
        hovertemplate="Step: %{x}<br>Value: $%{y:.2f}<extra></extra>"
    ))
    fig.update_layout(
        title='Strategy vs HODL in USD',
        xaxis_title='Step',
        yaxis_title='Portfolio Value (USD)',
        height=500,
        hovermode='x unified'
    )
    return fig


def plot_wallet_and_price(collected: dict) -> go.Figure:
    eth_scaled = [v / max(collected["ETH"]) for v in collected["ETH"]]
    btc_scaled = [v / max(collected["BTC"]) for v in collected["BTC"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=eth_scaled, mode="lines+markers", name="ETH (scaled)",
        hovertemplate="Time: %{x}<br>ETH (scaled): %{y:.3f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=btc_scaled, mode="lines+markers", name="BTC (scaled)",
        hovertemplate="Time: %{x}<br>BTC (scaled): %{y:.3f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=collected["Time"], y=collected["Price"], mode="lines", name="ETH/BTC Price", line=dict(dash="dot"),
        hovertemplate="Time: %{x}<br>Price: %{y:.4f}<extra></extra>"
    ))
    fig.update_layout(
        title="Normalized Wallet vs Price",
        xaxis_title="Time",
        yaxis_title="Value (normalized)",
        height=500,
        hovermode='x unified'
    )
    return fig

# --- Main Streamlit App ---

# --- Main Application ---
def main():
    st.set_page_config(layout='wide')
    st.title("Uniswap V4 Strategy Simulation & Analytics")

    # --- Navigation ---
    page = st.sidebar.selectbox(
        "Menu",
        ["Simulator", "Fees", "Guide"],
        help="Выберите страницу приложения"
    )

    # --- Fees Page ---
    if page == "Fees":
        st.header("💰 Комиссии Uniswap V4 — Анализ и Визуализация")

        # 1) Параметры периода
        start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2024-05-01"))
        end_date   = st.sidebar.date_input("End Date", pd.to_datetime("today"))

        # 2) Выбор файла по второму активу
        symbol = st.sidebar.selectbox(
            "Select token",
            options=["WBTC", "CRV", "LDO"],
            index=0
        )

        if st.sidebar.button("Generate Fees Plots"):
            # 3) Маппинг токена → CSV-файл
            file_map = {
                "WBTC": "./data/vol_with_usd_with_fee_eth_btc.csv",
                "CRV":  "./data/vol_with_usd_with_fee_eth_crv.csv",
                "LDO":  "./data/vol_with_usd_with_fee_eth_ldo.csv",
            }

            # 4) Читаем выбранный CSV
            df_fees = pd.read_csv(
                file_map[symbol],
                parse_dates=["date"]
            )

            # 5) Фильтрация по диапазону и сортировка
            mask = (
                (df_fees["date"] >= pd.to_datetime(start_date)) &
                (df_fees["date"] <= pd.to_datetime(end_date))
            )
            df_fees = df_fees.loc[mask].sort_values("date")

            # 7) Строим графики на основе готового DataFrame
            #    (предполагаем функцию produce_fees_from_df, 
            #     которая принимает DataFrame с датой + fees_usd* и рисует ваши три фигуры)
            fig_daily, fig_cum, fig_heatmap = generate_fee_visualizations(df_fees)

            st.subheader("Daily Fees")
            st.plotly_chart(fig_daily, use_container_width=True)

            st.subheader("Cumulative Fees")
            st.plotly_chart(fig_cum, use_container_width=True)

            st.subheader("Fees Heatmap")
            st.plotly_chart(fig_heatmap, use_container_width=True)

        return



    if page == "Guide":
        st.header("📖 User Guide")
        st.markdown("""
        ## 1. Simulation Parameters
        - **Start ETH Price**: начальная цена ETH (USD).  
        - **Start BTC Price**: начальная цена BTC (USD).  
        - **Correlation (rho)**: корреляция доходностей ETH и BTC.  
        - **ETH/BTC Volatility**: стандартные отклонения доходностей (per-step).  
        - **Trend**: ожидаемый дрифт (drift) per-step.  
        - **Number of Steps**: сколько шагов генерировать в симуляции.

        ## 2. Strategy Parameters
        - **Epsilon Ticks**: полуширина основного диапазона.  
        - **Range Ticks**: полуширина вторичного диапазона.  
        - **Alpha (Liquidity Shift)**: насколько агрессивно смещается ликвидность.  
        - **Lambda (EWMA)**: фактор затухания для расчёта скользящей оценки волатильности.  
        - **Initial ETH / BTC**: стартовые балансы в кошельке.

        ## 3. Visualization Options
        Вы можете включать/выключать:
        - **Price & Strategy Ranges**: цена и границы ордеров.  
        - **Ranges & Actions**: границы + точки входа/выхода.  
        - **Strategy vs HODL**: сравнение кумулятивных PnL.  
        - **Normalized Wallet & Price**: нормализованные балансы и цена.  
        - **Show Metrics & Drawdown**: Sharpe, волатильность, Max Drawdown + кривая DnD.  
        - **Run Monte Carlo Simulation**: оценка распределения будущих результатов (задайте число прогонов).  
        - **Show CDF of Final Values**: эмпирическая CDF финальных портфельных значений.

        ## 4. Monte Carlo Simulation
        После запуска собираются `mc_runs` траекторий:
        1. Для каждой — новая генерация цен и прогон стратегии + HODL.  
        2. По всем прогонкам строится область между 10-м и 90-м перцентилями и медиана.  
        3. Итоговая таблица показывает 10/50/90-е перцентили для Strategy и HODL.

        ## 5. Sensitivity Analysis
        Выполняется grid-search по трём параметрам:
        - ε в диапазоне `[eps_range[0]..eps_range[1]]`
        - α в диапазоне `[alpha_range[0]..alpha_range[1]]`
        - λ в диапазоне `[lambda_range[0]..lambda_range[1]]`
        
        **Результат**: теплокарта Sharpe при фиксированном λ = среднее значение из выбранного диапазона.

        ## 6. Как пользоваться
        1. Выберите «Simulator».  
        2. Задайте нужные входные параметры.  
        3. Отметьте нужные визуализации в боковой панели.  
        4. Нажмите **Run Simulation**.  
        5. При необходимости переключитесь на «Guide» для повторного ознакомления.

        > **Совет**: сперва попробуйте базовую симуляцию без Monte Carlo, 
        > чтобы быстро оценить поведение стратегии, затем запускайте Monte Carlo и Sensitivity Analysis.
        """)
        return  # выходим после показа гайда

    # Sidebar: Simulation Parameters
    st.sidebar.header("Simulation Parameters")
    start_price_eth = st.sidebar.number_input("Start ETH Price", value=2000.0, help="Initial price of ETH in USD")
    start_price_btc = st.sidebar.number_input("Start BTC Price", value=30000.0, help="Initial price of BTC in USD")
    rho = st.sidebar.number_input("Correlation (rho)", min_value=-1.0, max_value=1.0, value=0.0, help="Correlation between ETH and BTC returns")
    vol_eth = st.sidebar.number_input("ETH Volatility (std dev)", value=0.01, help="Per-step std of ETH returns")
    vol_btc = st.sidebar.number_input("BTC Volatility (std dev)", value=0.015, help="Per-step std of BTC returns")
    trend_eth = st.sidebar.number_input("ETH Trend", value=0.0, help="Expected per-step drift of ETH")
    trend_btc = st.sidebar.number_input("BTC Trend", value=0.0, help="Expected per-step drift of BTC")
    n_steps = st.sidebar.number_input("Number of Steps", value=100, step=1, help="Total simulation steps")

    # Sidebar: Strategy Parameters
    st.sidebar.header("Strategy Parameters")
    epsilon_ticks = st.sidebar.number_input("Epsilon Ticks", value=30, step=1, help="Primary range half-width (ticks)")
    range_ticks = st.sidebar.number_input("Range Ticks", value=300, step=1, help="Secondary range half-width (ticks)")
    alpha = st.sidebar.number_input("Alpha (Liquidity Shift)", value=0.33, help="Rebalance weight between ranges")
    lambda_ = st.sidebar.number_input("Lambda (EWMA)", value=0.9, help="Decay factor for EWMA")
    initial_eth = st.sidebar.number_input("Initial ETH", value=1000.0, help="Starting ETH balance")
    initial_btc = st.sidebar.number_input("Initial BTC", value=20.0, help="Starting BTC balance")

    # Sidebar: Visualization Options
    st.sidebar.header("Visualization Options")
    show_ranges = st.sidebar.checkbox("Price & Strategy Ranges")
    show_actions = st.sidebar.checkbox("Ranges & Actions")
    show_vs_hodl = st.sidebar.checkbox("Strategy vs HODL")
    show_wallet = st.sidebar.checkbox("Normalized Wallet & Price")
    show_metrics = st.sidebar.checkbox("Show Metrics & Drawdown")
    monte_carlo = st.sidebar.checkbox("Run Monte Carlo Simulation")
    mc_runs = st.sidebar.number_input("Monte Carlo Runs", value=100, min_value=1, step=1)

    # Sidebar: Parameter Sensitivity Analysis
    st.sidebar.header("Parameter Sensitivity Analysis")
    sens = st.sidebar.checkbox("Run Sensitivity Analysis", help="Grid search over strategy params")
    eps_range = st.sidebar.slider("Epsilon Ticks range", 5, 100, (10, 50), step=5)
    alpha_range = st.sidebar.slider("Alpha range", 0.0, 1.0, (0.1, 0.5), step=0.1)
    lambda_range = st.sidebar.slider("Lambda range", 0.5, 1.0, (0.8, 0.95), step=0.05)
    sens_steps = st.sidebar.number_input("Grid size per dimension", value=5, min_value=2, step=1)

    # Run Simulation
    if st.sidebar.button("Run Simulation"):
        # Base simulation run
        df_prices = simulate_prices(
            start_price_eth=start_price_eth,
            start_price_btc=start_price_btc,
            rho=rho,
            sigma_eth=vol_eth,
            sigma_btc=vol_btc,
            trend_eth=trend_eth,
            trend_btc=trend_btc,
            T=int(n_steps)
        )
        prices_ratio = df_prices["ETH/BTC"].tolist()
        eth_prices = df_prices["ETH"].tolist()
        btc_prices = df_prices["BTC"].tolist()

        # Run strategy
        strategy = UniswapV4Strategy(epsilon_ticks, range_ticks, alpha, lambda_, initial_eth, initial_btc)
        collected, strat_obj, strat_usd, hodl_usd = run_simulation(
            prices_ratio, eth_prices, btc_prices, strategy, initial_eth, initial_btc
        )

        # Performance Metrics
        st.subheader("Performance Metrics")
        st.write(f"Final Strategy Value: **{strat_usd[-1]:.2f} USD**")
        st.write(f"Final HODL Value: **{hodl_usd[-1]:.2f} USD**")

        # Aggregated Metrics & Drawdown
        if show_metrics:
            returns = np.diff(strat_usd) / strat_usd[:-1]
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
            volatility = np.std(returns) * np.sqrt(252)
            cum_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cum_returns)
            drawdown = (cum_returns - running_max) / running_max
            max_dd = drawdown.min()
            st.subheader("Aggregated Metrics")
            st.table(pd.DataFrame({'Sharpe Ratio': [sharpe], 'Volatility': [volatility], 'Max Drawdown': [max_dd]}))
            st.subheader("Drawdown Curve")
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=collected["Time"][1:], y=drawdown, mode="lines",
                hovertemplate="Time: %{x}<br>Drawdown: %{y:.2%}<extra></extra>"
            ))
            fig_dd.update_layout(
                title="Drawdown Curve", xaxis_title="Time", yaxis_title="Drawdown",
                hovermode='x unified', height=500
            )
            st.plotly_chart(fig_dd, use_container_width=True)

        # Show collected data and standard plots
        st.subheader("Collected Data")
        st.dataframe(pd.DataFrame(collected))
        if show_ranges:
            st.subheader("Price & Strategy Ranges")
            st.plotly_chart(plot_ranges(collected), use_container_width=True)
        if show_actions:
            st.subheader("Ranges & Actions")
            st.plotly_chart(plot_combined_ranges_and_actions(collected, strat_obj), use_container_width=True)
        if show_vs_hodl:
            st.subheader("Strategy vs HODL")
            st.plotly_chart(plot_strategy_vs_hodl(strat_usd, hodl_usd), use_container_width=True)
        if show_wallet:
            st.subheader("Normalized Wallet & Price")
            st.plotly_chart(plot_wallet_and_price(collected), use_container_width=True)

        # Monte Carlo Simulation block
        if monte_carlo:
            st.subheader("Monte Carlo Simulation Results")
            all_strat, all_hodl = [], []
            for _ in range(mc_runs):
                df_mc = simulate_prices(
                    start_price_eth=start_price_eth,
                    start_price_btc=start_price_btc,
                    rho=rho,
                    sigma_eth=vol_eth,
                    sigma_btc=vol_btc,
                    trend_eth=trend_eth,
                    trend_btc=trend_btc,
                    T=int(n_steps)
                )
                prices_mc = df_mc["ETH/BTC"].tolist()
                eth_mc, btc_mc = df_mc["ETH"].tolist(), df_mc["BTC"].tolist()
                strat_mc = UniswapV4Strategy(epsilon_ticks, range_ticks, alpha, lambda_, initial_eth, initial_btc)  
                _, _, usd_mc, hodl_mc = run_simulation(prices_mc, eth_mc, btc_mc, strat_mc, initial_eth, initial_btc)
                all_strat.append(usd_mc)
                all_hodl.append(hodl_mc)
            arr_strat, arr_hodl = np.array(all_strat), np.array(all_hodl)
            steps = list(range(arr_strat.shape[1]))
            strat_q10, strat_med, strat_q90 = np.percentile(arr_strat, [10,50,90], axis=0)
            hodl_q10, hodl_med, hodl_q90 = np.percentile(arr_hodl, [10,50,90], axis=0)
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=steps, y=strat_q90, fill=None, name='Strat 90pct'))
            fig_mc.add_trace(go.Scatter(x=steps, y=strat_q10, fill='tonexty', name='Strat 10pct'))
            fig_mc.add_trace(go.Scatter(x=steps, y=strat_med, name='Strat Median', mode='lines'))
            fig_mc.add_trace(go.Scatter(x=steps, y=hodl_q90, fill=None, name='HODL 90pct', line=dict(color='orange')))
            fig_mc.add_trace(go.Scatter(x=steps, y=hodl_q10, fill='tonexty', name='HODL 10pct', line=dict(color='orange')))
            fig_mc.add_trace(go.Scatter(x=steps, y=hodl_med, name='HODL Median', mode='lines', line=dict(color='orange')))
            fig_mc.update_layout(
                title='Monte Carlo: Strategy vs HODL Quantiles', xaxis_title='Step', yaxis_title='Value (USD)',
                hovermode='x unified', height=600
            )
            st.plotly_chart(fig_mc, use_container_width=True)
            final = pd.DataFrame({
                'Metric': ['10th_pct','Median','90th_pct'],
                'Strategy': [strat_q10[-1], strat_med[-1], strat_q90[-1]],
                'HODL': [hodl_q10[-1], hodl_med[-1], hodl_q90[-1]]
            })
            st.subheader('Monte Carlo Final Value Summary')
            st.table(final)

        # Sensitivity Analysis block
        if sens:
            st.subheader("Sensitivity Analysis: Sharpe Heatmap")
            eps_vals = np.linspace(eps_range[0], eps_range[1], sens_steps, dtype=int)
            alpha_vals = np.linspace(alpha_range[0], alpha_range[1], sens_steps)
            lambda_vals = np.linspace(lambda_range[0], lambda_range[1], sens_steps)
            results = []
            for eps in eps_vals:
                for a in alpha_vals:
                    for lam in lambda_vals:
                        strat_s = UniswapV4Strategy(eps, range_ticks, a, lam, initial_eth, initial_btc)
                        _, _, strat_usd_s, _ = run_simulation(prices_ratio, eth_prices, btc_prices, strat_s, initial_eth, initial_btc)
                        rets = np.diff(strat_usd_s) / strat_usd_s[:-1]
                        sharpe = np.mean(rets) / np.std(rets) * np.sqrt(252)
                        results.append({'epsilon': eps, 'alpha': a, 'lambda': lam, 'sharpe': sharpe})
            df_sens = pd.DataFrame(results)
            lam_mid = lambda_vals[len(lambda_vals)//2]
            # Use pivot_table to avoid duplicate index errors
            heat = df_sens[df_sens['lambda'] == lam_mid].pivot_table(
                index='alpha', columns='epsilon', values='sharpe'
            )
            fig_heat = px.imshow(
                heat,
                labels=dict(x='Epsilon', y='Alpha', color='Sharpe'),
                aspect='auto'
            )
            st.plotly_chart(fig_heat, use_container_width=True)
            st.write(f"Fixed Lambda (EWMA) = {lam_mid:.2f}")

if __name__ == '__main__':
    main()