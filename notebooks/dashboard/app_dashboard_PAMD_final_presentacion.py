import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Observatorio | Contratación Estatal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Busca los CSV junto al archivo app.py para facilitar el traslado del proyecto.
BASE_APP = Path(__file__).resolve().parent
RUTA = BASE_APP / "datos"
if not RUTA.exists():
    RUTA = Path("/home/jovyan/work/dashboard/datos")  # compatibilidad con el entorno original
NAVY, CYAN, GOLD = "#10243A", "#39B8C8", "#F2B84B"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp{background:#0B1724;}
[data-testid="stSidebar"]{background:#10243A;border-right:1px solid #29465F;}
[data-testid="stSidebar"] *{color:#EAF2F8;}
.block-container{padding-top:1.4rem;padding-bottom:2rem;max-width:1450px;}
h1,h2,h3{font-family:'Manrope',sans-serif!important;color:#F4F8FC!important;}
.hero{background:linear-gradient(115deg,#163653 0%,#1D5574 58%,#167A86 100%);
border:1px solid #3A7187;border-radius:22px;padding:27px 31px;margin-bottom:22px;color:white;}
.kicker{color:#BDECF0;font-size:.76rem;letter-spacing:.14em;font-weight:700;text-transform:uppercase;}
.hero-title{color:white;font-family:'Manrope',sans-serif;font-size:2rem;line-height:1.15;font-weight:800;margin:8px 0;}
.hero-sub{color:#D9EAF2;font-size:1rem;}
.metric-card{background:linear-gradient(145deg,#172E45,#12263A);border:1px solid #29465F;
border-radius:16px;padding:17px 19px;min-height:116px;}
.metric-label{color:#AFC2D3;font-size:.78rem;font-weight:700;}
.metric-value{color:white;font-family:'Manrope',sans-serif;font-size:1.55rem;font-weight:800;margin-top:9px;}
.metric-note{color:#7ED5D8;font-size:.74rem;margin-top:4px;}
.info-strip{background:#142B40;border-left:4px solid #39B8C8;border-radius:9px;padding:12px 15px;color:#D7E5EF;font-size:.85rem;margin:12px 0 18px;}
.small-note{color:#AFC2D3;font-size:.82rem;}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_csv(name):
    return pd.read_csv(RUTA / name)

try:
    dep = load_csv("departamentos.csv")
    ent = load_csv("entidades.csv")
    con = load_csv("contratistas.csv")
    anual = load_csv("evolucion_anual.csv")
except Exception as e:
    st.error("No fue posible cargar los cuatro CSV principales desde dashboard/datos.")
    st.exception(e)
    st.stop()

# Numeric conversion for display
for df, cols in [
    (dep, ["cantidad_contratos", "valor_total"]),
    (ent, ["cantidad_contratos", "valor_total"]),
    (con, ["cantidad_contratos", "valor_total"]),
    (anual, ["anio", "valor_total"])
]:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

# Required schema
schemas = [
    (dep, ["departamento", "cantidad_contratos", "valor_total"], "departamentos.csv"),
    (ent, ["entidad", "cantidad_contratos", "valor_total"], "entidades.csv"),
    (con, ["contratista", "cantidad_contratos", "valor_total"], "contratistas.csv"),
    (anual, ["anio", "valor_total"], "evolucion_anual.csv")
]
for df, cols, name in schemas:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        st.error(f"{name}: faltan columnas {missing}")
        st.stop()

def nfmt(x):
    try: return f"{int(round(float(x))):,}".replace(",", ".")
    except: return "—"

def es_numero(x, decimales=2):
    try:
        s = f"{float(x):,.{decimales}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"

def billones(x):
    try:
        return f"${es_numero(float(x)/1e12, 2)} billones COP"
    except Exception:
        return "—"

def valor_tabla_cop(x):
    try:
        return f"${es_numero(float(x)/1e12, 2)} billones"
    except Exception:
        return "—"

def fig_style(fig, height=400):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans",color="#DCE8F1",size=12),
        margin=dict(l=10,r=18,t=52,b=18),height=height,
        xaxis=dict(showgrid=True,gridcolor="rgba(160,185,205,.13)",zeroline=False),
        yaxis=dict(showgrid=False,zeroline=False)
    )
    return fig

# Sidebar filters
st.sidebar.markdown("## 🎛️ Panel de exploración")
st.sidebar.caption("Filtros sobre agregaciones precalculadas.")
dep_names = sorted(dep["departamento"].dropna().astype(str).unique())
sel_dep = st.sidebar.selectbox("Territorio", ["Todos los departamentos"] + dep_names)
anual["anio"] = pd.to_numeric(anual["anio"], errors="coerce")
years = sorted(anual["anio"].dropna().astype(int).unique())
if years:
    rango_anios = st.sidebar.slider(
        "Rango de años",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
        step=1
    )
    sel_years = [y for y in years if rango_anios[0] <= y <= rango_anios[1]]
else:
    sel_years = []
ent_names = sorted(ent["entidad"].dropna().astype(str).unique())
sel_ent = st.sidebar.selectbox("Entidad contratante", ["Todas las entidades"] + ent_names)
st.sidebar.markdown("---")
st.sidebar.caption("Territorio filtra indicadores territoriales; años filtra la serie anual; entidad filtra la consulta institucional. No son filtros cruzados.")

dep_view = dep.copy()
if sel_dep != "Todos los departamentos":
    dep_view = dep_view[dep_view.departamento.astype(str) == sel_dep]
anual_view = anual[anual.anio.isin(sel_years)].sort_values("anio")
ent_view = ent.copy()
if sel_ent != "Todas las entidades":
    ent_view = ent_view[ent_view.entidad.astype(str) == sel_ent]

# Hero
st.markdown("""
<div class="hero">
 <div class="kicker">SECOP II · ANALÍTICA DE DATOS PÚBLICOS</div>
 <div class="hero-title">Observatorio de Contratación Estatal</div>
 <div class="hero-sub">Auditoría y monitoreo de la contratación pública en Colombia · Proyecto PAMD</div>
</div>""", unsafe_allow_html=True)


# CONTEXTO, PROBLEMA Y OBJETIVOS DEL PROYECTO

st.divider()
st.header("Contexto y planteamiento del problema")

st.markdown("""
La contratación estatal en Colombia genera grandes volúmenes de información
que deben organizarse y analizarse para facilitar el seguimiento de los
recursos públicos.

Sin un procesamiento adecuado, resulta difícil identificar dónde se
concentran los contratos, cuáles son las entidades y los proveedores con
mayor participación y cómo cambia la contratación a través del tiempo.

**Problema central**

¿Cómo diseñar un flujo de procesamiento masivo de datos que permita integrar,
procesar, monitorear y analizar información de contratación estatal,
manteniendo la consistencia de los resultados y facilitando su consulta?
""")

st.markdown("### Objetivo general")

st.info("""
Construir un flujo de procesamiento distribuido para analizar información
de contratación pública de SECOP II, simular la llegada periódica de contratos,
evaluar la consistencia de los resultados y presentar indicadores mediante
un dashboard interactivo.
""")

st.markdown("### Objetivos específicos")

obj1, obj2 = st.columns(2)

with obj1:
    st.markdown("""
    **1. Integración y preparación de datos**

    Integrar, limpiar y transformar los registros de contratación,
    identificando las variables necesarias para el análisis y almacenando
    los resultados procesados.

    **2. Flujo continuo y ventanas temporales**

    Simular la llegada periódica de registros y calcular indicadores
    por ventanas mensuales, considerando los registros correspondientes
    a cada periodo.
    """)

with obj2:
    st.markdown("""
    **3. Resiliencia e idempotencia**

    Comprobar mediante pruebas controladas que el reprocesamiento de lotes
    y la llegada tardía de registros no generen duplicados.

    **4. Visualización interactiva**

    Construir un dashboard que permita explorar la contratación por
    territorio, periodo, entidad contratante y contratista.
    """)

st.markdown("### Arquitectura de la solución")

arq1, arq2, arq3, arq4 = st.columns(4)

arq1.markdown("**SECOP II**")
arq1.caption("Fuente de información")

arq2.markdown("**Apache Spark**")
arq2.caption("Limpieza y procesamiento distribuido")

arq3.markdown("**MinIO + Parquet**")
arq3.caption("Almacenamiento de resultados")

arq4.markdown("**Streamlit + Plotly**")
arq4.caption("Dashboard y visualización")

st.markdown("### Alcance del proyecto")

st.markdown("""
- Se procesó información histórica de contratación pública.
- Se simularon ventanas mensuales; no se implementó una conexión de ingesta en vivo.
- Se realizaron pruebas controladas de reprocesamiento e incorporación de registros tardíos.
- Se construyeron indicadores territoriales, temporales e institucionales.
- Los valores monetarios son preliminares y requieren validación de los formatos originales y de los registros atípicos.
""")

st.divider()


# ==========================================================
# ACTORES QUE PUEDEN UTILIZAR EL OBSERVATORIO
# ==========================================================

st.markdown("---")

st.markdown("""
<h2 style="color:#F1F5F9; margin-bottom:8px;">
    ¿A quién le sirve este observatorio?
</h2>

<p style="color:#94A3B8; font-size:15px; margin-bottom:20px;">
    Nuestra herramienta facilita el seguimiento y análisis
    de la contratación pública para diferentes actores.
</p>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

actores = [
    {
        "col": col1,
        "icono": "🏛️",
        "nombre": "Entidades públicas",
        "descripcion": "Consultar sus indicadores, revisar sus contratos y analizar su comportamiento contractual."
    },
    {
        "col": col2,
        "icono": "🔎",
        "nombre": "Organismos de control",
        "descripcion": "Identificar concentraciones de recursos y detectar situaciones que podrían requerir revisión."
    },
    {
        "col": col3,
        "icono": "🤝",
        "nombre": "Veedurías ciudadanas",
        "descripcion": "Consultar información pública y apoyar el seguimiento ciudadano a la contratación."
    },
    {
        "col": col4,
        "icono": "📊",
        "nombre": "Investigadores y analistas",
        "descripcion": "Estudiar tendencias y patrones territoriales, temporales e institucionales."
    }
]

for actor in actores:
    with actor["col"]:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, #172B40, #102033);
            border: 1px solid #29445E;
            border-radius: 14px;
            padding: 18px;
            min-height: 220px;
        ">
            <div style="font-size:30px; margin-bottom:12px;">
                {actor["icono"]}
            </div>
            <div style="
                color:#7DD3FC;
                font-size:16px;
                font-weight:700;
                margin-bottom:12px;
            ">
                {actor["nombre"]}
            </div>
            <div style="
                color:#CBD5E1;
                font-size:13px;
                line-height:1.6;
            ">
                {actor["descripcion"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<p style="
    color:#94A3B8;
    font-size:13px;
    margin-top:15px;
    font-style:italic;
">
    El observatorio es una herramienta exploratoria de apoyo.
    No reemplaza una auditoría oficial.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# KPI values
contracts = dep_view.cantidad_contratos.fillna(0).sum()
value = dep_view.valor_total.fillna(0).sum()
entities_n = ent.entidad.nunique()
a,b,c = st.columns(3)
for col, label, value_text, note in [
    (a,"CONTRATOS · ÁMBITO TERRITORIAL",nfmt(contracts),"Según selección territorial"),
    (b,"VALOR CONTRATADO · TERRITORIAL",billones(value),"Agregado preliminar en pesos colombianos"),
    (c,"ENTIDADES IDENTIFICADAS",nfmt(entities_n),"Universo general de entidades")
]:
    col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value_text}</div><div class="metric-note">{note}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="info-strip">Nota de lectura: las cifras monetarias son agregados exploratorios y requieren validar los formatos originales. Los filtros operan sobre agregaciones independientes y no representan un cruce simultáneo de todas las dimensiones.</div>',unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5 = st.tabs(["🌎 Territorio","📈 Evolución anual","🗓️ Ventanas mensuales","🏛️ Entidades","🤝 Contratistas"])

with tab1:
    st.subheader("Concentración territorial")
    st.caption("Departamentos ordenados por valor agregado. Los registros sin ubicación se muestran aparte, no dentro del ranking.")
    dep_plot = dep_view.copy()
    dep_plot["departamento"] = dep_plot.departamento.fillna("").astype(str).str.strip()
    dep_plot.loc[dep_plot.departamento.str.lower().isin(["no definido","sin definir","nan",""]), "departamento"] = "Sin departamento"
    dep_plot = dep_plot[dep_plot.departamento != "Sin departamento"]
    if not dep_plot.empty:
        top = dep_plot.nlargest(12,"valor_total").sort_values("valor_total")
        top["valor_billones"] = top["valor_total"] / 1e12
        fig = px.bar(top,x="valor_billones",y="departamento",orientation="h",
                     color="valor_billones",color_continuous_scale=["#245B7A",CYAN,GOLD],
                     labels={"valor_billones":"Valor contratado (billones de COP)","departamento":""})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.2f} billones COP<extra></extra>")
        fig.update_layout(coloraxis_showscale=False,xaxis_title="Billones de COP")
        st.plotly_chart(fig_style(fig,460),use_container_width=True)

        tabla_dep = top.sort_values("valor_total",ascending=False).copy()
        tabla_dep["Contratos"] = tabla_dep["cantidad_contratos"].apply(nfmt)
        tabla_dep["Valor contratado"] = tabla_dep["valor_total"].apply(valor_tabla_cop)
        st.dataframe(tabla_dep[["departamento","Contratos","Valor contratado"]].rename(
            columns={"departamento":"Departamento"}),use_container_width=True,hide_index=True)
        sin_dep = dep_view[dep_view.departamento.fillna("").astype(str).str.strip().str.lower().isin(
            ["no definido","sin definir","nan",""])]
        if not sin_dep.empty:
            st.caption(f"Registros sin departamento identificado: {nfmt(sin_dep.cantidad_contratos.sum())} contratos. Se excluyen del ranking territorial.")
    else:
        st.info("No hay datos para esta selección.")

with tab2:
    st.subheader("Evolución anual del valor contratado")
    st.caption("Valores expresados en billones de pesos colombianos. 2026 es un año parcial y no es directamente comparable con años completos.")
    if not anual_view.empty:
        av = anual_view.copy()
        av["valor_billones"] = av.valor_total/1e12
        complete = av[av.anio < 2026]
        partial = av[av.anio >= 2025]
        fig = go.Figure()
        if not complete.empty:
            fig.add_trace(go.Scatter(
                x=complete.anio, y=complete.valor_billones, mode="lines+markers",
                name="Años completos", line=dict(color=CYAN,width=3),
                marker=dict(size=8,color=CYAN),
                hovertemplate="<b>%{x:.0f}</b><br>%{y:.2f} billones COP<extra></extra>"
            ))
        if 2026 in av.anio.values:
            # Segmento discontinuo para señalar que 2026 es parcial.
            segment = av[av.anio.isin([2025, 2026])]
            if not segment.empty:
                fig.add_trace(go.Scatter(
                    x=segment.anio, y=segment.valor_billones, mode="lines+markers",
                    name="Tramo con 2026 parcial", line=dict(color=GOLD,width=3,dash="dash"),
                    marker=dict(size=10,color=GOLD,symbol="diamond"),
                    hovertemplate="<b>%{x:.0f}</b><br>%{y:.2f} billones COP<extra></extra>"
                ))
                row = av[av.anio == 2026].iloc[0]
                fig.add_annotation(x=2026,y=row.valor_billones,text="2026 · parcial",
                                   showarrow=True,arrowhead=2,ax=-45,ay=-38,
                                   font=dict(color=GOLD,size=12))
        fig.update_layout(yaxis_title="Billones de COP",xaxis_title="Año")
        st.plotly_chart(fig_style(fig,430),use_container_width=True)
        tabla_anual = av[["anio","valor_billones"]].copy()
        tabla_anual["Valor contratado"] = tabla_anual["valor_billones"].apply(lambda x: f"${es_numero(x,2)} billones")
        tabla_anual["Periodo"] = tabla_anual["anio"].apply(lambda y: "Parcial" if int(y)==2026 else "Año del conjunto")
        st.dataframe(tabla_anual.rename(columns={"anio":"Año"})[["Año","Valor contratado","Periodo"]],
                     use_container_width=True,hide_index=True)
    else:
        st.info("Selecciona un rango de años.")

with tab3:
    st.subheader("Ventanas mensuales de procesamiento")
    st.caption("Esta vista representa los lotes mensuales simulados durante el procesamiento histórico.")
    monthly_path = RUTA / "flujo_mensual.csv"
    if monthly_path.exists():
        mon = pd.read_csv(monthly_path)
        # Expected normalized export columns. Export them from Spark in the notebook.
        required_month = ["mes","contratos_recibidos"]
        missing = [x for x in required_month if x not in mon.columns]
        if missing:
            st.error(f"flujo_mensual.csv requiere estas columnas: {missing}. Consulta la guía de exportación.")
        else:
            mon["mes"] = pd.to_datetime(mon["mes"],errors="coerce")
            mon["contratos_recibidos"] = pd.to_numeric(mon["contratos_recibidos"],errors="coerce")
            mon = mon.dropna(subset=["mes"]).sort_values("mes")
            if "valor_normal" in mon.columns:
                mon["valor_normal"] = pd.to_numeric(mon["valor_normal"],errors="coerce")
            fig = px.bar(mon,x="mes",y="contratos_recibidos",labels={"mes":"Mes","contratos_recibidos":"Contratos recibidos"})
            fig.update_traces(marker_color=CYAN,hovertemplate="%{x|%Y-%m}<br>%{y:,.0f} contratos<extra></extra>")
            st.plotly_chart(fig_style(fig,420),use_container_width=True)
            if "valor_normal" in mon.columns:
                mon["valor_billones"] = mon.valor_normal/1e12
                fig2 = px.line(mon,x="mes",y="valor_billones",markers=True,
                               labels={"mes":"Mes","valor_billones":"Billones de COP"})
                fig2.update_traces(line=dict(color=GOLD,width=2),marker=dict(size=6),
                                   hovertemplate="%{x|%Y-%m}<br>%{y:,.2f} billones COP<extra></extra>")
                st.plotly_chart(fig_style(fig2,370),use_container_width=True)
            st.dataframe(mon,use_container_width=True,hide_index=True)
    else:
        st.warning("La vista mensual está preparada, pero aún falta exportar flujo_mensual.csv desde los resultados mensuales de MinIO. No se generan ni se inventan datos mensuales en el dashboard.")
        st.markdown("""
        **Columnas requeridas para el CSV mensual:**
        - `mes`: fecha del mes en formato `YYYY-MM-01`.
        - `contratos_recibidos`: cantidad de contratos del lote.
        - `valor_normal` (opcional): suma de valores clasificados como normales.

        Cuando se exporte este archivo a `dashboard/datos/`, la gráfica mensual aparecerá automáticamente.
        """)

with tab4:
    st.subheader("Entidades contratantes")
    st.caption("Top 15 por valor agregado o consulta individual.")
    table_ent = ent_view.nlargest(15,"valor_total") if sel_ent == "Todas las entidades" else ent_view
    table_ent = table_ent.sort_values("valor_total",ascending=False).copy()
    table_ent["Contratos"] = table_ent["cantidad_contratos"].apply(nfmt)
    table_ent["Valor contratado"] = table_ent["valor_total"].apply(valor_tabla_cop)
    st.dataframe(table_ent[["entidad","Contratos","Valor contratado"]].rename(
        columns={"entidad":"Entidad"}),use_container_width=True,hide_index=True)
    st.metric("Contratos en la consulta",nfmt(ent_view.cantidad_contratos.fillna(0).sum()))
    st.metric("Valor agregado preliminar",billones(ent_view.valor_total.fillna(0).sum()))

with tab5:
    st.subheader("Principales contratistas")
    st.caption("Top 10 por valor agregado. Se excluyen registros sin identificación del ranking visible.")
    con_view = con[con.contratista.fillna("").astype(str).str.strip().str.lower() != "sin descripcion"].copy()
    top_con = con_view.nlargest(10,"valor_total").copy()
    if not top_con.empty:
        top_con["valor_billones"] = top_con["valor_total"] / 1e12
        chart_con = top_con.sort_values("valor_billones",ascending=True)
        fig = px.bar(chart_con,x="valor_billones",y="contratista",orientation="h",
                     color="valor_billones",color_continuous_scale=["#245B7A",CYAN,GOLD],
                     labels={"valor_billones":"Valor agregado (billones de COP)","contratista":""})
        fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.2f} billones COP<extra></extra>")
        fig.update_layout(coloraxis_showscale=False,xaxis_title="Billones de COP")
        st.plotly_chart(fig_style(fig,470),use_container_width=True)
        top_con["Contratos"] = top_con["cantidad_contratos"].apply(nfmt)
        top_con["Valor contratado"] = top_con["valor_total"].apply(valor_tabla_cop)
        st.dataframe(top_con[["contratista","Contratos","Valor contratado"]].rename(
            columns={"contratista":"Contratista"}),use_container_width=True,hide_index=True)
    st.caption("El ranking identifica proveedores registrados como contratistas en SECOP II; pueden aparecer entidades financieras u otros tipos de proveedores. No debe interpretarse como un ranking exclusivo de empresas constructoras.")

st.markdown("---")
st.subheader("Metodología y alcance")
m1,m2=st.columns(2)
with m1:
    st.markdown("**Arquitectura**\n- SECOP II: fuente de datos.\n- Apache Spark: limpieza y agregación distribuida.\n- MinIO: almacenamiento de objetos y resultados Parquet.\n- Streamlit, Pandas y Plotly: visualización.")
with m2:
    st.markdown("**Alcance y limitaciones**\n- Ventanas mensuales simuladas sobre datos históricos; no es ingesta en vivo.\n- Los registros sin fecha interpretable no participan en la serie temporal.\n- Los valores monetarios requieren validación de separadores y atípicos.\n- Los filtros consultan agregaciones independientes.")
st.caption("Fuente: SECOP II · Proyecto PAMD · Indicadores procesados con Apache Spark y almacenados en MinIO.")
