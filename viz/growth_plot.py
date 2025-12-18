import plotly.graph_objects as go

def growth_line_plot(growth_payload):
    x = growth_payload.get("timeline_weeks", [])
    y = growth_payload.get("skill_index", [])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="Skill Index"))
    fig.update_layout(title="Skill Growth Over Time", xaxis_title="Weeks", yaxis_title="Skill Index (0–100)")
    return fig
