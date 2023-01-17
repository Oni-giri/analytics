import streamlit as st
from web3 import Web3
import requests
import json
import locale
from datetime import datetime
locale.setlocale(locale.LC_ALL, '')

w3 = Web3(Web3.HTTPProvider(
    "https://winter-empty-river.discover.quiknode.pro/9adcd34a82a8c99bc85a15b8131afc1b991c4116/"))
assert w3.isConnected()

# load contracts


def contract(address):
    abi = requests.get(
        f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey=Y7R1WPVCDKGCPI4PCUDKQKJGVIBR3ZPNN6").content
    return w3.eth.contract(address=address, abi=json.loads(abi)["result"])

# Display numbers


def pretty(number, decimals, ether):
    if ether:
        number = number/1e18

    if decimals:
        return "{:,}".format(round(number, decimals))
    else:
        return "{:,}".format(round(number))

# Coingecko


def cg_data(id, keys):
    data = requests.get(
        f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={id}&order=market_cap_desc&per_page=100&page=1&sparkline=false").content
    data = json.loads(data)[0]
    data_dict = {}
    for key in keys:
        data_dict[key] = data[key]
    return data_dict


def get_avg_bribe():
    data = requests.post("https://api.llama.airforce/bribes",
                         json={'platform': "hh", 'protocol': "aura-bal"}).json()
    data = data["epoch"]
    total_bribes = 0
    for i in range(0, len(data["bribes"])):
        total_bribes += data["bribes"][i]["amountDollars"]

    total_bribed = 0
    for i in data["bribed"]:
        total_bribed += data["bribed"][i]

    return total_bribes/total_bribed


# veBal
veBal_address = "0xC128a9954e6c874eA3d62ce62B468bA073093F25"
veBal = contract(veBal_address)
veBal_2022 = 145000
veBal_2023 = 121929
veBal_ts = veBal.caller.totalSupply()

# Bal
bal_cg = cg_data("balancer", ["current_price", "price_change_percentage_24h"])
bal_price = bal_cg["current_price"]
bal_per_week = veBal_2022 if datetime.now().year == 2022 else veBal_2023
bal_value_per_week = bal_per_week*bal_price

# veAura
veAura_address = "0x3Fa73f1E5d8A792C80F426fc8F84FBF7Ce9bBCAC"
veAura = contract(veAura_address)
veAura_ts = veAura.caller.totalSupply()

# Aura
aura_address = "0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF"
aura_cg = cg_data("aura-finance", ["current_price", "price_change_percentage_24h"])
aura_price = aura_cg["current_price"]
aura = contract(aura_address)
aura_ts = aura.caller.totalSupply()
aura_per_bal = ((500-(aura_ts/1e18-50000000)/100000)*2.5+700)/500

# AuraBal
auraBal_address = "0x616e8BfA43F920657B3497DBf40D6b1A02D4608d"
auraBal = contract(auraBal_address)
auraBal_ts = auraBal.caller.totalSupply()
veAuraBal_per_veAura = auraBal_ts/veAura_ts

# bribes
avg_bribe = 0.09  # TODO: how to get this on-chain?

avg_bribe = get_avg_bribe()
bal_p_week_p_veAura = 1e18*bal_per_week*(auraBal_ts/veBal_ts/veAura_ts)
bal_v_p_veAura_p_week = bal_p_week_p_veAura*bal_price
aura_v_p_veAura_p_week = bal_p_week_p_veAura*aura_price*aura_per_bal*0.75 # 25%% fee
total_per_cycle = (bal_v_p_veAura_p_week*(1-0.25) + aura_v_p_veAura_p_week)*2
bribe_p_y_p_aura = avg_bribe*28
renting_rate = bribe_p_y_p_aura/aura_price

eth_cg = cg_data("ethereum", ["current_price", "price_change_percentage_24h"])
eth_price = eth_cg["current_price"]


### App ####

st.title("Aura metrics for Astrolab.fi", anchor="aura-metrics")

col11, col21, col31 = st.columns(3)

with col11:
    st.metric("Aura price", f"${aura_price}",
              f"{pretty(aura_cg['price_change_percentage_24h'], 2, False)}%/24h")


with col21:
    st.metric("Bal price", f"${bal_price}",
              f"{pretty(bal_cg['price_change_percentage_24h'], 2, False)}%/24h")

with col31:
    st.metric("Eth price", f"${eth_price}",
              f"{pretty(eth_cg['price_change_percentage_24h'], 2, False)}%/24h")

# Emissions and bribes --------------
st.subheader("Emissions and bribes")
col12, col22, col23 = st.columns(3)

with col12:
    st.metric("veBal supply", pretty(veBal.caller.totalSupply(), 0, True))
    st.metric("Bal emission/week/veAura",
              f"${pretty(bal_v_p_veAura_p_week, 3, False)}")
    st.metric("Total incentive/veAura/2weeks",
              pretty(total_per_cycle, 3, False))
    st.metric("Aura yield increase (inc 25% fees)",
              f"{pretty(75*aura_per_bal * aura_price / bal_price - 25, 2, False)}%")

with col22:
    st.metric("Bal emissions/week", pretty(bal_per_week, 0, False))
    st.metric("Aura emission/week/veAura",
              f"${pretty(aura_v_p_veAura_p_week, 3, False)}")
    st.metric("Bribe APR for briber",
              f"{pretty(100*total_per_cycle/avg_bribe, 2, False)}%")
    st.metric("Aura yield increase (inc 50% fees)",
              f"{pretty(50*aura_per_bal * aura_price / bal_price - 50, 2, False)}%")

with col23:
    st.metric("Bal emissions value/year",
              f"${pretty(bal_value_per_week*56, 0, False)}")
    st.metric("Current avg bribe/veAura", f"${pretty(avg_bribe, 2, False)}")
    st.metric("Aura emission per Bal farmed (raw)", pretty(aura_per_bal, 2, False))
    st.metric("Aura yield increase (inc 33% fees)",
              f"{pretty(66*aura_per_bal * aura_price / bal_price - 33, 2, False)}%")


# Cost of yield -------------------------------------
st.subheader("Cost of yield")
col15, col25, col35 = st.columns(3)
with col15:
    st.metric("veAura for 10\% APR on 1M$", pretty(
        100000/(total_per_cycle*26), 0, False))
    st.metric("2% cap/1M$ TVL APR",
              f"{pretty(100*(veBal_ts * 0.02 / veAuraBal_per_veAura) * (total_per_cycle * 26)/ 1_000_000, 0 ,True) }%")

with col25:
    st.metric("veAura for 10\%/1M$",
              f"${pretty(aura_price * 100000/(total_per_cycle * 26), 0, False)}")
    st.metric("2% cap bribe cost/2weeks",
              f"${ pretty(avg_bribe * veBal_ts * 0.02 / veAuraBal_per_veAura, 0, True)}")

with col35:
    st.metric("veAura needed for 2\% of bal", pretty(
        veBal_ts * 0.02 / veAuraBal_per_veAura, 0, True))
    st.metric("2% cap bribe cost/year",
              f"${ pretty(avg_bribe * 26 * veBal_ts * 0.02 / veAuraBal_per_veAura, 0, True) }")

# Ownership
st.subheader("Ownership or rent?")

col13, col23, col33 = st.columns(3)
with col13:
    st.metric("Annual bribe cost per veAura",
              f"${pretty(avg_bribe*26, 3 , False)}")

with col23:
    st.metric("Yearly bribes/cost of Aura", f"{pretty(renting_rate*100, 1, False)}%")
